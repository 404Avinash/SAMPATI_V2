"""Supervised Fraud Model Training & Evaluation Pipeline for SAMPATI V2.

Ingests and cleans public PaySim fraud dataset (or generates high-fidelity benchmark data),
extracts aligned 13-dimensional features, trains the supervised classifier,
evaluates precision/recall/F1 on a held-out test split, computes False Negative reduction
vs the unsupervised Isolation Forest baseline, and serializes the model artifact.

Usage:
    ./.venv/bin/python app/engine/train_supervised.py [--data-path PATH] [--n-samples 5000]
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure workspace root is on sys.path for direct CLI execution
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import numpy as np

from app.engine.isolation_forest import get_isolation_forest
from app.engine.supervised_classifier import (
    PureNumpySupervisedClassifier,
    UpiSupervisedClassifier,
    generate_synthetic_supervised_data,
)


# ---------------------------------------------------------------------------
# Data Generation & Ingestion Helpers
# ---------------------------------------------------------------------------

def generate_paysim_benchmark_csv(
    output_path: str = "data/paysim_benchmark.csv",
    n_samples: int = 5000,
    fraud_ratio: float = 0.15,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate high-fidelity benchmark dataset in PaySim CSV format."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    rng = np.random.default_rng(random_state)

    X_mat, y_vec = generate_synthetic_supervised_data(
        n_samples=n_samples,
        fraud_ratio=fraud_ratio,
        random_state=random_state,
    )

    headers = [
        "step",
        "type",
        "amount",
        "nameOrig",
        "oldbalanceOrg",
        "newbalanceOrig",
        "nameDest",
        "oldbalanceDest",
        "newbalanceDest",
        "isFraud",
        "isFlaggedFraud",
        # Aligned telemetry columns
        "payer_account_age_days",
        "payee_vpa_age_days",
        "payee_is_new_for_payer",
        "payer_velocity_count_30m",
        "payer_velocity_amount_30m",
        "device_vpa_count",
        "dmv_score",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for i in range(len(y_vec)):
            feat = X_mat[i]
            amount = float(feat[0])
            hr = float(feat[2])
            step = int(rng.integers(1, 30) * 24 + int(hr))
            is_fraud = int(y_vec[i])

            payer_age = float(feat[6])
            payee_age = float(feat[7])
            new_payee = int(feat[8])
            vel_cnt = float(feat[9])
            vel_amt = float(feat[10])
            dev_cnt = float(feat[11])
            dmv = float(feat[12])

            if is_fraud:
                txn_type = rng.choice(["TRANSFER", "CASH_OUT"])
                old_bal_org = float(amount * rng.uniform(1.0, 1.2))
                new_bal_org = 0.0  # Drained
                old_bal_dest = 0.0
                new_bal_dest = float(amount)
                is_flagged = 1 if amount > 200000.0 else 0
            else:
                txn_type = rng.choice(["PAYMENT", "TRANSFER", "CASH_IN", "DEBIT"])
                old_bal_org = float(amount * rng.uniform(1.5, 10.0))
                new_bal_org = max(0.0, old_bal_org - amount)
                old_bal_dest = float(rng.uniform(100.0, 50000.0))
                new_bal_dest = old_bal_dest + amount
                is_flagged = 0

            orig_id = f"C{rng.integers(1000000, 9999999)}"
            dest_id = f"M{rng.integers(1000000, 9999999)}" if txn_type == "PAYMENT" else f"C{rng.integers(1000000, 9999999)}"

            row = [
                step,
                txn_type,
                f"{amount:.2f}",
                orig_id,
                f"{old_bal_org:.2f}",
                f"{new_bal_org:.2f}",
                dest_id,
                f"{old_bal_dest:.2f}",
                f"{new_bal_dest:.2f}",
                is_fraud,
                is_flagged,
                f"{payer_age:.1f}",
                f"{payee_age:.1f}",
                new_payee,
                f"{vel_cnt:.1f}",
                f"{vel_amt:.2f}",
                f"{dev_cnt:.1f}",
                f"{dmv:.2f}",
            ]
            writer.writerow(row)

    return X_mat, y_vec


def load_and_clean_dataset(file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Ingest and clean dataset from CSV file into feature matrix X and labels y."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Check if enriched telemetry columns exist in CSV
        has_enriched = all(
            k in fieldnames
            for k in [
                "payer_account_age_days",
                "payee_vpa_age_days",
                "payee_is_new_for_payer",
                "payer_velocity_count_30m",
                "payer_velocity_amount_30m",
                "device_vpa_count",
                "dmv_score",
            ]
        )

        X_rows: List[List[float]] = []
        y_rows: List[int] = []

        for row in reader:
            is_fraud = int(row.get("isFraud", row.get("is_fraud", 0)))
            amount = float(row.get("amount", 0.0))
            log_amt = math.log1p(max(0.0, amount))

            # Step / Time of day
            step = float(row.get("step", 14.0))
            hr = float(step % 24.0)
            hr_sin = math.sin(2.0 * math.pi * hr / 24.0)
            hr_cos = math.cos(2.0 * math.pi * hr / 24.0)
            is_night = 1.0 if (hr < 5.0 or hr >= 23.0) else 0.0

            if has_enriched:
                payer_age = float(row["payer_account_age_days"])
                payee_age = float(row["payee_vpa_age_days"])
                new_payee = float(row["payee_is_new_for_payer"])
                vel_cnt = float(row["payer_velocity_count_30m"])
                vel_amt = float(row["payer_velocity_amount_30m"])
                dev_cnt = float(row["device_vpa_count"])
                dmv = float(row["dmv_score"])
            else:
                # Derive signals from raw PaySim schema
                old_org = float(row.get("oldbalanceOrg", 0.0))
                new_org = float(row.get("newbalanceOrig", 0.0))
                txn_type = str(row.get("type", "TRANSFER")).upper()

                # Balance depletion / DMV signal
                if old_org > 0 and new_org == 0 and txn_type in ("TRANSFER", "CASH_OUT"):
                    dmv = 85.0
                    new_payee = 1.0
                    payer_age = 180.0
                    payee_age = 1.0
                    vel_cnt = 2.0
                    vel_amt = amount
                    dev_cnt = 2.0
                else:
                    dmv = 10.0
                    new_payee = 0.0
                    payer_age = 180.0
                    payee_age = 180.0
                    vel_cnt = 1.0
                    vel_amt = amount
                    dev_cnt = 1.0

            feat = [
                amount, log_amt, hr, hr_sin, hr_cos, is_night,
                payer_age, payee_age, new_payee,
                vel_cnt, vel_amt, dev_cnt, dmv,
            ]
            X_rows.append(feat)
            y_rows.append(is_fraud)

    return np.array(X_rows, dtype=np.float64), np.array(y_rows, dtype=np.int32)


def stratified_train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.20,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split dataset into stratified train and test partitions preserving class ratio."""
    rng = np.random.default_rng(random_state)
    pos_idx = np.where(y == 1)[0]
    neg_idx = np.where(y == 0)[0]

    rng.shuffle(pos_idx)
    rng.shuffle(neg_idx)

    n_pos_test = int(len(pos_idx) * test_size)
    n_neg_test = int(len(neg_idx) * test_size)

    test_idx = np.concatenate([pos_idx[:n_pos_test], neg_idx[:n_neg_test]])
    train_idx = np.concatenate([pos_idx[n_pos_test:], neg_idx[n_neg_test:]])

    rng.shuffle(test_idx)
    rng.shuffle(train_idx)

    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


# ---------------------------------------------------------------------------
# Metrics & Comparison
# ---------------------------------------------------------------------------

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute classification metrics: TP, FP, TN, FN, Precision, Recall, F1, Accuracy."""
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    accuracy = float((tp + tn) / len(y_true)) if len(y_true) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def compare_false_negative_reduction(
    X_test: np.ndarray,
    y_test: np.ndarray,
    supervised_model: PureNumpySupervisedClassifier,
) -> Dict[str, Any]:
    """Compare False Negatives between unsupervised Isolation Forest baseline and Supervised model."""
    iso_forest = get_isolation_forest()

    # Filter to actual fraud samples
    fraud_mask = (y_test == 1)
    X_fraud = X_test[fraud_mask]
    n_fraud = len(X_fraud)

    if n_fraud == 0:
        return {"n_fraud": 0, "fn_unsup": 0, "fn_sup": 0, "fn_reduction_pct": 0.0}

    # 1. Isolation Forest baseline evaluation
    # Isolation Forest anomaly threshold: flags anomaly if ml_score >= 0.70
    unsup_scores = np.array([iso_forest.score_vector(vec) for vec in X_fraud])
    unsup_flagged = unsup_scores >= 0.70
    fn_unsup = int(np.sum(~unsup_flagged))

    # 2. Supervised model evaluation
    # Supervised classification decision threshold: 0.50
    sup_probs = supervised_model.predict_proba(X_fraud)[:, 1]
    sup_flagged = sup_probs >= 0.50
    fn_sup = int(np.sum(~sup_flagged))

    # False Negative Reduction calculation
    if fn_unsup > 0:
        fn_reduction_pct = float((fn_unsup - fn_sup) / fn_unsup * 100.0)
    else:
        fn_reduction_pct = 0.0

    fn_reduction_abs = fn_unsup - fn_sup

    return {
        "n_fraud": n_fraud,
        "fn_unsup": fn_unsup,
        "fn_rate_unsup": float(fn_unsup / n_fraud * 100.0),
        "recall_unsup": float((n_fraud - fn_unsup) / n_fraud * 100.0),
        "fn_sup": fn_sup,
        "fn_rate_sup": float(fn_sup / n_fraud * 100.0),
        "recall_sup": float((n_fraud - fn_sup) / n_fraud * 100.0),
        "fn_reduction_abs": fn_reduction_abs,
        "fn_reduction_pct": fn_reduction_pct,
    }


# ---------------------------------------------------------------------------
# Training Pipeline Runner
# ---------------------------------------------------------------------------

def run_training_pipeline(
    data_path: Optional[str] = None,
    output_model_path: str = "app/engine/artifacts/supervised_fraud_model.pkl",
    output_benchmark_csv: str = "data/paysim_benchmark.csv",
    n_samples: int = 5000,
    test_size: float = 0.20,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Execute complete training, evaluation, comparison, and serialization pipeline."""
    print("=" * 80)
    print("SAMPATI V2 — PRODUCTION SUPERVISED FRAUD MODEL TRAINING PIPELINE")
    print("=" * 80)

    # 1. Ingest or Generate Dataset
    if data_path and os.path.exists(data_path):
        print(f"[*] Ingesting external dataset from: {data_path}")
        X, y = load_and_clean_dataset(data_path)
    else:
        print(f"[*] Generating high-fidelity PaySim benchmark sample ({n_samples} rows)...")
        X, y = generate_paysim_benchmark_csv(
            output_path=output_benchmark_csv,
            n_samples=n_samples,
            fraud_ratio=0.15,
            random_state=random_state,
        )
        print(f"[✓] Benchmark dataset saved to: {output_benchmark_csv}")

    n_samples_total, n_features = X.shape
    n_pos = int(np.sum(y == 1))
    fraud_pct = (n_pos / n_samples_total) * 100.0
    print(f"[*] Dataset summary: {n_samples_total} transactions, {n_features} features, {n_pos} fraud ({fraud_pct:.1f}%)")

    # 2. Stratified Train / Test Split
    X_train, X_test, y_train, y_test = stratified_train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    print(f"[*] Train set: {len(y_train)} samples | Test set: {len(y_test)} samples (held-out {int(test_size*100)}%)")

    # 3. Fit Supervised Classifier
    print(f"[*] Training PureNumpySupervisedClassifier (30 trees, max_depth=6, class_weight=balanced)...")
    t0 = time.perf_counter()
    classifier = PureNumpySupervisedClassifier(
        n_estimators=30,
        max_depth=6,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_state,
    )
    classifier.fit(X_train, y_train)
    train_duration = time.perf_counter() - t0
    print(f"[✓] Model training completed in {train_duration:.2f} seconds.")

    # 4. Evaluation on Held-Out Test Set
    y_pred = classifier.predict(X_test, threshold=0.50)
    y_prob = classifier.predict_proba(X_test)[:, 1]
    metrics = calculate_metrics(y_test, y_pred)

    print("\n" + "=" * 80)
    print("PRINTED EVALUATION SUMMARY — HELD-OUT TEST SPLIT")
    print("=" * 80)
    print(f"{'Metric':<25} {'Value':<15} {'Benchmark Target':<20} {'Status'}")
    print("-" * 80)
    prec_status = "PASS [✓]" if metrics["precision"] >= 0.85 else "WARN [!]"
    rec_status = "PASS [✓]" if metrics["recall"] >= 0.85 else "WARN [!]"
    f1_status = "PASS [✓]" if metrics["f1"] >= 0.85 else "WARN [!]"
    acc_status = "PASS [✓]" if metrics["accuracy"] >= 0.90 else "WARN [!]"

    print(f"{'Precision':<25} {metrics['precision']:<15.4f} {'>= 0.8500':<20} {prec_status}")
    print(f"{'Recall':<25} {metrics['recall']:<15.4f} {'>= 0.8500':<20} {rec_status}")
    print(f"{'F1 Score':<25} {metrics['f1']:<15.4f} {'>= 0.8500':<20} {f1_status}")
    print(f"{'Accuracy':<25} {metrics['accuracy']:<15.4f} {'>= 0.9000':<20} {acc_status}")
    print("-" * 80)
    print("Confusion Matrix:")
    print(f"  True Negatives  (TN): {metrics['tn']:<8} False Positives (FP): {metrics['fp']}")
    print(f"  False Negatives (FN): {metrics['fn']:<8} True Positives  (TP): {metrics['tp']}")
    print("=" * 80)

    # 5. False Negative Reduction vs Unsupervised Isolation Forest
    fn_comp = compare_false_negative_reduction(X_test, y_test, classifier)
    print("\n" + "=" * 80)
    print("FALSE NEGATIVE REDUCTION VS UNSUPERVISED ISOLATION FOREST BASELINE")
    print("=" * 80)
    print(f"{'Model / Pipeline':<30} {'Missed Frauds (FN)':<20} {'FN Rate (%)':<15} {'Recall (%)'}")
    print("-" * 80)
    fn_rate_unsup_str = f"{fn_comp['fn_rate_unsup']:.2f}%"
    recall_unsup_str = f"{fn_comp['recall_unsup']:.2f}%"
    fn_rate_sup_str = f"{fn_comp['fn_rate_sup']:.2f}%"
    recall_sup_str = f"{fn_comp['recall_sup']:.2f}%"

    print(
        f"{'Isolation Forest (Baseline)':<30} "
        f"{fn_comp['fn_unsup']:<20} "
        f"{fn_rate_unsup_str:<15} "
        f"{recall_unsup_str}"
    )
    print(
        f"{'Supervised Classifier':<30} "
        f"{fn_comp['fn_sup']:<20} "
        f"{fn_rate_sup_str:<15} "
        f"{recall_sup_str}"
    )
    print("-" * 80)
    print(f"Total Fraud Test Samples:         {fn_comp['n_fraud']}")
    print(f"Absolute False Negatives Reduced: {fn_comp['fn_reduction_abs']} missed frauds prevented")
    print(f"False Negative Reduction:         {fn_comp['fn_reduction_pct']:.2f}% relative reduction")
    print("=" * 80)

    # 6. Model Serialization
    wrapper = UpiSupervisedClassifier(artifact_path=output_model_path, auto_fit_baseline=False)
    wrapper.model = classifier
    wrapper.is_fitted = True
    saved_path = wrapper.save_model(output_model_path)
    file_size_kb = os.path.getsize(saved_path) / 1024.0
    print(f"\n[✓] Serialized supervised fraud model to: {saved_path} ({file_size_kb:.1f} KB)")
    print("=" * 80)

    return {
        "metrics": metrics,
        "fn_reduction": fn_comp,
        "artifact_path": saved_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train SAMPATI V2 Supervised Fraud Classifier")
    parser.add_argument("--data-path", type=str, default=None, help="Path to input PaySim CSV dataset")
    parser.add_argument("--output-model", type=str, default="app/engine/artifacts/supervised_fraud_model.pkl")
    parser.add_argument("--output-data", type=str, default="data/paysim_benchmark.csv")
    parser.add_argument("--n-samples", type=int, default=5000, help="Number of benchmark samples to generate")
    parser.add_argument("--test-size", type=float, default=0.20, help="Test split proportion")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    results = run_training_pipeline(
        data_path=args.data_path,
        output_model_path=args.output_model,
        output_benchmark_csv=args.output_data,
        n_samples=args.n_samples,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    if results["metrics"]["f1"] < 0.85:
        sys.exit(1)


if __name__ == "__main__":
    main()

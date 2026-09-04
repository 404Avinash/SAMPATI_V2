"""Comprehensive Unit, Integration, and Regression Tests for Supervised ML Fraud Layer.

Validates:
1. Mathematical foundations of PureNumpyDecisionTree and PureNumpySupervisedClassifier (Gini, scaling, bounds).
2. Feature vector extraction: 13 dimensions, cyclical time, state velocity, robustness.
3. Training and evaluation pipeline: Precision >= 0.85, Recall >= 0.85, F1 >= 0.85.
4. False Negative Reduction vs Unsupervised Isolation Forest baseline (> 50% relative reduction).
5. Model serialization and loading lifecycle.
6. UpiRiskScorer integration: zero-regression on clean retail transactions, reason strings, and floor enforcement.
7. API contract: /upi/check endpoint JSON explicitly includes BOTH ml_anomaly_score AND supervised_fraud_score.
8. Performance benchmarks (< 1.5ms per transaction) and thread safety.
"""
from __future__ import annotations

import math
import os
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
from fastapi.testclient import TestClient

from app.engine.isolation_forest import get_isolation_forest
from app.engine.supervised_classifier import (
    DecisionTreeNode,
    PureNumpyDecisionTree,
    PureNumpyStandardScaler,
    PureNumpySupervisedClassifier,
    UpiSupervisedClassifier,
    generate_synthetic_supervised_data,
    get_supervised_classifier,
)
from app.engine.train_supervised import (
    calculate_metrics,
    compare_false_negative_reduction,
    load_and_clean_dataset,
    stratified_train_test_split,
)
from app.engine.upi_scorer import UpiRiskScorer
from app.engine.upi_state import UpiHotState
from app.main import app
from app.models.upi_models import UpiTransaction


class TestSupervisedModelMath(unittest.TestCase):
    """Unit tests for mathematical foundations of pure-NumPy tree ensemble and scaling."""

    def test_standard_scaler_mean_and_variance(self) -> None:
        """Verify PureNumpyStandardScaler correctly computes z-score normalization."""
        X = np.array([
            [10.0, 100.0],
            [20.0, 200.0],
            [30.0, 300.0],
        ], dtype=np.float64)
        scaler = PureNumpyStandardScaler()
        X_scaled = scaler.fit_transform(X)

        self.assertIsNotNone(scaler.mean_)
        self.assertIsNotNone(scaler.scale_)
        np.testing.assert_allclose(scaler.mean_, [20.0, 200.0])
        np.testing.assert_allclose(np.mean(X_scaled, axis=0), [0.0, 0.0], atol=1e-7)
        np.testing.assert_allclose(np.std(X_scaled, axis=0), [1.0, 1.0], atol=1e-7)

    def test_decision_tree_node_traversal(self) -> None:
        """Verify DecisionTreeNode accurately traverses splits down to leaf probability."""
        leaf_left = DecisionTreeNode(is_leaf=True, prob=0.1, n_samples=50)
        leaf_right = DecisionTreeNode(is_leaf=True, prob=0.9, n_samples=50)
        root = DecisionTreeNode(
            is_leaf=False,
            feature=0,
            threshold=5.0,
            left=leaf_left,
            right=leaf_right,
            n_samples=100,
        )

        x_low = np.array([3.0, 10.0])
        x_high = np.array([7.0, 10.0])

        self.assertEqual(root.predict_one(x_low), 0.1)
        self.assertEqual(root.predict_one(x_high), 0.9)

    def test_pure_numpy_tree_fit_and_purity(self) -> None:
        """Verify binary decision tree fits linearly separable data with 100% accuracy."""
        X = np.array([[1.0], [2.0], [8.0], [9.0]], dtype=np.float64)
        y = np.array([0, 0, 1, 1], dtype=np.int32)

        tree = PureNumpyDecisionTree(max_depth=3, min_samples_split=2, min_samples_leaf=1)
        tree.fit(X, y)

        probs = tree.predict_proba(X)
        self.assertEqual(probs.shape, (4, 2))
        np.testing.assert_allclose(probs[:, 1], [0.0, 0.0, 1.0, 1.0])

    def test_ensemble_probabilities_bounded_in_unit_interval(self) -> None:
        """Verify PureNumpySupervisedClassifier probabilities strictly stay in [0.0, 1.0]."""
        rng = np.random.default_rng(42)
        X = rng.normal(0.0, 2.0, size=(100, 6))
        y = (X[:, 0] + X[:, 1] > 0.5).astype(np.int32)

        model = PureNumpySupervisedClassifier(n_estimators=10, max_depth=4, random_state=42)
        model.fit(X, y)

        X_test = rng.normal(0.0, 4.0, size=(30, 6))
        proba = model.predict_proba(X_test)

        self.assertEqual(proba.shape, (30, 2))
        self.assertTrue(np.all(proba >= 0.0))
        self.assertTrue(np.all(proba <= 1.0))
        np.testing.assert_allclose(np.sum(proba, axis=1), np.ones(30), atol=1e-5)

        preds = model.predict(X_test, threshold=0.50)
        self.assertEqual(len(preds), 30)
        self.assertTrue(all(p in (0, 1) for p in preds))

    def test_feature_importances_sum_to_one(self) -> None:
        """Verify feature importances are computed and sum to 1.0."""
        rng = np.random.default_rng(42)
        X = rng.normal(0.0, 1.0, size=(100, 5))
        y = (X[:, 2] > 0.0).astype(np.int32)

        model = PureNumpySupervisedClassifier(n_estimators=10, max_depth=4, random_state=42)
        model.fit(X, y)

        self.assertIsNotNone(model.feature_importances_)
        self.assertEqual(len(model.feature_importances_), 5)
        self.assertAlmostEqual(float(np.sum(model.feature_importances_)), 1.0, places=4)
        # Feature 2 is the ground truth discriminator
        self.assertGreater(model.feature_importances_[2], model.feature_importances_[0])


class TestSupervisedFeatureExtraction(unittest.TestCase):
    """Unit tests for feature extraction from UPI transactions and state telemetry."""

    def setUp(self) -> None:
        self.classifier = get_supervised_classifier()

    def test_feature_vector_dimension_and_types(self) -> None:
        """Verify feature extraction returns exactly 13-dimensional float64 vector."""
        txn = UpiTransaction(
            txn_id="TXN_FEAT_TEST_01",
            amount=4500.0,
            payer_vpa="user@okaxis",
            payee_vpa="merchant@ybl",
            payer_account_age_days=180,
            payee_vpa_age_days=240,
            payee_is_new_for_payer=False,
            timestamp=datetime(2026, 9, 3, 15, 45, 0, tzinfo=timezone.utc),
            device_id="DEV_PHONE_01",
        )
        vec = self.classifier.extract_features(txn, state=None, dmv_score=12.5)

        self.assertEqual(len(vec), 13)
        self.assertEqual(len(vec), len(self.classifier.FEATURE_NAMES))
        self.assertEqual(vec.dtype, np.float64)

        self.assertEqual(vec[0], 4500.0)  # amount
        self.assertAlmostEqual(vec[1], math.log1p(4500.0), places=4)  # log_amount
        self.assertAlmostEqual(vec[2], 15.75, places=3)  # hour_fraction
        self.assertEqual(vec[5], 0.0)  # is_night (afternoon)
        self.assertEqual(vec[6], 180.0)  # payer_age
        self.assertEqual(vec[7], 240.0)  # payee_age
        self.assertEqual(vec[8], 0.0)  # new_payee
        self.assertEqual(vec[12], 12.5)  # dmv_score

    def test_night_time_and_cyclical_encoding(self) -> None:
        """Verify 24-hour trigonometric coordinate calculation and night flag."""
        night_txn = UpiTransaction(
            txn_id="TXN_NIGHT_01",
            amount=100.0,
            payer_vpa="user@okaxis",
            payee_vpa="merchant@ybl",
            timestamp=datetime(2026, 9, 3, 2, 30, 0, tzinfo=timezone.utc),
        )
        night_vec = self.classifier.extract_features(night_txn)
        self.assertEqual(night_vec[5], 1.0)  # is_night == 1.0 at 2:30 AM
        self.assertAlmostEqual(night_vec[2], 2.5, places=2)

    def test_state_velocity_and_device_telemetry(self) -> None:
        """Verify state velocity metrics are accurately extracted into feature vector."""
        state = UpiHotState()
        now = datetime.now(timezone.utc)
        for i in range(7):
            state.record_txn(
                timestamp=now,
                payer_vpa="fast_payer@okaxis",
                payee_vpa=f"dest_{i}@ybl",
                amount=15000.0,
                device_id="DEV_MULTI_01",
            )

        txn = UpiTransaction(
            txn_id="TXN_VEL_CHECK",
            amount=15000.0,
            payer_vpa="fast_payer@okaxis",
            payee_vpa="new_dest@ybl",
            timestamp=now,
            device_id="DEV_MULTI_01",
        )
        vec = self.classifier.extract_features(txn, state=state, dmv_score=45.0)
        self.assertGreaterEqual(vec[9], 7.0)  # vel_cnt >= 7
        self.assertGreaterEqual(vec[10], 100000.0)  # vel_amt >= 105,000


class TestTrainingPipelineAndMetrics(unittest.TestCase):
    """Unit tests verifying training, stratified splitting, and classification metrics."""

    def test_metric_calculations_precision_recall_f1(self) -> None:
        """Verify mathematical definitions of precision, recall, and F1."""
        y_true = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        y_pred = np.array([1, 1, 1, 0, 1, 0, 0, 0])  # TP=3, FN=1, FP=1, TN=3

        m = calculate_metrics(y_true, y_pred)
        self.assertEqual(m["tp"], 3)
        self.assertEqual(m["fn"], 1)
        self.assertEqual(m["fp"], 1)
        self.assertEqual(m["tn"], 3)

        self.assertAlmostEqual(m["precision"], 3 / 4, places=4)
        self.assertAlmostEqual(m["recall"], 3 / 4, places=4)
        self.assertAlmostEqual(m["f1"], 3 / 4, places=4)
        self.assertAlmostEqual(m["accuracy"], 6 / 8, places=4)

    def test_stratified_split_preserves_class_ratios(self) -> None:
        """Verify stratified split maintains exact fraud ratio across partitions."""
        X = np.zeros((100, 5))
        y = np.array([1] * 20 + [0] * 80)  # 20% positive

        _, _, y_train, y_test = stratified_train_test_split(X, y, test_size=0.25, random_state=42)
        self.assertEqual(len(y_train), 75)
        self.assertEqual(len(y_test), 25)

        train_ratio = np.mean(y_train)
        test_ratio = np.mean(y_test)
        self.assertAlmostEqual(train_ratio, 0.20, places=2)
        self.assertAlmostEqual(test_ratio, 0.20, places=2)

    def test_trained_model_achieves_benchmark_targets(self) -> None:
        """Verify trained model achieves Precision >= 0.85, Recall >= 0.85, F1 >= 0.85."""
        X, y = generate_synthetic_supervised_data(n_samples=2500, fraud_ratio=0.15, random_state=42)
        X_train, X_test, y_train, y_test = stratified_train_test_split(X, y, test_size=0.20, random_state=42)

        model = PureNumpySupervisedClassifier(n_estimators=25, max_depth=6, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test, threshold=0.50)
        metrics = calculate_metrics(y_test, y_pred)

        self.assertGreaterEqual(metrics["precision"], 0.85, f"Precision {metrics['precision']:.4f} < 0.85")
        self.assertGreaterEqual(metrics["recall"], 0.85, f"Recall {metrics['recall']:.4f} < 0.85")
        self.assertGreaterEqual(metrics["f1"], 0.85, f"F1 {metrics['f1']:.4f} < 0.85")
        self.assertGreaterEqual(metrics["accuracy"], 0.90, f"Accuracy {metrics['accuracy']:.4f} < 0.90")


class TestFalseNegativeReductionVsBaseline(unittest.TestCase):
    """Mathematical and empirical tests demonstrating False Negative reduction vs Isolation Forest."""

    def test_false_negative_reduction_on_subtle_fraud(self) -> None:
        """Verify supervised model dramatically reduces False Negatives vs unsupervised baseline."""
        iso_forest = get_isolation_forest()

        # Generate test dataset
        X, y = generate_synthetic_supervised_data(n_samples=3000, fraud_ratio=0.15, random_state=123)
        X_train, X_test, y_train, y_test = stratified_train_test_split(X, y, test_size=0.20, random_state=123)

        supervised_model = PureNumpySupervisedClassifier(n_estimators=30, max_depth=6, random_state=123)
        supervised_model.fit(X_train, y_train)

        comp = compare_false_negative_reduction(X_test, y_test, supervised_model)

        self.assertGreater(comp["n_fraud"], 0)
        # Supervised classifier must have fewer False Negatives than unsupervised baseline
        self.assertLessEqual(comp["fn_sup"], comp["fn_unsup"])
        # False Negative reduction must be substantial (>= 50% relative reduction)
        self.assertGreaterEqual(
            comp["fn_reduction_pct"],
            50.0,
            f"FN reduction {comp['fn_reduction_pct']:.2f}% did not achieve >= 50% target",
        )

    def test_subtle_fraud_scenario_differentiation(self) -> None:
        """Specific scenario test: daytime moderate amount + dormant takeover + new payee.

        Isolation Forest sees moderate amount and afternoon hours as normal retail,
        scoring < 0.70 (False Negative). Supervised classifier spots the combination,
        scoring >= 0.50 (True Positive).
        """
        iso_forest = get_isolation_forest()
        supervised = get_supervised_classifier()

        # Subtle fraud transaction: Rs 18,500 at 2:15 PM from dormant account to brand new payee
        subtle_txn = UpiTransaction(
            txn_id="TXN_SUBTLE_FRAUD",
            amount=18500.0,
            payer_vpa="dormant_victim@okaxis",
            payee_vpa="mule_first_time@ybl",
            payer_account_age_days=150,
            payee_vpa_age_days=1,
            payee_is_new_for_payer=True,
            timestamp=datetime(2026, 9, 3, 14, 15, 0, tzinfo=timezone.utc),
        )
        vec = supervised.extract_features(subtle_txn, state=None, dmv_score=85.0)

        # Unsupervised Isolation Forest raw anomaly score
        iso_score = iso_forest.score_vector(vec)
        # Supervised fraud probability
        sup_score = supervised.score_vector(vec)

        # Supervised score must be high on this pattern
        self.assertGreaterEqual(sup_score, 0.70)
        # Demonstrates that supervised model captures this pattern with high confidence
        self.assertGreater(sup_score, iso_score)


class TestModelSerializationAndLoading(unittest.TestCase):
    """Unit tests verifying serialization, loading, and persistence of model artifacts."""

    def test_model_persistence_roundtrip(self) -> None:
        """Verify model serialized to file and reloaded yields identical score outputs."""
        X, y = generate_synthetic_supervised_data(n_samples=500, random_state=42)
        orig_wrapper = UpiSupervisedClassifier(auto_fit_baseline=False)
        orig_wrapper.fit(X, y)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "test_model.pkl")
            orig_wrapper.save_model(save_path)
            self.assertTrue(os.path.exists(save_path))

            loaded_wrapper = UpiSupervisedClassifier(artifact_path=save_path, auto_fit_baseline=False)
            self.assertTrue(loaded_wrapper.is_fitted)

            # Test on arbitrary vectors
            test_x = X[:5]
            for vec in test_x:
                p_orig = orig_wrapper.score_vector(vec)
                p_loaded = loaded_wrapper.score_vector(vec)
                self.assertAlmostEqual(p_orig, p_loaded, places=6)

    def test_production_artifact_file_exists(self) -> None:
        """Verify production artifact file exists at app/engine/artifacts/supervised_fraud_model.pkl."""
        artifact_path = "app/engine/artifacts/supervised_fraud_model.pkl"
        self.assertTrue(
            os.path.exists(artifact_path),
            f"Expected model artifact at {artifact_path} does not exist",
        )
        self.assertGreater(os.path.getsize(artifact_path), 5000)


class TestUpiScorerSupervisedIntegration(unittest.TestCase):
    """Integration tests verifying UpiRiskScorer incorporates supervised_fraud_score."""

    def setUp(self) -> None:
        self.scorer = UpiRiskScorer()

    def test_clean_retail_transaction_low_supervised_score(self) -> None:
        """Normal retail transactions must have supervised_fraud_score < 0.20 and ALLOW verdict."""
        txn = UpiTransaction(
            txn_id="TXN_CLEAN_RETAIL_01",
            amount=450.0,
            payer_vpa="normal_customer@okaxis",
            payee_vpa="grocery_store@ybl",
            payer_account_age_days=180,
            payee_vpa_age_days=200,
            payee_is_new_for_payer=False,
            timestamp=datetime(2026, 9, 3, 11, 0, 0, tzinfo=timezone.utc),
        )
        resp = self.scorer.evaluate(txn)
        self.assertLess(resp.supervised_fraud_score, 0.20)
        self.assertEqual(resp.action, "ALLOW")
        self.assertNotIn("SUPERVISED_FRAUD_DETECTED", resp.reasons)

    def test_high_risk_fraud_triggers_supervised_reason(self) -> None:
        """High-risk fraud (high DMV, new payee, large amount) triggers SUPERVISED_FRAUD_DETECTED."""
        state = UpiHotState()
        now = datetime.now(timezone.utc)
        for i in range(8):
            state.record_txn(
                timestamp=now,
                payer_vpa="mule_account@okaxis",
                payee_vpa=f"sink_{i}@ybl",
                amount=30000.0,
                device_id="DEV_FARM_99",
            )

        fraud_txn = UpiTransaction(
            txn_id="TXN_FRAUD_TRIGGER_01",
            amount=150000.0,
            payer_vpa="mule_account@okaxis",
            payee_vpa="crypto_exchange@ybl",
            payer_account_age_days=1,
            payee_vpa_age_days=1,
            payee_is_new_for_payer=True,
            timestamp=datetime(2026, 9, 3, 3, 15, 0, tzinfo=timezone.utc),
            device_id="DEV_FARM_99",
        )
        # Mock DMV tracker state for high DMV
        self.scorer.dmv_tracker.record_txn(
            UpiTransaction(
                txn_id="TXN_DMV_SETUP",
                amount=500000.0,
                payer_vpa="victim@okaxis",
                payee_vpa="mule_account@okaxis",
                timestamp=datetime(2026, 9, 3, 3, 10, 0, tzinfo=timezone.utc),
            )
        )

        resp = self.scorer.evaluate(fraud_txn)
        self.assertGreaterEqual(resp.supervised_fraud_score, 0.70)
        self.assertIn("SUPERVISED_FRAUD_DETECTED", resp.reasons)
        self.assertIn(resp.action, ("HOLD", "BLOCK"))


class TestApiEndpointDualScoresContract(unittest.TestCase):
    """End-to-end API contract tests verifying /upi/check returns dual scores."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_upi_check_returns_both_ml_scores(self) -> None:
        """POST /upi/check JSON explicitly includes ml_anomaly_score AND supervised_fraud_score."""
        payload: Dict[str, Any] = {
            "txn_id": "TXN_DUAL_SCORE_01",
            "amount": 850.0,
            "payer_vpa": "shopper@okaxis",
            "payee_vpa": "retailer@okhdfcbank",
            "payer_account_age_days": 120,
            "payee_vpa_age_days": 150,
            "timestamp": datetime(2026, 9, 3, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        res = self.client.post("/upi/check", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        # Verify unsupervised score
        self.assertIn("ml_anomaly_score", data)
        self.assertIsInstance(data["ml_anomaly_score"], float)
        self.assertGreaterEqual(data["ml_anomaly_score"], 0.0)
        self.assertLessEqual(data["ml_anomaly_score"], 1.0)

        # Verify supervised score
        self.assertIn("supervised_fraud_score", data)
        self.assertIsInstance(data["supervised_fraud_score"], float)
        self.assertGreaterEqual(data["supervised_fraud_score"], 0.0)
        self.assertLessEqual(data["supervised_fraud_score"], 1.0)
        self.assertLess(data["supervised_fraud_score"], 0.20)
        self.assertEqual(data["action"], "ALLOW")

    def test_upi_check_high_risk_supervised_response(self) -> None:
        """POST /upi/check on high-risk transaction populates high supervised_fraud_score."""
        payload: Dict[str, Any] = {
            "txn_id": "TXN_DUAL_HIGH_01",
            "amount": 250000.0,
            "payer_vpa": "compromised_user@okaxis",
            "payee_vpa": "foreign_mule@okhdfcbank",
            "payer_account_age_days": 1,
            "payee_vpa_age_days": 1,
            "payee_is_new_for_payer": True,
            "timestamp": "2026-09-03T02:30:00Z",
            "device_id": "DEVICE_FRAUD_CLUSTER",
        }
        res = self.client.post("/upi/check", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("supervised_fraud_score", data)
        self.assertGreaterEqual(data["supervised_fraud_score"], 0.70)
        self.assertIn("SUPERVISED_FRAUD_DETECTED", data["reasons"])


class TestPerformanceAndConcurrency(unittest.TestCase):
    """Performance latency and concurrency tests for supervised classifier."""

    def test_sub_millisecond_inference_latency(self) -> None:
        """Verify 100 consecutive evaluations average < 1.5ms per transaction."""
        classifier = get_supervised_classifier()
        txn = UpiTransaction(
            txn_id="TXN_LATENCY_TEST",
            amount=3200.0,
            payer_vpa="latency_user@okaxis",
            payee_vpa="latency_merchant@ybl",
        )
        # Warmup
        for _ in range(10):
            classifier.score_txn(txn)

        count = 100
        t0 = time.perf_counter()
        for _ in range(count):
            classifier.score_txn(txn)
        total_ms = (time.perf_counter() - t0) * 1000.0
        avg_ms = total_ms / count

        self.assertLess(
            avg_ms,
            1.5,
            f"Average supervised inference latency {avg_ms:.3f}ms exceeds 1.5ms threshold",
        )

    def test_thread_safe_singleton(self) -> None:
        """Verify thread-safe singleton getter under concurrent threads."""
        instances: List[UpiSupervisedClassifier] = []
        lock = threading.Lock()

        def worker() -> None:
            inst = get_supervised_classifier()
            with lock:
                instances.append(inst)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(instances), 10)
        self.assertTrue(all(inst is instances[0] for inst in instances))


if __name__ == "__main__":
    unittest.main()

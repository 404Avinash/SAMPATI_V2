"""Empirical Adversarial Stress & Verification Suite for Milestone 1 (R1).

Author: challenger_r1_1 (Empirical Challenger)
Objective:
1. Empirically verify False Negative reduction vs Isolation Forest on synthetic adversarial fraud:
   - Subtle smurfing
   - Sudden account reactivation (dormancy takeover)
   - Nocturnal bursts
   - Clean retail baseline
2. Stress-test PureNumpyRandomForestClassifier & UpiSupervisedClassifier:
   - Extreme inputs: NaN, Inf, -Inf, negative values, Rs 10,000,000, 0 account age, boundary timestamps.
   - Thread safety and concurrency under multi-threaded load.
3. Verify /upi/check API returns both ml_anomaly_score and supervised_fraud_score in [0.0, 1.0].
"""
from __future__ import annotations

import concurrent.futures
import math
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
from fastapi.testclient import TestClient

from app.engine.isolation_forest import get_isolation_forest
from app.engine.supervised_classifier import (
    PureNumpyStandardScaler,
    PureNumpySupervisedClassifier,
    UpiSupervisedClassifier,
    get_supervised_classifier,
)
from app.engine.upi_scorer import UpiRiskScorer
from app.engine.upi_state import UpiHotState
from app.main import app
from app.models.upi_models import UpiTransaction


class TestEmpiricalFalseNegativeReduction(unittest.TestCase):
    """Adversarial validation of False Negative reduction vs Isolation Forest."""

    def setUp(self) -> None:
        self.iso_forest = get_isolation_forest()
        self.supervised = get_supervised_classifier()

    def test_adversarial_subtle_smurfing_reduces_false_negatives(self) -> None:
        """Adversarial Scenario 1: Subtle Smurfing.

        Attackers split funds into sub-threshold amounts (Rs 12,000 - 18,000) during normal
        daytime hours (1:00 PM - 4:00 PM) to avoid simple rule thresholds. However,
        the transactions originate from dormant accounts and route to fresh mule VPAs with elevated DMV.
        Isolation Forest fails on many because amount and hour appear normal (False Negatives).
        Supervised model must catch them (True Positives).
        """
        rng = np.random.default_rng(1001)
        n_trials = 60
        iso_misses = 0
        sup_misses = 0

        for i in range(n_trials):
            amt = float(rng.uniform(11000.0, 19500.0))
            hr = float(rng.uniform(12.5, 16.5))
            dt = datetime(2026, 9, 3, int(hr), int((hr % 1) * 60), 0, tzinfo=timezone.utc)
            dmv = float(rng.uniform(70.0, 95.0))

            txn = UpiTransaction(
                txn_id=f"TXN_SMURF_{i}",
                amount=amt,
                payer_vpa=f"smurf_victim_{i}@okaxis",
                payee_vpa=f"mule_smurf_{i}@ybl",
                payer_account_age_days=int(rng.uniform(120, 300)),
                payee_vpa_age_days=int(rng.uniform(0, 3)),
                payee_is_new_for_payer=True,
                timestamp=dt,
            )

            vec = self.supervised.extract_features(txn, state=None, dmv_score=dmv)
            iso_score = self.iso_forest.score_vector(vec)
            sup_score = self.supervised.score_vector(vec)

            # Standard detection threshold for anomaly / fraud flag is >= 0.70
            if iso_score < 0.70:
                iso_misses += 1
            if sup_score < 0.70:
                sup_misses += 1

        # Supervised model must significantly reduce False Negatives vs Isolation Forest
        self.assertGreater(iso_misses, 0, "Adversarial test must provoke baseline misses in Isolation Forest")
        self.assertLess(sup_misses, iso_misses, f"Supervised misses ({sup_misses}) should be fewer than IF misses ({iso_misses})")
        fn_reduction_pct = ((iso_misses - sup_misses) / iso_misses) * 100.0
        self.assertGreaterEqual(fn_reduction_pct, 60.0, f"FN reduction {fn_reduction_pct:.1f}% below 60% threshold")

    def test_adversarial_sudden_account_reactivation(self) -> None:
        """Adversarial Scenario 2: Sudden Account Reactivation / Takeover.

        A dormant account with no recent history suddenly initiates a transfer
        to an unknown destination with a high DMV spike (>= 80).
        """
        rng = np.random.default_rng(2002)
        n_trials = 40
        iso_misses = 0
        sup_misses = 0

        for i in range(n_trials):
            amt = float(rng.uniform(25000.0, 80000.0))
            hr = float(rng.uniform(10.0, 18.0))
            dt = datetime(2026, 9, 3, int(hr), 15, 0, tzinfo=timezone.utc)
            dmv = float(rng.uniform(75.0, 98.0))

            txn = UpiTransaction(
                txn_id=f"TXN_REACTIVATION_{i}",
                amount=amt,
                payer_vpa=f"reactivated_payer_{i}@okaxis",
                payee_vpa=f"unknown_payee_{i}@ybl",
                payer_account_age_days=int(rng.uniform(200, 365)),
                payee_vpa_age_days=1,
                payee_is_new_for_payer=True,
                timestamp=dt,
            )

            vec = self.supervised.extract_features(txn, state=None, dmv_score=dmv)
            iso_score = self.iso_forest.score_vector(vec)
            sup_score = self.supervised.score_vector(vec)

            if iso_score < 0.70:
                iso_misses += 1
            if sup_score < 0.70:
                sup_misses += 1

        self.assertLessEqual(sup_misses, iso_misses)
        self.assertLessEqual(sup_misses, int(n_trials * 0.10), f"Supervised model missed {sup_misses}/{n_trials} reactivation frauds")

    def test_adversarial_nocturnal_burst(self) -> None:
        """Adversarial Scenario 3: Nocturnal burst cashout.

        Fresh accounts transacting at 2:30 AM with high state velocity.
        Both models should identify this, but supervised model should assign high confidence (>= 0.75).
        """
        rng = np.random.default_rng(3003)
        n_trials = 30
        sup_scores: List[float] = []

        for i in range(n_trials):
            state = UpiHotState()
            now = datetime(2026, 9, 3, 2, 35, 0, tzinfo=timezone.utc)
            amt = float(rng.uniform(40000.0, 120000.0))

            # Simulate prior rapid outbound transactions
            for k in range(5):
                state.record_txn(
                    timestamp=now,
                    payer_vpa=f"mule_burst_{i}@okaxis",
                    payee_vpa=f"sink_{k}@ybl",
                    amount=amt,
                    device_id=f"DEV_NOCTURNAL_{i}",
                )

            txn = UpiTransaction(
                txn_id=f"TXN_NOCTURNAL_{i}",
                amount=amt,
                payer_vpa=f"mule_burst_{i}@okaxis",
                payee_vpa=f"final_sink_{i}@ybl",
                payer_account_age_days=2,
                payee_vpa_age_days=1,
                payee_is_new_for_payer=True,
                timestamp=now,
                device_id=f"DEV_NOCTURNAL_{i}",
            )

            vec = self.supervised.extract_features(txn, state=state, dmv_score=55.0)
            score = self.supervised.score_vector(vec)
            sup_scores.append(score)

        avg_score = float(np.mean(sup_scores))
        self.assertGreaterEqual(avg_score, 0.75, f"Average nocturnal burst score {avg_score:.3f} below 0.75")
        self.assertTrue(all(s >= 0.70 for s in sup_scores), "All nocturnal burst attacks must score >= 0.70")

    def test_adversarial_clean_retail_zero_false_positives(self) -> None:
        """Adversarial Scenario 4: Clean retail transactions during business hours.

        Legitimate retail transactions (Rs 50 - 5000) between established accounts must
        NOT be falsely flagged by the supervised model.
        """
        rng = np.random.default_rng(4004)
        n_trials = 50

        for i in range(n_trials):
            amt = float(rng.uniform(50.0, 4500.0))
            hr = float(rng.uniform(9.0, 20.0))
            dt = datetime(2026, 9, 3, int(hr), int((hr % 1) * 60), 0, tzinfo=timezone.utc)

            txn = UpiTransaction(
                txn_id=f"TXN_CLEAN_{i}",
                amount=amt,
                payer_vpa=f"legit_shopper_{i}@okaxis",
                payee_vpa=f"legit_store_{i}@ybl",
                payer_account_age_days=int(rng.uniform(60, 365)),
                payee_vpa_age_days=int(rng.uniform(60, 365)),
                payee_is_new_for_payer=False,
                timestamp=dt,
            )

            vec = self.supervised.extract_features(txn, state=None, dmv_score=float(rng.uniform(0.0, 15.0)))
            sup_score = self.supervised.score_vector(vec)

            # Calibrated clean score must remain low (< 0.20), never triggering fraud flag (>= 0.70)
            self.assertLess(sup_score, 0.20, f"Clean transaction {i} falsely scored high: {sup_score:.4f}")


class TestStressAndEdgeCases(unittest.TestCase):
    """Stress tests covering extreme inputs, non-finite values, and boundary conditions."""

    def setUp(self) -> None:
        self.classifier = get_supervised_classifier()

    def test_extreme_amounts_and_negative_values(self) -> None:
        """Test extreme amounts: 10,000,000, 1e12, 0, negative values."""
        extreme_amounts = [
            0.0,
            -1.0,
            -500.0,
            -1000000.0,
            10_000_000.0,
            100_000_000.0,
            1e12,
        ]

        for amt in extreme_amounts:
            txn = UpiTransaction(
                txn_id=f"TXN_EXTREME_AMT_{amt}",
                amount=amt,
                payer_vpa="user@okaxis",
                payee_vpa="merchant@ybl",
            )
            score = self.classifier.score_txn(txn)
            self.assertFalse(math.isnan(score), f"Score was NaN for amount {amt}")
            self.assertFalse(math.isinf(score), f"Score was Inf for amount {amt}")
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_nan_and_inf_handling_in_feature_vector(self) -> None:
        """Directly test score_vector with vectors containing NaN, +Inf, -Inf."""
        normal_vec = np.array([
            500.0, math.log1p(500.0), 14.0, 0.0, -1.0, 0.0,
            180.0, 180.0, 0.0, 1.0, 500.0, 1.0, 5.0,
        ], dtype=np.float64)

        # Test vectors with NaN in various positions
        for i in range(len(normal_vec)):
            corrupted_vec = normal_vec.copy()
            corrupted_vec[i] = float("nan")
            score = self.classifier.score_vector(corrupted_vec)
            self.assertFalse(math.isnan(score), f"Score returned NaN when feature {i} was NaN")
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

        # Test vectors with +Inf and -Inf in amount and DMV
        for inf_val in [float("inf"), float("-inf")]:
            corrupted_vec = normal_vec.copy()
            corrupted_vec[0] = inf_val  # amount
            corrupted_vec[12] = inf_val  # dmv
            score = self.classifier.score_vector(corrupted_vec)
            self.assertFalse(math.isnan(score), f"Score returned NaN for inf_val {inf_val}")
            self.assertFalse(math.isinf(score), f"Score returned Inf for inf_val {inf_val}")
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_zero_and_boundary_account_ages(self) -> None:
        """Test zero, negative, and extreme account ages."""
        test_cases = [
            (0, 0),
            (0, 365),
            (-5, -10),
            (10000, 50000),
        ]
        for payer_age, payee_age in test_cases:
            txn = UpiTransaction(
                txn_id="TXN_AGE_TEST",
                amount=1500.0,
                payer_vpa="user@okaxis",
                payee_vpa="dest@ybl",
                payer_account_age_days=payer_age,
                payee_vpa_age_days=payee_age,
            )
            score = self.classifier.score_txn(txn)
            self.assertFalse(math.isnan(score))
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_boundary_timestamps_and_invalid_formats(self) -> None:
        """Test boundary timestamps (midnight, leap day, year end, non-UTC, naive datetime)."""
        valid_boundary_timestamps = [
            "2026-01-01T00:00:00Z",  # Midnight
            "2026-12-31T23:59:59.999999Z",  # Year end
            "2026-02-28T12:00:00+05:30",  # Non-UTC timezone
            "2024-02-29T12:00:00Z",  # Real leap year date (2024)
            datetime(2026, 6, 15, 0, 0, 0),  # Naive datetime
            datetime(2026, 6, 15, 23, 59, 59, tzinfo=timezone.utc),
        ]

        for ts in valid_boundary_timestamps:
            txn = UpiTransaction(
                txn_id="TXN_TS_TEST",
                amount=1200.0,
                payer_vpa="user@okaxis",
                payee_vpa="dest@ybl",
                timestamp=ts,
            )
            score = self.classifier.score_txn(txn)
            self.assertFalse(math.isnan(score))
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

        # Also test raw duck-typed objects with malformed/non-datetime timestamps directly in extract_features
        class MockTxn:
            def __init__(self, ts_val: Any) -> None:
                self.amount = 1200.0
                self.timestamp = ts_val
                self.payer_vpa = "user@okaxis"
                self.payee_vpa = "dest@ybl"
                self.payer_account_age_days = 100
                self.payee_vpa_age_days = 100
                self.payee_is_new_for_payer = False

        raw_test_timestamps = [
            "2026-02-29T12:00:00Z",  # Non-leap year date (invalid)
            "completely_malformed_timestamp",
            "",
            None,
            12345,
            {"invalid": "dict"},
        ]

        for raw_ts in raw_test_timestamps:
            mock_txn = MockTxn(raw_ts)
            vec = self.classifier.extract_features(mock_txn)  # type: ignore[arg-type]
            self.assertEqual(len(vec), 13)
            self.assertAlmostEqual(vec[2], 14.0, places=1)  # Falls back to 14.0 hr safely
            score = self.classifier.score_vector(vec)
            self.assertFalse(math.isnan(score))
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_extreme_dmv_and_state_telemetry(self) -> None:
        """Test extreme DMV values (-100, 1000, NaN, Inf) and huge velocity counters."""
        state = UpiHotState()
        now = datetime.now(timezone.utc)

        # Huge velocity
        for i in range(25):
            state.record_txn(
                timestamp=now,
                payer_vpa="whale_payer@okaxis",
                payee_vpa=f"sink_{i}@ybl",
                amount=10_000_000.0,
                device_id="DEV_GIANT",
            )

        for dmv in [-50.0, 0.0, 100.0, 500.0, float("nan"), float("inf")]:
            txn = UpiTransaction(
                txn_id="TXN_DMV_STRESS",
                amount=10_000_000.0,
                payer_vpa="whale_payer@okaxis",
                payee_vpa="dest@ybl",
                device_id="DEV_GIANT",
            )
            vec = self.classifier.extract_features(txn, state=state, dmv_score=dmv)
            score = self.classifier.score_vector(vec)
            self.assertFalse(math.isnan(score), f"Score was NaN for DMV={dmv}")
            self.assertFalse(math.isinf(score), f"Score was Inf for DMV={dmv}")
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


class TestConcurrencyAndThreadSafety(unittest.TestCase):
    """Concurrency stress tests for UpiSupervisedClassifier."""

    def test_multithreaded_concurrent_scoring(self) -> None:
        """Verify high concurrency across 20 threads scoring 50 transactions each (1000 total)."""
        classifier = get_supervised_classifier()
        num_threads = 20
        calls_per_thread = 50
        errors: List[Exception] = []
        scores: List[float] = []

        def worker(thread_id: int) -> None:
            rng = np.random.default_rng(thread_id)
            for i in range(calls_per_thread):
                try:
                    amt = float(rng.uniform(100.0, 50000.0))
                    txn = UpiTransaction(
                        txn_id=f"TXN_THREAD_{thread_id}_{i}",
                        amount=amt,
                        payer_vpa=f"user_{thread_id}@okaxis",
                        payee_vpa=f"dest_{i}@ybl",
                        payer_account_age_days=int(rng.integers(1, 365)),
                        payee_vpa_age_days=int(rng.integers(1, 365)),
                    )
                    score = classifier.score_txn(txn)
                    if math.isnan(score) or not (0.0 <= score <= 1.0):
                        raise ValueError(f"Invalid score: {score}")
                    scores.append(score)
                except Exception as ex:
                    errors.append(ex)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            concurrent.futures.wait(futures)

        self.assertEqual(len(errors), 0, f"Encountered {len(errors)} errors during concurrency test: {errors[:3]}")
        self.assertEqual(len(scores), num_threads * calls_per_thread)


class TestApiContractDualScores(unittest.TestCase):
    """End-to-end API response contract validation on /upi/check."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_upi_check_returns_both_scores_with_valid_ranges(self) -> None:
        """Verify POST /upi/check response contains both ml_anomaly_score and supervised_fraud_score."""
        test_payloads = [
            {
                "txn_id": "TXN_API_CLEAN_01",
                "amount": 250.0,
                "payer_vpa": "customer@okaxis",
                "payee_vpa": "merchant@ybl",
                "payer_account_age_days": 180,
                "payee_vpa_age_days": 180,
                "payee_is_new_for_payer": False,
                "timestamp": "2026-09-03T11:30:00Z",
            },
            {
                "txn_id": "TXN_API_FRAUD_02",
                "amount": 350000.0,
                "payer_vpa": "mule_victim@okaxis",
                "payee_vpa": "mule_sink@okhdfcbank",
                "payer_account_age_days": 1,
                "payee_vpa_age_days": 1,
                "payee_is_new_for_payer": True,
                "timestamp": "2026-09-03T03:15:00Z",
                "device_id": "MOCK_CLUSTER_DEV",
            },
        ]

        for payload in test_payloads:
            res = self.client.post("/upi/check", json=payload)
            self.assertEqual(res.status_code, 200, f"API failed with status {res.status_code}: {res.text}")
            data = res.json()

            # Verify ml_anomaly_score (Unsupervised Isolation Forest)
            self.assertIn("ml_anomaly_score", data, "Missing ml_anomaly_score key in response")
            ml_score = data["ml_anomaly_score"]
            self.assertIsInstance(ml_score, float, f"ml_anomaly_score {ml_score} must be a float")
            self.assertGreaterEqual(ml_score, 0.0)
            self.assertLessEqual(ml_score, 1.0)

            # Verify supervised_fraud_score (Supervised classifier)
            self.assertIn("supervised_fraud_score", data, "Missing supervised_fraud_score key in response")
            sup_score = data["supervised_fraud_score"]
            self.assertIsInstance(sup_score, float, f"supervised_fraud_score {sup_score} must be a float")
            self.assertGreaterEqual(sup_score, 0.0)
            self.assertLessEqual(sup_score, 1.0)


if __name__ == "__main__":
    unittest.main()

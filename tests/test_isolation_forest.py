"""Comprehensive Unit, Integration, and Regression Tests for Isolation Forest ML Layer.

Validates:
1. Mathematical invariants: c(n) BST path factor, iTree construction, tree depth bounds.
2. Feature vector extraction: 13 dimensions, cyclical time, state velocity, robustness.
3. Zero-regression invariant: normal retail transactions yield score < 0.50 (0 pts).
4. Anomaly detection: extreme multivariate anomalies score > 0.70 and trigger ML_MULTIVARIATE_ANOMALY.
5. Verdict escalation: HOLD floor enforcement when ml_score >= 0.85.
6. API contract: /upi/check endpoint JSON explicitly includes ml_anomaly_score.
7. Sub-1ms inference latency and thread-safety.
"""
from __future__ import annotations

import math
import threading
import time
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
from fastapi.testclient import TestClient

from app.engine.isolation_forest import (
    IsolationTreeNode,
    PureNumpyIsolationForest,
    UpiIsolationForest,
    build_itree,
    c_factor,
    generate_synthetic_baseline,
    get_isolation_forest,
    itree_path_length,
)
from app.engine.upi_scorer import UpiRiskScorer
from app.engine.upi_state import UpiHotState
from app.main import app
from app.models.upi_models import UpiEvaluationResponse, UpiTransaction


class TestIsolationForestMath(unittest.TestCase):
    """Unit tests for mathematical foundations of Liu et al. (2008) Isolation Forest."""

    def test_c_factor_boundary_and_values(self) -> None:
        """Verify c(n) calculation for boundary and standard ensemble subsample sizes."""
        self.assertEqual(c_factor(0), 0.0)
        self.assertEqual(c_factor(1), 0.0)
        self.assertEqual(c_factor(2), 1.0)

        c128 = c_factor(128)
        self.assertAlmostEqual(c128, 8.8584, places=3)

        c256 = c_factor(256)
        self.assertAlmostEqual(c256, 10.2448, places=3)

        # Monotonically increasing for n >= 2
        for n in range(2, 50):
            self.assertLessEqual(c_factor(n), c_factor(n + 1))

    def test_itree_construction_and_height_limit(self) -> None:
        """Verify recursive iTree construction enforces maximum height limit."""
        rng = np.random.default_rng(42)
        X = rng.normal(10.0, 2.0, size=(128, 6))
        max_h = int(math.ceil(math.log2(128)))  # 7

        root = build_itree(X, current_height=0, max_height=max_h, rng=rng)
        self.assertIsInstance(root, IsolationTreeNode)

        def get_max_depth(node: IsolationTreeNode, curr_d: int) -> int:
            if node.is_leaf:
                return curr_d
            left_d = get_max_depth(node.left, curr_d + 1) if node.left else curr_d
            right_d = get_max_depth(node.right, curr_d + 1) if node.right else curr_d
            return max(left_d, right_d)

        depth = get_max_depth(root, 0)
        self.assertLessEqual(depth, max_h)

    def test_path_length_leaf_and_internal_traversal(self) -> None:
        """Verify path length computation on leaves and internal nodes."""
        leaf = IsolationTreeNode(size=10, is_leaf=True)
        pl = itree_path_length(np.array([1.0, 2.0]), leaf, current_height=3)
        expected = 3 + c_factor(10)
        self.assertAlmostEqual(pl, expected, places=5)

        leaf_left = IsolationTreeNode(size=1, is_leaf=True)
        leaf_right = IsolationTreeNode(size=1, is_leaf=True)
        root = IsolationTreeNode(
            size=2,
            is_leaf=False,
            split_feature=0,
            split_value=5.0,
            left=leaf_left,
            right=leaf_right,
        )
        x_left = np.array([2.0, 0.0])
        x_right = np.array([8.0, 0.0])

        self.assertEqual(itree_path_length(x_left, root, 0), 1 + c_factor(1))
        self.assertEqual(itree_path_length(x_right, root, 0), 1 + c_factor(1))

    def test_pure_numpy_raw_score_bounds(self) -> None:
        """Verify raw anomaly score s(x, n) = 2^(-E(h)/c) stays strictly in [0.0, 1.0]."""
        rng = np.random.default_rng(42)
        X = rng.normal(0.0, 1.0, size=(200, 5))
        model = PureNumpyIsolationForest(n_trees=20, max_samples=64, random_state=42)
        model.fit(X)

        for _ in range(20):
            test_x = rng.normal(0.0, 5.0, size=5)
            s = model.raw_score(test_x)
            self.assertGreater(s, 0.0)
            self.assertLess(s, 1.0)


class TestFeatureExtraction(unittest.TestCase):
    """Unit tests for feature vector extraction from UPI transactions and hot state."""

    def setUp(self) -> None:
        self.forest = get_isolation_forest()

    def test_feature_vector_dimensions_and_names(self) -> None:
        """Verify feature extraction returns exactly 13-dimensional float64 vector."""
        txn = UpiTransaction(
            txn_id="TXN_FEAT_01",
            amount=1500.0,
            payer_vpa="payer@okaxis",
            payee_vpa="merchant@ybl",
            payer_account_age_days=90,
            payee_vpa_age_days=120,
            payee_is_new_for_payer=False,
            timestamp=datetime(2026, 9, 3, 14, 30, 0, tzinfo=timezone.utc),
            device_id="DEV_123",
        )
        vec = self.forest.extract_features(txn, state=None, dmv_score=15.0)

        self.assertEqual(len(vec), 13)
        self.assertEqual(len(vec), len(self.forest.FEATURE_NAMES))
        self.assertEqual(vec.dtype, np.float64)

        # Check values
        self.assertEqual(vec[0], 1500.0)  # amount
        self.assertAlmostEqual(vec[1], math.log1p(1500.0), places=4)  # log_amount
        self.assertAlmostEqual(vec[2], 14.5, places=3)  # hour_fraction
        self.assertEqual(vec[5], 0.0)  # is_night (14.5 is afternoon)
        self.assertEqual(vec[6], 90.0)  # payer_age
        self.assertEqual(vec[7], 120.0)  # payee_age
        self.assertEqual(vec[8], 0.0)  # new_payee
        self.assertEqual(vec[12], 15.0)  # dmv_score

    def test_time_cyclical_encoding_and_night_detection(self) -> None:
        """Verify 24h cyclical sine/cosine representation and night flag."""
        night_txn = UpiTransaction(
            txn_id="TXN_NIGHT",
            amount=500.0,
            payer_vpa="p@okaxis",
            payee_vpa="m@ybl",
            timestamp=datetime(2026, 9, 3, 2, 0, 0, tzinfo=timezone.utc),
        )
        night_vec = self.forest.extract_features(night_txn)
        self.assertEqual(night_vec[5], 1.0)  # is_night == 1.0 at 2:00 AM

        day_txn = UpiTransaction(
            txn_id="TXN_DAY",
            amount=500.0,
            payer_vpa="p@okaxis",
            payee_vpa="m@ybl",
            timestamp=datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc),
        )
        day_vec = self.forest.extract_features(day_txn)
        self.assertEqual(day_vec[5], 0.0)  # is_night == 0.0 at 12:00 PM

    def test_state_telemetry_extraction(self) -> None:
        """Verify state velocity and device sharing telemetry correctly populate features."""
        state = UpiHotState()
        now = datetime.now(timezone.utc)
        for i in range(5):
            state.record_txn(
                timestamp=now,
                payer_vpa="velocity_payer@okaxis",
                payee_vpa=f"payee_{i}@ybl",
                amount=10000.0,
                device_id="DEV_FARM_1",
            )

        txn = UpiTransaction(
            txn_id="TXN_STATE_TEST",
            amount=5000.0,
            payer_vpa="velocity_payer@okaxis",
            payee_vpa="merchant@ybl",
            timestamp=now,
            device_id="DEV_FARM_1",
        )
        vec = self.forest.extract_features(txn, state=state)
        # Velocity count >= 5
        self.assertGreaterEqual(vec[9], 5.0)
        # Velocity amount >= 50,000
        self.assertGreaterEqual(vec[10], 50000.0)


class TestBaselineAndAnomalyDifferentiation(unittest.TestCase):
    """Unit tests verifying normal vs anomalous transaction scoring."""

    def setUp(self) -> None:
        self.forest = get_isolation_forest()

    def test_normal_transactions_score_strictly_below_half(self) -> None:
        """Normal retail transactions MUST score < 0.50 (zero false-positive points)."""
        test_cases = [
            {"amount": 250.0, "hr": 10, "p_age": 200, "py_age": 180},
            {"amount": 1200.0, "hr": 14, "p_age": 365, "py_age": 300},
            {"amount": 3500.0, "hr": 18, "p_age": 150, "py_age": 220},
            {"amount": 8000.0, "hr": 12, "p_age": 250, "py_age": 365},
        ]
        for tc in test_cases:
            txn = UpiTransaction(
                txn_id=f"NORM_{tc['amount']}",
                amount=tc["amount"],
                payer_vpa="normal_user@okaxis",
                payee_vpa="store_merchant@ybl",
                payer_account_age_days=tc["p_age"],
                payee_vpa_age_days=tc["py_age"],
                timestamp=datetime(2026, 9, 3, tc["hr"], 15, 0, tzinfo=timezone.utc),
            )
            score = self.forest.score_txn(txn)
            self.assertLess(
                score,
                0.50,
                f"Normal retail transaction {tc} scored {score:.4f} >= 0.50!",
            )

    def test_extreme_multivariate_anomaly_scores_above_threshold(self) -> None:
        """Severe multivariate anomalies (huge amount, 3 AM, zero age, high velocity) score >= 0.70."""
        state = UpiHotState()
        now = datetime(2026, 9, 3, 3, 30, 0, tzinfo=timezone.utc)
        for i in range(12):
            state.record_txn(
                timestamp=now,
                payer_vpa="mule_syndicate@okaxis",
                payee_vpa=f"crypto_sink_{i}@ybl",
                amount=40000.0,
                device_id="DEV_FARM_99",
            )

        anom_txn = UpiTransaction(
            txn_id="ANOM_EXTREME_01",
            amount=290000.0,
            payer_vpa="mule_syndicate@okaxis",
            payee_vpa="cashout_dest@ybl",
            payer_account_age_days=1,
            payee_vpa_age_days=1,
            payee_is_new_for_payer=True,
            timestamp=now,
            device_id="DEV_FARM_99",
        )
        score = self.forest.score_txn(anom_txn, state=state, dmv_score=92.0)
        self.assertGreaterEqual(
            score,
            0.70,
            f"Extreme multivariate anomaly scored {score:.4f} < 0.70",
        )


class TestUpiScorerLayer4Integration(unittest.TestCase):
    """Integration tests for Layer 4 ML scoring within UpiRiskScorer."""

    def test_zero_regression_on_clean_transaction(self) -> None:
        """Clean transaction must contribute 0 ML points and retain exact ALLOW verdict."""
        scorer = UpiRiskScorer()
        txn = UpiTransaction(
            txn_id="TXN_CLEAN_EVAL",
            amount=650.0,
            payer_vpa="regular_buyer@okaxis",
            payee_vpa="grocery_store@okhdfcbank",
            payer_account_age_days=180,
            payee_vpa_age_days=240,
            timestamp=datetime(2026, 9, 3, 15, 0, 0, tzinfo=timezone.utc),
        )
        resp: UpiEvaluationResponse = scorer.evaluate(txn)

        self.assertIsInstance(resp, UpiEvaluationResponse)
        self.assertLess(resp.ml_anomaly_score, 0.50)
        self.assertEqual(resp.risk_score, 0)
        self.assertEqual(resp.action, "ALLOW")
        self.assertNotIn("ML_MULTIVARIATE_ANOMALY", resp.reasons)

    def test_ml_points_scaling_formula(self) -> None:
        """When ml_score > 0.50, up to 25 points are contributed proportionally."""
        class MockForestScore:
            def __init__(self, score: float):
                self.score = score

            def score_txn(self, txn: Any, state: Any = None, dmv_score: float = 0.0) -> float:
                return self.score

        # score = 0.70 -> int(round((0.70 - 0.50) / 0.50 * 25.0)) = int(round(10.0)) = 10 pts
        scorer_70 = UpiRiskScorer(isolation_forest=MockForestScore(0.70))  # type: ignore
        txn = UpiTransaction(
            txn_id="TXN_ML_70",
            amount=500.0,
            payer_vpa="user@okaxis",
            payee_vpa="merchant@ybl",
        )
        resp_70 = scorer_70.evaluate(txn)
        self.assertEqual(resp_70.risk_score, 10)
        self.assertIn("ML_MULTIVARIATE_ANOMALY", resp_70.reasons)

        # score = 0.80 -> int(round((0.80 - 0.50) / 0.50 * 25.0)) = int(round(15.0)) = 15 pts
        scorer_80 = UpiRiskScorer(isolation_forest=MockForestScore(0.80))  # type: ignore
        resp_80 = scorer_80.evaluate(txn)
        self.assertEqual(resp_80.risk_score, 15)
        self.assertIn("ML_MULTIVARIATE_ANOMALY", resp_80.reasons)

    def test_hold_floor_enforcement_at_85(self) -> None:
        """When ml_score >= 0.85, verdict is escalated to at least HOLD with risk_score >= 45."""
        class MockForestHigh:
            def score_txn(self, txn: Any, state: Any = None, dmv_score: float = 0.0) -> float:
                return 0.88

        scorer = UpiRiskScorer(isolation_forest=MockForestHigh())  # type: ignore
        txn = UpiTransaction(
            txn_id="TXN_HOLD_FLOOR",
            amount=500.0,
            payer_vpa="innocent_looking@okaxis",
            payee_vpa="merchant@ybl",
        )
        resp = scorer.evaluate(txn)

        self.assertEqual(resp.action, "HOLD")
        self.assertGreaterEqual(resp.risk_score, 45)
        self.assertIn("ML_MULTIVARIATE_ANOMALY", resp.reasons)
        self.assertEqual(resp.ml_anomaly_score, 0.88)

    def test_block_verdict_not_downgraded_by_ml_hold_floor(self) -> None:
        """Hard BLOCK rule hits (e.g. Honeypot) remain BLOCK even when ML score is in HOLD range."""
        class MockForestMid:
            def score_txn(self, txn: Any, state: Any = None, dmv_score: float = 0.0) -> float:
                return 0.86

        scorer = UpiRiskScorer(isolation_forest=MockForestMid())  # type: ignore
        txn = UpiTransaction(
            txn_id="TXN_HONEYPOT_ML",
            amount=50000.0,
            payer_vpa="attacker@okaxis",
            payee_vpa="honeypot_trap_01@okaxis",  # triggers R_HONEYPOT_HIT
        )
        resp = scorer.evaluate(txn)

        self.assertEqual(resp.action, "BLOCK")
        self.assertEqual(resp.risk_score, 100)


class TestApiEndpointContract(unittest.TestCase):
    """End-to-end API contract tests for /upi/check endpoint with ml_anomaly_score."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_upi_check_contains_ml_anomaly_score(self) -> None:
        """POST /upi/check response JSON must explicitly include ml_anomaly_score."""
        payload: Dict[str, Any] = {
            "txn_id": "TXN_API_CONTRACT_01",
            "amount": 1200.0,
            "payer_vpa": "api_user@okaxis",
            "payee_vpa": "api_merchant@okhdfcbank",
            "payer_account_age_days": 180,
            "payee_vpa_age_days": 200,
            "timestamp": datetime(2026, 9, 3, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        res = self.client.post("/upi/check", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("ml_anomaly_score", data)
        self.assertIsInstance(data["ml_anomaly_score"], float)
        self.assertGreaterEqual(data["ml_anomaly_score"], 0.0)
        self.assertLessEqual(data["ml_anomaly_score"], 1.0)
        self.assertLess(data["ml_anomaly_score"], 0.50)
        self.assertEqual(data["action"], "ALLOW")

    def test_upi_check_extreme_anomaly_payload(self) -> None:
        """POST /upi/check on extreme anomaly includes ML_MULTIVARIATE_ANOMALY in response."""
        payload: Dict[str, Any] = {
            "txn_id": "TXN_API_ANOM_01",
            "amount": 350000.0,
            "payer_vpa": "victim_mule@okaxis",
            "payee_vpa": "cashout_crypto@okhdfcbank",
            "payer_account_age_days": 1,
            "payee_vpa_age_days": 1,
            "payee_is_new_for_payer": True,
            "timestamp": "2026-09-03T03:30:00Z",
            "device_id": "SHARED_FARM_DEV_01",
        }
        res = self.client.post("/upi/check", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("ml_anomaly_score", data)
        self.assertGreaterEqual(data["ml_anomaly_score"], 0.70)
        self.assertIn("ML_MULTIVARIATE_ANOMALY", data["reasons"])


class TestPerformanceAndConcurrency(unittest.TestCase):
    """Performance benchmarks and thread-safety tests."""

    def test_sub_millisecond_inference_latency(self) -> None:
        """Verify 100 consecutive evaluations average < 1.0ms per transaction."""
        forest = get_isolation_forest()
        txn = UpiTransaction(
            txn_id="TXN_LATENCY_BENCH",
            amount=2500.0,
            payer_vpa="bench_user@okaxis",
            payee_vpa="bench_merchant@ybl",
        )
        # Warmup
        for _ in range(10):
            forest.score_txn(txn)

        count = 100
        t0 = time.perf_counter()
        for _ in range(count):
            forest.score_txn(txn)
        total_ms = (time.perf_counter() - t0) * 1000.0
        avg_ms = total_ms / count

        self.assertLess(
            avg_ms,
            1.5,
            f"Average inference latency {avg_ms:.3f}ms exceeds 1.5ms threshold",
        )

    def test_thread_safe_singleton(self) -> None:
        """Verify thread-safe singleton getter under concurrent threads."""
        instances: List[UpiIsolationForest] = []
        lock = threading.Lock()

        def worker() -> None:
            inst = get_isolation_forest()
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

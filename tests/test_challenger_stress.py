"""Empirical Challenger 1 Stress Harness & Adversarial Validation Suite.

Adversarially challenges Sprint 2 backend implementations:
- SAR PDF generation under toxic, high-volume, and extreme inputs
- Auto-Feed lifecycle under race conditions, rapid toggles, boundary clamps
- 7x24 Heatmap structure, temporal boundary precision, rolling 30-day filtering
- Fresh account scoring escalation matrix
"""
from __future__ import annotations

import concurrent.futures
import io
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.engine.upi_rules import FRESH_VPA_DAYS, rule_new_account_high_value
from app.forensics.sar_pdf import build_sar_pdf
from app.main import app
from app.models.upi_models import UpiTransaction
from app.services.autofeed import AutoFeedEngine
from app.services.upi_cases import UpiCaseService


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# CHALLENGE 1: SAR PDF BINARY INTEGRITY & ADVERSARIAL RESILIENCE
# ==============================================================================

class TestChallengeSarPdf:
    def test_sar_pdf_magic_bytes_and_trailer(self):
        """Verify %PDF-1.4 magic header and proper trailer structure."""
        case_data = {
            "case_id": "CASE_STRESS_001",
            "verdict": "BLOCK",
            "risk_score": 95,
            "status": "OPEN",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payer_vpa": "victim@okaxis",
            "payee_vpa": "mule@okhdfcbank",
            "amount": 250000.0,
            "trigger_txn_id": "TXN_STRESS_001",
            "reasons": ["R_SIM_DEVICE_MISMATCH", "R_IMPOSSIBLE_TRAVEL"],
            "rule_hits": [
                {"code": "R_SIM_DEVICE_MISMATCH", "points": 30, "detail": "SIM swap detected"},
                {"code": "R_IMPOSSIBLE_TRAVEL", "points": 35, "detail": "1200 km/h velocity"},
            ],
            "ring_members_vpas": [f"mule_{i}@okhdfcbank" for i in range(10)],
            "ring_hash": "RING_STRESS_HASH_ABC",
            "dmv_score": 88.5,
            "campaign_id": "CAMP_STRESS_01",
        }
        pdf_bytes = build_sar_pdf(case_data)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-1.4")
        assert b"%%EOF" in pdf_bytes[-1024:]

    def test_sar_pdf_extreme_toxic_payload(self):
        """Stress-test with empty dictionary, unicode emojis, huge strings, and zero/negative amounts."""
        toxic_case = {
            "case_id": "CASE_TOXIC_⚠️_🎉_002",
            "verdict": "HOLD",
            "risk_score": 0,
            "status": "UNDER_REVIEW",
            "payer_vpa": "payer_🧪@okaxis",
            "payee_vpa": "payee_💥@okhdfcbank",
            "amount": -500.0,
            "trigger_txn_id": "TXN_⚠️_999",
            "reasons": ["⚠️_REASON_" + "X" * 200],
            "rule_hits": [{"code": "UNKNOWN_RULE", "points": 999, "detail": "🔥" * 100}],
            "ring_members_vpas": [f"mule_node_{i}_👾@psp" for i in range(200)],
            "ring_hash": "A" * 500,
            "dmv_score": -10.0,
            "sar_markdown": "# Custom Toxic Markdown\n" + ("Repeating text line for pagination stress.\n" * 50),
        }
        pdf_bytes = build_sar_pdf(toxic_case)
        assert pdf_bytes.startswith(b"%PDF-1.4")
        assert b"%%EOF" in pdf_bytes[-1024:]

    def test_sar_pdf_empty_case_fallback(self):
        """Verify building SAR PDF on an empty dict does not throw uncaught exception."""
        pdf_bytes = build_sar_pdf({})
        assert pdf_bytes.startswith(b"%PDF-1.4")

    def test_sar_pdf_404_nonexistent_routes(self, client):
        """Verify both endpoints return exact 404 for missing cases."""
        r1 = client.get("/cases/NONEXISTENT_CASE_99999/sar/pdf")
        assert r1.status_code == 404
        assert "not found" in r1.json()["detail"].lower()

        r2 = client.get("/upi/cases/NONEXISTENT_CASE_99999/sar/pdf")
        assert r2.status_code == 404
        assert "not found" in r2.json()["detail"].lower()

    def test_sar_pdf_batch_generation_memory_stability(self):
        """Generate 30 PDFs consecutively to ensure Matplotlib figures close cleanly and memory does not leak."""
        for i in range(30):
            case = {
                "case_id": f"CASE_BATCH_{i}",
                "amount": float(i * 1000),
                "payer_vpa": f"user_{i}@okaxis",
                "payee_vpa": f"merchant_{i}@paytm",
            }
            res = build_sar_pdf(case)
            assert len(res) > 500


# ==============================================================================
# CHALLENGE 2: AUTO-FEED LIFECYCLE, CONCURRENCY & BOUNDARY CLAMPS
# ==============================================================================

class TestChallengeAutoFeed:
    def test_autofeed_boundary_clamps(self):
        """Test rate_tps and fraud_ratio boundary clamping."""
        engine = AutoFeedEngine()
        try:
            # Over max TPS (50.0)
            res1 = engine.start(rate_tps=999.0, fraud_ratio=5.0)
            assert res1["active"] is True
            assert res1["rate_tps"] == 50.0
            status = engine.get_status()
            assert status["rate_tps"] == 50.0
            assert status["fraud_ratio"] == 1.0
            engine.stop()

            # Under min TPS (0.1) & negative fraud ratio
            res2 = engine.start(rate_tps=-10.0, fraud_ratio=-0.5)
            assert res2["active"] is True
            assert res2["rate_tps"] == 0.1
            status2 = engine.get_status()
            assert status2["rate_tps"] == 0.1
            assert status2["fraud_ratio"] == 0.0
            engine.stop()
        finally:
            engine.stop()

    def test_autofeed_idempotency_and_double_calls(self):
        """Test double start and double stop idempotency."""
        engine = AutoFeedEngine()
        try:
            r_start1 = engine.start(rate_tps=5.0)
            assert r_start1["status"] == "started"
            assert r_start1["active"] is True

            r_start2 = engine.start(rate_tps=10.0)
            assert r_start2["status"] == "already_running"
            assert r_start2["active"] is True

            r_stop1 = engine.stop()
            assert r_stop1["status"] == "stopped"
            assert r_stop1["active"] is False

            r_stop2 = engine.stop()
            assert r_stop2["status"] == "not_running"
            assert r_stop2["active"] is False
        finally:
            engine.stop()

    def test_autofeed_rapid_toggle_stress(self):
        """Rapidly toggle start/stop 15 times to stress thread lifecycle and avoid deadlock."""
        engine = AutoFeedEngine()
        try:
            for _ in range(15):
                engine.start(rate_tps=20.0)
                assert engine.is_active() is True
                time.sleep(0.01)
                engine.stop()
                assert engine.is_active() is False
        finally:
            engine.stop()

    def test_autofeed_concurrent_requests_race_condition(self, client):
        """Simultaneously call start, status, and stop across 10 threads."""
        def call_endpoint(action: str):
            if action == "start":
                return client.post("/upi/autofeed/start", json={"rate_tps": 15.0, "fraud_ratio": 0.3})
            elif action == "status":
                return client.get("/upi/autofeed/status")
            else:
                return client.post("/upi/autofeed/stop")

        actions = ["start", "status", "start", "status", "stop", "status", "stop", "start", "status", "stop"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_endpoint, act) for act in actions]
            results = [f.result() for f in futures]

        for r in results:
            assert r.status_code == 200

        # Clean up
        client.post("/upi/autofeed/stop")


# ==============================================================================
# CHALLENGE 3: 7x24 HEATMAP MATRIX & ANALYTICS INTEGRITY
# ==============================================================================

class TestChallengeHeatmap:
    def test_heatmap_exact_dimensions_and_keys(self, client):
        """Verify heatmap has exactly 168 entries (7x24) with correct keys and types."""
        resp = client.get("/upi/stats/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "workload_heatmap" in data
        heatmap = data["workload_heatmap"]
        assert len(heatmap) == 168

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        seen_coords = set()
        for cell in heatmap:
            assert "day" in cell and 0 <= cell["day"] <= 6
            assert "day_name" in cell and cell["day_name"] == day_names[cell["day"]]
            assert "hour" in cell and 0 <= cell["hour"] <= 23
            assert "count" in cell and isinstance(cell["count"], int) and cell["count"] >= 0
            assert "total_amount" in cell and isinstance(cell["total_amount"], (int, float)) and cell["total_amount"] >= 0.0
            seen_coords.add((cell["day"], cell["hour"]))

        assert len(seen_coords) == 168

    def test_heatmap_rolling_30_day_boundary(self):
        """Verify cases older than 30 days are excluded, while cases <= 30 days are counted."""
        service = UpiCaseService()
        now = datetime.now(timezone.utc)

        # Inject case from 10 days ago (within 30d window)
        case_inside = {
            "case_id": "CASE_HEAT_IN_01",
            "verdict": "HOLD",
            "amount": 50000.0,
            "created_at": (now - timedelta(days=10)).isoformat(),
            "payer_vpa": "payer1@okaxis",
            "payee_vpa": "payee1@okhdfcbank",
        }
        # Inject case from 45 days ago (outside 30d window)
        case_outside = {
            "case_id": "CASE_HEAT_OUT_01",
            "verdict": "BLOCK",
            "amount": 100000.0,
            "created_at": (now - timedelta(days=45)).isoformat(),
            "payer_vpa": "payer2@okaxis",
            "payee_vpa": "payee2@okhdfcbank",
        }

        service._cases = {"CASE_HEAT_IN_01": case_inside, "CASE_HEAT_OUT_01": case_outside}
        analytics = service.get_analytics()
        heatmap = analytics["workload_heatmap"]

        total_counted = sum(cell["count"] for cell in heatmap)
        total_amount = sum(cell["total_amount"] for cell in heatmap)

        assert total_counted == 1
        assert total_amount == 50000.0


# ==============================================================================
# CHALLENGE 4: FRESH ACCOUNT SCORING ESCALATION MATRIX
# ==============================================================================

class TestChallengeScoringMatrix:
    @pytest.mark.parametrize(
        "age_days,amount,expected_pts",
        [
            # Fresh accounts (age < 15 days = FRESH_VPA_DAYS)
            (0, 10_000_000.0, 50),
            (1, 10_000_000.0, 50),
            (5, 1_000_000.0, 50),
            (10, 500_000.0, 45),
            (14, 100_000.0, 45),
            (14, 50_000.0, 25),
            (14, 10_000.0, 15),
            (14, 9_999.0, 0),
            # Boundary check: age == 15 (FRESH_VPA_DAYS threshold) -> rule should not fire
            (15, 10_000_000.0, 0),
            (15, 100_000.0, 0),
            (30, 10_000_000.0, 0),
            (90, 500_000.0, 0),
        ],
    )
    def test_fresh_account_rule_escalation(self, age_days, amount, expected_pts):
        txn = UpiTransaction(
            txn_id="TXN_SCORE_TEST",
            timestamp=datetime.now(timezone.utc),
            amount=amount,
            payer_vpa="fresh_user@okaxis",
            payee_vpa="some_merchant@okhdfcbank",
            payer_account_age_days=age_days,
        )
        hit = rule_new_account_high_value(txn)
        if expected_pts == 0:
            assert hit is None
        else:
            assert hit is not None
            assert hit.points == expected_pts
            assert hit.code == "NEW_ACCOUNT_HIGH_VALUE"

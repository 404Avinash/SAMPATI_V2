"""Comprehensive Unit, Integration, and Boundary Test Suite for VPA Honeypot Network.

Tests cover:
1. Seeded Honeypot VPA Registry & prefix detection
2. Thread-safe hit counting, last-hit timestamps, and 24h rolling aggregation
3. R_HONEYPOT_HIT detection rule (100 points, CRITICAL, BLOCK verdict, reasons)
4. Composite 3-layer risk scoring behavior for honeypot transactions
5. Service-level telemetry & stats aggregation (honeypot_hits_24h, honeypot_hits)
6. REST API endpoints: /upi/check, /upi/stats, /upi/honeypots, /federation/honeypots
7. Edge cases, concurrency stress, and rolling window eviction
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
import pytest

from fastapi.testclient import TestClient

from app.engine.honeypot import (
    DEFAULT_HONEYPOTS,
    HoneypotRegistry,
    get_honeypot_registry,
)
from app.engine.upi_rules import evaluate_rules, rule_honeypot_hit
from app.engine.upi_scorer import UpiRiskScorer, get_upi_scorer
from app.engine.upi_state import get_upi_state
from app.main import app
from app.models.upi_models import UpiTransaction
from app.services.upi_cases import RULE_METADATA, get_upi_case_service


@pytest.fixture(autouse=True)
def reset_global_honeypot():
    """Reset global honeypot registry and service state between tests."""
    reg = get_honeypot_registry()
    reg.clear()
    svc = get_upi_case_service()
    svc.clear()
    yield
    reg.clear()
    svc.clear()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# ── 1. Registry Unit & Seed Tests ─────────────────────────────────────────────

class TestHoneypotRegistryUnit:
    """Test suite for HoneypotRegistry core data structures and methods."""

    def test_seeded_default_vpas_present(self):
        """Verify all mandated seeded synthetic honeypot VPAs exist in registry."""
        reg = HoneypotRegistry()
        expected_seeds = [
            "honeypot_trap_01@okaxis",
            "honeypot_mule_99@okhdfcbank",
            "phish_trap_node@okicici",
            "botnet_sink_04@oksbi",
            "mule_honeypot_prime@okaxis",
        ]
        for seed in expected_seeds:
            assert reg.is_honeypot(seed) is True, f"Expected {seed} to be recognized as honeypot"

    def test_case_insensitivity_and_whitespace(self):
        """Verify VPA matching is case-insensitive and trims whitespace."""
        reg = HoneypotRegistry()
        assert reg.is_honeypot("HONEYPOT_TRAP_01@OKAXIS") is True
        assert reg.is_honeypot("  honeypot_mule_99@okhdfcbank  ") is True
        assert reg.is_honeypot("Phish_Trap_Node@OKICICI") is True

    def test_prefix_matching_for_synthetic_traps(self):
        """Verify prefix patterns automatically match dynamic honeypot traps."""
        reg = HoneypotRegistry()
        assert reg.is_honeypot("honeypot_custom_trap@okaxis") is True
        assert reg.is_honeypot("phish_trap_999@paytm") is True
        assert reg.is_honeypot("botnet_sink_alpha@ybl") is True
        assert reg.is_honeypot("mule_honeypot_sink@oksbi") is True

    def test_legitimate_vpas_not_matched(self):
        """Verify legitimate VPAs are never flagged as honeypots."""
        reg = HoneypotRegistry()
        legit_vpas = [
            "avinash.jha@okaxis",
            "user9823@okhdfcbank",
            "merchant_store@okicici",
            "alice.bob@paytm",
            "rahul_sharma@oksbi",
            "swiggy.orders@ybl",
        ]
        for vpa in legit_vpas:
            assert reg.is_honeypot(vpa) is False, f"Legitimate VPA {vpa} should not match honeypot"

    def test_invalid_and_empty_vpas(self):
        """Verify empty, None, or invalid inputs return False without raising."""
        reg = HoneypotRegistry()
        assert reg.is_honeypot("") is False
        assert reg.is_honeypot(None) is False  # type: ignore
        assert reg.is_honeypot("   ") is False
        assert reg.is_honeypot(123) is False  # type: ignore

    def test_dynamic_registration(self):
        """Verify new honeypot VPAs can be registered at runtime."""
        reg = HoneypotRegistry()
        custom_trap = "special_honeypot_vector@okhdfcbank"
        assert reg.is_honeypot(custom_trap) is False
        reg.register_honeypot(custom_trap)
        assert reg.is_honeypot(custom_trap) is True

    def test_hit_recording_and_telemetry(self):
        """Verify record_hit accurately updates hit counts, amounts, and timestamps."""
        reg = HoneypotRegistry()
        target = "honeypot_trap_01@okaxis"
        assert reg.total_hits() == 0
        assert reg.get_hits_24h() == 0

        reg.record_hit(vpa=target, txn_id="TXN_001", amount=1500.50, payer_vpa="victim@okhdfcbank")

        assert reg.total_hits() == 1
        assert reg.get_hits_24h() == 1
        assert reg.total_amount_deflected() == 1500.50

        stats = reg.get_stats()
        assert stats["total_hits"] == 1
        assert stats["hits_24h"] == 1
        assert stats["total_amount_deflected"] == 1500.50

        honeypot_items = {item["vpa"]: item for item in stats["honeypots"]}
        assert target in honeypot_items
        assert honeypot_items[target]["hit_count"] == 1
        assert honeypot_items[target]["amount_deflected"] == 1500.50
        assert honeypot_items[target]["last_hit_at"] is not None

    def test_rolling_24h_window_aggregation(self):
        """Verify hits older than 24 hours are excluded from get_hits_24h()."""
        reg = HoneypotRegistry()
        now = datetime.now(timezone.utc)
        target = "honeypot_trap_01@okaxis"

        # Record a fresh hit
        reg.record_hit(vpa=target, txn_id="TXN_NOW", amount=1000.0)

        # Inject an entry from 25 hours ago into _hit_log for window boundary testing
        past_25h = now - timedelta(hours=25)
        with reg._lock:
            reg._hit_log.append({
                "vpa": target,
                "txn_id": "TXN_OLD",
                "payer_vpa": "old@ybl",
                "amount": 2000.0,
                "timestamp": past_25h.isoformat(),
                "epoch": past_25h.timestamp(),
            })
            reg._hit_counts[target] += 1
            reg._amount_deflected[target] += 2000.0

        assert reg.total_hits() == 2
        assert reg.get_hits_24h(now=now) == 1

    def test_thread_safe_concurrent_hits(self):
        """Verify HoneypotRegistry is thread-safe under heavy parallel hit load."""
        reg = HoneypotRegistry()
        target = "honeypot_trap_01@okaxis"
        threads = []
        hits_per_thread = 50
        num_threads = 10

        def hit_worker(thread_id: int):
            for i in range(hits_per_thread):
                reg.record_hit(
                    vpa=target,
                    txn_id=f"TXN_T{thread_id}_{i}",
                    amount=10.0,
                    payer_vpa=f"payer_{thread_id}@okaxis",
                )

        for t_id in range(num_threads):
            t = threading.Thread(target=hit_worker, args=(t_id,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        expected_total = num_threads * hits_per_thread
        assert reg.total_hits() == expected_total
        assert reg.get_hits_24h() == expected_total
        assert reg.total_amount_deflected() == expected_total * 10.0


# ── 2. Rule & Scorer Layer Tests ──────────────────────────────────────────────

class TestHoneypotRulesAndScorer:
    """Test suite for R_HONEYPOT_HIT rule triggering and 3-layer scoring integration."""

    def test_rule_honeypot_hit_direct_trigger(self):
        """Verify rule_honeypot_hit awards 100 points with code R_HONEYPOT_HIT."""
        txn = UpiTransaction(
            txn_id="TXN_HP_001",
            payer_vpa="victim@okhdfcbank",
            payee_vpa="honeypot_trap_01@okaxis",
            amount=5000.0,
        )
        hit = rule_honeypot_hit(txn)
        assert hit is not None
        assert hit.code == "R_HONEYPOT_HIT"
        assert hit.points == 100
        assert "Transaction directed to active synthetic honeypot VPA" in hit.detail

    def test_rule_honeypot_hit_does_not_trigger_on_legit(self):
        """Verify rule_honeypot_hit returns None for legitimate payees."""
        txn = UpiTransaction(
            txn_id="TXN_LEGIT_001",
            payer_vpa="alice@okaxis",
            payee_vpa="bob@okhdfcbank",
            amount=5000.0,
        )
        hit = rule_honeypot_hit(txn)
        assert hit is None

    def test_evaluate_rules_includes_r_honeypot_hit(self):
        """Verify evaluate_rules includes R_HONEYPOT_HIT in rule hits list."""
        state = get_upi_state()
        txn = UpiTransaction(
            txn_id="TXN_HP_002",
            payer_vpa="mule_suspect@ybl",
            payee_vpa="honeypot_mule_99@okhdfcbank",
            amount=12000.0,
        )
        hits = evaluate_rules(txn, state)
        hit_codes = [h.code for h in hits]
        assert "R_HONEYPOT_HIT" in hit_codes
        hp_hit = next(h for h in hits if h.code == "R_HONEYPOT_HIT")
        assert hp_hit.points == 100

    def test_upi_scorer_guarantees_block_and_score_100(self):
        """Verify UpiRiskScorer produces risk_score=100 and action='BLOCK' for honeypot txns."""
        scorer = get_upi_scorer()
        txn = UpiTransaction(
            txn_id="TXN_HP_003",
            payer_vpa="attacker@okaxis",
            payee_vpa="phish_trap_node@okicici",
            amount=45000.0,
        )
        resp = scorer.evaluate(txn)

        assert resp.risk_score == 100
        assert resp.action == "BLOCK"
        assert "R_HONEYPOT_HIT" in resp.reasons
        assert any(h.code == "R_HONEYPOT_HIT" for h in resp.rule_breakdown)

    def test_rule_metadata_includes_r_honeypot_hit(self):
        """Verify RULE_METADATA contains R_HONEYPOT_HIT with CRITICAL severity."""
        assert "R_HONEYPOT_HIT" in RULE_METADATA
        meta = RULE_METADATA["R_HONEYPOT_HIT"]
        assert meta["severity"] == "CRITICAL"


# ── 3. UpiCaseService & Telemetry Tests ───────────────────────────────────────

class TestUpiCaseServiceHoneypot:
    """Test suite for UpiCaseService evaluation, stats, and honeypot telemetry."""

    def test_service_evaluate_opens_blocked_case_for_honeypot(self):
        """Verify UpiCaseService.evaluate() creates a BLOCK case with R_HONEYPOT_HIT."""
        svc = get_upi_case_service()
        txn = UpiTransaction(
            txn_id="TXN_HP_SVC_01",
            payer_vpa="bot_mule@oksbi",
            payee_vpa="botnet_sink_04@oksbi",
            amount=25000.0,
        )
        resp = svc.evaluate(txn)

        assert resp.action == "BLOCK"
        assert resp.risk_score == 100
        assert "R_HONEYPOT_HIT" in resp.reasons
        assert resp.case_id is not None

        case_obj = svc.get_case(resp.case_id)
        assert case_obj is not None
        assert case_obj["verdict"] == "BLOCK"
        assert case_obj["risk_score"] == 100
        assert "R_HONEYPOT_HIT" in case_obj["reasons"]

    def test_service_get_current_stats_includes_honeypot_metrics(self):
        """Verify get_current_stats() accurately aggregates honeypot_hits_24h and honeypot_hits."""
        svc = get_upi_case_service()
        stats_before = svc.get_current_stats()
        assert "honeypot_hits_24h" in stats_before
        assert "honeypot_hits" in stats_before
        initial_hits = stats_before["honeypot_hits"]

        txn = UpiTransaction(
            txn_id="TXN_HP_SVC_02",
            payer_vpa="victim_sender@okaxis",
            payee_vpa="mule_honeypot_prime@okaxis",
            amount=8000.0,
        )
        svc.evaluate(txn)

        stats_after = svc.get_current_stats()
        assert stats_after["honeypot_hits"] == initial_hits + 1
        assert stats_after["honeypot_hits_24h"] >= 1
        assert stats_after["blocked"] >= 1


# ── 4. REST API Endpoint Tests ────────────────────────────────────────────────

class TestHoneypotApiEndpoints:
    """Test suite for FastAPI endpoints /upi/check, /upi/stats, /upi/honeypots, /federation/honeypots."""

    def test_post_upi_check_honeypot_transaction(self, client: TestClient):
        """Verify POST /upi/check triggers R_HONEYPOT_HIT, BLOCK verdict, and risk score 100."""
        payload = {
            "txn_id": "TXN_API_HP_01",
            "payer_vpa": "victim@okhdfcbank",
            "payee_vpa": "honeypot_trap_01@okaxis",
            "amount": 9500.0,
            "payer_account_age_days": 180,
            "payee_vpa_age_days": 180,
        }
        res = client.post("/upi/check", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["action"] == "BLOCK"
        assert data["risk_score"] == 100
        assert "R_HONEYPOT_HIT" in data["reasons"]
        assert any(h["code"] == "R_HONEYPOT_HIT" for h in data["rule_breakdown"])

    def test_get_upi_stats_contains_honeypot_counters(self, client: TestClient):
        """Verify GET /upi/stats returns honeypot_hits_24h and honeypot_hits."""
        # Generate a honeypot hit first
        client.post("/upi/check", json={
            "txn_id": "TXN_API_HP_02",
            "payer_vpa": "victim@ybl",
            "payee_vpa": "honeypot_mule_99@okhdfcbank",
            "amount": 15000.0,
        })

        res = client.get("/upi/stats")
        assert res.status_code == 200
        data = res.json()

        assert "honeypot_hits_24h" in data
        assert "honeypot_hits" in data
        assert data["honeypot_hits_24h"] >= 1
        assert data["honeypot_hits"] >= 1

    def test_get_upi_honeypots_endpoint(self, client: TestClient):
        """Verify GET /upi/honeypots returns registered honeypots and telemetry."""
        res = client.get("/upi/honeypots")
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "ok"
        assert data["total_registered"] >= 5
        assert isinstance(data["honeypots"], list)
        assert len(data["honeypots"]) >= 5

        first_hp = data["honeypots"][0]
        assert "vpa" in first_hp
        assert "hit_count" in first_hp
        assert "amount_deflected" in first_hp
        assert "status" in first_hp

    def test_get_federation_honeypots_endpoint(self, client: TestClient):
        """Verify GET /federation/honeypots returns mesh-wide honeypot statistics."""
        # Ingest a hit via /upi/check
        client.post("/upi/check", json={
            "txn_id": "TXN_FED_HP_01",
            "payer_vpa": "mule_feeder@oksbi",
            "payee_vpa": "phish_trap_node@okicici",
            "amount": 32000.0,
        })

        res = client.get("/federation/honeypots")
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "ok"
        assert data["total_hits"] >= 1
        assert data["hits_24h"] >= 1
        assert data["total_amount_deflected"] >= 32000.0

        vpa_map = {item["vpa"]: item for item in data["honeypots"]}
        assert "phish_trap_node@okicici" in vpa_map
        assert vpa_map["phish_trap_node@okicici"]["hit_count"] >= 1
        assert vpa_map["phish_trap_node@okicici"]["amount_deflected"] >= 32000.0
        assert vpa_map["phish_trap_node@okicici"]["last_hit_at"] is not None

    def test_multiple_hits_increment_counters_accurately(self, client: TestClient):
        """Verify consecutive honeypot transactions accurately increment hit counters and amounts."""
        hp_vpa = "mule_honeypot_prime@okaxis"
        for i in range(3):
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_MULTI_HP_{i}",
                "payer_vpa": f"mule_source_{i}@okaxis",
                "payee_vpa": hp_vpa,
                "amount": 10000.0 * (i + 1),
            })
            assert res.status_code == 200
            assert res.json()["action"] == "BLOCK"

        res_stats = client.get("/federation/honeypots")
        assert res_stats.status_code == 200
        data = res_stats.json()
        vpa_item = next(item for item in data["honeypots"] if item["vpa"] == hp_vpa)
        assert vpa_item["hit_count"] == 3
        assert vpa_item["amount_deflected"] == 60000.0  # 10k + 20k + 30k

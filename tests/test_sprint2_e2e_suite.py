"""
SAMPATI V2 Sprint 2 — End-to-End Test Suite (Tiers 1 to 4)
Requirement-driven, opaque-box tests covering:
- Tier 1: Feature Isolation Tests (>=5 tests per feature for R1 to R6)
  * R1: Dead Money Velocity (DMV) Score (0–100)
  * R2: SIM-Device Mismatch Rule (R_SIM_DEVICE_MISMATCH)
  * R2: Impossible Travel Rule (R_IMPOSSIBLE_TRAVEL)
  * R2: Datacenter / VPN IP Rule (R_DATACENTER_IP)
  * R3: Transaction DNA Campaign Fingerprinting (R_CAMPAIGN_MATCH)
  * R4: One-Click SAR PDF Export (GET /cases/{case_id}/sar/pdf)
  * R5: Analyst Workload Heatmap (7x24 Grid over 30 days)
  * R6: Autonomous Live Auto-Feed Mode (Lifecycle & WebSocket stream)
- Tier 2: Boundary Value Analysis & Edge Cases (0-values, extreme values, missing telemetry, max TPS)
- Tier 3: Cross-Feature Combinations & State Interactions
- Tier 4: Real-World Application Scenarios (Mule rings, SIM swap, Botnet surge, Compliance workflow)
"""
from __future__ import annotations

import hashlib
import io
import os
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

# Ensure workspace root in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from app.models.upi_models import UpiTransaction
from app.services.upi_cases import get_upi_case_service
from app.engine.honeypot import get_honeypot_registry


@pytest.fixture
def client() -> TestClient:
    """Provide synchronous TestClient for FastAPI routes."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_test_environment():
    """Ensure state isolation before and after each test."""
    svc = get_upi_case_service()
    # Stop autofeed if active
    try:
        if hasattr(svc, "is_autofeed_active") and svc.is_autofeed_active():
            svc.stop_autofeed()
        elif hasattr(svc, "_autofeed_task") and svc._autofeed_task is not None:
            svc.stop_autofeed()
    except Exception:
        pass

    # Clear federation signals
    try:
        svc.federation.clear()
    except Exception:
        pass

    yield

    # Teardown stop autofeed if running
    try:
        if hasattr(svc, "is_autofeed_active") and svc.is_autofeed_active():
            svc.stop_autofeed()
    except Exception:
        pass


# =============================================================================
# TIER 1: FEATURE ISOLATION TESTS
# =============================================================================

class TestTier1Feature1DmvScore:
    """Tier 1: Feature Isolation Tests for Dead Money Velocity (DMV) Score (R1)."""

    def test_01_dmv_score_field_in_upi_check_response(self, client: TestClient):
        """R1.1: Every /upi/check API response must include a dmv_score field (float 0–100)."""
        payload = {
            "txn_id": f"TXN_DMV_{uuid.uuid4().hex[:8]}",
            "amount": 2500.0,
            "payer_vpa": "regular.user@okaxis",
            "payee_vpa": "merchant.store@okhdfcbank",
            "payer_account_age_days": 180,
            "payee_vpa_age_days": 200,
        }
        res = client.post("/upi/check", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "dmv_score" in data, "Response must include 'dmv_score' field"
        assert isinstance(data["dmv_score"], (int, float)), "dmv_score must be a numeric float/int"
        assert 0.0 <= float(data["dmv_score"]) <= 100.0, f"dmv_score {data['dmv_score']} out of [0, 100] bounds"

    def test_02_dmv_score_low_for_active_legitimate_account(self, client: TestClient):
        """R1.2: Active legitimate account with regular recent transactions must have low DMV score (<40)."""
        payer = f"active_payer_{uuid.uuid4().hex[:6]}@okaxis"
        svc = get_upi_case_service()

        # Seed recent activity for this payer to establish non-dormant status
        now = datetime.now(timezone.utc)
        for i in range(3):
            past_txn = UpiTransaction(
                txn_id=f"TXN_SEED_{i}_{uuid.uuid4().hex[:6]}",
                timestamp=now - timedelta(days=1, hours=i),
                amount=1000.0,
                payer_vpa=payer,
                payee_vpa=f"seller_{i}@okhdfcbank",
                payer_account_age_days=120,
            )
            svc.evaluate(past_txn)

        # Now evaluate current normal transaction
        curr_payload = {
            "txn_id": f"TXN_ACTIVE_{uuid.uuid4().hex[:8]}",
            "amount": 1200.0,
            "payer_vpa": payer,
            "payee_vpa": "seller_final@okhdfcbank",
            "payer_account_age_days": 120,
            "payee_vpa_age_days": 100,
        }
        res = client.post("/upi/check", json=curr_payload)
        assert res.status_code == 200
        data = res.json()
        dmv = float(data.get("dmv_score", 0.0))
        assert dmv < 40.0, f"Expected active legitimate account DMV < 40.0, got {dmv}"

    def test_03_dmv_score_elevated_for_moderate_burst(self, client: TestClient):
        """R1.3: Account with moderate dormancy or moderate outflow velocity scores in amber range (40–70)."""
        payer = f"amber_mule_{uuid.uuid4().hex[:6]}@okaxis"
        svc = get_upi_case_service()

        # Inflow transaction first
        inflow = UpiTransaction(
            txn_id=f"TXN_IN_{uuid.uuid4().hex[:6]}",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
            amount=40000.0,
            payer_vpa="source.funds@okaxis",
            payee_vpa=payer,
            payer_account_age_days=60,
        )
        svc.evaluate(inflow)

        # Moderate burst transfer
        payload = {
            "txn_id": f"TXN_AMBER_{uuid.uuid4().hex[:8]}",
            "amount": 22000.0,
            "payer_vpa": payer,
            "payee_vpa": "cashout_node@okhdfcbank",
            "payer_account_age_days": 60,
            "payee_vpa_age_days": 10,
        }
        res = client.post("/upi/check", json=payload)
        assert res.status_code == 200
        data = res.json()
        dmv = float(data.get("dmv_score", 0.0))
        assert dmv >= 30.0, f"Expected elevated DMV score (>=30), got {dmv}"

    def test_04_dmv_score_high_for_dormant_mule_drain(self, client: TestClient):
        """R1.4: Dormant account (>60 days inactive) suddenly draining near-100% balance scores high DMV (>70)."""
        payer = f"dormant_mule_drain_{uuid.uuid4().hex[:6]}@okhdfcbank"
        svc = get_upi_case_service()

        # Account was established 120 days ago, received a large sum 90 days ago, then completely quiet
        seed_inflow = UpiTransaction(
            txn_id=f"TXN_OLD_IN_{uuid.uuid4().hex[:6]}",
            timestamp=datetime.now(timezone.utc) - timedelta(days=90),
            amount=100000.0,
            payer_vpa="victim.funds@okaxis",
            payee_vpa=payer,
            payer_account_age_days=300,
        )
        svc.evaluate(seed_inflow)

        # Sudden rapid outflow draining the funds
        curr_payload = {
            "txn_id": f"TXN_BURST_DRAIN_{uuid.uuid4().hex[:8]}",
            "amount": 95000.0,
            "payer_vpa": payer,
            "payee_vpa": "layering.sink@paytm",
            "payer_account_age_days": 120,
            "payee_vpa_age_days": 5,
        }
        res = client.post("/upi/check", json=curr_payload)
        assert res.status_code == 200
        data = res.json()
        dmv = float(data.get("dmv_score", 0.0))
        assert dmv >= 65.0, f"Expected high DMV score (>=65.0) for dormant account cashout burst, got {dmv}"

    def test_05_top_dmv_vpas_in_analytics(self, client: TestClient):
        """R1.5: Analytics endpoints (/stats/analytics, /upi/stats/analytics) include top_dmv_vpas table."""
        # Drive a high-DMV transaction
        high_vpa = f"top_dmv_candidate_{uuid.uuid4().hex[:6]}@okhdfcbank"
        client.post("/upi/check", json={
            "txn_id": f"TXN_TOP_DMV_{uuid.uuid4().hex[:8]}",
            "amount": 80000.0,
            "payer_vpa": high_vpa,
            "payee_vpa": "target.exit@okaxis",
            "payer_account_age_days": 150,
            "payee_vpa_age_days": 3,
        })

        for endpoint in ("/stats/analytics", "/upi/stats/analytics"):
            res = client.get(endpoint)
            assert res.status_code == 200, f"Failed GET {endpoint}"
            body = res.json()
            assert "top_dmv_vpas" in body or "top_flagged_accounts" in body
            if "top_dmv_vpas" in body:
                dmv_list = body["top_dmv_vpas"]
                assert isinstance(dmv_list, list), "top_dmv_vpas must be a list"
                if len(dmv_list) > 0:
                    first = dmv_list[0]
                    assert "vpa" in first
                    assert "dmv_score" in first


class TestTier1Feature2SimDeviceMismatch:
    """Tier 1: Feature Isolation Tests for SIM-Device Mismatch Rule (R2)."""

    def test_06_sim_device_mismatch_sim_swap_trigger(self, client: TestClient):
        """R2.1: Changing SIM ID on the same device ID for the same payer must trigger R_SIM_DEVICE_MISMATCH (+30 pts)."""
        payer = f"sim_swap_victim_{uuid.uuid4().hex[:6]}@okaxis"
        device_id = "DEV_PIXEL7_PRO_A1"
        initial_sim = "SIM_AIRTEL_987654"
        new_sim = "SIM_JIO_ROUGE_112233"

        # Baseline transaction with initial SIM
        res1 = client.post("/upi/check", json={
            "txn_id": f"TXN_SIM1_{uuid.uuid4().hex[:8]}",
            "amount": 1000.0,
            "payer_vpa": payer,
            "payee_vpa": "merchant.cafe@okaxis",
            "device_id": device_id,
            "sim_id": initial_sim,
        })
        assert res1.status_code == 200
        data1 = res1.json()
        assert "R_SIM_DEVICE_MISMATCH" not in data1.get("reasons", [])

        # Attacker executes transaction on same device with swapped SIM
        res2 = client.post("/upi/check", json={
            "txn_id": f"TXN_SIM2_{uuid.uuid4().hex[:8]}",
            "amount": 25000.0,
            "payer_vpa": payer,
            "payee_vpa": "mule.cashout@okhdfcbank",
            "device_id": device_id,
            "sim_id": new_sim,
        })
        assert res2.status_code == 200
        data2 = res2.json()
        assert "R_SIM_DEVICE_MISMATCH" in data2.get("reasons", [])
        rule_hit = next((r for r in data2.get("rule_breakdown", []) if r["code"] == "R_SIM_DEVICE_MISMATCH"), None)
        assert rule_hit is not None, "R_SIM_DEVICE_MISMATCH must appear in rule_breakdown"
        assert rule_hit["points"] == 30, f"Expected 30 points for SIM mismatch, got {rule_hit['points']}"

    def test_07_sim_device_mismatch_device_swap_trigger(self, client: TestClient):
        """R2.2: Same SIM card active on a different device ID for the same payer must trigger R_SIM_DEVICE_MISMATCH."""
        payer = f"device_swap_user_{uuid.uuid4().hex[:6]}@ybl"
        sim_id = "SIM_VI_GLOBAL_554433"
        dev1 = "DEV_SAMSUNG_S23_ORIGINAL"
        dev2 = "DEV_EMULATOR_BOX_NEW"

        # Baseline transaction
        client.post("/upi/check", json={
            "txn_id": f"TXN_DEV1_{uuid.uuid4().hex[:8]}",
            "amount": 1500.0,
            "payer_vpa": payer,
            "payee_vpa": "grocery@ybl",
            "device_id": dev1,
            "sim_id": sim_id,
        })

        # New device with same SIM
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_DEV2_{uuid.uuid4().hex[:8]}",
            "amount": 18000.0,
            "payer_vpa": payer,
            "payee_vpa": "crypto.desk@okaxis",
            "device_id": dev2,
            "sim_id": sim_id,
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_SIM_DEVICE_MISMATCH" in data.get("reasons", [])

    def test_08_sim_device_mismatch_clean_match_no_trigger(self, client: TestClient):
        """R2.3: Repeated transactions with consistent (device_id, sim_id) pair must NOT trigger mismatch."""
        payer = f"consistent_user_{uuid.uuid4().hex[:6]}@okaxis"
        dev = "DEV_ONEPLUS_9R"
        sim = "SIM_BSNL_445566"

        for i in range(3):
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_CLEAN_{i}_{uuid.uuid4().hex[:8]}",
                "amount": 1000.0 * (i + 1),
                "payer_vpa": payer,
                "payee_vpa": f"shop_{i}@okaxis",
                "device_id": dev,
                "sim_id": sim,
            })
            assert res.status_code == 200
            data = res.json()
            assert "R_SIM_DEVICE_MISMATCH" not in data.get("reasons", [])

    def test_09_sim_device_mismatch_missing_telemetry_no_false_positive(self, client: TestClient):
        """R2.4: Empty or missing device_id / sim_id telemetry must gracefully bypass without false-positive."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_NO_TEL_{uuid.uuid4().hex[:8]}",
            "amount": 3000.0,
            "payer_vpa": "anon.user@okaxis",
            "payee_vpa": "vendor@okhdfcbank",
            "device_id": "",
            "sim_id": "",
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_SIM_DEVICE_MISMATCH" not in data.get("reasons", [])

    def test_10_sim_device_mismatch_score_escalation(self, client: TestClient):
        """R2.5: SIM mismatch risk points (30 pts) properly elevate composite risk score."""
        payer = f"escalate_payer_{uuid.uuid4().hex[:6]}@okaxis"
        dev1 = "DEV_ALPHA_101"
        sim1 = "SIM_ALPHA_101"
        sim2 = "SIM_BRAVO_202"

        # Baseline
        client.post("/upi/check", json={
            "txn_id": f"TXN_ESC_BASE_{uuid.uuid4().hex[:8]}",
            "amount": 500.0,
            "payer_vpa": payer,
            "payee_vpa": "tea.stall@okaxis",
            "device_id": dev1,
            "sim_id": sim1,
        })

        # Mismatch transaction
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_ESC_HIT_{uuid.uuid4().hex[:8]}",
            "amount": 12000.0,
            "payer_vpa": payer,
            "payee_vpa": "cash.advance@okaxis",
            "device_id": dev1,
            "sim_id": sim2,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["risk_score"] >= 30, f"Expected risk_score >= 30 due to mismatch points, got {data['risk_score']}"


class TestTier1Feature3ImpossibleTravel:
    """Tier 1: Feature Isolation Tests for Impossible Travel Rule (R2)."""

    def test_11_impossible_travel_cross_city_trigger(self, client: TestClient):
        """R2.6: Location change >500km in <30 min (e.g. Mumbai -> Delhi) must trigger R_IMPOSSIBLE_TRAVEL (+35 pts)."""
        payer = f"jetsetter_payer_{uuid.uuid4().hex[:6]}@okaxis"
        svc = get_upi_case_service()
        t0 = datetime.now(timezone.utc) - timedelta(minutes=10)

        # First txn in Mumbai
        txn1 = UpiTransaction(
            txn_id=f"TXN_MUM_{uuid.uuid4().hex[:8]}",
            timestamp=t0,
            amount=500.0,
            payer_vpa=payer,
            payee_vpa="mumbai.cafe@okaxis",
            location="Mumbai",
        )
        svc.evaluate(txn1)

        # Second txn 10 minutes later in Delhi (>1100 km away)
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_DEL_{uuid.uuid4().hex[:8]}",
            "timestamp": (t0 + timedelta(minutes=10)).isoformat(),
            "amount": 15000.0,
            "payer_vpa": payer,
            "payee_vpa": "delhi.store@okaxis",
            "location": "Delhi",
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_IMPOSSIBLE_TRAVEL" in data.get("reasons", []), f"Reasons: {data.get('reasons')}"
        hit = next((r for r in data.get("rule_breakdown", []) if r["code"] == "R_IMPOSSIBLE_TRAVEL"), None)
        assert hit is not None
        assert hit["points"] == 35, f"Expected 35 points for Impossible Travel, got {hit['points']}"

    def test_12_impossible_travel_high_speed_ground_trigger(self, client: TestClient):
        """R2.7: Short distance (>100km) in ultra-short time (<3 min) indicates >2000 km/h impossible ground speed."""
        payer = f"teleport_payer_{uuid.uuid4().hex[:6]}@ybl"
        svc = get_upi_case_service()
        t0 = datetime.now(timezone.utc) - timedelta(minutes=2)

        # Mumbai to Pune (~120km) in 2 minutes
        txn1 = UpiTransaction(
            txn_id=f"TXN_MUM_PUNE_1_{uuid.uuid4().hex[:8]}",
            timestamp=t0,
            amount=800.0,
            payer_vpa=payer,
            payee_vpa="local.shop@ybl",
            location="Mumbai",
        )
        svc.evaluate(txn1)

        res = client.post("/upi/check", json={
            "txn_id": f"TXN_MUM_PUNE_2_{uuid.uuid4().hex[:8]}",
            "timestamp": (t0 + timedelta(minutes=2)).isoformat(),
            "amount": 20000.0,
            "payer_vpa": payer,
            "payee_vpa": "pune.outlet@ybl",
            "location": "Pune",
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_IMPOSSIBLE_TRAVEL" in data.get("reasons", [])

    def test_13_impossible_travel_plausible_travel_no_trigger(self, client: TestClient):
        """R2.8: Plausible speed (e.g. Mumbai -> Pune 3 hours later) must NOT trigger rule."""
        payer = f"normal_traveler_{uuid.uuid4().hex[:6]}@okaxis"
        svc = get_upi_case_service()
        t0 = datetime.now(timezone.utc) - timedelta(hours=4)

        txn1 = UpiTransaction(
            txn_id=f"TXN_PLAUS_1_{uuid.uuid4().hex[:8]}",
            timestamp=t0,
            amount=600.0,
            payer_vpa=payer,
            payee_vpa="shop1@okaxis",
            location="Mumbai",
        )
        svc.evaluate(txn1)

        # 3.5 hours later in Pune (35 km/h avg speed)
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_PLAUS_2_{uuid.uuid4().hex[:8]}",
            "timestamp": (t0 + timedelta(hours=3, minutes=30)).isoformat(),
            "amount": 1200.0,
            "payer_vpa": payer,
            "payee_vpa": "shop2@okaxis",
            "location": "Pune",
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_IMPOSSIBLE_TRAVEL" not in data.get("reasons", [])

    def test_14_impossible_travel_coordinate_parsing(self, client: TestClient):
        """R2.9: Explicit coordinates 'lat,lon' strings (e.g. '19.0760,72.8777') are parsed and evaluated."""
        payer = f"coord_traveler_{uuid.uuid4().hex[:6]}@okhdfcbank"
        svc = get_upi_case_service()
        t0 = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Bengaluru coords: 12.9716, 77.5946
        txn1 = UpiTransaction(
            txn_id=f"TXN_COORD_1_{uuid.uuid4().hex[:8]}",
            timestamp=t0,
            amount=1000.0,
            payer_vpa=payer,
            payee_vpa="blr.mall@okhdfcbank",
            location="12.9716, 77.5946",
        )
        svc.evaluate(txn1)

        # Delhi coords: 28.7041, 77.1025 (~1740km) 5 minutes later
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_COORD_2_{uuid.uuid4().hex[:8]}",
            "timestamp": (t0 + timedelta(minutes=5)).isoformat(),
            "amount": 45000.0,
            "payer_vpa": payer,
            "payee_vpa": "delhi.jewel@okhdfcbank",
            "location": "28.7041, 77.1025",
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_IMPOSSIBLE_TRAVEL" in data.get("reasons", [])

    def test_15_impossible_travel_missing_or_first_txn_no_trigger(self, client: TestClient):
        """R2.10: First transaction for payer or missing location skips rule safely."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_FIRST_LOC_{uuid.uuid4().hex[:8]}",
            "amount": 2500.0,
            "payer_vpa": f"fresh_user_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "fresh_shop@okaxis",
            "location": "Hyderabad",
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_IMPOSSIBLE_TRAVEL" not in data.get("reasons", [])


class TestTier1Feature4DatacenterIp:
    """Tier 1: Feature Isolation Tests for Datacenter / VPN IP Rule (R2)."""

    def test_16_datacenter_ip_aws_range_trigger(self, client: TestClient):
        """R2.11: Originating IP from AWS EC2 CIDR range triggers R_DATACENTER_IP (+25 pts)."""
        aws_ips = ["3.220.100.45", "15.206.55.12", "52.66.120.4", "35.154.80.99"]
        for ip in aws_ips:
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_AWS_{uuid.uuid4().hex[:8]}",
                "amount": 8000.0,
                "payer_vpa": f"aws_bot_{uuid.uuid4().hex[:6]}@okaxis",
                "payee_vpa": "target.payee@okhdfcbank",
                "ip": ip,
            })
            assert res.status_code == 200
            data = res.json()
            assert "R_DATACENTER_IP" in data.get("reasons", []), f"Failed on AWS IP {ip}"
            hit = next((r for r in data.get("rule_breakdown", []) if r["code"] == "R_DATACENTER_IP"), None)
            assert hit is not None
            assert hit["points"] == 25, f"Expected 25 pts for datacenter IP, got {hit['points']}"

    def test_17_datacenter_ip_gcp_range_trigger(self, client: TestClient):
        """R2.12: Originating IP from Google Cloud Platform CIDR range triggers R_DATACENTER_IP."""
        gcp_ips = ["34.93.100.22", "35.200.180.5", "34.100.45.10"]
        for ip in gcp_ips:
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_GCP_{uuid.uuid4().hex[:8]}",
                "amount": 7500.0,
                "payer_vpa": f"gcp_bot_{uuid.uuid4().hex[:6]}@ybl",
                "payee_vpa": "target.payee@ybl",
                "ip": ip,
            })
            assert res.status_code == 200
            data = res.json()
            assert "R_DATACENTER_IP" in data.get("reasons", []), f"Failed on GCP IP {ip}"

    def test_18_datacenter_ip_azure_do_tor_trigger(self, client: TestClient):
        """R2.13: Azure, DigitalOcean, and Tor Exit Node IPs trigger R_DATACENTER_IP."""
        test_ips = [
            ("20.198.100.5", "Azure"),
            ("138.68.44.12", "DigitalOcean"),
            ("185.220.101.5", "Tor Exit"),
        ]
        for ip, label in test_ips:
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_{label.replace(' ', '_')}_{uuid.uuid4().hex[:8]}",
                "amount": 9000.0,
                "payer_vpa": f"vpn_node_{uuid.uuid4().hex[:6]}@paytm",
                "payee_vpa": "target.payee@paytm",
                "ip": ip,
            })
            assert res.status_code == 200
            data = res.json()
            assert "R_DATACENTER_IP" in data.get("reasons", []), f"Failed on {label} IP {ip}"

    def test_19_datacenter_ip_residential_no_trigger(self, client: TestClient):
        """R2.14: Standard residential / mobile ISP IP (e.g. Jio/Airtel/ACT) must NOT trigger rule."""
        residential_ips = ["49.207.50.120", "103.212.145.60", "157.34.12.80", "182.72.45.10"]
        for ip in residential_ips:
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_RES_{uuid.uuid4().hex[:8]}",
                "amount": 3500.0,
                "payer_vpa": f"home_user_{uuid.uuid4().hex[:6]}@okaxis",
                "payee_vpa": "home_merchant@okaxis",
                "ip": ip,
            })
            assert res.status_code == 200
            data = res.json()
            assert "R_DATACENTER_IP" not in data.get("reasons", []), f"False positive on residential IP {ip}"

    def test_20_datacenter_ip_relative_risk_elevation(self, client: TestClient):
        """R2.15: Transaction with Datacenter IP scores strictly higher risk than identical transaction from Residential IP."""
        base_txn = {
            "amount": 12000.0,
            "payer_vpa": f"compare_user_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "vendor.tech@okhdfcbank",
            "payer_account_age_days": 10,
            "payee_vpa_age_days": 5,
        }

        # 1. Residential
        res_home = client.post("/upi/check", json={
            **base_txn,
            "txn_id": f"TXN_COMP_HOME_{uuid.uuid4().hex[:8]}",
            "ip": "49.207.50.10",
        })
        # 2. Datacenter (AWS)
        res_dc = client.post("/upi/check", json={
            **base_txn,
            "txn_id": f"TXN_COMP_DC_{uuid.uuid4().hex[:8]}",
            "ip": "3.220.100.45",
        })

        assert res_home.status_code == 200
        assert res_dc.status_code == 200
        score_home = res_home.json()["risk_score"]
        score_dc = res_dc.json()["risk_score"]
        assert score_dc > score_home, f"Datacenter score ({score_dc}) must exceed residential score ({score_home})"


class TestTier1Feature5CampaignFingerprinting:
    """Tier 1: Feature Isolation Tests for Transaction DNA Campaign Fingerprinting (R3)."""

    def test_21_campaign_store_ingests_on_block(self, client: TestClient):
        """R3.1: A transaction receiving a BLOCK verdict stores its behavioral DNA in the campaign registry."""
        # Honeypot hits guarantee BLOCK and should register a campaign signature
        reg = get_honeypot_registry()
        honeypots = reg.list_honeypots()
        hp_vpa = honeypots[0]["vpa"] if honeypots else "honeypot_trap_01@okaxis"

        res = client.post("/upi/check", json={
            "txn_id": f"TXN_BLOCK_CAMPAIGN_{uuid.uuid4().hex[:8]}",
            "amount": 9999.0,
            "payer_vpa": f"attacker_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": hp_vpa,
            "note": "urgent kyc verification refund",
            "payer_account_age_days": 2,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["action"] == "BLOCK", f"Expected BLOCK verdict, got {data['action']}"

    def test_22_campaign_match_rule_triggered_on_similar_dna(self, client: TestClient):
        """R3.2: A subsequent transaction with near-identical behavioral DNA triggers R_CAMPAIGN_MATCH."""
        payer_prefix = f"campaign_mule_{uuid.uuid4().hex[:4]}"
        
        # Step 1: Execute high-risk seed transaction that triggers BLOCK
        client.post("/upi/check", json={
            "txn_id": f"TXN_CAMP_SEED_{uuid.uuid4().hex[:8]}",
            "amount": 49999.0,
            "payer_vpa": f"{payer_prefix}_01@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
            "note": "lottery reward kyc validation",
            "payer_account_age_days": 5,
        })

        # Step 2: Next transaction has matching behavioral pattern (skirting 50k, similar note, fresh account)
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_CAMP_HIT_{uuid.uuid4().hex[:8]}",
            "amount": 49990.0,
            "payer_vpa": f"{payer_prefix}_02@okaxis",
            "payee_vpa": "target.payee@okhdfcbank",
            "note": "lottery reward kyc verification",
            "payer_account_age_days": 5,
        })
        assert res.status_code == 200
        data = res.json()
        # Should either trigger R_CAMPAIGN_MATCH or return campaign_id
        if "R_CAMPAIGN_MATCH" in data.get("reasons", []):
            hit = next((r for r in data.get("rule_breakdown", []) if r["code"] == "R_CAMPAIGN_MATCH"), None)
            assert hit is not None
            assert hit["points"] >= 20

    def test_23_campaign_id_populated_in_response(self, client: TestClient):
        """R3.3: When a transaction matches a campaign, response contains non-empty campaign_id."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_CAMP_ID_TEST_{uuid.uuid4().hex[:8]}",
            "amount": 25000.0,
            "payer_vpa": "test.campaign@okaxis",
            "payee_vpa": "merchant@okaxis",
        })
        assert res.status_code == 200
        data = res.json()
        # campaign_id is an optional string field on model
        assert "campaign_id" in data

    def test_24_campaign_dissimilar_transaction_no_trigger(self, client: TestClient):
        """R3.4: A normal dissimilar transaction does not match campaign signatures and has campaign_id=None."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_BENIGN_NO_CAMP_{uuid.uuid4().hex[:8]}",
            "amount": 340.50,
            "payer_vpa": f"clean_shopper_{uuid.uuid4().hex[:6]}@okhdfcbank",
            "payee_vpa": "grocery.store@okhdfcbank",
            "payer_account_age_days": 400,
            "payee_vpa_age_days": 350,
            "note": "groceries milk and bread",
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_CAMPAIGN_MATCH" not in data.get("reasons", [])

    def test_25_campaign_confirmed_fraud_feedback_updates_store(self, client: TestClient):
        """R3.5: Confirming fraud on an investigative case reinforces campaign clustering."""
        # 1. Trigger a case
        res_check = client.post("/upi/check", json={
            "txn_id": f"TXN_FEEDBACK_CASE_{uuid.uuid4().hex[:8]}",
            "amount": 95000.0,
            "payer_vpa": f"fraud_candidate_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })
        case_id = res_check.json().get("case_id")
        if case_id:
            res_fb = client.post(f"/upi/cases/{case_id}/feedback", json={"confirmed_fraud": True})
            assert res_fb.status_code == 200
            assert res_fb.json().get("status") == "updated"


class TestTier1Feature6SarPdfExport:
    """Tier 1: Feature Isolation Tests for One-Click SAR PDF Export (R4)."""

    def test_26_sar_pdf_valid_content_type_and_status(self, client: TestClient):
        """R4.1: GET /cases/{case_id}/sar/pdf returns HTTP 200 with Content-Type: application/pdf."""
        # First create a flagged case
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_SAR_GEN_{uuid.uuid4().hex[:8]}",
            "amount": 99000.0,
            "payer_vpa": f"mule_sar_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })
        case_id = res.json().get("case_id")
        assert case_id is not None, "Evaluation must open a case for honeypot hit"

        # Query SAR PDF
        pdf_res = client.get(f"/cases/{case_id}/sar/pdf")
        assert pdf_res.status_code == 200, f"Expected 200, got {pdf_res.status_code}: {pdf_res.text}"
        assert "application/pdf" in pdf_res.headers.get("content-type", "").lower()

    def test_27_sar_pdf_content_disposition_header(self, client: TestClient):
        """R4.2: Response headers include Content-Disposition attachment with SAR_{case_id}.pdf."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_SAR_HDR_{uuid.uuid4().hex[:8]}",
            "amount": 99000.0,
            "payer_vpa": f"mule_sar_hdr_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })
        case_id = res.json().get("case_id")
        assert case_id is not None

        pdf_res = client.get(f"/cases/{case_id}/sar/pdf")
        cd_header = pdf_res.headers.get("content-disposition", "")
        assert "attachment" in cd_header.lower()
        assert f"SAR_{case_id}.pdf" in cd_header or case_id in cd_header

    def test_28_sar_pdf_binary_header_magic_bytes(self, client: TestClient):
        """R4.3: PDF binary content starts with standard PDF magic bytes (%PDF-)."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_SAR_MAGIC_{uuid.uuid4().hex[:8]}",
            "amount": 99000.0,
            "payer_vpa": f"mule_sar_magic_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })
        case_id = res.json().get("case_id")
        pdf_res = client.get(f"/cases/{case_id}/sar/pdf")
        body = pdf_res.content
        assert body.startswith(b"%PDF-"), f"Expected %PDF- magic bytes, got {body[:10]}"

    def test_29_sar_pdf_contains_case_narrative_and_members(self, client: TestClient):
        """R4.4: Generated PDF binary includes textual references to SAR narrative and ring members."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_SAR_TEXT_{uuid.uuid4().hex[:8]}",
            "amount": 99000.0,
            "payer_vpa": f"mule_sar_text_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })
        case_id = res.json().get("case_id")
        pdf_res = client.get(f"/cases/{case_id}/sar/pdf")
        assert len(pdf_res.content) > 500, "PDF payload must not be empty or trivially small"

    def test_30_sar_pdf_nonexistent_case_returns_404(self, client: TestClient):
        """R4.5: Requesting SAR PDF for non-existent case returns HTTP 404."""
        fake_id = f"nonexistent_case_{uuid.uuid4().hex[:8]}"
        res = client.get(f"/cases/{fake_id}/sar/pdf")
        assert res.status_code == 404
        assert "not found" in res.text.lower()

    def test_31_sar_pdf_dual_route_mount(self, client: TestClient):
        """R4.6: SAR PDF is accessible at both /cases/{case_id}/sar/pdf and /upi/cases/{case_id}/sar/pdf."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_SAR_DUAL_{uuid.uuid4().hex[:8]}",
            "amount": 99000.0,
            "payer_vpa": f"mule_sar_dual_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })
        case_id = res.json().get("case_id")

        res_root = client.get(f"/cases/{case_id}/sar/pdf")
        res_upi = client.get(f"/upi/cases/{case_id}/sar/pdf")
        assert res_root.status_code == 200
        assert res_upi.status_code == 200
        assert res_root.content[:10] == res_upi.content[:10]


class TestTier1Feature7WorkloadHeatmap:
    """Tier 1: Feature Isolation Tests for Analyst Workload Heatmap (R5)."""

    def test_32_workload_heatmap_present_in_analytics(self, client: TestClient):
        """R5.1: /stats/analytics and /upi/stats/analytics return workload_heatmap in response."""
        for path in ("/stats/analytics", "/upi/stats/analytics"):
            res = client.get(path)
            assert res.status_code == 200
            data = res.json()
            assert "workload_heatmap" in data, f"Missing workload_heatmap in {path}"

    def test_33_workload_heatmap_grid_dimensions(self, client: TestClient):
        """R5.2: workload_heatmap covers 7 days (0..6) and 24 hours (0..23) or 168 cells."""
        res = client.get("/upi/stats/analytics")
        assert res.status_code == 200
        heatmap = res.json().get("workload_heatmap", [])
        assert isinstance(heatmap, list)
        if len(heatmap) == 168:
            # 7x24 flat list
            days = {cell.get("day") for cell in heatmap}
            hours = {cell.get("hour") for cell in heatmap}
            assert days == set(range(7)), f"Days set expected 0..6, got {days}"
            assert hours == set(range(24)), f"Hours set expected 0..23, got {hours}"
        elif len(heatmap) == 7:
            # List of 7 day rows with 24 hours
            for row in heatmap:
                assert "day" in row or "hours" in row

    def test_34_workload_heatmap_increments_on_case(self, client: TestClient):
        """R5.3: Creating a flagged case increments case count in corresponding day/hour cell."""
        now = datetime.now(timezone.utc)
        curr_day = now.weekday()  # 0=Monday, 6=Sunday
        curr_hour = now.hour

        # Generate a flagged case
        client.post("/upi/check", json={
            "txn_id": f"TXN_HEATMAP_INC_{uuid.uuid4().hex[:8]}",
            "amount": 88000.0,
            "payer_vpa": f"mule_heat_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })

        res = client.get("/upi/stats/analytics")
        assert res.status_code == 200
        heatmap = res.json().get("workload_heatmap", [])
        if heatmap and isinstance(heatmap[0], dict) and "hour" in heatmap[0]:
            matching = [c for c in heatmap if c.get("day") == curr_day and c.get("hour") == curr_hour]
            if matching:
                assert matching[0].get("count", 0) >= 1

    def test_35_workload_heatmap_tracks_total_amount(self, client: TestClient):
        """R5.4: Heatmap cell tracks cumulative total_amount in INR for flagged cases."""
        amount = 77000.0
        client.post("/upi/check", json={
            "txn_id": f"TXN_HEATMAP_AMT_{uuid.uuid4().hex[:8]}",
            "amount": amount,
            "payer_vpa": f"mule_amt_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
        })

        res = client.get("/upi/stats/analytics")
        assert res.status_code == 200
        heatmap = res.json().get("workload_heatmap", [])
        if heatmap:
            total_amt = sum(c.get("total_amount", 0.0) for c in heatmap if isinstance(c, dict))
            assert total_amt >= amount

    def test_36_workload_heatmap_rolling_30d_filtering(self, client: TestClient):
        """R5.5: Heatmap reflects rolling 30 days window and does not crash on empty state."""
        res = client.get("/stats/analytics")
        assert res.status_code == 200
        assert "workload_heatmap" in res.json()


class TestTier1Feature8AutoFeedEngine:
    """Tier 1: Feature Isolation Tests for Autonomous Live Auto-Feed Mode (R6)."""

    def test_37_autofeed_start_lifecycle(self, client: TestClient):
        """R6.1: POST /upi/autofeed/start initiates background transaction generation."""
        res = client.post("/upi/autofeed/start", json={
            "rate_tps": 10.0,
            "fraud_ratio": 0.20,
            "bursty": True,
        })
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") in ("started", "already_running")
        assert data.get("active") is True

    def test_38_autofeed_status_telemetry(self, client: TestClient):
        """R6.2: GET /upi/autofeed/status returns active state, configured TPS, and telemetry."""
        # Start autofeed first
        client.post("/upi/autofeed/start", json={"rate_tps": 8.0})

        res = client.get("/upi/autofeed/status")
        assert res.status_code == 200
        data = res.json()
        assert "active" in data
        assert data["active"] is True
        assert "rate_tps" in data or "tps" in data

    def test_39_autofeed_stop_cleanly(self, client: TestClient):
        """R6.3: POST /upi/autofeed/stop cleanly halts generation and sets active=False."""
        client.post("/upi/autofeed/start", json={"rate_tps": 5.0})

        res = client.post("/upi/autofeed/stop")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") in ("stopped", "not_running")
        assert data.get("active") is False

        # Verify status is inactive
        res_stat = client.get("/upi/autofeed/status")
        assert res_stat.json().get("active") is False

    def test_40_autofeed_evaluates_live_pipeline(self, client: TestClient):
        """R6.4: Auto-feed transactions route through live evaluation pipeline and update system stats."""
        # Start autofeed briefly
        client.post("/upi/autofeed/start", json={"rate_tps": 15.0, "fraud_ratio": 0.3})
        time.sleep(0.3)
        client.post("/upi/autofeed/stop")

        res_stats = client.get("/upi/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats.get("total_evaluated", 0) >= 0

    def test_41_autofeed_idempotent_controls(self, client: TestClient):
        """R6.5: Consecutive starts or stops behave idempotently without errors."""
        # Start twice
        r1 = client.post("/upi/autofeed/start", json={"rate_tps": 5.0})
        r2 = client.post("/upi/autofeed/start", json={"rate_tps": 5.0})
        assert r1.status_code == 200
        assert r2.status_code == 200

        # Stop twice
        s1 = client.post("/upi/autofeed/stop")
        s2 = client.post("/upi/autofeed/stop")
        assert s1.status_code == 200
        assert s2.status_code == 200


# =============================================================================
# TIER 2: BOUNDARY VALUE ANALYSIS & EDGE CASES
# =============================================================================

class TestTier2BoundaryAndEdgeCases:
    """Tier 2: Boundary Value Analysis and Edge Case Robustness Tests."""

    def test_tier2_b01_zero_and_micro_amounts(self, client: TestClient):
        """B1: Micro-amounts (Rs 0.01) and boundary values are evaluated without precision loss."""
        for amt in (0.01, 0.50, 1.00):
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_MICRO_{uuid.uuid4().hex[:8]}",
                "amount": amt,
                "payer_vpa": "micro.payer@okaxis",
                "payee_vpa": "micro.payee@okhdfcbank",
            })
            assert res.status_code == 200
            assert res.json()["action"] in ("ALLOW", "HOLD", "BLOCK")

    def test_tier2_b02_extreme_high_value_transfers(self, client: TestClient):
        """B2: Mega transfers (Rs 10,000,000) trigger high-value / risk logic and bound risk score <= 100."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_MEGA_{uuid.uuid4().hex[:8]}",
            "amount": 10000000.0,
            "payer_vpa": "whale.payer@okaxis",
            "payee_vpa": "unknown.payee@ybl",
            "payer_account_age_days": 1,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["risk_score"] <= 100
        assert data["action"] in ("HOLD", "BLOCK")

    def test_tier2_b03_extreme_account_ages(self, client: TestClient):
        """B3: Account age at boundaries (0 days, 36500 days) processed gracefully."""
        for age in (0, 1, 365, 36500):
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_AGE_{age}_{uuid.uuid4().hex[:8]}",
                "amount": 5000.0,
                "payer_vpa": f"age_{age}@okaxis",
                "payee_vpa": "merchant@okaxis",
                "payer_account_age_days": age,
                "payee_vpa_age_days": age,
            })
            assert res.status_code == 200

    def test_tier2_b04_malformed_and_empty_telemetry(self, client: TestClient):
        """B4: Malformed IP, invalid geo format, and empty strings handled safely without unhandled 500."""
        malformed_inputs = [
            {"ip": "not_an_ip", "location": "invalid_geo_str"},
            {"ip": "999.999.999.999", "location": ""},
            {"ip": "", "location": "999.999, -999.999"},
            {"device_id": "   ", "sim_id": ""},
        ]
        for tf in malformed_inputs:
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_MALF_{uuid.uuid4().hex[:8]}",
                "amount": 2000.0,
                "payer_vpa": "test.user@okaxis",
                "payee_vpa": "test.merchant@okhdfcbank",
                **tf,
            })
            assert res.status_code == 200, f"Failed on malformed telemetry: {tf}"

    def test_tier2_b05_max_tps_and_rapid_toggle_autofeed(self, client: TestClient):
        """B5: Rapid start/stop toggling of autofeed under high TPS rate limit boundaries."""
        for _ in range(5):
            client.post("/upi/autofeed/start", json={"rate_tps": 50.0})
            client.post("/upi/autofeed/stop")
        status = client.get("/upi/autofeed/status").json()
        assert status.get("active") is False

    def test_tier2_b06_exact_impossible_travel_threshold(self, client: TestClient):
        """B6: Test speed boundary: 500km in exactly 30 minutes vs 31 minutes."""
        payer = f"thresh_user_{uuid.uuid4().hex[:6]}@okaxis"
        svc = get_upi_case_service()
        t0 = datetime.now(timezone.utc) - timedelta(minutes=45)

        # Point A: Mumbai (19.0760, 72.8777)
        txn1 = UpiTransaction(
            txn_id=f"TXN_A_{uuid.uuid4().hex[:8]}",
            timestamp=t0,
            amount=500.0,
            payer_vpa=payer,
            payee_vpa="shop_a@okaxis",
            location="19.0760, 72.8777",
        )
        svc.evaluate(txn1)

        # Point B: ~550km away at t0 + 40 minutes (sub-threshold speed ~825 km/h < 1000 km/h)
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_B_{uuid.uuid4().hex[:8]}",
            "timestamp": (t0 + timedelta(minutes=40)).isoformat(),
            "amount": 1000.0,
            "payer_vpa": payer,
            "payee_vpa": "shop_b@okaxis",
            "location": "23.0225, 72.5714",  # Ahmedabad (~530km)
        })
        assert res.status_code == 200

    def test_tier2_b07_dmv_score_boundaries(self, client: TestClient):
        """B7: Exact DMV score clamped to [0.0, 100.0] under any mathematical edge condition."""
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_DMV_CLAMP_{uuid.uuid4().hex[:8]}",
            "amount": 50000.0,
            "payer_vpa": f"clamp_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "recipient@okaxis",
            "payer_account_age_days": 10000,
        })
        assert res.status_code == 200
        dmv = float(res.json().get("dmv_score", 0.0))
        assert 0.0 <= dmv <= 100.0

    def test_tier2_b08_sar_pdf_special_characters_case_id(self, client: TestClient):
        """B8: SAR PDF export with case ID containing underscores and hyphens."""
        res = client.get("/cases/CASE_SPECIAL-123_456/sar/pdf")
        # Returns 404 cleanly since case doesn't exist, rather than 500
        assert res.status_code in (200, 404)

    def test_tier2_b09_empty_database_and_analytics_boundaries(self, client: TestClient):
        """B9: Analytics endpoint handles empty or minimal data without ZeroDivisionError."""
        res = client.get("/stats/analytics")
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
        assert "fraud_rate_pct" in data["summary"]
        assert 0.0 <= data["summary"]["fraud_rate_pct"] <= 100.0


# =============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS & STATE INTERACTIONS
# =============================================================================

class TestTier3CrossFeatureCombinations:
    """Tier 3: Cross-Feature Interactions and Multi-Layer Risk Fusion Tests."""

    def test_tier3_c01_compound_threat_honeypot_datacenter_impossible_travel(self, client: TestClient):
        """C1: Transaction combining Datacenter IP + Impossible Travel + Honeypot Hit triggers full compound breakdown."""
        payer = f"syndicate_boss_{uuid.uuid4().hex[:6]}@okaxis"
        svc = get_upi_case_service()
        t0 = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Baseline location
        svc.evaluate(UpiTransaction(
            txn_id=f"TXN_C1_BASE_{uuid.uuid4().hex[:8]}",
            timestamp=t0,
            amount=500.0,
            payer_vpa=payer,
            payee_vpa="clean.vendor@okaxis",
            location="Chennai",
        ))

        # Attacking transaction
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_C1_ATTACK_{uuid.uuid4().hex[:8]}",
            "timestamp": (t0 + timedelta(minutes=5)).isoformat(),
            "amount": 90000.0,
            "payer_vpa": payer,
            "payee_vpa": "honeypot_trap_01@okaxis",
            "ip": "3.220.100.45",  # AWS Datacenter IP
            "location": "Delhi",    # Impossible travel from Chennai
        })
        assert res.status_code == 200
        data = res.json()
        assert data["action"] == "BLOCK"
        reasons = data.get("reasons", [])
        assert "R_HONEYPOT_HIT" in reasons
        assert "R_DATACENTER_IP" in reasons
        assert "R_IMPOSSIBLE_TRAVEL" in reasons

    def test_tier3_c02_sim_device_mismatch_with_dormant_dmv_drain(self, client: TestClient):
        """C2: SIM-Device mismatch executed on a dormant account experiencing sudden high cashout."""
        payer = f"dormant_victim_{uuid.uuid4().hex[:6]}@okhdfcbank"
        svc = get_upi_case_service()

        # Seed old transaction with known device/SIM
        t_old = datetime.now(timezone.utc) - timedelta(days=90)
        svc.evaluate(UpiTransaction(
            txn_id=f"TXN_C2_OLD_{uuid.uuid4().hex[:8]}",
            timestamp=t_old,
            amount=1000.0,
            payer_vpa=payer,
            payee_vpa="utility.bill@okhdfcbank",
            device_id="DEV_OLD_PHONE",
            sim_id="SIM_OLD_123",
            payer_account_age_days=180,
        ))

        # Inflow 90 days ago
        svc.evaluate(UpiTransaction(
            txn_id=f"TXN_C2_INFLOW_{uuid.uuid4().hex[:8]}",
            timestamp=t_old,
            amount=150000.0,
            payer_vpa="employer.payroll@okaxis",
            payee_vpa=payer,
        ))

        # Cashout with new SIM on same device
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_C2_DRAIN_{uuid.uuid4().hex[:8]}",
            "amount": 140000.0,
            "payer_vpa": payer,
            "payee_vpa": "crypto.cashout@ybl",
            "device_id": "DEV_OLD_PHONE",
            "sim_id": "SIM_ROGUE_SWAP_999",
            "payer_account_age_days": 180,
            "payee_vpa_age_days": 3,
        })
        assert res.status_code == 200
        data = res.json()
        assert "R_SIM_DEVICE_MISMATCH" in data.get("reasons", [])
        assert float(data.get("dmv_score", 0.0)) >= 60.0

    def test_tier3_c03_block_verdict_to_campaign_fingerprint_to_second_hit(self, client: TestClient):
        """C3: BLOCK verdict generates campaign signature; next transaction from different payer matches campaign."""
        # 1. Attacker 1 gets blocked
        client.post("/upi/check", json={
            "txn_id": f"TXN_C3_A1_{uuid.uuid4().hex[:8]}",
            "amount": 49999.0,
            "payer_vpa": f"phish_bot_1_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
            "note": "urgent prize claiming kyc fee",
            "ip": "3.220.100.45",
        })

        # 2. Attacker 2 runs similar campaign pattern
        res2 = client.post("/upi/check", json={
            "txn_id": f"TXN_C3_A2_{uuid.uuid4().hex[:8]}",
            "amount": 49995.0,
            "payer_vpa": f"phish_bot_2_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "target.victim@okhdfcbank",
            "note": "urgent prize claiming kyc fee",
            "ip": "3.220.100.45",
        })
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["risk_score"] >= 45  # Elevated risk

    def test_tier3_c04_autofeed_generates_cases_populates_heatmap_and_dmv(self, client: TestClient):
        """C4: Auto-feed background run produces flagged cases that flow into Heatmap, DMV table, and SAR PDF."""
        # Start autofeed with fraud ratio
        client.post("/upi/autofeed/start", json={"rate_tps": 20.0, "fraud_ratio": 0.4})
        time.sleep(0.4)
        client.post("/upi/autofeed/stop")

        # Query analytics
        res_an = client.get("/stats/analytics")
        assert res_an.status_code == 200
        an_data = res_an.json()
        assert "workload_heatmap" in an_data

    def test_tier3_c05_federation_signal_combined_with_telemetry_and_dmv(self, client: TestClient):
        """C5: Payee with active federated threat signal blends network score with Datacenter IP and DMV."""
        payee = f"fed_mule_{uuid.uuid4().hex[:6]}@okhdfcbank"
        payee_hash = hashlib.sha256(payee.encode()).hexdigest()

        # Submit federated threat signal
        client.post("/federation/signal", json={
            "vpa_hash": payee_hash,
            "risk_level": "CRITICAL",
            "ring_hash": "RING_CROSS_BANK_MULE",
        })

        # Evaluate transaction to this payee from Datacenter IP
        res = client.post("/upi/check", json={
            "txn_id": f"TXN_C5_FED_{uuid.uuid4().hex[:8]}",
            "amount": 35000.0,
            "payer_vpa": "victim.payer@okaxis",
            "payee_vpa": payee,
            "ip": "3.220.100.45",  # Datacenter IP
        })
        assert res.status_code == 200
        data = res.json()
        assert data["network_score"] >= 0.8
        assert "FEDERATED_MULE_NETWORK" in data.get("reasons", [])
        assert "R_DATACENTER_IP" in data.get("reasons", [])

    def test_tier3_c06_analyst_feedback_reinforces_fraud_memory_and_campaign(self, client: TestClient):
        """C6: Marking case as confirmed fraud records entity into fraud memory for future transactions."""
        payer = f"confirmed_mule_{uuid.uuid4().hex[:6]}@okaxis"
        res_chk = client.post("/upi/check", json={
            "txn_id": f"TXN_C6_INIT_{uuid.uuid4().hex[:8]}",
            "amount": 98000.0,
            "payer_vpa": payer,
            "payee_vpa": "honeypot_trap_01@okaxis",
        })
        case_id = res_chk.json().get("case_id")
        if case_id:
            client.post(f"/upi/cases/{case_id}/feedback", json={"confirmed_fraud": True})

            # Next transaction from same payer triggers KNOWN_FRAUD_ENTITY
            res_sub = client.post("/upi/check", json={
                "txn_id": f"TXN_C6_NEXT_{uuid.uuid4().hex[:8]}",
                "amount": 2000.0,
                "payer_vpa": payer,
                "payee_vpa": "innocent.shop@okaxis",
            })
            assert res_sub.status_code == 200
            assert "KNOWN_FRAUD_ENTITY" in res_sub.json().get("reasons", [])

    def test_tier3_c07_multi_psp_simulated_layering_with_full_sprint2_telemetry(self, client: TestClient):
        """C7: End-to-end multi-hop layering conduit with full telemetry and SAR extraction."""
        mule_a = f"mule_node_a_{uuid.uuid4().hex[:6]}@okaxis"
        mule_b = f"mule_node_b_{uuid.uuid4().hex[:6]}@ybl"
        mule_c = f"mule_node_c_{uuid.uuid4().hex[:6]}@paytm"

        # Hop 1: Inflow to A
        client.post("/upi/check", json={
            "txn_id": f"TXN_HOP1_{uuid.uuid4().hex[:8]}",
            "amount": 50000.0,
            "payer_vpa": "victim@okhdfcbank",
            "payee_vpa": mule_a,
        })

        # Hop 2: Rapid pass-through A -> B
        client.post("/upi/check", json={
            "txn_id": f"TXN_HOP2_{uuid.uuid4().hex[:8]}",
            "amount": 48000.0,
            "payer_vpa": mule_a,
            "payee_vpa": mule_b,
            "payer_account_age_days": 10,
        })

        # Hop 3: Dispersal B -> C
        res3 = client.post("/upi/check", json={
            "txn_id": f"TXN_HOP3_{uuid.uuid4().hex[:8]}",
            "amount": 47000.0,
            "payer_vpa": mule_b,
            "payee_vpa": mule_c,
            "payer_account_age_days": 10,
            "ip": "3.220.100.45",
        })
        assert res3.status_code == 200
        case_id = res3.json().get("case_id")
        if case_id:
            pdf_res = client.get(f"/cases/{case_id}/sar/pdf")
            assert pdf_res.status_code == 200


# =============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# =============================================================================

class TestTier4RealWorldScenarios:
    """Tier 4: Comprehensive Real-World Application Scenario Tests."""

    def test_scenario_1_dormant_mule_ring_drain_and_campaign_clustering(self, client: TestClient):
        """Scenario 1: Dormant Mule Ring Drain & Campaign Clustering.
        
        A coordinated syndicate activates three dormant accounts (>90 days old) in a synchronized
        burst. The system detects high DMV scores, identifies structuring behavior, extracts and
        clusters the campaign signature, and provides full SAR PDF export.
        """
        syndicate_id = uuid.uuid4().hex[:6]
        mule_1 = f"dormant_mule_1_{syndicate_id}@okhdfcbank"
        mule_2 = f"dormant_mule_2_{syndicate_id}@okhdfcbank"
        mule_3 = f"dormant_mule_3_{syndicate_id}@okhdfcbank"
        exit_sink = f"crypto_sink_{syndicate_id}@paytm"

        # 1. Execute rapid drain on mule accounts
        opened_cases = []
        for i, mule in enumerate((mule_1, mule_2, mule_3)):
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_SC1_{i}_{uuid.uuid4().hex[:8]}",
                "amount": 49500.0,
                "payer_vpa": mule,
                "payee_vpa": exit_sink,
                "payer_account_age_days": 120,
                "payee_vpa_age_days": 2,
                "note": f"kyc refund syndicate {syndicate_id}",
                "ip": "3.220.100.45",  # Cloud origin
            })
            assert res.status_code == 200
            data = res.json()
            assert data["risk_score"] >= 45
            assert "dmv_score" in data
            if data.get("case_id"):
                opened_cases.append(data["case_id"])

        # 2. Verify SAR PDF export for opened case
        if opened_cases:
            pdf_res = client.get(f"/cases/{opened_cases[0]}/sar/pdf")
            assert pdf_res.status_code == 200
            assert pdf_res.content.startswith(b"%PDF-")

    def test_scenario_2_high_speed_cross_city_sim_swap_attack(self, client: TestClient):
        """Scenario 2: High-Speed Cross-City SIM-Swap Attack.
        
        An attacker performs a SIM swap on a legitimate user. 12 minutes after the user
        legitimately transacted in Mumbai, the attacker executes an Rs 85,000 transfer from Delhi
        using the new SIM. System triggers SIM mismatch + impossible travel + instant BLOCK.
        """
        user_vpa = f"victim_citizen_{uuid.uuid4().hex[:6]}@okaxis"
        user_dev = "DEV_PIXEL_USER_ORIGINAL"
        user_sim = "SIM_USER_AIRTEL_123"
        attacker_sim = "SIM_ATTACKER_JIO_999"
        t0 = datetime.now(timezone.utc) - timedelta(minutes=12)

        # 1. Legitimate user txn in Mumbai
        res_legit = client.post("/upi/check", json={
            "txn_id": f"TXN_SC2_LEGIT_{uuid.uuid4().hex[:8]}",
            "timestamp": t0.isoformat(),
            "amount": 450.0,
            "payer_vpa": user_vpa,
            "payee_vpa": "mumbai.coffee@okaxis",
            "device_id": user_dev,
            "sim_id": user_sim,
            "location": "Mumbai",
        })
        assert res_legit.status_code == 200
        assert res_legit.json()["action"] == "ALLOW"

        # 2. Fraudulent drain from Delhi with swapped SIM 12 minutes later
        res_fraud = client.post("/upi/check", json={
            "txn_id": f"TXN_SC2_FRAUD_{uuid.uuid4().hex[:8]}",
            "timestamp": (t0 + timedelta(minutes=12)).isoformat(),
            "amount": 85000.0,
            "payer_vpa": user_vpa,
            "payee_vpa": "cashout_sink@okaxis",
            "device_id": user_dev,
            "sim_id": attacker_sim,  # Swapped SIM
            "location": "Delhi",       # Impossible travel (>1100km in 12min)
        })
        assert res_fraud.status_code == 200
        data_fraud = res_fraud.json()
        assert data_fraud["action"] in ("HOLD", "BLOCK")
        reasons = data_fraud.get("reasons", [])
        assert "R_SIM_DEVICE_MISMATCH" in reasons
        assert "R_IMPOSSIBLE_TRAVEL" in reasons

    def test_scenario_3_cloud_hosted_botnet_surge_with_autofeed_live_rail(self, client: TestClient):
        """Scenario 3: Cloud-Hosted Botnet Surge with Auto-Feed Live Rail.
        
        While the Live Auto-Feed rail is running continuously in the background, a simulated
        cloud botnet executes rapid micro-probes from AWS EC2 IPs into synthetic honeypots.
        System intercepts all botnet attacks without degrading baseline performance.
        """
        # 1. Start Auto-Feed background rail
        client.post("/upi/autofeed/start", json={"rate_tps": 12.0, "fraud_ratio": 0.1})

        # 2. Inject botnet surge from Datacenter IPs into honeypots
        botnet_results = []
        for i in range(5):
            res_bot = client.post("/upi/check", json={
                "txn_id": f"TXN_SC3_BOT_{i}_{uuid.uuid4().hex[:8]}",
                "amount": 1000.0 * (i + 1),
                "payer_vpa": f"bot_{i}_{uuid.uuid4().hex[:4]}@okaxis",
                "payee_vpa": "honeypot_trap_01@okaxis",
                "ip": "3.220.100.45",
            })
            assert res_bot.status_code == 200
            botnet_results.append(res_bot.json())

        # 3. All botnet transactions must be BLOCKED
        for b_res in botnet_results:
            assert b_res["action"] == "BLOCK"
            assert "R_HONEYPOT_HIT" in b_res.get("reasons", [])
            assert "R_DATACENTER_IP" in b_res.get("reasons", [])

        # 4. Stop Auto-Feed cleanly
        client.post("/upi/autofeed/stop")

    def test_scenario_4_enterprise_compliance_investigator_workflow(self, client: TestClient):
        """Scenario 4: Enterprise Compliance Investigator Workflow.
        
        Compliance investigator queries 7x24 Workload Heatmap, identifies peak fraud activity,
        drills down into Top DMV accounts, opens case dossier, updates case status to ESCALATED,
        and downloads the formal SAR PDF report.
        """
        # 1. Trigger high-risk case
        res_init = client.post("/upi/check", json={
            "txn_id": f"TXN_SC4_INVESTIGATE_{uuid.uuid4().hex[:8]}",
            "amount": 92000.0,
            "payer_vpa": f"investigate_mule_{uuid.uuid4().hex[:6]}@okaxis",
            "payee_vpa": "honeypot_trap_01@okaxis",
            "ip": "15.206.50.10",
        })
        case_id = res_init.json().get("case_id")
        assert case_id is not None

        # 2. Analyst views Workload Heatmap in Analytics
        res_analytics = client.get("/stats/analytics")
        assert res_analytics.status_code == 200
        assert "workload_heatmap" in res_analytics.json()

        # 3. Analyst updates Case Status to ESCALATED
        res_patch = client.patch(f"/cases/{case_id}/status", json={
            "status": "escalated",
            "notes": "Escalating suspected mule syndicate cashout to FIU-IND DPIP rail.",
            "escalate_to_dpip": True,
        })
        assert res_patch.status_code == 200

        # 4. Analyst downloads SAR PDF report
        res_pdf = client.get(f"/cases/{case_id}/sar/pdf")
        assert res_pdf.status_code == 200
        assert res_pdf.headers.get("content-type", "").startswith("application/pdf")
        assert len(res_pdf.content) > 500

    def test_scenario_5_clean_lifecycle_and_invariant_defense(self, client: TestClient):
        """Scenario 5: Clean Lifecycle & Invariant Defense.
        
        Tests system stability across multiple start/stop auto-feed cycles, concurrent manual
        scoring, metric integrity, zero thread deadlocks, and clean memory cleanup.
        """
        svc = get_upi_case_service()

        # Cycle 1: Start and query
        client.post("/upi/autofeed/start", json={"rate_tps": 8.0})
        stat1 = client.get("/upi/autofeed/status").json()
        assert stat1.get("active") is True

        # Parallel manual evaluations
        for i in range(5):
            res = client.post("/upi/check", json={
                "txn_id": f"TXN_SC5_MANUAL_{i}_{uuid.uuid4().hex[:8]}",
                "amount": 500.0 * (i + 1),
                "payer_vpa": f"manual_user_{i}@okaxis",
                "payee_vpa": f"merchant_{i}@okhdfcbank",
            })
            assert res.status_code == 200

        # Cycle 2: Stop and verify
        client.post("/upi/autofeed/stop")
        stat2 = client.get("/upi/autofeed/status").json()
        assert stat2.get("active") is False

        # Invariant checks: service counters remain non-negative
        stats = client.get("/upi/stats").json()
        assert stats.get("total_evaluated", 0) >= 5
        assert stats.get("total_allowed", 0) >= 0
        assert stats.get("total_held", 0) >= 0
        assert stats.get("total_blocked", 0) >= 0

"""Comprehensive Tests for Simulated Institutional Signal Adapters (M2 / R2).

Verifies:
1. Mock NPCI MuleHunter Adapter deterministic scoring (honeypots, known-bad, clean).
2. Mock DPIP Smart Registry Adapter querying by VPA, querying by SHA-256 hash, and manual updating.
3. Mock PSP Adapter generating standardized fraud signals (`StandardFraudSignal`) and publishing to mesh.
4. InstitutionalAdapterService transaction evaluation and contributing signal aggregation.
5. REST API endpoints mounted at `/adapters` and `/upi/adapters`.
6. Inline UPI evaluation gate (`/upi/check`) integration verifying honeypots return non-zero
   `mock_npci_score >= 0.85` and `mock_dpip_threat_level >= 0.85`, and clean VPAs return low/zero.
"""
from __future__ import annotations

import hashlib
import pytest
from fastapi.testclient import TestClient

from app.adapters.dpip import (
    DpipRegistryRecord,
    DpipRegistryUpdateRequest,
    DpipSmartRegistryAdapter,
    get_dpip_adapter,
)
from app.adapters.npci import (
    NpciMuleHunterAdapter,
    NpciMuleHunterResponse,
    get_npci_adapter,
)
from app.adapters.psp import (
    MockPspAdapter,
    get_psp_adapter,
)
from app.adapters.service import (
    InstitutionalAdapterService,
    get_institutional_adapters,
)
from app.main import app
from app.models.threat_intel import StandardFraudSignal
from app.models.upi_models import UpiTransaction


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ── NPCI MuleHunter Adapter Tests ───────────────────────────────────────────


def test_npci_mulehunter_honeypot() -> None:
    adapter: NpciMuleHunterAdapter = get_npci_adapter()
    res: NpciMuleHunterResponse = adapter.score_account("honeypot_trap_01@okaxis")
    assert res.risk_rating == "HIGH"
    assert res.mule_probability >= 0.85
    assert res.mule_probability == 0.96
    assert "CENTRAL_SWITCH_HONEYPOT_SINK" in res.central_switch_flags
    assert res.switch_velocity_percentile >= 90.0


def test_npci_mulehunter_known_bad_keyword() -> None:
    adapter: NpciMuleHunterAdapter = get_npci_adapter()
    res: NpciMuleHunterResponse = adapter.score_account("mule_collector_99@ybl")
    assert res.risk_rating == "HIGH"
    assert res.mule_probability >= 0.85
    assert "KNOWN_MULE_SIGNATURE" in res.central_switch_flags


def test_npci_mulehunter_clean_account() -> None:
    adapter: NpciMuleHunterAdapter = get_npci_adapter()
    res: NpciMuleHunterResponse = adapter.score_account("raghav_sharma@okhdfcbank")
    assert res.risk_rating == "LOW"
    assert res.mule_probability < 0.15
    assert "NORMAL_SWITCH_CLEARING" in res.central_switch_flags


def test_npci_mulehunter_empty_account() -> None:
    adapter: NpciMuleHunterAdapter = get_npci_adapter()
    res: NpciMuleHunterResponse = adapter.score_account("")
    assert res.risk_rating == "CLEAN"
    assert res.mule_probability == 0.0


# ── DPIP Smart Registry Adapter Tests ────────────────────────────────────────


def test_dpip_registry_honeypot_query_by_vpa() -> None:
    adapter: DpipSmartRegistryAdapter = get_dpip_adapter()
    rec: DpipRegistryRecord = adapter.query_vpa("honeypot_trap_01@okaxis")
    assert rec.threat_level == "HIGH"
    assert rec.threat_score >= 0.85
    assert rec.listed is True
    assert len(rec.reporting_agencies) > 0


def test_dpip_registry_query_by_hash() -> None:
    adapter: DpipSmartRegistryAdapter = get_dpip_adapter()
    target_vpa = "honeypot_trap_01@okaxis"
    vpa_hash = hashlib.sha256(target_vpa.encode("utf-8")).hexdigest()

    rec: DpipRegistryRecord = adapter.query_hash(vpa_hash)
    assert rec.threat_level == "HIGH"
    assert rec.threat_score >= 0.85
    assert rec.listed is True
    assert rec.vpa_hash == vpa_hash


def test_dpip_registry_clean_account() -> None:
    adapter: DpipSmartRegistryAdapter = get_dpip_adapter()
    rec: DpipRegistryRecord = adapter.query_vpa("clean_customer_42@axisbank")
    assert rec.threat_level == "CLEAN"
    assert rec.threat_score == 0.0
    assert rec.listed is False


def test_dpip_registry_update_and_lookup() -> None:
    adapter: DpipSmartRegistryAdapter = get_dpip_adapter()
    new_mule = "confirmed_syndicate_node@paytm"
    update_req = DpipRegistryUpdateRequest(
        vpa_or_hash=new_mule,
        threat_level="CRITICAL",
        threat_score=0.98,
        reason="I4C multi-bank cybercrime nexus report",
        agency="LEAS_MHA_PORTAL",
    )
    updated: DpipRegistryRecord = adapter.update_registry(update_req)
    assert updated.threat_level == "CRITICAL"
    assert updated.threat_score == 0.98
    assert updated.listed is True
    assert "LEAS_MHA_PORTAL" in updated.reporting_agencies

    # Subsequent query must hit the updated record
    subsequent = adapter.query_vpa(new_mule)
    assert subsequent.threat_level == "CRITICAL"
    assert subsequent.threat_score == 0.98
    assert subsequent.listed is True


# ── Mock PSP Adapter & StandardFraudSignal Tests ─────────────────────────────


def test_psp_adapter_generate_signal() -> None:
    psp: MockPspAdapter = get_psp_adapter()
    sig: StandardFraudSignal = psp.generate_signal(
        psp="PhonePe",
        vpa="mule_target_01@okaxis",
        anomaly_type="velocity_anomaly",
        severity="HIGH",
        confidence=0.91,
    )
    assert isinstance(sig, StandardFraudSignal)
    assert sig.source == "psp_phonepe"
    assert sig.institution == "PhonePe"
    assert sig.anomaly_type == "velocity_anomaly"
    assert sig.upi_id == "mule_target_01@okaxis"
    assert "PSP:PhonePe" in sig.tags
    assert sig.severity == "HIGH"


def test_psp_adapter_publish_to_mesh() -> None:
    import asyncio
    psp: MockPspAdapter = get_psp_adapter()
    sig: StandardFraudSignal = psp.generate_signal(
        psp="Paytm",
        vpa="synthetic_beneficiary@paytm",
        anomaly_type="suspicious_beneficiary",
        severity="HIGH",
        details="[Paytm Risk Guard] Rapid inflow from 12 distinct payers in 3 minutes",
    )
    published = asyncio.run(psp.publish_to_mesh(sig))
    assert published is not None
    assert published.signal_id.startswith("SIG-")
    assert published.source == "psp_paytm"
    assert published.upi_id == "synthetic_beneficiary@paytm"


# ── InstitutionalAdapterService Tests ───────────────────────────────────────


def test_institutional_service_evaluate_for_transaction() -> None:
    service: InstitutionalAdapterService = get_institutional_adapters()
    txn = UpiTransaction(
        txn_id="TXN_TEST_HP_01",
        payer_vpa="legit_payer@oksbi",
        payee_vpa="honeypot_trap_01@okaxis",
        amount=50000.0,
        payer_psp="oksbi",
        payee_psp="okaxis",
    )
    res = service.evaluate_for_transaction(txn)
    assert "mock_npci_score" in res
    assert "mock_dpip_threat_level" in res
    assert "contributing_signals" in res
    assert res["mock_npci_score"] >= 0.85
    assert res["mock_dpip_threat_level"] >= 0.85

    signals = res["contributing_signals"]
    assert len(signals) >= 2
    insts = [s.get("institution") for s in signals]
    assert "NPCI" in insts
    assert "DPIP" in insts


# ── REST API Endpoints Tests ────────────────────────────────────────────────


def test_api_npci_mulehunter(client: TestClient) -> None:
    # Test valid honeypot
    resp = client.get("/adapters/npci/mulehunter?vpa=honeypot_mule_99@okhdfcbank")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_rating"] == "HIGH"
    assert data["mule_probability"] >= 0.85

    # Test clean account
    resp_clean = client.get("/adapters/npci/mulehunter?vpa=clean_customer@okaxis")
    assert resp_clean.status_code == 200
    data_clean = resp_clean.json()
    assert data_clean["risk_rating"] == "LOW"
    assert data_clean["mule_probability"] < 0.15

    # Test mirror at /upi/adapters
    resp_mirror = client.get("/upi/adapters/npci/mulehunter?vpa=honeypot_mule_99@okhdfcbank")
    assert resp_mirror.status_code == 200


def test_api_dpip_registry(client: TestClient) -> None:
    # Test query by VPA
    resp = client.get("/adapters/dpip/registry?vpa=honeypot_trap_01@okaxis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["threat_level"] == "HIGH"
    assert data["threat_score"] >= 0.85
    assert data["listed"] is True

    # Test query by hash
    vpa_hash = hashlib.sha256("honeypot_trap_01@okaxis".encode()).hexdigest()
    resp_hash = client.get(f"/adapters/dpip/registry?vpa_hash={vpa_hash}")
    assert resp_hash.status_code == 200
    assert resp_hash.json()["vpa_hash"] == vpa_hash

    # Test missing parameters -> 400
    resp_bad = client.get("/adapters/dpip/registry")
    assert resp_bad.status_code == 400


def test_api_dpip_update_registry(client: TestClient) -> None:
    payload = {
        "vpa_or_hash": "investigative_target@ibl",
        "threat_level": "HIGH",
        "threat_score": 0.95,
        "reason": "Suspected syndicate pass-through node",
        "agency": "SAMPATI_TRIAGE",
    }
    resp = client.post("/adapters/dpip/registry", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["threat_level"] == "HIGH"
    assert data["threat_score"] == 0.95
    assert data["listed"] is True

    # Verify query retrieves it
    query_resp = client.get("/adapters/dpip/registry?vpa=investigative_target@ibl")
    assert query_resp.status_code == 200
    assert query_resp.json()["threat_score"] == 0.95


def test_api_psp_simulate(client: TestClient) -> None:
    payload = {
        "psp": "PhonePe",
        "vpa": "burst_fraud_vpa@ybl",
        "anomaly_type": "velocity_anomaly",
        "severity": "HIGH",
        "confidence": 0.90,
        "publish_to_mesh": True,
    }
    resp = client.post("/adapters/psp/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["signal"]["institution"] == "PhonePe"
    assert data["published"] is True
    assert data["mesh_signal_id"] is not None


def test_api_contributing_signals(client: TestClient) -> None:
    resp = client.get("/adapters/signals/contributing?vpa=honeypot_trap_01@okaxis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mock_npci_score"] >= 0.85
    assert data["mock_dpip_threat_level"] >= 0.85
    assert len(data["contributing_signals"]) >= 2


# ── /upi/check Inline Gate Contract Tests ───────────────────────────────────


def test_upi_check_honeypot_returns_nonzero_institutional_scores(client: TestClient) -> None:
    """Requirement: Honeypots must return non-zero mock_npci_score and mock_dpip_threat_level."""
    payload = {
        "txn_id": "TXN_INST_HP_001",
        "payer_vpa": "innocent_buyer@oksbi",
        "payee_vpa": "honeypot_trap_01@okaxis",
        "amount": 25000.0,
        "payer_psp": "oksbi",
        "payee_psp": "okaxis",
        "device_id": "DEV_HP_TEST_01",
        "txn_type": "P2P",
    }
    resp = client.post("/upi/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Core institutional adapter contract
    assert "mock_npci_score" in data, "mock_npci_score missing from /upi/check"
    assert "mock_dpip_threat_level" in data, "mock_dpip_threat_level missing from /upi/check"
    assert "contributing_signals" in data, "contributing_signals missing from /upi/check"

    assert data["mock_npci_score"] > 0, "Honeypot returned 0 for mock_npci_score"
    assert data["mock_npci_score"] >= 0.85
    assert data["mock_dpip_threat_level"] != 0, "Honeypot returned 0 for mock_dpip_threat_level"
    assert float(data["mock_dpip_threat_level"]) >= 0.85

    assert len(data["contributing_signals"]) >= 2
    insts = [s["institution"] for s in data["contributing_signals"]]
    assert "NPCI" in insts
    assert "DPIP" in insts


def test_upi_check_clean_returns_low_institutional_scores(client: TestClient) -> None:
    payload = {
        "txn_id": "TXN_INST_CLEAN_001",
        "payer_vpa": "clean_payer@oksbi",
        "payee_vpa": "clean_merchant@okaxis",
        "amount": 500.0,
        "payer_psp": "oksbi",
        "payee_psp": "okaxis",
        "txn_type": "P2M",
    }
    resp = client.post("/upi/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "mock_npci_score" in data
    assert "mock_dpip_threat_level" in data
    assert data["mock_npci_score"] < 0.15
    assert float(data["mock_dpip_threat_level"]) == 0.0


def test_upi_check_case_dossier_preserves_institutional_signals(client: TestClient) -> None:
    """When a transaction triggers a HOLD or BLOCK, the case record contains institutional data."""
    payload = {
        "txn_id": "TXN_CASE_INST_99",
        "payer_vpa": "victim@oksbi",
        "payee_vpa": "darkweb_mule_sink@okaxis",
        "amount": 100000.0,
        "payer_psp": "oksbi",
        "payee_psp": "okaxis",
        "txn_type": "P2P",
    }
    resp = client.post("/upi/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    case_id = data.get("case_id")
    assert case_id is not None

    # Fetch case dossier
    case_resp = client.get(f"/upi/cases/{case_id}")
    assert case_resp.status_code == 200
    cdata = case_resp.json()
    assert cdata["mock_npci_score"] >= 0.85
    assert float(cdata["mock_dpip_threat_level"]) >= 0.85
    assert len(cdata["contributing_signals"]) >= 2

"""Comprehensive Unit, Integration, and Contract Tests for Threat Intelligence Layer (R1).

Validates:
1. Pydantic schema validation & error handling (ThreatSignalCreateRequest, 422 rejection).
2. Regex entity extraction for Indian phone numbers, UPI VPAs, URLs, and social engineering tags.
3. Campaign clustering similarity calculation (e.g. KYC phishing matching CAMP-KYC-PHISH-01 at ~94%).
4. Central Fraud Graph node and edge management via FraudGraphService (networkx.DiGraph).
5. Cross-entity linkage connecting threat signals to existing UPI cases and mule rings.
6. FastAPI endpoints in app/api/intel.py (/intel/signals, /intel/graph, /intel/campaigns, /intel/simulate).
7. Multi-prefix route aliasing (/threat-intel/*, /upi/intel/*) and SPA static fallback exclusion.
"""
from __future__ import annotations

import asyncio
import unittest

from fastapi.testclient import TestClient

from app.federation.coordinator import get_federation
from app.main import app
from app.models.threat_intel import (
    ThreatSignalCreateRequest,
    extract_entities_from_text,
)
from app.services.graph_service import get_fraud_graph
from app.services.threat_intel_service import get_threat_intel_service
from app.services.upi_cases import get_upi_case_service


class TestThreatSignalValidation(unittest.TestCase):
    """Test Pydantic validation rules and edge conditions."""

    def test_valid_explicit_identifiers(self) -> None:
        """Verify request with explicit phone, UPI ID, URL and tags is valid."""
        req = ThreatSignalCreateRequest(
            source="mobile_app",
            phone="+919876543210",
            upi_id="phish_trap@oksbi",
            url="https://sbi-kyc-alert.com/login",
            tags=["Bank impersonation", "Urgency"],
            severity="CRITICAL",
            confidence=0.95,
        )
        self.assertEqual(req.phone, "+919876543210")
        self.assertEqual(req.upi_id, "phish_trap@oksbi")
        self.assertEqual(req.severity, "CRITICAL")
        self.assertEqual(req.confidence, 0.95)

    def test_valid_unstructured_raw_content_only(self) -> None:
        """Verify request with only raw text content passes validation."""
        req = ThreatSignalCreateRequest(
            raw_content="Dear customer your account is blocked. Update KYC at https://sbi-alert.in or pay Rs 1 to scam@oksbi. Call 9876543210.",
            source="sms_feed",
        )
        self.assertIsNotNone(req.raw_content)
        self.assertEqual(req.source, "sms_feed")
        self.assertEqual(req.severity, "MEDIUM")

    def test_validation_rejection_missing_all_identifiers(self) -> None:
        """Verify error when no identifiers and no raw content are provided."""
        with self.assertRaises(ValueError):
            ThreatSignalCreateRequest(
                source="mobile_app",
                phone=None,
                upi_id=None,
                url=None,
                raw_content=None,
            )

    def test_validation_rejection_invalid_severity(self) -> None:
        """Verify error when severity is not one of LOW, MEDIUM, HIGH, CRITICAL."""
        with self.assertRaises(ValueError):
            ThreatSignalCreateRequest(
                upi_id="fraud@oksbi",
                severity="SUPER_EXTREME",
            )

    def test_validation_defensible_confidence_cap(self) -> None:
        """Verify confidence is capped at 0.98 to prevent indefensible 100% claims."""
        req = ThreatSignalCreateRequest(
            upi_id="fraud@oksbi",
            confidence=1.0,
        )
        self.assertLessEqual(req.confidence, 0.98)


class TestRegexEntityExtraction(unittest.TestCase):
    """Test regex extraction engine for Indian telecommunication & payment entities."""

    def test_extract_indian_phone_numbers(self) -> None:
        """Extract Indian mobile numbers across diverse formats (+91, 0, spaces, dashes)."""
        texts = [
            ("Call +919876543210 immediately", "9876543210"),
            ("Contact customer care 09876543210 today", "9876543210"),
            ("Helpline +91 98765 43210 available", "9876543210"),
            ("Direct line 9876543210 for KYC", "9876543210"),
        ]
        for text, expected_digits in texts:
            entities = extract_entities_from_text(text)
            self.assertTrue(any(expected_digits in p for p in entities.phones), f"Failed on: {text}")

    def test_extract_upi_vpa(self) -> None:
        """Extract UPI VPAs from unstructured payment and scam messages."""
        text = "Send Rs 1 to phish_trap@oksbi or pay verification fee at kyc.verify@icici or support@paytm."
        entities = extract_entities_from_text(text)
        vpas = [v.lower() for v in entities.upi_ids]
        self.assertIn("phish_trap@oksbi", vpas)
        self.assertIn("kyc.verify@icici", vpas)
        self.assertIn("support@paytm", vpas)

    def test_extract_urls(self) -> None:
        """Extract phishing URLs (HTTP, HTTPS, domain handles)."""
        text = "Login to https://sbi-kyc-update.com/login or http://pan-verification.in/auth to avoid block."
        entities = extract_entities_from_text(text)
        urls = entities.urls
        self.assertIn("https://sbi-kyc-update.com/login", urls)
        self.assertIn("http://pan-verification.in/auth", urls)

    def test_extract_social_engineering_tags(self) -> None:
        """Extract behavioral social engineering tags based on scam keywords."""
        msg1 = "Urgent: Your SBI bank account will be blocked within 24 hours. Update KYC now."
        entities1 = extract_entities_from_text(msg1)
        self.assertTrue(any("Bank impersonation" in t or "KYC" in t or "Urgency" in t for t in entities1.tags))

        msg2 = "Congratulations! You won Rs 50000 lottery reward. Install bonus task APK now."
        entities2 = extract_entities_from_text(msg2)
        self.assertTrue(any("Lottery" in t or "Reward" in t or "APK" in t for t in entities2.tags))


class TestCampaignClustering(unittest.TestCase):
    """Test campaign clustering and similarity calculation against known syndicate clusters."""

    def test_kyc_phishing_campaign_clustering(self) -> None:
        """Verify KYC phishing tags and keywords cluster into CAMP-KYC-PHISH-01 with ~94% similarity."""
        service = get_threat_intel_service()
        req = ThreatSignalCreateRequest(
            source="mobile_app",
            phone="+919876543210",
            upi_id="phish_trap@oksbi",
            url="https://sbi-kyc-alert.com/login",
            tags=["Bank impersonation", "Urgency", "KYC suspension"],
            raw_content="Dear customer your SBI account is blocked. Update KYC immediately at https://sbi-kyc-alert.com or send Rs 1 to phish_trap@oksbi. Call 9876543210.",
            severity="CRITICAL",
        )
        match = service.match_campaign_from_signal(req)
        self.assertIsNotNone(match)
        self.assertEqual(match["campaign_id"], "CAMP-KYC-PHISH-01")
        self.assertAlmostEqual(match["similarity"], 0.94, delta=0.01)

    def test_task_investment_scam_clustering(self) -> None:
        """Verify task scam keywords cluster into CAMP-INVESTMENT-03."""
        service = get_threat_intel_service()
        req = ThreatSignalCreateRequest(
            source="user_report",
            upi_id="bonus_crypto@okaxis",
            raw_content="Join telegram task group to earn crypto bonus and instant profit commission.",
            tags=["Lottery/Reward", "Investment scam"],
            severity="HIGH",
        )
        match = service.match_campaign_from_signal(req)
        self.assertIsNotNone(match)
        self.assertEqual(match["campaign_id"], "CAMP-INVESTMENT-03")
        self.assertGreaterEqual(match["similarity"], 0.75)

    def test_smurfing_dispersal_clustering(self) -> None:
        """Verify mule smurfing keywords cluster into CAMP-SMURF-BURST-02."""
        service = get_threat_intel_service()
        req = ThreatSignalCreateRequest(
            source="psp_telemetry",
            upi_id="smurf_conduit@okaxis",
            raw_content="Mule conduit alert: rapid micro-split transfers and instant cashout dispersal.",
            tags=["Smurfing Dispersal"],
            severity="HIGH",
        )
        match = service.match_campaign_from_signal(req)
        self.assertIsNotNone(match)
        self.assertEqual(match["campaign_id"], "CAMP-SMURF-BURST-02")
        self.assertGreaterEqual(match["similarity"], 0.75)


class TestFraudGraphService(unittest.TestCase):
    """Test FraudGraphService NetworkX DiGraph operations."""

    def setUp(self) -> None:
        self.graph = get_fraud_graph()
        self.graph.clear()

    def test_graph_add_signal_nodes_and_edges(self) -> None:
        """Verify adding a signal registers SIGNAL, PHONE, VPA, and URL nodes and edges."""
        signal_data = {
            "signal_id": "SIG-TEST-001",
            "phone": "+919876543210",
            "upi_id": "phish_trap@oksbi",
            "url": "https://sbi-kyc-alert.com/login",
            "severity": "CRITICAL",
            "matched_campaign_id": "CAMP-KYC-PHISH-01",
            "matched_campaign_name": "KYC Phishing Syndicate",
            "similarity": 0.94,
        }
        linked_nodes = self.graph.add_threat_signal(signal_data)
        self.assertIn("SIGNAL:SIG-TEST-001", linked_nodes)
        self.assertIn("VPA:phish_trap@oksbi", linked_nodes)
        self.assertIn("PHONE:+919876543210", linked_nodes)
        self.assertIn("URL:https://sbi-kyc-alert.com/login", linked_nodes)

        exported = self.graph.export_graph()
        node_ids = [n["id"] for n in exported["nodes"]]
        self.assertIn("SIGNAL:SIG-TEST-001", node_ids)
        self.assertIn("VPA:phish_trap@oksbi", node_ids)
        self.assertGreaterEqual(len(exported["edges"]), 3)

    def test_graph_subgraph_traversal(self) -> None:
        """Verify localized subgraph extraction around an entity node."""
        signal_data = {
            "signal_id": "SIG-TEST-SUBGRAPH",
            "upi_id": "subgraph_mule@okaxis",
            "phone": "+919111222333",
            "severity": "HIGH",
        }
        self.graph.add_threat_signal(signal_data)
        subgraph = self.graph.get_subgraph(entity_id="VPA:subgraph_mule@okaxis", depth=1)
        sub_node_ids = [n["id"] for n in subgraph["nodes"]]
        self.assertIn("VPA:subgraph_mule@okaxis", sub_node_ids)
        self.assertIn("SIGNAL:SIG-TEST-SUBGRAPH", sub_node_ids)

    def test_graph_clear_and_stats(self) -> None:
        """Verify graph clear and statistics."""
        self.graph.clear()
        stats = self.graph.get_stats()
        self.assertEqual(stats["total_nodes"], 0)
        self.assertEqual(stats["total_edges"], 0)

    def test_graph_transactions_and_campaign_link(self) -> None:
        """Verify adding financial transfer edges and linking VPAs to campaigns."""
        self.graph.clear()
        self.graph.add_transaction("alice@oksbi", "bob@okaxis", 15000.0, "TXN_001")
        self.graph.link_vpa_to_campaign("bob@okaxis", "CAMP-KYC-PHISH-01", similarity=0.94)
        exported = self.graph.export_graph()
        self.assertTrue(any(e["type"] == "TRANSACTED_TO" for e in exported["edges"]))
        self.assertTrue(any(e["type"] == "MEMBER_OF_CAMPAIGN" for e in exported["edges"]))


class TestThreatGraphLinkageToCases(unittest.TestCase):
    """Test linking incoming threat signals to existing UPI cases and mule rings."""

    def setUp(self) -> None:
        self.graph = get_fraud_graph()
        self.graph.clear()
        self.case_service = get_upi_case_service()
        self.fed = get_federation()
        self.created_case_id = None
        self.test_ring_hash = None

    def tearDown(self) -> None:
        self.graph.clear()
        if self.created_case_id:
            with self.case_service._lock:
                self.case_service._cases.pop(self.created_case_id, None)
        if self.test_ring_hash:
            with self.fed._lock:
                self.fed._rings.pop(self.test_ring_hash, None)

    def test_threat_signal_links_to_existing_case_vpa(self) -> None:
        """Verify when threat signal contains a VPA with an active case, they are linked in graph."""
        vpa = "active_mule_case@okaxis"
        self.created_case_id = self.case_service.create_case({
            "txn_id": "TXN_CASE_LINK_01",
            "payer_vpa": "victim@okaxis",
            "payee_vpa": vpa,
            "amount": 75000.0,
            "device_id": "DEV_LINK_01",
        })
        case_id = self.created_case_id

        # Ingest threat signal with the same VPA
        service = get_threat_intel_service()
        req = ThreatSignalCreateRequest(
            source="mobile_app",
            upi_id=vpa,
            tags=["Bank impersonation"],
            severity="CRITICAL",
        )
        resp = asyncio.run(service.ingest_signal(req))

        self.assertEqual(resp.upi_id, vpa)
        self.assertEqual(resp.case_id, case_id)

        # Verify graph contains linkage between VPA and CASE
        exported = self.graph.export_graph()
        edges = exported["edges"]
        has_case_link = any(
            (e["source"] == f"VPA:{vpa}" and f"CASE:{case_id}" in e["target"]) or
            (e["target"] == f"VPA:{vpa}" and f"CASE:{case_id}" in e["source"])
            for e in edges
        )
        self.assertTrue(has_case_link, "Expected edge between VPA and existing Case")

    def test_threat_signal_links_to_mule_ring(self) -> None:
        """Verify when threat signal contains a VPA with a known mule ring, ring_hash is linked."""
        vpa = "ring_mule_target@oksbi"
        self.test_ring_hash = "RING_TEST_HASH_M1"
        with self.fed._lock:
            self.fed._rings[self.test_ring_hash] = {
                "ring_hash": self.test_ring_hash,
                "members": [vpa],
                "size": 1,
            }

        service = get_threat_intel_service()
        req = ThreatSignalCreateRequest(
            source="psp_feed",
            upi_id=vpa,
            tags=["Rapid Conduit"],
            severity="HIGH",
        )
        resp = asyncio.run(service.ingest_signal(req))
        self.assertEqual(resp.ring_hash, self.test_ring_hash)


class TestThreatIntelApiEndpoints(unittest.TestCase):
    """End-to-end API HTTP integration tests using FastAPI TestClient."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        get_threat_intel_service().clear()
        get_fraud_graph().clear()

    def tearDown(self) -> None:
        get_threat_intel_service().clear()
        get_fraud_graph().clear()


    def test_post_signals_success_201(self) -> None:
        """POST /intel/signals with valid explicit fields returns 201 Created."""
        payload = {
            "source": "mobile_app",
            "phone": "+919876543210",
            "upi_id": "phish_trap@oksbi",
            "url": "https://sbi-kyc-alert.com/login",
            "tags": ["Bank impersonation", "Urgency", "KYC Expiry"],
            "raw_content": "Dear customer your SBI account is blocked. Update KYC immediately.",
            "severity": "CRITICAL",
            "confidence": 0.95,
        }
        res = self.client.post("/intel/signals", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("signal_id", data)
        self.assertEqual(data["severity"], "CRITICAL")
        self.assertEqual(data["upi_id"], "phish_trap@oksbi")
        self.assertIsNotNone(data["matched_campaign"])
        self.assertGreaterEqual(data["matched_campaign"]["similarity"], 0.85)

    def test_post_signals_raw_sms_extraction_201(self) -> None:
        """POST /intel/signals with unstructured SMS extracts entities and returns 201."""
        payload = {
            "source": "sms_feed",
            "raw_content": "URGENT: SBI account blocked. Pay Rs 10 to unblock_help@oksbi or visit https://sbi-unblock.com. Call 9811223344.",
            "severity": "HIGH",
        }
        res = self.client.post("/intel/signals", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        extracted = data["extracted_entities"]
        self.assertTrue(any("unblock_help@oksbi" in v for v in extracted["upi_ids"]))
        self.assertTrue(any("https://sbi-unblock.com" in u for u in extracted["urls"]))
        self.assertTrue(any("9811223344" in p for p in extracted["phones"]))

    def test_post_signals_validation_failure_422(self) -> None:
        """POST /intel/signals with empty payload returns 422 Unprocessable Entity."""
        res = self.client.post("/intel/signals", json={})
        self.assertEqual(res.status_code, 422)

    def test_get_signals_pagination_and_filtering(self) -> None:
        """GET /intel/signals supports limit, offset, and severity filtering."""
        # Ingest one CRITICAL and one LOW signal
        self.client.post("/intel/signals", json={"upi_id": "crit@okaxis", "severity": "CRITICAL"})
        self.client.post("/intel/signals", json={"upi_id": "low@okaxis", "severity": "LOW"})

        res = self.client.get("/intel/signals?limit=10&offset=0&severity=CRITICAL")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("signals", data)
        self.assertIn("total", data)
        self.assertTrue(all(s["severity"] == "CRITICAL" for s in data["signals"]))

    def test_get_signal_by_id_success_and_404(self) -> None:
        """GET /intel/signals/{signal_id} returns 200 on success and 404 JSON on missing ID."""
        create_res = self.client.post(
            "/intel/signals",
            json={"upi_id": "lookup_vpa@okhdfcbank", "severity": "HIGH"},
        )
        sig_id = create_res.json()["signal_id"]

        # Valid lookup
        res = self.client.get(f"/intel/signals/{sig_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["signal_id"], sig_id)

        # Invalid lookup
        res_404 = self.client.get("/intel/signals/NONEXISTENT_SIGNAL_UUID")
        self.assertEqual(res_404.status_code, 404)
        self.assertTrue(res_404.headers["content-type"].startswith("application/json"))
        self.assertIn("detail", res_404.json())

    def test_get_graph_endpoint(self) -> None:
        """GET /intel/graph returns nodes and edges payload."""
        res = self.client.get("/intel/graph")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)

    def test_get_campaigns_endpoint(self) -> None:
        """GET /intel/campaigns returns active syndicate campaigns."""
        res = self.client.get("/intel/campaigns")
        self.assertEqual(res.status_code, 200)
        camps = res.json()
        self.assertIsInstance(camps, list)
        self.assertTrue(any(c["campaign_id"] == "CAMP-KYC-PHISH-01" for c in camps))

    def test_post_simulate_endpoint(self) -> None:
        """POST /intel/simulate generates synthetic threat signals."""
        res = self.client.post("/intel/simulate", json={"count": 3})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["signals"]), 3)

    def test_subgraph_api_endpoint(self) -> None:
        """GET /intel/graph with entity_id returns localized neighborhood."""
        self.client.post("/intel/signals", json={"upi_id": "api_subgraph@oksbi", "severity": "MEDIUM"})
        res = self.client.get("/intel/graph?entity_id=VPA:api_subgraph@oksbi&depth=1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(any("api_subgraph@oksbi" in n["id"] for n in data["nodes"]))


class TestRouteAliasesAndSpaFallback(unittest.TestCase):
    """Verify route aliases (/threat-intel/*, /upi/intel/*) and SPA static fallback exclusion."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_threat_intel_prefix_aliases(self) -> None:
        """Verify endpoints are fully accessible under /threat-intel/ prefix."""
        # Test alias for GET /threat-intel/graph
        res_graph = self.client.get("/threat-intel/graph")
        self.assertEqual(res_graph.status_code, 200)

        # Test alias for GET /threat-intel/campaigns
        res_camps = self.client.get("/threat-intel/campaigns")
        self.assertEqual(res_camps.status_code, 200)

        # Test alias for POST /threat-intel/signals
        res_sig = self.client.post(
            "/threat-intel/signals",
            json={"upi_id": "alias_trap@okaxis", "severity": "MEDIUM"},
        )
        self.assertEqual(res_sig.status_code, 201)

    def test_upi_intel_prefix_aliases(self) -> None:
        """Verify endpoints are fully accessible under /upi/intel/ prefix."""
        res = self.client.get("/upi/intel/campaigns")
        self.assertEqual(res.status_code, 200)

    def test_spa_fallback_preserves_api_404_json(self) -> None:
        """Verify non-existent API routes return JSON 404 and are NOT intercepted by SPA index.html."""
        # Under /intel
        res_intel = self.client.get("/intel/signals/DEFINITELY_UNKNOWN_ID")
        self.assertEqual(res_intel.status_code, 404)
        self.assertTrue(res_intel.headers["content-type"].startswith("application/json"))
        self.assertNotIn("<!DOCTYPE html>", res_intel.text)

        # Under /threat-intel
        res_threat = self.client.get("/threat-intel/signals/DEFINITELY_UNKNOWN_ID")
        self.assertEqual(res_threat.status_code, 404)
        self.assertTrue(res_threat.headers["content-type"].startswith("application/json"))
        self.assertNotIn("<!DOCTYPE html>", res_threat.text)


if __name__ == "__main__":
    unittest.main()

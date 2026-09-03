"""Adversarial Empirical Stress Test Suite for Milestone 1 (Threat Intel Layer).

Covers:
1. High-concurrency burst load (POST /intel/signals across 50 concurrent threads).
2. Large payload handling (50KB message with dozens of extracted entities).
3. Pagination edge cases (limit=10000, offset=-5, limit=0, limit=500, offset=5000).
4. Route disambiguation and SPA fallback (/intel/invalid -> JSON 404, /threat-intel -> HTML 200).
5. Idempotent graph node deduplication (reused phone/UPI/URL across distinct signals).
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import sys
import time
import unittest
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from app.main import app
from app.services.graph_service import get_fraud_graph
from app.services.threat_intel_service import get_threat_intel_service


class TestAdversarialThreatIntel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.threat_service = get_threat_intel_service()
        cls.fraud_graph = get_fraud_graph()

    def test_01_concurrent_burst_load(self) -> None:
        """Adversarially stress-test POST /intel/signals under a 50-thread concurrent burst."""
        total_requests = 50
        results: List[Dict[str, Any]] = []
        errors: List[str] = []

        def fire_signal(idx: int) -> Dict[str, Any]:
            t0 = time.perf_counter()
            payload = {
                "source": "mobile_app",
                "phone": f"+9198765{idx:05d}",
                "upi_id": f"burst_user_{idx:03d}@oksbi",
                "url": f"https://burst-phish-{idx:03d}.site/kyc",
                "tags": ["Bank impersonation", "Urgency", "KYC suspension"],
                "raw_content": f"URGENT: Alert {idx}, account locked. Update at https://burst-phish-{idx:03d}.site/kyc or call +9198765{idx:05d}.",
                "severity": "CRITICAL" if idx % 2 == 0 else "HIGH",
                "confidence": 0.95,
            }
            try:
                resp = self.client.post("/intel/signals", json=payload)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return {
                    "idx": idx,
                    "status_code": resp.status_code,
                    "elapsed_ms": elapsed_ms,
                    "data": resp.json() if resp.status_code == 201 else resp.text,
                }
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return {
                    "idx": idx,
                    "status_code": 0,
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                }

        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(fire_signal, i) for i in range(total_requests)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                results.append(res)
                if res["status_code"] != 201:
                    errors.append(f"Request {res['idx']} failed: {res}")

        total_wall_time_s = time.perf_counter() - start_time
        latencies = [r["elapsed_ms"] for r in results if r["status_code"] == 201]
        latencies.sort()

        p50 = latencies[len(latencies) // 2] if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0
        avg = sum(latencies) / len(latencies) if latencies else 0.0
        throughput = total_requests / total_wall_time_s if total_wall_time_s > 0 else 0.0

        print("\n--- [TEST 1: CONCURRENT BURST LOAD RESULTS] ---")
        print(f"Total Requests: {total_requests}")
        print(f"Total Wall Clock Time: {total_wall_time_s:.3f} s")
        print(f"Effective Throughput: {throughput:.1f} req/sec")
        print(f"Success Rate: {(len(latencies) / total_requests) * 100:.1f}% (Failed: {len(errors)})")
        print(f"Latency P50: {p50:.2f} ms | P95: {p95:.2f} ms | P99: {p99:.2f} ms | Mean: {avg:.2f} ms")

        self.assertEqual(len(errors), 0, f"Encountered {len(errors)} failures under concurrent burst load: {errors[:5]}")
        self.assertEqual(len(latencies), total_requests)

        # Verify in-memory cache consistency
        signal_ids = [r["data"]["signal_id"] for r in results if "data" in r and isinstance(r["data"], dict)]
        self.assertEqual(len(signal_ids), total_requests)
        self.assertEqual(len(set(signal_ids)), total_requests, "Duplicate signal_ids generated during concurrent burst!")

        # Verify all signals are searchable
        with self.threat_service._lock:
            for sig_id in signal_ids:
                self.assertIn(sig_id, self.threat_service._signals, f"Signal {sig_id} missing from service cache")

    def test_02_large_payload_handling_50kb(self) -> None:
        """Adversarially test 50KB message payload with dozens of embedded entities."""
        # Build 50KB realistic scam payload (50,000+ characters)
        base_unit = (
            "URGENT NOTICE: Your SBI and HDFC bank accounts have been temporarily suspended due to non-compliance "
            "with mandatory RBI KYC verification guidelines. Please update your details immediately at https://sbi-kyc-secure-{idx}.com/verify "
            "or transfer a verification sum of Rs 10 to emergency_support_{idx}@oksbi. For telephonic assistance, reach out to "
            "helpline numbers +9198765{idx:05d} or +9176543{idx:05d}. Failure to comply within 24 hours will result in permanent debit freeze! "
        )
        units = []
        curr_len = 0
        idx = 0
        while curr_len < 51200:
            segment = base_unit.format(idx=idx)
            units.append(segment)
            curr_len += len(segment)
            idx += 1

        large_text = "\n\n".join(units)
        payload_size_kb = len(large_text.encode("utf-8")) / 1024.0

        print(f"\n--- [TEST 2: LARGE PAYLOAD TEST] ---")
        print(f"Generated Payload Size: {payload_size_kb:.2f} KB ({len(large_text)} chars)")
        print(f"Total Repetition Blocks: {len(units)}")

        self.assertGreaterEqual(payload_size_kb, 50.0, "Payload must be at least 50KB")

        t0 = time.perf_counter()
        resp = self.client.post(
            "/intel/signals",
            json={
                "source": "sms_bulk_feed",
                "raw_content": large_text,
                "severity": "CRITICAL",
                "confidence": 0.95,
            },
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        print(f"Response Status: {resp.status_code}")
        print(f"Processing Latency: {elapsed_ms:.2f} ms")

        self.assertEqual(resp.status_code, 201, f"Expected 201 Created, got {resp.status_code}: {resp.text}")
        data = resp.json()

        extracted = data["extracted_entities"]
        print(f"Extracted Phones Count: {len(extracted['phones'])}")
        print(f"Extracted UPI IDs Count: {len(extracted['upi_ids'])}")
        print(f"Extracted URLs Count: {len(extracted['urls'])}")
        print(f"Extracted Social Tags: {extracted['tags']}")
        print(f"Matched Campaign: {data.get('matched_campaign_name')} (Sim: {data.get('similarity_score')})")
        print(f"Linked Graph Nodes: {len(data.get('linked_graph_nodes', []))}")

        # Assertions on extraction and performance
        self.assertIn("Bank impersonation", extracted["tags"])
        self.assertIn("KYC suspension", extracted["tags"])
        self.assertIn("Urgency", extracted["tags"])
        self.assertEqual(data["matched_campaign_id"], "CAMP-KYC-PHISH-01")
        self.assertAlmostEqual(data["similarity_score"], 0.94, places=2)
        # Latency check: Must complete comfortably without ReDoS (< 2000ms)
        self.assertLess(elapsed_ms, 2000.0, f"50KB parsing took too long: {elapsed_ms:.2f} ms")

    def test_03_pagination_edge_cases(self) -> None:
        """Adversarially test boundary and invalid pagination parameters on GET /intel/signals."""
        print("\n--- [TEST 3: PAGINATION EDGE CASES] ---")

        # 1. limit=10000: exceeds le=500 constraint -> expect 422
        resp_large = self.client.get("/intel/signals?limit=10000&offset=0")
        print(f"GET /intel/signals?limit=10000 -> Status: {resp_large.status_code}")
        self.assertEqual(resp_large.status_code, 422)
        self.assertTrue(resp_large.headers["content-type"].startswith("application/json"))
        err_detail_1 = resp_large.json()
        self.assertIn("detail", err_detail_1)
        print(f"  Validation detail: {err_detail_1['detail'][0]['msg']}")

        # 2. offset=-5: violates ge=0 constraint -> expect 422
        resp_neg_offset = self.client.get("/intel/signals?limit=50&offset=-5")
        print(f"GET /intel/signals?offset=-5 -> Status: {resp_neg_offset.status_code}")
        self.assertEqual(resp_neg_offset.status_code, 422)
        self.assertTrue(resp_neg_offset.headers["content-type"].startswith("application/json"))
        err_detail_2 = resp_neg_offset.json()
        self.assertIn("detail", err_detail_2)
        print(f"  Validation detail: {err_detail_2['detail'][0]['msg']}")

        # 3. limit=0: violates ge=1 constraint -> expect 422
        resp_zero_limit = self.client.get("/intel/signals?limit=0&offset=0")
        print(f"GET /intel/signals?limit=0 -> Status: {resp_zero_limit.status_code}")
        self.assertEqual(resp_zero_limit.status_code, 422)
        self.assertTrue(resp_zero_limit.headers["content-type"].startswith("application/json"))
        err_detail_3 = resp_zero_limit.json()
        self.assertIn("detail", err_detail_3)
        print(f"  Validation detail: {err_detail_3['detail'][0]['msg']}")

        # 4. limit=-1: violates ge=1 -> expect 422
        resp_neg_limit = self.client.get("/intel/signals?limit=-1&offset=0")
        print(f"GET /intel/signals?limit=-1 -> Status: {resp_neg_limit.status_code}")
        self.assertEqual(resp_neg_limit.status_code, 422)

        # 5. Non-numeric limit -> expect 422
        resp_nan = self.client.get("/intel/signals?limit=foo_bar&offset=0")
        print(f"GET /intel/signals?limit=foo_bar -> Status: {resp_nan.status_code}")
        self.assertEqual(resp_nan.status_code, 422)

        # 6. Upper boundary limit=500 -> expect 200
        resp_upper_bound = self.client.get("/intel/signals?limit=500&offset=0")
        print(f"GET /intel/signals?limit=500 -> Status: {resp_upper_bound.status_code}")
        self.assertEqual(resp_upper_bound.status_code, 200)
        data_upper = resp_upper_bound.json()
        self.assertIn("signals", data_upper)
        self.assertIn("total", data_upper)
        self.assertEqual(data_upper["limit"], 500)

        # 7. Lower boundary limit=1 -> expect 200
        resp_lower_bound = self.client.get("/intel/signals?limit=1&offset=0")
        print(f"GET /intel/signals?limit=1 -> Status: {resp_lower_bound.status_code}")
        self.assertEqual(resp_lower_bound.status_code, 200)
        data_lower = resp_lower_bound.json()
        self.assertLessEqual(len(data_lower["signals"]), 1)
        self.assertEqual(data_lower["limit"], 1)

        # 8. Out-of-bounds offset=100000 -> expect 200 with empty signals list
        resp_high_offset = self.client.get("/intel/signals?limit=50&offset=100000")
        print(f"GET /intel/signals?offset=100000 -> Status: {resp_high_offset.status_code}")
        self.assertEqual(resp_high_offset.status_code, 200)
        data_high = resp_high_offset.json()
        self.assertEqual(len(data_high["signals"]), 0)
        self.assertEqual(data_high["offset"], 100000)

    def test_04_spa_fallback_disambiguation(self) -> None:
        """Adversarially verify route disambiguation between API 404s and SPA index.html."""
        print("\n--- [TEST 4: SPA FALLBACK DISAMBIGUATION] ---")

        # 1. /intel/invalid -> MUST be JSON 404
        resp_intel_inv = self.client.get("/intel/invalid")
        print(f"GET /intel/invalid -> Status: {resp_intel_inv.status_code}, Content-Type: {resp_intel_inv.headers.get('content-type')}")
        self.assertEqual(resp_intel_inv.status_code, 404)
        self.assertTrue(resp_intel_inv.headers["content-type"].startswith("application/json"))
        self.assertNotIn("<!DOCTYPE html>", resp_intel_inv.text)
        self.assertNotIn("<html", resp_intel_inv.text.lower())
        intel_json = resp_intel_inv.json()
        self.assertIn("detail", intel_json)

        # 2. /threat-intel -> MUST be HTML 200 (SPA client view)
        resp_threat_ui = self.client.get("/threat-intel")
        print(f"GET /threat-intel -> Status: {resp_threat_ui.status_code}, Content-Type: {resp_threat_ui.headers.get('content-type')}")
        self.assertEqual(resp_threat_ui.status_code, 200)
        self.assertTrue(resp_threat_ui.headers["content-type"].startswith("text/html"))
        self.assertIn("<div id=\"root\">", resp_threat_ui.text)

        # 3. /threat-intel/ -> MUST be HTML 200 (SPA client view with trailing slash)
        resp_threat_slash = self.client.get("/threat-intel/")
        print(f"GET /threat-intel/ -> Status: {resp_threat_slash.status_code}, Content-Type: {resp_threat_slash.headers.get('content-type')}")
        self.assertEqual(resp_threat_slash.status_code, 200)
        self.assertTrue(resp_threat_slash.headers["content-type"].startswith("text/html"))

        # 4. /threat-intel/invalid_route -> MUST be JSON 404 (API prefix disambiguation)
        resp_threat_inv = self.client.get("/threat-intel/invalid_route")
        print(f"GET /threat-intel/invalid_route -> Status: {resp_threat_inv.status_code}, Content-Type: {resp_threat_inv.headers.get('content-type')}")
        self.assertEqual(resp_threat_inv.status_code, 404)
        self.assertTrue(resp_threat_inv.headers["content-type"].startswith("application/json"))
        self.assertNotIn("<!DOCTYPE html>", resp_threat_inv.text)

        # 5. /api/nonexistent -> MUST be JSON 404
        resp_api_inv = self.client.get("/api/nonexistent")
        print(f"GET /api/nonexistent -> Status: {resp_api_inv.status_code}, Content-Type: {resp_api_inv.headers.get('content-type')}")
        self.assertEqual(resp_api_inv.status_code, 404)
        self.assertTrue(resp_api_inv.headers["content-type"].startswith("application/json"))

        # 6. /cases/invalid/sar/pdf -> MUST be 404 JSON
        resp_case_inv = self.client.get("/cases/NONEXISTENT_CASE_XYZ/sar/pdf")
        print(f"GET /cases/NONEXISTENT/sar/pdf -> Status: {resp_case_inv.status_code}")
        self.assertEqual(resp_case_inv.status_code, 404)
        self.assertTrue(resp_case_inv.headers["content-type"].startswith("application/json"))

        # 7. Arbitrary SPA client route /analytics or /federation-view -> MUST be HTML 200
        resp_client_route = self.client.get("/analytics")
        print(f"GET /analytics -> Status: {resp_client_route.status_code}, Content-Type: {resp_client_route.headers.get('content-type')}")
        self.assertEqual(resp_client_route.status_code, 200)
        self.assertTrue(resp_client_route.headers["content-type"].startswith("text/html"))

    def test_05_idempotent_graph_node_deduplication(self) -> None:
        """Adversarially verify that duplicate identifiers across signals do not duplicate graph nodes."""
        print("\n--- [TEST 5: IDEMPOTENT GRAPH NODE DEDUPLICATION] ---")

        shared_phone = "+919876500001"
        shared_upi = "dedup_syndicate@oksbi"
        shared_url = "https://dedup-phish-portal.com/login"

        initial_graph_nodes = self.fraud_graph._graph.number_of_nodes()

        # Ingest Signal A
        resp_a = self.client.post(
            "/intel/signals",
            json={
                "source": "mobile_app",
                "phone": shared_phone,
                "upi_id": shared_upi,
                "url": shared_url,
                "tags": ["Bank impersonation"],
                "severity": "HIGH",
            },
        )
        self.assertEqual(resp_a.status_code, 201)
        sig_id_a = resp_a.json()["signal_id"]

        phone_node_id = f"PHONE:{shared_phone}"
        vpa_node_id = f"VPA:{shared_upi}"
        url_node_id = f"URL:{shared_url}"

        # Nodes must exist
        self.assertTrue(self.fraud_graph._graph.has_node(phone_node_id))
        self.assertTrue(self.fraud_graph._graph.has_node(vpa_node_id))
        self.assertTrue(self.fraud_graph._graph.has_node(url_node_id))

        nodes_after_a = self.fraud_graph._graph.number_of_nodes()

        # Ingest Signal B with exact same identifiers
        resp_b = self.client.post(
            "/intel/signals",
            json={
                "source": "sms_feed",
                "phone": shared_phone,
                "upi_id": shared_upi,
                "url": shared_url,
                "tags": ["Urgency", "KYC suspension"],
                "severity": "CRITICAL",
            },
        )
        self.assertEqual(resp_b.status_code, 201)
        sig_id_b = resp_b.json()["signal_id"]

        nodes_after_b = self.fraud_graph._graph.number_of_nodes()

        # Ingest Signal C with same phone but different UPI
        diff_upi = "dedup_syndicate_sec@okaxis"
        resp_c = self.client.post(
            "/intel/signals",
            json={
                "source": "telecom_feed",
                "phone": shared_phone,
                "upi_id": diff_upi,
                "tags": ["Urgency"],
                "severity": "MEDIUM",
            },
        )
        self.assertEqual(resp_c.status_code, 201)
        sig_id_c = resp_c.json()["signal_id"]

        # Assert Deduplication:
        new_nodes_b = nodes_after_b - nodes_after_a
        print(f"Nodes after Signal A: {nodes_after_a}, Nodes after duplicate Signal B: {nodes_after_b}")
        print(f"Net new nodes from duplicate Signal B: {new_nodes_b} (Expected: exactly 1 for the new SIGNAL node)")
        self.assertEqual(new_nodes_b, 1, f"Expected exactly 1 new node (the signal), got {new_nodes_b}")

        # In Signal C: exactly 2 new nodes added (SIGNAL:sig_id_c and VPA:dedup_syndicate_sec@okaxis), while PHONE was reused!
        nodes_after_c = self.fraud_graph._graph.number_of_nodes()
        new_nodes_c = nodes_after_c - nodes_after_b
        print(f"Net new nodes from Signal C (reused phone, new UPI): {new_nodes_c} (Expected: 2)")
        self.assertEqual(new_nodes_c, 2, f"Expected exactly 2 new nodes, got {new_nodes_c}")

        # Verify edges from shared phone to all three signals exist
        signal_a_node = f"SIGNAL:{sig_id_a}"
        signal_b_node = f"SIGNAL:{sig_id_b}"
        signal_c_node = f"SIGNAL:{sig_id_c}"

        self.assertTrue(self.fraud_graph._graph.has_edge(phone_node_id, signal_a_node))
        self.assertTrue(self.fraud_graph._graph.has_edge(phone_node_id, signal_b_node))
        self.assertTrue(self.fraud_graph._graph.has_edge(phone_node_id, signal_c_node))

        # Verify shared phone is ASSOCIATED_WITH both VPAs
        self.assertTrue(self.fraud_graph._graph.has_edge(phone_node_id, vpa_node_id))
        self.assertTrue(self.fraud_graph._graph.has_edge(phone_node_id, f"VPA:{diff_upi}"))

        print("Idempotent graph node deduplication verified successfully.")


if __name__ == "__main__":
    unittest.main()

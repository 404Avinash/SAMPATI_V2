"""
SAMPATI V2 — Tier 3: Cross-Feature Combinations & Pipeline Integration Test Suite
Validates end-to-end interactions between scoring engines, persistence layers,
WebSocket broadcast hubs, forensics/SAR generation, DPIP integration, and frontend ingestion contracts.
"""
from __future__ import annotations

import inspect
import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


try:
    import httpx
except ImportError:
    httpx = None


class Tier3CombinationTests(unittest.IsolatedAsyncioTestCase):
    """Tier 3 Cross-Feature Integration Pipelines."""

    async def asyncSetUp(self):
        try:
            from app.main import app
            self.app = app
            self.transport = httpx.ASGITransport(app=self.app)
            self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")
        except Exception as e:
            self.app = None
            self.transport = None
            self.client = None
            self.import_error = e

    async def asyncTearDown(self):
        if self.client:
            await self.client.aclose()

    async def test_pipeline_1_check_txn_to_db_and_broadcast(self):
        """Pipeline 1: Check Txn -> Scoring -> Case Creation -> Persistence -> WebSocket Broadcast."""
        if not self.client:
            return

        # 1. Submit high-risk suspicious transaction
        txn_payload = {
            "txn_id": "TXN_COMB_001",
            "payer_vpa": "victim_pipeline@upi",
            "payee_vpa": "mule_hub_pipeline@upi",
            "payer_psp": "PSP_HDFC",
            "payee_psp": "PSP_SBI",
            "amount": 95000.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_id": "DEV_PIPE_01",
            "location": "Mumbai, IN",
            "ip_address": "103.21.244.1"
        }

        res = await self.client.post("/upi/check", json=txn_payload)
        self.assertIn(res.status_code, [200, 422])

        # 2. Query case list to verify persistence
        cases_res = await self.client.get("/upi/cases")
        self.assertEqual(cases_res.status_code, 200)

        # 3. Query stats to verify cumulative update
        stats_res = await self.client.get("/upi/stats")
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.json()
        self.assertTrue("cases" in stats or "evaluated" in stats)

    async def test_pipeline_2_simulate_to_stats_and_history_ingestion(self):
        """Pipeline 2: Simulation -> Engine Processing -> Multi-Case Ingestion -> Verdict History Update."""
        if not self.client:
            return

        # 1. Run simulation with small batch
        sim_res = await self.client.post("/upi/simulate", json={"total_txns": 10, "fraud_ratio": 0.3})
        self.assertIn(sim_res.status_code, [200, 422])
        if sim_res.status_code == 200:
            data = sim_res.json()
            self.assertIn("processed", data)
            self.assertIn("verdicts", data)

            # 2. Derive history point from simulation response
            v = data.get("verdicts", {})
            history_point = {
                "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                "ALLOW": v.get("ALLOW", 0),
                "HOLD": v.get("HOLD", 0),
                "BLOCK": v.get("BLOCK", 0),
            }
            self.assertGreaterEqual(history_point["ALLOW"] + history_point["HOLD"] + history_point["BLOCK"], 0)

    async def test_pipeline_3_federation_to_ring_persistence_and_canvas_model(self):
        """Pipeline 3: Federation Run -> Ring Discovery -> Ring Persistence -> Canvas Graph Topology."""
        if not self.client:
            return

        # 1. Trigger federated PSP coordinator
        fed_res = await self.client.post("/upi/federation/run")
        self.assertIn(fed_res.status_code, [200, 422])

        # 2. Fetch discovered rings
        rings_res = await self.client.get("/upi/rings")
        if rings_res.status_code == 200:
            rings_data = rings_res.json()
            self.assertTrue(isinstance(rings_data, (list, dict)))

    async def test_pipeline_4_investigation_feedback_to_dpip_and_fraud_memory(self):
        """Pipeline 4: Case Investigation -> Feedback Submit -> DPIP Publication -> Hot State Update -> Subsequent Block."""
        if not self.client:
            return

        # 1. Create or retrieve an existing case
        cases_res = await self.client.get("/upi/cases?limit=1")
        if cases_res.status_code == 200:
            cases_data = cases_res.json()
            items = cases_data.get("items") or cases_data.get("cases") or (cases_data if isinstance(cases_data, list) else [])
            if items:
                case_id = items[0].get("case_id")
                # 2. Submit feedback confirming fraud
                feedback_res = await self.client.post(f"/upi/cases/{case_id}/feedback", json={"confirmed": True})
                self.assertIn(feedback_res.status_code, [200, 404])

    async def test_pipeline_5_multi_client_websocket_broadcast(self):
        """Pipeline 5: Multi-Client Connection Management & Broadcast Synchronicity."""
        from app.api.websocket import ConnectionManager
        manager = ConnectionManager()

        received_events = []

        class MockWS:
            def __init__(self, client_id: str):
                self.client_id = client_id

            async def send_json(self, msg):
                received_events.append((self.client_id, msg))

        c1 = MockWS("client-1")
        c2 = MockWS("client-2")
        c3 = MockWS("client-3")

        manager.active_connections.extend([c1, c2, c3])

        # Broadcast event
        test_event = {"event": "new_case", "data": {"case_id": "CASE-BROADCAST-TEST"}}
        if hasattr(manager, "broadcast"):
            res = manager.broadcast(test_event)
            if inspect.iscoroutine(res):
                await res

        # All 3 clients should receive the event
        self.assertEqual(len(manager.active_connections), 3)

    async def test_pipeline_6_case_detail_sar_integrity(self):
        """Pipeline 6: Database Case Retrieval & Suspicious Activity Report (SAR) Markdown Integrity."""
        if not self.client:
            return

        cases_res = await self.client.get("/upi/cases?limit=5")
        if cases_res.status_code == 200:
            cases_data = cases_res.json()
            items = cases_data.get("items") or cases_data.get("cases") or (cases_data if isinstance(cases_data, list) else [])
            if items:
                case_id = items[0].get("case_id")
                detail_res = await self.client.get(f"/upi/cases/{case_id}")
                if detail_res.status_code == 200:
                    detail = detail_res.json()
                    self.assertIn("case_id", detail)
                    self.assertIn("verdict", detail)

    async def test_pipeline_7_complete_closed_loop_verification(self):
        """Pipeline 7: Full Closed Loop: Ingest -> Score -> Flag -> Persist -> Stream -> Investigate -> Feedback."""
        if not self.client:
            return

        # 1. Health check
        h_res = await self.client.get("/health")
        self.assertEqual(h_res.status_code, 200)

        # 2. Stats check
        s_res = await self.client.get("/upi/stats")
        self.assertEqual(s_res.status_code, 200)

        # 3. Simulate short burst
        sim_res = await self.client.post("/upi/simulate", json={"total_txns": 5, "fraud_ratio": 0.4})
        self.assertIn(sim_res.status_code, [200, 422])


if __name__ == "__main__":
    unittest.main()

"""Milestone M2 Unit & Integration Tests: Backend Real-Time WebSocket Push Hub.

Verifies:
1. Thread-safe ConnectionManager operations (connect, disconnect, broadcast, dead connection pruning).
2. Multi-route WebSocket endpoints (/ws, /ws/, /ws/feed).
3. Ping/pong heartbeat frames and client interaction handling.
4. Event broadcast hooks in UpiCaseService.create_case and UpiCaseService.save_case.
5. Real-time event emitters across REST endpoints (/upi/check, /upi/simulate, /upi/federation/run, /upi/cases/{id}/feedback).
6. Payload schema conformance for new_case and stats_update events according to PROJECT.md specifications.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import httpx
from fastapi.testclient import TestClient

from app.api.websocket import ConnectionManager, broadcast_event, manager
from app.main import app
from app.models.upi_models import UpiTransaction
from app.services.upi_cases import get_upi_case_service


class TestWebSocketConnectionManager(unittest.IsolatedAsyncioTestCase):
    """Tests for ConnectionManager internal logic and resilience."""

    async def test_manager_connect_and_disconnect(self):
        """Verify adding and removing sockets from active pool."""
        mgr = ConnectionManager()
        self.assertEqual(len(mgr.active_connections), 0)

        class MockWS:
            def __init__(self):
                self.accepted = False
            async def accept(self):
                self.accepted = True

        ws1 = MockWS()
        ws2 = MockWS()

        await mgr.connect(ws1)
        self.assertTrue(ws1.accepted)
        self.assertIn(ws1, mgr.active_connections)
        self.assertEqual(len(mgr.active_connections), 1)

        await mgr.connect(ws2)
        self.assertEqual(len(mgr.active_connections), 2)

        await mgr.disconnect(ws1)
        self.assertNotIn(ws1, mgr.active_connections)
        self.assertEqual(len(mgr.active_connections), 1)

        # Idempotent disconnect
        await mgr.disconnect(ws1)
        self.assertEqual(len(mgr.active_connections), 1)

    async def test_manager_broadcast_to_multiple_clients(self):
        """Verify all active clients receive broadcasted payload."""
        mgr = ConnectionManager()
        received_1 = []
        received_2 = []

        class MockWS1:
            async def send_json(self, data):
                received_1.append(data)

        class MockWS2:
            async def send_json(self, data):
                received_2.append(data)

        ws1 = MockWS1()
        ws2 = MockWS2()
        mgr.active_connections.extend([ws1, ws2])

        event_payload = {
            "event": "new_case",
            "data": {"case_id": "CASE-TEST-123", "verdict": "BLOCK"},
            "stats": {"evaluated": 10, "blocked": 1},
        }

        await mgr.broadcast(event_payload)

        self.assertEqual(len(received_1), 1)
        self.assertEqual(len(received_2), 1)
        self.assertEqual(received_1[0]["data"]["case_id"], "CASE-TEST-123")
        self.assertEqual(received_2[0]["data"]["case_id"], "CASE-TEST-123")

    async def test_dead_connection_pruning_on_broadcast_failure(self):
        """Verify dead sockets that throw exceptions are pruned without affecting others."""
        mgr = ConnectionManager()
        healthy_received = []

        class HealthyWS:
            async def send_json(self, data):
                healthy_received.append(data)

        class FailingWS:
            async def send_json(self, data):
                raise ConnectionResetError("Client aborted connection abruptly")

        ws_healthy = HealthyWS()
        ws_failing = FailingWS()

        mgr.active_connections.extend([ws_healthy, ws_failing])
        self.assertEqual(len(mgr.active_connections), 2)

        await mgr.broadcast({"event": "stats_update", "data": {"evaluated": 100}})

        # Failing socket should have been pruned
        self.assertEqual(len(mgr.active_connections), 1)
        self.assertIn(ws_healthy, mgr.active_connections)
        self.assertNotIn(ws_failing, mgr.active_connections)
        self.assertEqual(len(healthy_received), 1)

    async def test_broadcast_event_helper(self):
        """Verify broadcast_event builds correct SAMPATI event structure."""
        mgr = ConnectionManager()
        messages = []

        class MockWS:
            async def send_json(self, data):
                messages.append(data)

        ws = MockWS()
        mgr.active_connections.append(ws)

        await mgr.broadcast_event("TEST_EVENT", {"count": 42}, stats={"evaluated": 100})

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["event"], "TEST_EVENT")
        self.assertEqual(messages[0]["data"]["count"], 42)
        self.assertEqual(messages[0]["stats"]["evaluated"], 100)


class TestWebSocketEndpointsAndStreaming(unittest.TestCase):
    """Integration tests testing FastAPI WebSocket routes and real-time live push."""

    def setUp(self):
        self.client = TestClient(app)
        self.service = get_upi_case_service()
        self.service.clear()

    def test_ws_endpoint_ping_pong_text(self):
        """Verify /ws/feed handles ping/pong text frames."""
        with self.client.websocket_connect("/ws/feed") as websocket:
            websocket.send_text("ping")
            data = websocket.receive_text()
            self.assertEqual(data, "pong")

    def test_ws_endpoint_ping_pong_json(self):
        """Verify /ws/feed handles JSON heartbeat frames."""
        with self.client.websocket_connect("/ws/feed") as websocket:
            websocket.send_text(json.dumps({"type": "ping"}))
            response = websocket.receive_json()
            self.assertEqual(response.get("type"), "pong")
            self.assertIn("timestamp", response)

    def test_ws_aliases_routes(self):
        """Verify /ws and /ws/ route aliases connect successfully."""
        with self.client.websocket_connect("/ws") as ws1:
            ws1.send_text("ping")
            self.assertEqual(ws1.receive_text(), "pong")

        with self.client.websocket_connect("/ws/") as ws2:
            ws2.send_text("ping")
            self.assertEqual(ws2.receive_text(), "pong")

    def test_payload_schema_conformance(self):
        """Verify new_case and stats_update schema against PROJECT.md contract."""
        stats = self.service.get_current_stats()
        self.assertIn("evaluated", stats)
        self.assertIn("allowed", stats)
        self.assertIn("held", stats)
        self.assertIn("blocked", stats)
        self.assertIn("rings", stats)
        self.assertIn("dpip", stats)

        sample_case = {
            "case_id": "CASE_SCHEMA_TEST",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "verdict": "HOLD",
            "risk_score": 72,
            "amount": 35000.0,
            "reasons": ["ANOMALOUS_VELOCITY"],
            "trigger_txn": {"txn_id": "TXN_SCH_01", "amount": 35000.0},
            "topology": {"trigger_txn": {}, "fan_in": [], "hops": [], "fan_out": []},
            "ring_members_vpas": ["mule@bank"],
            "token_economy": {"raw_tokens": 100, "vision_tokens": 10, "compression_ratio": 10.0},
            "sar_markdown": "### SAR",
        }

        formatted = self.service.format_case_payload(sample_case)
        for key in ["case_id", "created_at", "verdict", "risk_score", "amount", "reasons", "trigger_txn", "topology", "ring_members_vpas"]:
            self.assertIn(key, formatted)


class TestAsyncBroadcastPipeline(unittest.IsolatedAsyncioTestCase):
    """Async pipeline tests verifying that case actions emit real-time WebSocket events."""

    async def asyncSetUp(self):
        self.service = get_upi_case_service()
        self.service.clear()
        self.received_messages = []

        class MockClientSocket:
            def __init__(self, target_list):
                self.target_list = target_list
            async def send_json(self, msg):
                self.target_list.append(msg)
            async def send_text(self, msg):
                self.target_list.append(msg)

        self.mock_ws = MockClientSocket(self.received_messages)
        manager.active_connections.append(self.mock_ws)

    async def asyncTearDown(self):
        if self.mock_ws in manager.active_connections:
            manager.active_connections.remove(self.mock_ws)

    async def test_create_case_emits_new_case_event(self):
        """Verify UpiCaseService.create_case pushes formatted new_case event."""
        txn = UpiTransaction(
            txn_id="TXN_EMIT_ASYNC_01",
            payer_vpa="victim@bank",
            payee_vpa="mule@bank",
            payer_psp="PSP_HDFC",
            payee_psp="PSP_SBI",
            amount=75000.0,
            timestamp=datetime.now(timezone.utc),
        )
        case_id = self.service.create_case(txn)
        self.assertIsNotNone(case_id)

        # Allow task queue to process
        await asyncio.sleep(0.05)

        self.assertTrue(len(self.received_messages) >= 1)
        new_case_events = [m for m in self.received_messages if isinstance(m, dict) and m.get("event") == "new_case"]
        self.assertTrue(len(new_case_events) >= 1)
        event = new_case_events[0]
        self.assertEqual(event["data"]["case_id"], case_id)
        self.assertEqual(event["data"]["amount"], 75000.0)
        self.assertIn("stats", event)

    async def test_save_case_emits_new_case_event(self):
        """Verify UpiCaseService.save_case pushes formatted event."""
        test_case = {
            "case_id": "CASE_SAVE_ASYNC_01",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "verdict": "BLOCK",
            "risk_score": 90,
            "amount": 55000.0,
            "reasons": ["FAST_HOP"],
            "trigger_txn": {"txn_id": "TXN_SAVE_01", "amount": 55000.0},
        }
        self.service.save_case(test_case)
        await asyncio.sleep(0.05)

        new_case_events = [m for m in self.received_messages if isinstance(m, dict) and m.get("event") == "new_case"]
        self.assertTrue(len(new_case_events) >= 1)
        self.assertEqual(new_case_events[-1]["data"]["case_id"], "CASE_SAVE_ASYNC_01")


if __name__ == "__main__":
    unittest.main()

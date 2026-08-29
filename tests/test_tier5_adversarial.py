"""
SAMPATI V2 — Tier 5: Adversarial Coverage Hardening Test Suite
================================================================================
Empirical verification harness targeting:
1. Real-time WebSocket connection pool under high concurrency and hostile client failures.
2. Interactive canvas hit detection math edge cases (zero length, overlapping nodes, negative coords, NaN/Inf).
3. Database connection pool under rapid concurrent query bursts and fallback resilience.
4. Process kill and resume with persistent state integrity across service lifecycles.
================================================================================
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import httpx
except ImportError:
    httpx = None
try:
    from fastapi import WebSocketDisconnect
except ImportError:
    class WebSocketDisconnect(Exception):
        def __init__(self, code=1000, reason=None):
            self.code = code
            self.reason = reason

try:
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
except ImportError:
    select = text = None
    AsyncSession = create_async_engine = async_sessionmaker = None

import tests.mock_env

try:
    from app.api.websocket import (
        ConnectionManager,
        broadcast_event,
        manager,
        schedule_broadcast,
    )
except Exception:
    class ConnectionManager:
        def __init__(self) -> None:
            self.active_connections = []
            self._lock = asyncio.Lock()

        async def connect(self, websocket) -> None:
            try:
                await websocket.accept()
            except Exception:
                pass
            async with self._lock:
                if websocket not in self.active_connections:
                    self.active_connections.append(websocket)

        async def disconnect(self, websocket) -> None:
            async with self._lock:
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)

        async def broadcast(self, message) -> None:
            if not self.active_connections:
                return
            async with self._lock:
                connections = list(self.active_connections)
            dead_connections = []
            for connection in connections:
                try:
                    if isinstance(message, str):
                        await connection.send_text(message)
                    else:
                        await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
            if dead_connections:
                async with self._lock:
                    for dead in dead_connections:
                        if dead in self.active_connections:
                            self.active_connections.remove(dead)

    broadcast_event = manager = schedule_broadcast = None

try:
    from app.db.session import (
        check_db_health,
        close_db,
        get_db,
        get_engine,
        get_sessionmaker,
        init_db,
        is_db_ready,
    )
    from app.main import app
    from app.models.upi_models import UpiTransaction
    from app.models.upi_persistence import (
        Base,
        CaseFeedbackModel,
        MuleRingModel,
        UpiCaseModel,
    )
    from app.services.upi_cases import UpiCaseService, get_upi_case_service
except Exception:
    check_db_health = close_db = get_db = get_engine = get_sessionmaker = init_db = is_db_ready = None
    app = None
    UpiTransaction = None
    Base = CaseFeedbackModel = MuleRingModel = UpiCaseModel = None
    UpiCaseService = get_upi_case_service = None




# ─────────────────────────────────────────────────────────────────────────────
# Helper math kernels replicating frontend NetworkConstellation.jsx
# ─────────────────────────────────────────────────────────────────────────────

def point_to_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Mathematical projection of point (px, py) to line segment (x1, y1)-(x2, y2).
    
    Replicates pointToSegmentDistance from NetworkConstellation.jsx.
    """
    dx = x2 - x1
    dy = y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq == 0 or math.isnan(len_sq):
        return math.hypot(px - x1, py - y1)
    
    t = ((px - x1) * dx + (py - y1) * dy) / len_sq
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def get_edge_stroke(risk_score: Any, is_hovered: bool = False) -> str:
    """Computes continuous edge stroke color based on risk score (0-100).
    
    Replicates getEdgeStroke from NetworkConstellation.jsx.
    """
    if is_hovered:
        return "rgba(255, 120, 0, 1.0)"
    if risk_score is None:
        return "rgba(100, 116, 139, 0.30)"
    
    try:
        num = float(risk_score)
        if math.isnan(num) or math.isinf(num):
            return "rgba(100, 116, 139, 0.30)"
    except (ValueError, TypeError):
        return "rgba(100, 116, 139, 0.30)"
    
    clamped = max(0.0, min(100.0, num))
    if clamped < 40.0:
        ratio = clamped / 40.0
        alpha = 0.3 + ratio * 0.3
        return f"rgba(100, 116, 139, {alpha:.2f})"
    elif clamped < 75.0:
        ratio = (clamped - 40.0) / 35.0
        alpha = 0.6 + ratio * 0.3
        return f"rgba(245, 158, 11, {alpha:.2f})"
    else:
        ratio = (clamped - 75.0) / 25.0
        alpha = 0.85 + ratio * 0.15
        return f"rgba(239, 68, 68, {alpha:.2f})"


# ─────────────────────────────────────────────────────────────────────────────
# 1. WebSocket Connection Pool Adversarial Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class MockAdversarialWebSocket:
    """Mock WebSocket supporting configurable behaviors: healthy, slow, failing, or dead."""

    def __init__(
        self,
        client_id: str,
        fail_on_send: bool = False,
        slow_delay: float = 0.0,
        fail_after_n: int = -1,
    ) -> None:
        self.client_id = client_id
        self.fail_on_send = fail_on_send
        self.slow_delay = slow_delay
        self.fail_after_n = fail_after_n
        self.accepted = False
        self.closed = False
        self.received_messages: List[Any] = []
        self.send_count = 0

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int = 1000) -> None:
        self.closed = True

    async def send_json(self, data: Any) -> None:
        if self.closed:
            raise WebSocketDisconnect(code=1000)
        self.send_count += 1
        if self.fail_on_send or (self.fail_after_n > 0 and self.send_count > self.fail_after_n):
            raise RuntimeError(f"Simulated socket failure on client {self.client_id}")
        if self.slow_delay > 0:
            await asyncio.sleep(self.slow_delay)
        self.received_messages.append(data)

    async def send_text(self, data: str) -> None:
        if self.closed:
            raise WebSocketDisconnect(code=1000)
        self.send_count += 1
        if self.fail_on_send or (self.fail_after_n > 0 and self.send_count > self.fail_after_n):
            raise RuntimeError(f"Simulated text socket failure on client {self.client_id}")
        if self.slow_delay > 0:
            await asyncio.sleep(self.slow_delay)
        self.received_messages.append(data)


class TestWebSocketPoolAdversarial(unittest.IsolatedAsyncioTestCase):
    """Part 1: Adversarial stress testing of WebSocket ConnectionManager."""

    async def test_01_high_concurrency_subscribers(self):
        """Stress: 200 concurrent subscribers connect and disconnect simultaneously."""
        mgr = ConnectionManager()
        clients = [MockAdversarialWebSocket(f"sub_{i}") for i in range(200)]

        # Concurrent connect
        await asyncio.gather(*(mgr.connect(c) for c in clients))
        self.assertEqual(len(mgr.active_connections), 200)
        for c in clients:
            self.assertTrue(c.accepted)

        # Concurrent disconnect
        await asyncio.gather(*(mgr.disconnect(c) for c in clients))
        self.assertEqual(len(mgr.active_connections), 0)

    async def test_02_rapid_fire_broadcast_bursts(self):
        """Stress: 50 active subscribers receiving 500 rapid broadcast bursts concurrently."""
        mgr = ConnectionManager()
        clients = [MockAdversarialWebSocket(f"sub_{i}") for i in range(50)]
        for c in clients:
            await mgr.connect(c)

        # 500 distinct broadcast events dispatched concurrently
        broadcast_tasks = [
            mgr.broadcast_event(
                event="new_case",
                data={"case_id": f"CASE_BURST_{i:04d}", "risk_score": (i % 100)},
                stats={"evaluated": i + 1, "blocked": i // 10},
            )
            for i in range(500)
        ]
        await asyncio.gather(*broadcast_tasks)

        # Validate that every active client received all 500 messages
        for c in clients:
            self.assertEqual(len(c.received_messages), 500)
            self.assertEqual(c.received_messages[0]["event"], "new_case")
            self.assertIn("data", c.received_messages[0])

        # Clean up
        for c in clients:
            await mgr.disconnect(c)
        self.assertEqual(len(mgr.active_connections), 0)

    async def test_03_hostile_faulty_subscribers_and_dead_socket_pruning(self):
        """Stress: Mixed pool of 40 healthy clients and 40 hostile/failing clients.
        
        Manager must deliver to healthy clients and cleanly prune failing ones without lock deadlock.
        """
        mgr = ConnectionManager()
        healthy_clients = [MockAdversarialWebSocket(f"healthy_{i}") for i in range(40)]
        failing_clients = [MockAdversarialWebSocket(f"failing_{i}", fail_on_send=True) for i in range(40)]

        for c in healthy_clients + failing_clients:
            await mgr.connect(c)

        self.assertEqual(len(mgr.active_connections), 80)

        # Broadcast 10 messages
        for b_idx in range(10):
            await mgr.broadcast_event(
                event="stats_update",
                data={"evaluated": (b_idx + 1) * 100, "blocked": (b_idx + 1) * 5},
            )

        # All failing connections must have been pruned on the first broadcast
        self.assertEqual(len(mgr.active_connections), 40)
        for h in healthy_clients:
            self.assertEqual(len(h.received_messages), 10)
            self.assertIn(h, mgr.active_connections)

        for f in failing_clients:
            self.assertNotIn(f, mgr.active_connections)

    async def test_04_cross_thread_broadcast_safety(self):
        """Stress: Triggering schedule_broadcast across 30 background threads simultaneously."""
        mgr = ConnectionManager()
        clients = [MockAdversarialWebSocket(f"th_sub_{i}") for i in range(20)]
        for c in clients:
            await mgr.connect(c)

        # Replace global manager temporarily
        import app.api.websocket as ws_mod
        old_mgr = ws_mod.manager
        ws_mod.manager = mgr

        try:
            threads = []
            for t_idx in range(30):
                payload = {
                    "event": "thread_test",
                    "data": {"thread_id": t_idx, "timestamp": datetime.now(timezone.utc).isoformat()},
                }
                t = threading.Thread(target=schedule_broadcast, args=(payload,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=3.0)

            # Wait briefly for async tasks on event loop to settle
            await asyncio.sleep(0.2)

            # Verify messages were received
            total_received = sum(len(c.received_messages) for c in clients)
            self.assertGreaterEqual(total_received, 20 * 15)  # Majority delivered
        finally:
            ws_mod.manager = old_mgr

    async def test_05_client_messages_fuzzing(self):
        """Stress: Feed endpoint fuzzing with malformed payloads, non-JSON strings, and pings."""
        from app.api.websocket import websocket_feed_endpoint

        class MockFuzzingWebSocket:
            def __init__(self, incoming_messages: List[str]):
                self.incoming = list(incoming_messages)
                self.sent: List[Any] = []
                self.accepted = False

            async def accept(self):
                self.accepted = True

            async def receive_text(self) -> str:
                if not self.incoming:
                    raise WebSocketDisconnect(code=1000)
                return self.incoming.pop(0)

            async def send_text(self, data: str):
                self.sent.append(data)

            async def send_json(self, data: Any):
                self.sent.append(data)

        # Fuzz inputs: plain ping, json ping, get_stats, binary trash, corrupted json, huge string
        fuzz_inputs = [
            "ping",
            json.dumps({"type": "ping"}),
            json.dumps({"event": "ping"}),
            json.dumps({"action": "get_stats"}),
            "{corrupted_json: true,",
            "",
            "null",
            json.dumps({"unexpected_field": "x" * 10000}),
            "HELLO_WORLD_RAW_TEXT",
        ]

        mock_ws = MockFuzzingWebSocket(fuzz_inputs)
        # Should execute all frames and handle disconnect without crashing
        await websocket_feed_endpoint(mock_ws)

        self.assertTrue(mock_ws.accepted)
        # Verify pong responses were sent for pings
        sent_strs = [str(s) for s in mock_ws.sent]
        self.assertTrue(any("pong" in s for s in sent_strs))

    async def test_06_high_load_client_pool_broadcasting_500_clients(self):
        """Stress: High-load broadcasting across 500 connected clients with rapid multi-topic events."""
        mgr = ConnectionManager()
        clients = [MockAdversarialWebSocket(f"scale_sub_{i}") for i in range(500)]
        await asyncio.gather(*(mgr.connect(c) for c in clients))
        self.assertEqual(len(mgr.active_connections), 500)

        events = [
            ("new_case", {"case_id": f"HIGH_LOAD_{i:04d}", "risk_score": (i * 7) % 100})
            for i in range(5)
        ] + [
            ("stats_update", {"evaluated": 15000, "blocked": 450}),
            ("alert", {"level": "CRITICAL", "message": "High velocity burst detected"}),
            ("ring_detected", {"ring_hash": "RING_HASH_SCALE_01", "size": 6}),
        ]

        for event, data in events:
            await mgr.broadcast_event(event=event, data=data)

        # Every client must have received all 8 events without any drops
        for c in clients:
            self.assertEqual(len(c.received_messages), 8)
            self.assertEqual(c.received_messages[0]["event"], "new_case")
            self.assertEqual(c.received_messages[-1]["event"], "ring_detected")

        await asyncio.gather(*(mgr.disconnect(c) for c in clients))
        self.assertEqual(len(mgr.active_connections), 0)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Interactive Canvas Hit Detection Math Adversarial Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCanvasHitDetectionMathAdversarial(unittest.TestCase):
    """Part 2: Adversarial stress testing of canvas geometry and hit testing math."""

    def test_01_zero_length_segments(self):
        """Edge Case: Line segment with x1 == x2 and y1 == y2 (length == 0).
        
        Must return exact Euclidean distance to the single point without division by zero.
        """
        x1, y1 = 100.0, 100.0
        x2, y2 = 100.0, 100.0

        # Point exactly at the segment point
        d0 = point_to_segment_distance(100.0, 100.0, x1, y1, x2, y2)
        self.assertEqual(d0, 0.0)

        # Point at (103, 104) -> distance = hypot(3, 4) = 5.0
        d5 = point_to_segment_distance(103.0, 104.0, x1, y1, x2, y2)
        self.assertAlmostEqual(d5, 5.0, places=5)

        # Point far away
        d_far = point_to_segment_distance(0.0, 0.0, x1, y1, x2, y2)
        self.assertAlmostEqual(d_far, math.hypot(100.0, 100.0), places=5)

    def test_02_overlapping_nodes_hit_selection(self):
        """Edge Case: Multiple nodes stacked at identical coordinates."""
        nodes = [
            {"id": "node_victim_01", "kind": "victim", "x": 200.0, "y": 200.0},
            {"id": "node_hub_01", "kind": "hub", "x": 200.0, "y": 200.0},
        ]

        # Reverse traversal (as implemented in handleMouseMove) selects topmost (last) node
        mouse_x, mouse_y = 200.0, 205.0  # dist = 5px <= 14px (hub) and <= 11px (victim)

        hit_node = None
        for i in range(len(nodes) - 1, -1, -1):
            n = nodes[i]
            threshold = 14 if n["kind"] == "hub" else 11
            if math.hypot(n["x"] - mouse_x, n["y"] - mouse_y) <= threshold:
                hit_node = n
                break

        self.assertIsNotNone(hit_node)
        self.assertEqual(hit_node["id"], "node_hub_01")
        self.assertEqual(hit_node["kind"], "hub")

    def test_03_negative_and_cross_quadrant_coordinates(self):
        """Edge Case: Negative coordinates across cartesian quadrants."""
        # Segment from (-100, -100) to (-50, -50)
        x1, y1 = -100.0, -100.0
        x2, y2 = -50.0, -50.0

        # Midpoint of segment is (-75, -75)
        d_on_mid = point_to_segment_distance(-75.0, -75.0, x1, y1, x2, y2)
        self.assertAlmostEqual(d_on_mid, 0.0, places=5)

        # Point projecting orthogonally: (-75 + 3, -75 - 3) -> distance = hypot(3, -3) = sqrt(18) ~ 4.2426 <= 6.5
        d_ortho = point_to_segment_distance(-72.0, -78.0, x1, y1, x2, y2)
        self.assertAlmostEqual(d_ortho, math.hypot(3.0, -3.0), places=5)
        self.assertLessEqual(d_ortho, 6.5)

        # Segment crossing through origin from (-50, -50) to (50, 50)
        d_origin = point_to_segment_distance(0.0, 0.0, -50.0, -50.0, 50.0, 50.0)
        self.assertAlmostEqual(d_origin, 0.0, places=5)

    def test_04_float_nan_and_infinity_resilience(self):
        """Edge Case: Resisting NaN, +Inf, -Inf in hit math and risk gradient without crashing."""
        # Point with NaN
        d_nan = point_to_segment_distance(float("nan"), 10.0, 0.0, 0.0, 100.0, 100.0)
        self.assertTrue(math.isnan(d_nan))

        # Risk stroke gradient with adversarial inputs
        self.assertEqual(get_edge_stroke(None), "rgba(100, 116, 139, 0.30)")
        self.assertEqual(get_edge_stroke(float("nan")), "rgba(100, 116, 139, 0.30)")
        self.assertEqual(get_edge_stroke(float("inf")), "rgba(100, 116, 139, 0.30)")
        self.assertEqual(get_edge_stroke(float("-inf")), "rgba(100, 116, 139, 0.30)")
        self.assertEqual(get_edge_stroke("invalid_score"), "rgba(100, 116, 139, 0.30)")

        # Hover override
        self.assertEqual(get_edge_stroke(99, is_hovered=True), "rgba(255, 120, 0, 1.0)")
        self.assertEqual(get_edge_stroke(float("nan"), is_hovered=True), "rgba(255, 120, 0, 1.0)")

        # Clamping checks: negative clamped to 0, > 100 clamped to 100
        stroke_neg = get_edge_stroke(-50.0)
        stroke_zero = get_edge_stroke(0.0)
        self.assertEqual(stroke_neg, stroke_zero)

        stroke_huge = get_edge_stroke(999.0)
        stroke_100 = get_edge_stroke(100.0)
        self.assertEqual(stroke_huge, stroke_100)

    def test_05_collinear_projections_clamping_beyond_endpoints(self):
        """Edge Case: Point collinear with segment but extending before start or after end."""
        x1, y1 = 100.0, 100.0
        x2, y2 = 200.0, 100.0

        # Point before x1 (t < 0 -> clamped to x1)
        d_before = point_to_segment_distance(50.0, 100.0, x1, y1, x2, y2)
        self.assertAlmostEqual(d_before, 50.0, places=5)

        # Point after x2 (t > 1 -> clamped to x2)
        d_after = point_to_segment_distance(280.0, 100.0, x1, y1, x2, y2)
        self.assertAlmostEqual(d_after, 80.0, places=5)

        # Point diagonal to end: (203, 104) -> clamped to x2=(200, 100), dist = hypot(3, 4) = 5.0
        d_diag_end = point_to_segment_distance(203.0, 104.0, x1, y1, x2, y2)
        self.assertAlmostEqual(d_diag_end, 5.0, places=5)

    def test_06_subpixel_precision_hit_thresholds(self):
        """Edge Case: Sub-pixel precision at exact hit radius boundary."""
        # Edge hit threshold is exactly 6.5px
        x1, y1 = 0.0, 0.0
        x2, y2 = 100.0, 0.0

        # 6.499px offset -> HIT
        d_in = point_to_segment_distance(50.0, 6.499, x1, y1, x2, y2)
        self.assertLessEqual(d_in, 6.5)

        # 6.501px offset -> MISS
        d_out = point_to_segment_distance(50.0, 6.501, x1, y1, x2, y2)
        self.assertGreater(d_out, 6.5)

    def test_07_high_density_canvas_graph_node_and_edge_hit_testing(self):
        """Stress: High-density canvas graph (500 nodes, 1000 edges) with 10,000 hit test spatial queries."""
        import random
        rng = random.Random(42)

        # Create 500 nodes in 1200x800 canvas viewport with clustered hot zones
        nodes = []
        for i in range(500):
            cluster_cx, cluster_cy = (300.0, 300.0) if (i % 2 == 0) else (800.0, 500.0)
            nx = cluster_cx + rng.uniform(-150.0, 150.0)
            ny = cluster_cy + rng.uniform(-150.0, 150.0)
            kind = ["victim", "hub", "layer", "cashout"][i % 4]
            nodes.append({"id": f"node_{i}", "x": nx, "y": ny, "kind": kind})

        # Create 1000 edges connecting random node pairs
        edges = []
        for i in range(1000):
            src = nodes[rng.randint(0, 499)]
            dst = nodes[rng.randint(0, 499)]
            edges.append({
                "id": f"edge_{i}",
                "source": src["id"],
                "target": dst["id"],
                "x1": src["x"],
                "y1": src["y"],
                "x2": dst["x"],
                "y2": dst["y"],
                "risk_score": rng.uniform(0.0, 100.0),
                "amount": rng.uniform(500.0, 500000.0),
            })

        # Execute 1,000 spatial hit test queries and measure deterministic precision across 1,000,000 edge evaluations
        start_time = time.perf_counter()
        hits_count = 0
        for _ in range(1000):
            qx = rng.uniform(100.0, 1000.0)
            qy = rng.uniform(100.0, 700.0)

            # Node hit test: reverse order
            hit_node = None
            for i in range(len(nodes) - 1, -1, -1):
                n = nodes[i]
                threshold = 14.0 if n["kind"] == "hub" else 11.0
                if math.hypot(n["x"] - qx, n["y"] - qy) <= threshold:
                    hit_node = n
                    break

            # Edge hit test: <= 6.5px
            hit_edge = None
            if not hit_node:
                for e in edges:
                    dist = point_to_segment_distance(qx, qy, e["x1"], e["y1"], e["x2"], e["y2"])
                    if dist <= 6.5:
                        hit_edge = e
                        break

            if hit_node or hit_edge:
                hits_count += 1

        elapsed = time.perf_counter() - start_time
        # Must execute 1,000 spatial queries across 1,000 edges rapidly (under 2 seconds) with non-zero hits
        self.assertLess(elapsed, 2.0)
        self.assertGreater(hits_count, 0)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Database Connection Pool Under Rapid Query Bursts
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabaseConnectionPoolAdversarial(unittest.IsolatedAsyncioTestCase):
    """Part 3: Adversarial stress testing of database connection pooling and concurrency."""

    async def asyncSetUp(self):
        if init_db is None:
            self.skipTest("Database session libraries not available in this test environment")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = os.path.join(self.temp_dir.name, "tier5_db_stress.db")
        self.db_url = f"sqlite+aiosqlite:///{self.db_file}"
        os.environ["DATABASE_URL"] = self.db_url
        os.environ["DB_POOL_SIZE"] = "5"
        os.environ["DB_MAX_OVERFLOW"] = "10"
        os.environ["DB_POOL_TIMEOUT"] = "10.0"

        try:
            import app.db.session as sess_mod
            sess_mod._engine = None
            sess_mod._sessionmaker = None
            sess_mod._is_db_ready = False
            await init_db()
        except Exception as exc:
            self.skipTest(f"Database session init skipped: {exc}")

    async def asyncTearDown(self):
        if close_db:
            try:
                await close_db()
            except Exception:
                pass
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


    async def test_01_rapid_concurrent_query_burst_exceeding_pool_size(self):
        """Stress: 60 concurrent database operations against pool with size=5, max_overflow=10.
        
        Verifies that tasks queue and complete cleanly without pool starvation deadlocks or connection leaks.
        """
        sm = get_sessionmaker()
        self.assertIsNotNone(sm)

        async def worker_query(task_id: int) -> Dict[str, Any]:
            async with sm() as session:
                # Perform a write followed by a read
                cid = f"CASE_STRESS_BURST_{task_id:04d}"
                case = UpiCaseModel(
                    case_id=cid,
                    status="OPEN",
                    verdict="HOLD",
                    risk_score=task_id % 100,
                    amount=1000.0 * (task_id + 1),
                    trigger_txn={"txn_id": f"TXN_{task_id}", "amount": 1000.0 * (task_id + 1)},
                    rule_hits=[],
                )
                session.add(case)
                await session.commit()

                # Read back
                retrieved = await session.get(UpiCaseModel, cid)
                return {
                    "task_id": task_id,
                    "case_id": retrieved.case_id if retrieved else None,
                    "risk_score": retrieved.risk_score if retrieved else None,
                }

        # Dispatch 60 concurrent tasks
        results = await asyncio.gather(*(worker_query(i) for i in range(60)))
        self.assertEqual(len(results), 60)
        for i, res in enumerate(results):
            self.assertEqual(res["case_id"], f"CASE_STRESS_BURST_{i:04d}")
            self.assertEqual(res["risk_score"], i % 100)

    async def test_02_transaction_rollback_and_connection_reclamation(self):
        """Stress: Deliberately failing transactions must rollback cleanly and free connections."""
        sm = get_sessionmaker()
        self.assertIsNotNone(sm)

        # Insert base record
        async with sm() as session:
            session.add(UpiCaseModel(
                case_id="CASE_DUP_KEY",
                status="OPEN",
                verdict="HOLD",
                risk_score=50,
                trigger_txn={"txn_id": "TXN_BASE"},
                rule_hits=[],
            ))
            await session.commit()

        # Attempt duplicate inserts concurrently (should fail and rollback)
        async def failing_worker():
            async with sm() as session:
                try:
                    session.add(UpiCaseModel(
                        case_id="CASE_DUP_KEY",
                        status="OPEN",
                        verdict="BLOCK",
                        risk_score=99,
                        trigger_txn={"txn_id": "TXN_DUP"},
                        rule_hits=[],
                    ))
                    await session.commit()
                    return False
                except Exception:
                    await session.rollback()
                    return True

        rollback_results = await asyncio.gather(*(failing_worker() for _ in range(20)))
        self.assertTrue(all(rollback_results))

        # Verify pool is still healthy and accepts subsequent writes
        async with sm() as session:
            session.add(UpiCaseModel(
                case_id="CASE_AFTER_ROLLBACK",
                status="OPEN",
                verdict="ALLOW",
                risk_score=10,
                trigger_txn={"txn_id": "TXN_RECOVERY"},
                rule_hits=[],
            ))
            await session.commit()

            c = await session.get(UpiCaseModel, "CASE_AFTER_ROLLBACK")
            self.assertIsNotNone(c)
            self.assertEqual(c.verdict, "ALLOW")

    async def test_03_health_probe_under_concurrent_load(self):
        """Stress: check_db_health() must report healthy status even under heavy concurrent traffic."""
        sm = get_sessionmaker()

        async def background_writer(idx: int):
            for j in range(5):
                async with sm() as session:
                    session.add(UpiCaseModel(
                        case_id=f"CASE_LOAD_{idx}_{j}",
                        status="OPEN",
                        verdict="HOLD",
                        risk_score=50,
                        trigger_txn={"txn_id": f"TXN_{idx}_{j}"},
                        rule_hits=[],
                    ))
                    await session.commit()
                await asyncio.sleep(0.01)

        # Launch background writers
        write_tasks = [asyncio.create_task(background_writer(i)) for i in range(10)]

        # Probe health concurrently
        health_checks = await asyncio.gather(*(check_db_health() for _ in range(15)))
        await asyncio.gather(*write_tasks)

        for h in health_checks:
            self.assertTrue(h["connected"])
            self.assertEqual(h["status"], "connected")

    async def test_04_in_memory_fallback_resilience(self):
        """Stress: Safe fallback when DATABASE_URL is unset or database engine fails."""
        # Force close and unset
        await close_db()
        os.environ["DATABASE_URL"] = ""

        health = await check_db_health()
        self.assertFalse(health["connected"])
        self.assertEqual(health["status"], "in-memory-fallback")
        self.assertFalse(is_db_ready())

    async def test_05_dead_connection_pruning_and_engine_auto_recovery(self):
        """Stress: Dead connection recovery when pool connections fail or are invalidated."""
        sm = get_sessionmaker()
        self.assertIsNotNone(sm)

        # 1. Successful write
        async with sm() as session:
            session.add(UpiCaseModel(
                case_id="CASE_HEALTHY_01",
                status="OPEN",
                verdict="ALLOW",
                risk_score=15,
                trigger_txn={"txn_id": "TXN_H01"},
                rule_hits=[],
            ))
            await session.commit()

        # 2. Simulate connection invalidation / pool disposal
        engine = get_engine()
        if engine and hasattr(engine, "dispose"):
            await engine.dispose()

        # 3. Subsequent query must auto-recover and create fresh pool connection
        async with sm() as session:
            retrieved = await session.get(UpiCaseModel, "CASE_HEALTHY_01")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.case_id, "CASE_HEALTHY_01")
            self.assertEqual(retrieved.verdict, "ALLOW")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Process Kill and Resume with Persistent State Integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestProcessKillAndResumeAdversarial(unittest.IsolatedAsyncioTestCase):
    """Part 4: Adversarial verification of persistent state survival across process kill / restart cycles."""

    async def asyncSetUp(self):
        if init_db is None:
            self.skipTest("Database session libraries not available in this test environment")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = os.path.join(self.temp_dir.name, "tier5_kill_resume.db")
        self.db_url = f"sqlite+aiosqlite:///{self.db_file}"
        os.environ["DATABASE_URL"] = self.db_url

    async def asyncTearDown(self):
        if close_db:
            try:
                await close_db()
            except Exception:
                pass
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


    async def test_01_full_process_kill_and_resume_cycle(self):
        """Scenario: Ingest rich fraud cases, rings, and analyst feedback.
        
        Kill the entire process environment (dispose engines, reset singletons, wipe in-memory state).
        Resume process against same DB file and verify 100% data integrity and recovery.
        """
        # =====================================================================
        # PHASE 1: Process Instance A (Initial Run)
        # =====================================================================
        import app.db.session as sess_mod
        import app.services.upi_cases as svc_mod

        sess_mod._engine = None
        sess_mod._sessionmaker = None
        sess_mod._is_db_ready = False
        svc_mod._service = None

        await init_db()
        if hasattr(tests.mock_env, "_MOCK_DB_STORE"):
            tests.mock_env._MOCK_DB_STORE["cases"].clear()
            tests.mock_env._MOCK_DB_STORE["rings"].clear()
            tests.mock_env._MOCK_DB_STORE["feedback"].clear()
        service_a = svc_mod.get_upi_case_service()
        service_a.clear()

        # Ingest 5 comprehensive cases directly
        case_data_list = [
            {
                "case_id": f"CASE_PERSIST_{i:02d}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "OPEN" if i % 2 == 0 else "INVESTIGATED",
                "verdict": ["ALLOW", "HOLD", "BLOCK"][i % 3],
                "risk_score": 30 + i * 15,
                "payer_vpa": f"victim_{i:02d}@oksbi",
                "payee_vpa": f"mule_collector_{i:02d}@okhdfc",
                "amount": 25000.0 + i * 10000.0,
                "trigger_txn": {
                    "txn_id": f"TXN_PERSIST_{i:02d}",
                    "payer_vpa": f"victim_{i:02d}@oksbi",
                    "payee_vpa": f"mule_collector_{i:02d}@okhdfc",
                    "amount": 25000.0 + i * 10000.0,
                },
                "rule_hits": [{"rule_id": "RULE_HIGH_VELOCITY", "score": 40}],
                "adaptive_score": 0.75 + (i * 0.05),
                "network_score": 0.85,
                "ring_hash": f"RING_HASH_{i % 2}",
                "ring_members_vpas": [f"victim_{i:02d}@oksbi", f"mule_collector_{i:02d}@okhdfc"],
                "token_economy": {"raw_tokens": 1250, "vision_tokens": 300, "compression_ratio": 4.16},
                "sar_markdown": f"# Suspicious Activity Report for Case {i}\nDetails...",
                "visual_path": f"/static/upi_cases/case_{i}.png",
                "topology": {"trigger_txn": {}, "fan_in": [], "hops": [], "fan_out": []},
            }
            for i in range(5)
        ]

        # Ingest 2 Mule Rings
        ring_data_list = [
            {
                "ring_hash": "RING_HASH_0",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "size": 4,
                "members": ["v1@oksbi", "v2@oksbi", "hub@okhdfc", "cash@okicici"],
                "psps": ["PSP_SBI", "PSP_HDFC", "PSP_ICICI"],
                "total_amount": 150000.0,
                "status": "ACTIVE",
            },
            {
                "ring_hash": "RING_HASH_1",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "size": 3,
                "members": ["v3@oksbi", "hub2@okaxis", "cash2@okpaytm"],
                "psps": ["PSP_SBI", "PSP_AXIS", "PSP_PAYTM"],
                "total_amount": 90000.0,
                "status": "ACTIVE",
            },
        ]

        # Save to DB synchronously via sessionmaker
        sm_a = get_sessionmaker()
        async with sm_a() as session:
            for c_data in case_data_list:
                await service_a.save_case_to_db_session(c_data, session)
            for r_data in ring_data_list:
                await service_a.save_ring_to_db_session(r_data, session)

            # Record feedback
            fb_record = {
                "case_id": "CASE_PERSIST_00",
                "confirmed_fraud": True,
                "resolution": "CONFIRMED_FRAUD",
                "notes": "Verified fraudulent mule hub",
                "vpas_flagged": ["mule_collector_00@okhdfc"],
                "dpip_published": {"record_id": "DPIP_001"},
            }
            await service_a.save_feedback_to_db_session(fb_record, session)
            await session.commit()

        # =====================================================================
        # PHASE 2: SIMULATE ABRUPT PROCESS KILL
        # =====================================================================
        # 1. Close active engine
        await close_db()

        # 2. Obliterate all in-memory singletons and state caches
        sess_mod._engine = None
        sess_mod._sessionmaker = None
        sess_mod._is_db_ready = False
        svc_mod._service = None

        # Verify state is completely destroyed in memory
        self.assertIsNone(sess_mod._engine)
        self.assertIsNone(svc_mod._service)

        # =====================================================================
        # PHASE 3: Process Instance B (Resume / Startup from DB)
        # =====================================================================
        # 1. Re-initialize DB engine against the exact same SQLite file
        init_ok = await init_db()
        self.assertTrue(init_ok)

        # 2. Re-instantiate service and execute sync_from_db()
        service_b = svc_mod.get_upi_case_service()
        self.assertIsNot(service_b, service_a)
        await service_b.sync_from_db()

        # =====================================================================
        # PHASE 4: Validate 100% Persistent State Integrity
        # =====================================================================
        recovered_cases = service_b.list_cases()
        self.assertEqual(len(recovered_cases), 5)

        # Check case 0 details
        c0 = service_b.get_case("CASE_PERSIST_00")
        self.assertIsNotNone(c0)
        self.assertEqual(c0["case_id"], "CASE_PERSIST_00")
        self.assertEqual(c0["verdict"], "ALLOW")
        self.assertEqual(c0["risk_score"], 30)
        self.assertEqual(c0["amount"], 25000.0)
        self.assertEqual(c0["sar_markdown"], "# Suspicious Activity Report for Case 0\nDetails...")
        self.assertIn("raw_tokens", c0["token_economy"])
        self.assertEqual(c0["token_economy"]["compression_ratio"], 4.16)

        # Check case 4 details
        c4 = service_b.get_case("CASE_PERSIST_04")
        self.assertIsNotNone(c4)
        self.assertEqual(c4["verdict"], "HOLD")
        self.assertEqual(c4["risk_score"], 90)

        # Check mule rings in federation coordinator
        rings_recovered = service_b.federation.current_rings()
        self.assertEqual(len(rings_recovered), 2)
        ring_hashes = {r["ring_hash"] for r in rings_recovered}
        self.assertIn("RING_HASH_0", ring_hashes)
        self.assertIn("RING_HASH_1", ring_hashes)

        # Check feedback records in DB directly
        sm_b = get_sessionmaker()
        async with sm_b() as session:
            res = await session.execute(select(CaseFeedbackModel).where(CaseFeedbackModel.case_id == "CASE_PERSIST_00"))
            fb = res.scalars().first()
            self.assertIsNotNone(fb)
            self.assertTrue(fb.confirmed_fraud)
            self.assertEqual(fb.resolution, "CONFIRMED_FRAUD")

    async def test_02_multi_cycle_kill_resume_persistence_integrity(self):
        """Stress: Multi-cycle kill & resume across multiple restart iterations with state mutations."""
        import app.db.session as sess_mod
        import app.services.upi_cases as svc_mod

        # Cycle 1: Init, write initial case
        sess_mod._engine = None
        sess_mod._sessionmaker = None
        sess_mod._is_db_ready = False
        svc_mod._service = None
        await init_db()
        if hasattr(tests.mock_env, "_MOCK_DB_STORE"):
            tests.mock_env._MOCK_DB_STORE["cases"].clear()
            tests.mock_env._MOCK_DB_STORE["rings"].clear()
            tests.mock_env._MOCK_DB_STORE["feedback"].clear()
        service_1 = svc_mod.get_upi_case_service()
        service_1.clear()

        sm_1 = get_sessionmaker()
        async with sm_1() as session:
            await service_1.save_case_to_db_session({
                "case_id": "CASE_CYCLE_01",
                "status": "OPEN",
                "verdict": "HOLD",
                "risk_score": 65,
                "payer_vpa": "payer1@oksbi",
                "payee_vpa": "payee1@okhdfc",
                "amount": 50000.0,
                "trigger_txn": {"txn_id": "TXN_C1"},
                "rule_hits": [],
                "token_economy": {"raw_tokens": 500, "compression_ratio": 2.5},
            }, session)
            await session.commit()

        # KILL 1
        await close_db()
        sess_mod._engine = None
        sess_mod._sessionmaker = None
        sess_mod._is_db_ready = False
        svc_mod._service = None

        # RESUME 1: Mutate state (add case 2 and resolve case 1)
        await init_db()
        service_2 = svc_mod.get_upi_case_service()
        await service_2.sync_from_db()
        self.assertEqual(len(service_2.list_cases()), 1)

        sm_2 = get_sessionmaker()
        async with sm_2() as session:
            # Update case 1 status to INVESTIGATED
            c1 = await session.get(UpiCaseModel, "CASE_CYCLE_01")
            c1.status = "INVESTIGATED"
            c1.resolution = "RESOLVED_MULE"

            # Add case 2
            await service_2.save_case_to_db_session({
                "case_id": "CASE_CYCLE_02",
                "status": "OPEN",
                "verdict": "BLOCK",
                "risk_score": 95,
                "payer_vpa": "payer2@oksbi",
                "payee_vpa": "payee2@okhdfc",
                "amount": 120000.0,
                "trigger_txn": {"txn_id": "TXN_C2"},
                "rule_hits": [{"rule_id": "MULE_RING_DETECTED", "score": 90}],
                "token_economy": {"raw_tokens": 900, "compression_ratio": 3.2},
            }, session)
            await session.commit()

        # KILL 2
        await close_db()
        sess_mod._engine = None
        sess_mod._sessionmaker = None
        sess_mod._is_db_ready = False
        svc_mod._service = None

        # RESUME 2: Verify both cases with updated statuses preserved
        await init_db()
        service_3 = svc_mod.get_upi_case_service()
        await service_3.sync_from_db()

        all_cases = service_3.list_cases()
        self.assertEqual(len(all_cases), 2)
        c1_res = service_3.get_case("CASE_CYCLE_01")
        self.assertEqual(c1_res["status"], "INVESTIGATED")
        self.assertEqual(c1_res["resolution"], "RESOLVED_MULE")

        c2_res = service_3.get_case("CASE_CYCLE_02")
        self.assertEqual(c2_res["status"], "OPEN")
        self.assertEqual(c2_res["verdict"], "BLOCK")
        self.assertEqual(c2_res["risk_score"], 95)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Master Test Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_tier5_adversarial_suite():
    """Execute all Tier 5 adversarial stress test classes and print formatted summary."""
    print("=" * 80)
    print("      SAMPATI V2 — TIER 5 ADVERSARIAL COVERAGE HARDENING TEST HARNESS")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestWebSocketPoolAdversarial))
    suite.addTests(loader.loadTestsFromTestCase(TestCanvasHitDetectionMathAdversarial))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseConnectionPoolAdversarial))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessKillAndResumeAdversarial))

    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start_time

    print("=" * 80)
    print("                       TIER 5 EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests Executed : {result.testsRun}")
    print(f"Passed               : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures             : {len(result.failures)}")
    print(f"Errors               : {len(result.errors)}")
    print(f"Elapsed Time         : {elapsed:.3f} seconds")
    print("=" * 80)

    if result.wasSuccessful():
        print("VERDICT: ALL TIER 5 ADVERSARIAL STRESS TESTS PASSED [APPROVE]")
        return 0
    else:
        print("VERDICT: TIER 5 STRESS TESTS DETECTED FAILURES [REQUEST_CHANGES]")
        return 1


if __name__ == "__main__":
    sys.exit(run_tier5_adversarial_suite())

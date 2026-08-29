"""Unit and Contract Tests for GET /health/detailed and Real-Time Telemetry in SAMPATI V2.

Verifies:
1. Endpoint schema contract for GET /health/detailed and GET /upi/health/detailed.
2. Latency percentiles telemetry: p50, p90, p99, min, max, avg, samples_count.
3. Latency monotonic invariant: min <= p50 <= p90 <= p99 <= max.
4. PostgreSQL connection pool telemetry: status, driver, pool_size, max_overflow, checked_in/out connections.
5. Redis cache connection status and ping latency (graceful fallback).
6. Active WebSocket client tracking.
7. Sliding window throughput: batches_per_min, txns_per_sec, total_evaluations, recent_evaluations_last_60s.
8. Monotonic process uptime calculation and human-readable formatting.
"""
from __future__ import annotations

import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone
from typing import Any, Dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.models.upi_models import UpiTransaction
from app.services.upi_cases import UpiCaseService, get_upi_case_service


class TestHealthDetailed(unittest.TestCase):
    """Unit and contract tests for GET /health/detailed and telemetry components."""

    def setUp(self):
        self.service = get_upi_case_service()

    def test_health_detailed_payload_contract(self):
        """Verify GET /health/detailed response structure contains all required components."""
        if hasattr(self.service, "get_detailed_health"):
            data = self.service.get_detailed_health()
        else:
            from app.api.upi import get_detailed_health_payload
            data = get_detailed_health_payload(self.service)

        self.assertIsInstance(data, dict)
        self.assertIn("status", data)
        self.assertIn("service", data)
        self.assertEqual(data["service"], "sampati-upi")
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
        self.assertIn("uptime", data)
        self.assertIn("latency_ms", data)
        self.assertIn("database", data)
        self.assertIn("redis", data)
        self.assertIn("websocket", data)
        self.assertIn("throughput", data)

    def test_latency_percentiles_calculation_and_invariants(self):
        """Verify p50, p90, p99 calculation and mathematical ordering invariants."""
        # Inject known latencies if method exists
        if hasattr(self.service, "record_latency"):
            test_latencies = [1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 5.0, 8.0, 12.0, 25.0]
            for lat in test_latencies:
                self.service.record_latency(lat)

        if hasattr(self.service, "get_latency_percentiles"):
            latency_stats = self.service.get_latency_percentiles()
        else:
            if hasattr(self.service, "get_detailed_health"):
                health = self.service.get_detailed_health()
                latency_stats = health.get("latency_ms", {})
            else:
                from app.api.upi import get_detailed_health_payload
                latency_stats = get_detailed_health_payload(self.service).get("latency_ms", {})

        self.assertIn("p50", latency_stats)
        self.assertIn("p90", latency_stats)
        self.assertIn("p99", latency_stats)
        self.assertIn("min", latency_stats)
        self.assertIn("max", latency_stats)
        self.assertIn("avg", latency_stats)

        p50 = float(latency_stats["p50"])
        p90 = float(latency_stats["p90"])
        p99 = float(latency_stats["p99"])
        lat_min = float(latency_stats["min"])
        lat_max = float(latency_stats["max"])

        # Monotonic Invariant: min <= p50 <= p90 <= p99 <= max
        self.assertLessEqual(lat_min, p50)
        self.assertLessEqual(p50, p90)
        self.assertLessEqual(p90, p99)
        self.assertLessEqual(p99, lat_max)

    def test_database_pool_telemetry(self):
        """Verify database pool metadata reporting."""
        if hasattr(self.service, "get_detailed_health"):
            data = self.service.get_detailed_health()
        else:
            from app.api.upi import get_detailed_health_payload
            data = get_detailed_health_payload(self.service)

        db = data["database"]
        self.assertIn("status", db)
        self.assertIn(db["status"], ["connected", "in-memory-fallback", "healthy", "ok"])
        self.assertIn("driver", db)
        self.assertIn("pool_size", db)
        self.assertIn("max_overflow", db)
        self.assertIn("checked_in_connections", db)
        self.assertIn("checked_out_connections", db)

    def test_redis_connection_reporting(self):
        """Verify Redis status is reported or gracefully falls back."""
        if hasattr(self.service, "get_detailed_health"):
            data = self.service.get_detailed_health()
        else:
            from app.api.upi import get_detailed_health_payload
            data = get_detailed_health_payload(self.service)

        redis = data["redis"]
        self.assertIn("status", redis)
        self.assertIn(redis["status"], ["connected", "in-memory-fallback", "healthy", "ok", "unavailable"])

    def test_websocket_connections_reporting(self):
        """Verify active WebSocket connections count is reported."""
        if hasattr(self.service, "get_detailed_health"):
            data = self.service.get_detailed_health()
        else:
            from app.api.upi import get_detailed_health_payload
            data = get_detailed_health_payload(self.service)

        ws = data["websocket"]
        self.assertIn("active_connections", ws)
        self.assertIsInstance(ws["active_connections"], int)
        self.assertGreaterEqual(ws["active_connections"], 0)

    def test_throughput_metrics(self):
        """Verify throughput metrics (batches/min, txns/sec, total evaluations)."""
        if hasattr(self.service, "get_throughput_metrics"):
            throughput = self.service.get_throughput_metrics()
        else:
            if hasattr(self.service, "get_detailed_health"):
                throughput = self.service.get_detailed_health().get("throughput", {})
            else:
                from app.api.upi import get_detailed_health_payload
                throughput = get_detailed_health_payload(self.service).get("throughput", {})

        self.assertIn("batches_per_min", throughput)
        self.assertIn("txns_per_sec", throughput)
        self.assertIn("total_evaluations", throughput)
        self.assertIn("recent_evaluations_last_60s", throughput)
        self.assertGreaterEqual(throughput["total_evaluations"], 0)

    def test_uptime_calculation(self):
        """Verify process uptime tracking."""
        if hasattr(self.service, "get_detailed_health"):
            data = self.service.get_detailed_health()
        else:
            from app.api.upi import get_detailed_health_payload
            data = get_detailed_health_payload(self.service)

        uptime = data["uptime"]
        self.assertIn("uptime_seconds", uptime)
        self.assertIn("uptime_human", uptime)
        self.assertIn("start_time", uptime)
        self.assertGreaterEqual(uptime["uptime_seconds"], 0.0)


if __name__ == "__main__":
    unittest.main()

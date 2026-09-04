"""Test suite & End-to-End Latency Benchmark for Mobile Push Notifications & FCM Integration."""
from __future__ import annotations

import asyncio
import statistics
import time
import unittest
from typing import Any, Dict

from fastapi.testclient import TestClient

from app.main import app
from app.services.notification_service import (
    DeviceRegistrationRequest,
    HttpV1FcmProvider,
    MockFcmProvider,
    NotificationPayload,
    NotificationService,
    get_notification_service,
)


class TestNotificationsAndBenchmark(unittest.TestCase):
    """Unit, integration, and latency benchmark tests for the FCM notification subsystem."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.svc = get_notification_service()
        self.svc.clear()

    def tearDown(self) -> None:
        self.svc.clear()

    def test_device_registration_new_token(self) -> None:
        """Registering a new device token should return 200 with status 'registered'."""
        res = self.client.post(
            "/notifications/register",
            json={
                "device_token": "fcm_token_device_alpha_12345",
                "platform": "android",
                "vpa": "victim@oksbi",
                "device_id": "HW-DEV-001",
                "user_id": "USR-9901",
                "app_version": "2.1.0",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "registered")
        self.assertEqual(data["device_token"], "fcm_token_device_alpha_12345")
        self.assertEqual(data["platform"], "android")
        self.assertEqual(data["total_registered_devices"], 1)

    def test_device_registration_duplicate_token_updates_metadata(self) -> None:
        """Re-registering an existing token should return status 'updated' and not duplicate count."""
        # First registration
        self.client.post(
            "/notifications/register",
            json={
                "device_token": "fcm_token_device_alpha_12345",
                "platform": "android",
                "vpa": "victim@oksbi",
                "app_version": "2.0.0",
            },
        )
        # Second registration with updated app_version
        res2 = self.client.post(
            "/notifications/register",
            json={
                "device_token": "fcm_token_device_alpha_12345",
                "platform": "android",
                "vpa": "victim@oksbi",
                "app_version": "2.1.0",
            },
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["status"], "updated")
        self.assertEqual(data2["total_registered_devices"], 1)

        # Verify metadata was updated in service registry
        with self.svc._lock:
            rec = self.svc._tokens["fcm_token_device_alpha_12345"]
            self.assertEqual(rec["app_version"], "2.1.0")

    def test_device_registration_token_alias(self) -> None:
        """Clients sending 'token' instead of 'device_token' should be accepted seamlessly."""
        res = self.client.post(
            "/notifications/register",
            json={
                "token": "fcm_token_alias_supported_123",
                "platform": "ios",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "registered")
        self.assertEqual(data["device_token"], "fcm_token_alias_supported_123")

    def test_device_registration_validation_error(self) -> None:
        """Tokens shorter than 10 characters should fail schema validation with HTTP 422."""
        res = self.client.post(
            "/notifications/register",
            json={"device_token": "short", "platform": "android"},
        )
        self.assertEqual(res.status_code, 422)

    def test_list_registered_tokens_endpoint(self) -> None:
        """GET /notifications/tokens returns all registered tokens and attributes."""
        self.client.post(
            "/notifications/register",
            json={"device_token": "fcm_token_dev_1_123456", "platform": "android", "vpa": "user1@oksbi"},
        )
        self.client.post(
            "/notifications/register",
            json={"device_token": "fcm_token_dev_2_123456", "platform": "ios", "vpa": "user2@okhdfc"},
        )
        res = self.client.get("/notifications/tokens")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 2)
        tokens = [t["token"] for t in data["tokens"]]
        self.assertIn("fcm_token_dev_1_123456", tokens)
        self.assertIn("fcm_token_dev_2_123456", tokens)

    def test_list_notification_history_endpoint(self) -> None:
        """GET /notifications/history returns recent dispatches."""
        self.client.post(
            "/notifications/register",
            json={"device_token": "fcm_token_dev_history_123", "platform": "android"},
        )
        # Ingest a high-severity signal to generate history
        self.client.post(
            "/intel/signals",
            json={
                "upi_id": "threat_target@oksbi",
                "tags": ["Bank impersonation"],
                "severity": "HIGH",
            },
        )
        res = self.client.get("/notifications/history?limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total"], 1)
        self.assertGreaterEqual(len(data["history"]), 1)

    def test_notification_status_endpoint(self) -> None:
        """GET /notifications/status returns health and provider information."""
        res = self.client.get("/notifications/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn(data["provider"], ("MockFcmProvider", "HttpV1FcmProvider"))

    def test_high_risk_intel_signal_triggers_fcm_dispatch(self) -> None:
        """POST /intel/signals with HIGH severity must trigger FCM dispatch."""
        self.client.post(
            "/notifications/register",
            json={"device_token": "fcm_token_high_risk_test_999", "platform": "android"},
        )
        res = self.client.post(
            "/intel/signals",
            json={
                "upi_id": "urgent_scam@oksbi",
                "tags": ["Bank impersonation", "Urgency"],
                "severity": "HIGH",
                "confidence": 0.95,
            },
        )
        self.assertEqual(res.status_code, 201)

        # Verify notification was dispatched
        hist = self.svc.dispatch_history
        self.assertGreaterEqual(len(hist), 1)
        last_notif = hist[-1]["payload"]
        self.assertEqual(last_notif["risk_score"], 85)
        self.assertEqual(last_notif["verdict"], "BLOCK")
        self.assertTrue(any(t in last_notif["top_reason"] for t in ["Bank impersonation", "Urgency"]))
        self.assertEqual(last_notif["target_vpa"], "urgent_scam@oksbi")

    def test_critical_risk_intel_signal_triggers_fcm_dispatch(self) -> None:
        """POST /intel/signals with CRITICAL severity must trigger FCM dispatch with risk_score=95."""
        self.client.post(
            "/notifications/register",
            json={"device_token": "fcm_token_crit_risk_test_999", "platform": "android"},
        )
        res = self.client.post(
            "/intel/signals",
            json={
                "upi_id": "critical_threat@oksbi",
                "tags": ["KYC suspension"],
                "severity": "CRITICAL",
                "confidence": 0.98,
            },
        )
        self.assertEqual(res.status_code, 201)

        hist = self.svc.dispatch_history
        self.assertGreaterEqual(len(hist), 1)
        last_notif = hist[-1]["payload"]
        self.assertEqual(last_notif["risk_score"], 95)
        self.assertEqual(last_notif["verdict"], "BLOCK")
        self.assertIn("KYC suspension", last_notif["top_reason"])

    def test_low_risk_intel_signal_does_not_trigger_fcm(self) -> None:
        """POST /intel/signals with LOW severity must NOT trigger FCM dispatch."""
        self.client.post(
            "/notifications/register",
            json={"device_token": "fcm_token_low_risk_test_111", "platform": "android"},
        )
        res = self.client.post(
            "/intel/signals",
            json={
                "upi_id": "clean_merchant@oksbi",
                "tags": ["Refund/Delivery"],
                "severity": "LOW",
                "confidence": 0.3,
            },
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(len(self.svc.dispatch_history), 0)

    def test_upi_check_block_verdict_triggers_fcm_dispatch(self) -> None:
        """POST /upi/check with BLOCK verdict must trigger FCM dispatch."""
        self.client.post(
            "/notifications/register",
            json={
                "device_token": "fcm_token_upi_payer_alert_12345",
                "platform": "android",
                "vpa": "payer_victim@oksbi",
            },
        )

        txn_payload: Dict[str, Any] = {
            "txn_id": "TXN_BLOCK_FCM_TEST_01",
            "payer_vpa": "payer_victim@oksbi",
            "payee_vpa": "darkweb_mule_sink@okaxis",
            "amount": 150000.0,
            "payer_account_age_days": 1,
            "payer_psp": "oksbi",
            "payee_psp": "okaxis",
            "txn_type": "P2P",
        }
        res = self.client.post("/upi/check", json=txn_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["action"], "BLOCK")

        # Verify FCM notification was triggered
        hist = self.svc.dispatch_history
        self.assertGreaterEqual(len(hist), 1)
        last_dispatch = hist[-1]
        payload = last_dispatch["payload"]
        self.assertEqual(payload["verdict"], "BLOCK")
        self.assertEqual(payload["risk_score"], data["risk_score"])
        self.assertEqual(payload["target_vpa"], "payer_victim@oksbi")
        self.assertEqual(payload["data"]["txn_id"], "TXN_BLOCK_FCM_TEST_01")

    def test_upi_check_allow_verdict_does_not_trigger_fcm(self) -> None:
        """POST /upi/check with ALLOW verdict must NOT trigger FCM dispatch."""
        self.client.post(
            "/notifications/register",
            json={
                "device_token": "fcm_token_clean_payer_12345",
                "platform": "android",
                "vpa": "clean_payer@oksbi",
            },
        )

        txn_payload: Dict[str, Any] = {
            "txn_id": "TXN_ALLOW_FCM_TEST_01",
            "payer_vpa": "clean_payer@oksbi",
            "payee_vpa": "clean_merchant@okicici",
            "amount": 250.0,
            "payer_account_age_days": 365,
            "payer_psp": "oksbi",
            "payee_psp": "okicici",
            "txn_type": "P2M",
        }
        res = self.client.post("/upi/check", json=txn_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["action"], "ALLOW")
        self.assertEqual(len(self.svc.dispatch_history), 0)

    def test_targeted_vpa_notification_filtering(self) -> None:
        """Service should target devices matching the target VPA, falling back to broadcast."""
        self.svc.register_device(
            DeviceRegistrationRequest(
                device_token="fcm_token_target_vpa_1",
                platform="android",
                vpa="targeted_victim@oksbi",
            )
        )
        self.svc.register_device(
            DeviceRegistrationRequest(
                device_token="fcm_token_other_vpa_2",
                platform="ios",
                vpa="other_user@okhdfc",
            )
        )

        # Target specific VPA
        matched = self.svc.get_registered_tokens("targeted_victim@oksbi")
        self.assertEqual(matched, ["fcm_token_target_vpa_1"])

        # Unknown VPA falls back to broadcast
        fallback = self.svc.get_registered_tokens("unknown_user@oksbi")
        self.assertEqual(len(fallback), 2)

    def test_mock_fcm_provider_unit(self) -> None:
        """MockFcmProvider records dispatches accurately with microsecond latency."""
        provider = MockFcmProvider()
        payload = NotificationPayload(
            risk_score=90,
            verdict="BLOCK",
            top_reason="Unit test trigger",
            target_vpa="test@oksbi",
        )
        result = asyncio.run(provider.send(["token_1", "token_2"], payload))
        self.assertTrue(result.success)
        self.assertEqual(result.dispatched_count, 2)
        self.assertEqual(result.mode, "mock")
        self.assertGreater(result.latency_ms, 0.0)
        self.assertEqual(len(provider.dispatches), 1)

    def test_http_v1_fcm_provider_unit(self) -> None:
        """HttpV1FcmProvider initializes correctly and handles requests gracefully."""
        provider = HttpV1FcmProvider(project_id="sampati-unit-test")
        payload = NotificationPayload(
            risk_score=95,
            verdict="BLOCK",
            top_reason="Live provider test",
        )
        # Sending with empty tokens
        empty_result = asyncio.run(provider.send([], payload))
        self.assertTrue(empty_result.success)
        self.assertEqual(empty_result.dispatched_count, 0)

        # Sending with token in unauthenticated test mode
        result = asyncio.run(provider.send(["fake_fcm_token_12345678"], payload))
        self.assertTrue(result.success)
        self.assertEqual(result.mode, "http_v1")
        self.assertEqual(result.dispatched_count, 1)

    def test_end_to_end_latency_benchmark_under_500ms(self) -> None:
        """Benchmark end-to-end latency from signal ingestion to FCM dispatch is strictly under 500ms.

        Runs 50+ iterations via POST /intel/signals, computing average, median (p50),
        p95, p99, and max latency. Asserts p99 and max are strictly under 500ms.
        """
        # Register benchmark device
        self.client.post(
            "/notifications/register",
            json={
                "device_token": "fcm_token_benchmark_perf_device_123",
                "platform": "android",
                "vpa": "bench_victim@oksbi",
            },
        )

        # Pre-warm runtime paths
        self.client.post(
            "/intel/signals",
            json={
                "upi_id": "warmup@oksbi",
                "severity": "HIGH",
                "tags": ["Bank impersonation"],
            },
        )

        iterations = 60
        latencies_ms = []

        for i in range(iterations):
            payload = {
                "upi_id": f"bench_mule_{i:03d}@okhdfcbank",
                "phone": f"+9198765{i:05d}",
                "tags": ["KYC suspension", "Urgency"],
                "severity": "HIGH",
                "confidence": 0.92,
            }
            t0 = time.perf_counter()
            res = self.client.post("/intel/signals", json=payload)
            t1 = time.perf_counter()

            self.assertEqual(res.status_code, 201)
            lat_ms = (t1 - t0) * 1000.0
            latencies_ms.append(lat_ms)

        avg_lat = statistics.mean(latencies_ms)
        p50_lat = statistics.median(latencies_ms)
        sorted_lat = sorted(latencies_ms)
        p95_lat = sorted_lat[int(len(sorted_lat) * 0.95)]
        p99_lat = sorted_lat[int(len(sorted_lat) * 0.99)]
        max_lat = max(latencies_ms)

        print("\n" + "=" * 70)
        print(f"=== SAMPATI V2 FCM Push Notification Latency Benchmark ({iterations} runs) ===")
        print(f"  • Average Latency : {avg_lat:.2f} ms")
        print(f"  • Median (p50)    : {p50_lat:.2f} ms")
        print(f"  • 95th Percentile : {p95_lat:.2f} ms")
        print(f"  • 99th Percentile : {p99_lat:.2f} ms")
        print(f"  • Maximum Latency : {max_lat:.2f} ms")
        print(f"  • SLA Target      : < 500.00 ms")
        print("=" * 70 + "\n")

        # Assertions
        self.assertLess(
            p99_lat,
            500.0,
            f"p99 latency ({p99_lat:.2f} ms) must be strictly under 500.0 ms",
        )
        self.assertLess(
            max_lat,
            500.0,
            f"Max latency ({max_lat:.2f} ms) must be strictly under 500.0 ms",
        )
        # Typical execution on local machine is well under 50ms
        self.assertLess(p50_lat, 100.0, f"p50 latency ({p50_lat:.2f} ms) is expected under 100.0 ms")


if __name__ == "__main__":
    unittest.main()

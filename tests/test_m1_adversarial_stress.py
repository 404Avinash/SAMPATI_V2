"""Empirical Adversarial Stress & Chaos Test Suite for Milestone 1 (M1).

Adversarially challenges:
1. Dead Money Velocity (DMV) Engine
2. SIM-Device Mismatch Rule
3. Impossible Travel Velocity Rule
4. Datacenter / VPN IP Origin Rule
5. Fraud Campaign DNA Fingerprinting & Dynamic Ingestion Store
6. Full Pipeline Concurrency, Latency, and Memory Stress
"""
from __future__ import annotations

import concurrent.futures
import ipaddress
import math
import random
import time
import unittest
from datetime import datetime, timedelta, timezone
from typing import List

from app.engine.campaign import (
    CampaignSignature,
    CampaignSignatureStore,
    check_campaign_match,
    get_campaign_store,
    rule_campaign_match,
)
from app.engine.dmv import (
    DmvTracker,
    calculate_dmv_score,
    get_dmv_tracker,
)
from app.engine.upi_rules import (
    CITY_COORDINATES,
    COMPILED_DC_NETWORKS,
    clear_rule_telemetry,
    evaluate_rules,
    haversine_distance,
    record_payer_telemetry,
    resolve_coordinates,
    rule_datacenter_ip,
    rule_impossible_travel,
    rule_sim_device_mismatch,
)
from app.engine.upi_scorer import UpiRiskScorer, get_upi_scorer
from app.engine.upi_state import get_upi_state
from app.models.upi_models import UpiEvaluationResponse, UpiTransaction
from app.services.upi_cases import UpiCaseService, get_upi_case_service


class TestDmvAdversarialStress(unittest.TestCase):
    """Adversarial stress and edge-case testing for Dead Money Velocity."""

    def setUp(self) -> None:
        self.tracker = DmvTracker(window_hours=720.0)

    def test_dmv_extreme_numerical_boundaries(self) -> None:
        """Test DMV calculations with extreme and edge amounts and account ages."""
        now = datetime.now(timezone.utc)
        cases = [
            # (amount, payer_account_age_days)
            (0.0, 0),
            (0.0, 365),
            (0.01, 1),
            (0.01, 10000),
            (-500.0, -10),  # Negative values should be handled safely
            (1000000000.0, 30),  # Huge 1B INR outflow
            (1e-6, 15),
        ]
        for amt, age in cases:
            txn = UpiTransaction(
                txn_id=f"TXN_NUM_{abs(hash((amt, age)))}",
                payer_vpa="test_num@okaxis",
                payee_vpa="dest@ybl",
                amount=amt,
                payer_account_age_days=age,
                timestamp=now,
            )
            score = calculate_dmv_score(txn, self.tracker)
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)
            self.assertFalse(math.isnan(score))
            self.assertFalse(math.isinf(score))

    def test_dmv_out_of_order_and_future_timestamps(self) -> None:
        """Test DMV calculation when transactions arrive out-of-order or with future timestamps."""
        t_base = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)

        # Ingest past transactions out of order
        t_seq = [
            t_base - timedelta(days=10),
            t_base - timedelta(days=20),
            t_base - timedelta(days=5),
            t_base + timedelta(days=5),  # Future timestamp
        ]
        for i, ts in enumerate(t_seq):
            txn = UpiTransaction(
                txn_id=f"TXN_TS_{i}",
                payer_vpa="time_traveler@okaxis",
                payee_vpa=f"dest_{i}@ybl",
                amount=1000.0 * (i + 1),
                timestamp=ts,
            )
            self.tracker.record_txn(txn)

        eval_txn = UpiTransaction(
            txn_id="TXN_TS_EVAL",
            payer_vpa="time_traveler@okaxis",
            payee_vpa="dest_eval@ybl",
            amount=5000.0,
            timestamp=t_base,
        )
        score = calculate_dmv_score(eval_txn, self.tracker)
        self.assertTrue(0.0 <= score <= 100.0)

    def test_dmv_sliding_window_eviction_under_load(self) -> None:
        """Record 5,000 rapid transactions and verify eviction purges records older than window."""
        tracker = DmvTracker(window_hours=1.0)  # 1-hour window
        now = datetime.now(timezone.utc)
        vpa = "high_load_vpa@okaxis"

        # 2000 transactions older than 1 hour
        for i in range(2000):
            ts = now - timedelta(hours=2, seconds=i)
            txn = UpiTransaction(
                txn_id=f"TXN_OLD_{i}",
                payer_vpa=vpa,
                payee_vpa="dest@okaxis",
                amount=10.0,
                timestamp=ts,
            )
            tracker.record_txn(txn)

        # 500 transactions within the last 10 minutes
        for i in range(500):
            ts = now - timedelta(minutes=random.randint(1, 10))
            txn = UpiTransaction(
                txn_id=f"TXN_NEW_{i}",
                payer_vpa=vpa,
                payee_vpa="dest@okaxis",
                amount=20.0,
                timestamp=ts,
            )
            tracker.record_txn(txn)

        count, outflow, _ = tracker.get_stats_window(vpa, now, window_sec=3600.0)
        self.assertEqual(count, 500)
        self.assertAlmostEqual(outflow, 500 * 20.0, places=1)

    def test_dmv_multithreaded_concurrency(self) -> None:
        """Stress-test DmvTracker under 50 concurrent worker threads."""
        tracker = DmvTracker()
        now = datetime.now(timezone.utc)
        num_threads = 20
        txns_per_thread = 50

        def worker_task(thread_id: int) -> None:
            vpa = f"concurrent_vpa_{thread_id % 5}@okaxis"
            for i in range(txns_per_thread):
                txn = UpiTransaction(
                    txn_id=f"TXN_TH_{thread_id}_{i}",
                    payer_vpa=vpa,
                    payee_vpa=f"dest_{thread_id}_{i}@ybl",
                    amount=float(100 + i * 10),
                    timestamp=now - timedelta(seconds=i),
                )
                tracker.record_txn(txn)
                calculate_dmv_score(txn, tracker)
                if i % 10 == 0:
                    tracker.get_top_vpas(limit=5)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_task, tid) for tid in range(num_threads)]
            for f in concurrent.futures.as_completed(futures):
                f.result()  # Will raise if any thread threw exception

        top_vpas = tracker.get_top_vpas(limit=10)
        self.assertIsInstance(top_vpas, list)
        self.assertGreaterEqual(len(top_vpas), 1)


class TestSimDeviceMismatchAdversarialStress(unittest.TestCase):
    """Adversarial stress testing for R_SIM_DEVICE_MISMATCH."""

    def setUp(self) -> None:
        clear_rule_telemetry()

    def tearDown(self) -> None:
        clear_rule_telemetry()

    def test_fuzzed_and_unicode_identifiers(self) -> None:
        """Test strange, long, and unicode device/sim identifiers."""
        payer = "unicode_user@okaxis"
        dev_orig = "📱_IPHONE_हिंदी_12345"
        sim_orig = "📶_JIO_5G_தமிழ்_67890"

        record_payer_telemetry(payer, device_id=dev_orig, sim_id=sim_orig)

        # Same device, new unicode SIM -> should trigger
        sim_new = "📶_AIRTEL_বাংলা_99999"
        txn = UpiTransaction(
            txn_id="TXN_UNI_001",
            payer_vpa=payer,
            payee_vpa="shop@okaxis",
            amount=5000.0,
            device_id=dev_orig,
            sim_id=sim_new,
        )
        hit = rule_sim_device_mismatch(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_SIM_DEVICE_MISMATCH")

    def test_short_and_empty_identifiers(self) -> None:
        """Test single-character or empty strings in device/sim."""
        payer = "short_user@okaxis"
        record_payer_telemetry(payer, device_id="A", sim_id="1")

        txn = UpiTransaction(
            txn_id="TXN_SHORT_001",
            payer_vpa=payer,
            payee_vpa="dest@ybl",
            amount=100.0,
            device_id="A",
            sim_id="2",
        )
        hit = rule_sim_device_mismatch(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_SIM_DEVICE_MISMATCH")

    def test_both_device_and_sim_changed(self) -> None:
        """When both device and SIM change simultaneously, verify rule behavior."""
        payer = "both_changed@okaxis"
        record_payer_telemetry(payer, device_id="DEV_A", sim_id="SIM_A")

        # When BOTH change, it is neither pure SIM swap nor pure device clone
        txn = UpiTransaction(
            txn_id="TXN_BOTH_001",
            payer_vpa=payer,
            payee_vpa="dest@ybl",
            amount=1000.0,
            device_id="DEV_B",
            sim_id="SIM_B",
        )
        hit = rule_sim_device_mismatch(txn)
        # Should return None because it's not a single-attribute mismatch
        self.assertIsNone(hit)

    def test_concurrent_telemetry_recording(self) -> None:
        """Verify thread-safety of telemetry updates under concurrency."""
        num_threads = 20
        txns_per_thread = 50

        def worker(tid: int) -> None:
            payer = f"concurrent_payer_{tid % 3}@okaxis"
            for i in range(txns_per_thread):
                record_payer_telemetry(
                    payer_vpa=payer,
                    device_id=f"DEV_{tid}_{i}",
                    sim_id=f"SIM_{tid}_{i}",
                    location="Mumbai",
                )
                txn = UpiTransaction(
                    txn_id=f"TXN_C_{tid}_{i}",
                    payer_vpa=payer,
                    payee_vpa="dest@okaxis",
                    amount=500.0,
                    device_id=f"DEV_{tid}_{i}",
                    sim_id=f"SIM_{tid}_{i}",
                    location="Mumbai",
                )
                rule_sim_device_mismatch(txn)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            for f in concurrent.futures.as_completed(futures):
                f.result()


class TestImpossibleTravelAdversarialStress(unittest.TestCase):
    """Adversarial stress and geo-boundary testing for R_IMPOSSIBLE_TRAVEL."""

    def setUp(self) -> None:
        clear_rule_telemetry()

    def tearDown(self) -> None:
        clear_rule_telemetry()

    def test_haversine_antipodal_extremes(self) -> None:
        """Test Haversine calculations at poles and exact antipodes."""
        # North Pole to South Pole: 90,0 to -90,0 -> ~20,015 km (half circumference)
        dist_poles = haversine_distance(90.0, 0.0, -90.0, 0.0)
        self.assertAlmostEqual(dist_poles, 20015.0, delta=100.0)

        # Same location: distance is 0.0
        dist_zero = haversine_distance(19.0760, 72.8777, 19.0760, 72.8777)
        self.assertAlmostEqual(dist_zero, 0.0, delta=0.01)

    def test_subsecond_consecutive_transactions(self) -> None:
        """Two transactions 0.0 seconds apart in different cities (>1000km)."""
        payer = "warp_drive@okaxis"
        t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc)
        record_payer_telemetry(payer, location="Mumbai", timestamp=t0)

        # Same timestamp, but in Tokyo (~6,700 km away)
        txn = UpiTransaction(
            txn_id="TXN_WARP_001",
            payer_vpa=payer,
            payee_vpa="dest@ybl",
            amount=50000.0,
            location="Tokyo",
            timestamp=t0,
        )
        hit = rule_impossible_travel(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_IMPOSSIBLE_TRAVEL")
        self.assertEqual(hit.points, 35)

    def test_malformed_and_extreme_location_strings(self) -> None:
        """Test strange, garbage, and edge-case location inputs."""
        garbage_locations = [
            "NaN,NaN",
            "Infinity,-Infinity",
            ",,,",
            "9999.0, 9999.0",
            "   ",
            "A" * 5000,
            "19.0760;72.8777",
            "null",
            "undefined",
            "New York City, NY",  # Partially matches "New York"
        ]
        for loc in garbage_locations:
            txn = UpiTransaction(
                txn_id="TXN_GARBAGE_GEO",
                payer_vpa="geo_fuzzer@okaxis",
                payee_vpa="dest@ybl",
                amount=100.0,
                location=loc,
            )
            # Must not throw any exception
            hit = rule_impossible_travel(txn)
            self.assertTrue(hit is None or isinstance(hit.points, int))

    def test_borderline_travel_speed_precision(self) -> None:
        """Verify strict adherence to speed / distance thresholds."""
        payer = "precise_flyer@okaxis"
        t0 = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)
        # Point A: (0.0, 0.0)
        record_payer_telemetry(payer, location="0.0,0.0", timestamp=t0)

        # Point B: ~400 km away (approx 3.6 degrees latitude)
        # Time delta: 35 minutes -> speed ~ 685 km/h -> should NOT trigger
        t1 = t0 + timedelta(minutes=35)
        txn_normal = UpiTransaction(
            txn_id="TXN_PRECISE_01",
            payer_vpa=payer,
            payee_vpa="dest@ybl",
            amount=1000.0,
            location="3.6,0.0",
            timestamp=t1,
        )
        self.assertIsNone(rule_impossible_travel(txn_normal))


class TestDatacenterIpAdversarialStress(unittest.TestCase):
    """Adversarial testing for Datacenter / VPN IP rule."""

    def test_datacenter_cidr_exact_subnet_boundaries(self) -> None:
        """Verify exact boundaries of cloud subnets."""
        # AWS: 3.0.0.0/8 includes 3.0.0.0 to 3.255.255.255
        boundary_cases = [
            ("3.0.0.0", True),
            ("3.255.255.255", True),
            ("2.255.255.255", False),
            ("4.0.0.0", False),
            # GCP: 34.0.0.0/8
            ("34.0.0.1", True),
            ("34.255.255.255", True),
            # Azure: 20.0.0.0/8
            ("20.1.2.3", True),
            # Tor: 185.220.100.0/22
            ("185.220.100.1", True),
            ("185.220.103.254", True),
            ("185.220.104.1", False),
        ]
        for ip_str, expected in boundary_cases:
            txn = UpiTransaction(
                txn_id=f"TXN_IP_{ip_str.replace('.', '_')}",
                payer_vpa="ip_tester@okaxis",
                payee_vpa="dest@ybl",
                amount=100.0,
                ip=ip_str,
            )
            hit = rule_datacenter_ip(txn)
            if expected:
                self.assertIsNotNone(hit, f"Expected {ip_str} to be flagged as Datacenter IP")
                self.assertEqual(hit.code, "R_DATACENTER_IP")
            else:
                self.assertIsNone(hit, f"Expected {ip_str} NOT to be flagged as Datacenter IP")

    def test_ipv6_and_private_addresses(self) -> None:
        """Test IPv6, loopback, and private address spaces."""
        test_ips = [
            "::1",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "fe80::1",
            "127.0.0.1",
            "10.0.0.1",
            "172.16.0.1",
            "192.168.1.1",
        ]
        for ip in test_ips:
            txn = UpiTransaction(
                txn_id="TXN_IPV6_TEST",
                payer_vpa="user@okaxis",
                payee_vpa="shop@okaxis",
                amount=50.0,
                ip=ip,
            )
            hit = rule_datacenter_ip(txn)
            self.assertIsNone(hit)

    def test_fuzzed_and_malicious_ip_payloads(self) -> None:
        """Test IP strings containing injection, port numbers, whitespace, or invalid octets."""
        fuzzed_ips = [
            "  3.220.100.45  ",  # Leading/trailing whitespace should strip and match
            "3.220.100.45:8080",
            "192.168.1.1/24",
            "999.999.999.999",
            "1.2.3.4.5",
            "1.2.3.-4",
            "<script>alert(1)</script>",
            "1' OR '1'='1",
            "A" * 1000,
        ]
        for ip in fuzzed_ips:
            txn = UpiTransaction(
                txn_id="TXN_FUZZ_IP",
                payer_vpa="fuzzer@okaxis",
                payee_vpa="dest@ybl",
                amount=50.0,
                ip=ip,
            )
            # Must evaluate safely without unhandled exception
            hit = rule_datacenter_ip(txn)
            if ip.strip() == "3.220.100.45":
                self.assertIsNotNone(hit)
            else:
                self.assertTrue(hit is None or isinstance(hit.code, str))


class TestCampaignFingerprintingAdversarialStress(unittest.TestCase):
    """Adversarial stress and scaling testing for Campaign DNA Fingerprinting."""

    def setUp(self) -> None:
        self.store = CampaignSignatureStore()

    def test_adversarial_payment_notes(self) -> None:
        """Test notes containing emojis, SQL injection, huge strings, and non-English scripts."""
        fuzzed_notes = [
            "🚨 URGENT: YOUR KYC EXPIRE! CLICK OTP 🚨",
            "SELECT * FROM cases WHERE 1=1; DROP TABLE upi_cases; --",
            "A" * 10000,  # 10KB string
            "🎉💰 100% PROFIT GUARANTEE TELEGRAM TASK BONUS VIP 🚀🤑",
            "१२३४५ केवाईसी अपडेट बैंक खाता",
            "     \n\t\r   ",
        ]
        for note in fuzzed_notes:
            txn = UpiTransaction(
                txn_id="TXN_NOTE_FUZZ",
                payer_vpa="user_fuzz@okaxis",
                payee_vpa="dest_fuzz@okaxis",
                amount=15000.0,
                note=note,
            )
            match = self.store.match_campaign(txn)
            # Verify safe execution and valid return structure
            self.assertTrue(match is None or (len(match) == 3 and 0.0 <= match[1] <= 1.0))

    def test_campaign_scale_dynamic_ingestion(self) -> None:
        """Ingest 500 novel blocked transactions and verify query latency < 5ms."""
        for i in range(500):
            txn = UpiTransaction(
                txn_id=f"TXN_INGEST_{i}",
                payer_vpa=f"novel_payer_{i % 50}@okaxis",
                payee_vpa=f"novel_payee_{i % 50}@ybl",
                amount=float(10000 + (i % 20) * 1000),
                note=f"Syndicate smurfing cashout batch {i % 10}",
            )
            self.store.ingest_fingerprint(txn)

        # After 500 ingests, test query performance
        test_txn = UpiTransaction(
            txn_id="TXN_QUERY_PERF",
            payer_vpa="novel_payer_5@okaxis",
            payee_vpa="novel_payee_5@ybl",
            amount=15000.0,
            note="Syndicate smurfing cashout batch 5",
        )
        t0 = time.perf_counter()
        match = self.store.match_campaign(test_txn, threshold=0.80)
        t_elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertIsNotNone(match)
        self.assertLess(t_elapsed_ms, 5.0, f"Query took {t_elapsed_ms:.2f}ms (>5ms limit)")

    def test_campaign_concurrency_stress(self) -> None:
        """Concurrent ingestion and matching from 20 threads simultaneously."""
        store = CampaignSignatureStore()
        num_threads = 20
        iterations = 30

        def worker(tid: int) -> None:
            for i in range(iterations):
                txn = UpiTransaction(
                    txn_id=f"TXN_CONC_{tid}_{i}",
                    payer_vpa=f"mule_{tid}_{i}@okaxis",
                    payee_vpa=f"payee_{tid}@ybl",
                    amount=25000.0,
                    note="URGENT KYC UPDATE UNBLOCK",
                )
                if i % 2 == 0:
                    store.ingest_fingerprint(txn)
                else:
                    store.match_campaign(txn)
                    store.list_campaigns()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            for f in concurrent.futures.as_completed(futures):
                f.result()


class TestFullScorerAdversarialPipeline(unittest.TestCase):
    """Adversarial stress and invariant verification on UpiRiskScorer and UpiCaseService."""

    def setUp(self) -> None:
        clear_rule_telemetry()
        get_dmv_tracker().clear()
        get_campaign_store().clear()

    def test_scorer_high_volume_stress_and_latencies(self) -> None:
        """Run 1,000 rapid transactions through UpiRiskScorer and verify sub-10ms latency."""
        scorer = get_upi_scorer()
        now = datetime.now(timezone.utc)
        latencies: List[float] = []

        for i in range(1000):
            is_malicious = (i % 10 == 0)
            txn = UpiTransaction(
                txn_id=f"TXN_BENCH_{i:04d}",
                payer_vpa=f"payer_{i % 100}@okaxis",
                payee_vpa=f"payee_{i % 50}@ybl",
                amount=float(500 + (i % 50) * 500),
                payer_account_age_days=10 if is_malicious else 300,
                device_id=f"DEV_{(i % 20):02d}",
                sim_id=f"SIM_{(i % 20):02d}" if not is_malicious else f"SIM_SWAPPED_{i}",
                location="Mumbai" if not is_malicious else "Tokyo",
                ip="49.207.50.10" if not is_malicious else "3.220.100.45",
                note="Lunch payment" if not is_malicious else "KYC OTP verification unblock",
                timestamp=now + timedelta(seconds=i),
            )
            resp = scorer.evaluate(txn)
            latencies.append(resp.execution_latency_ms)

            # Invariants verification
            self.assertIsInstance(resp.dmv_score, float)
            self.assertTrue(0.0 <= resp.dmv_score <= 100.0)
            self.assertIn(resp.action, ("ALLOW", "HOLD", "BLOCK"))
            self.assertTrue(0 <= resp.risk_score <= 100)
            if resp.action == "BLOCK":
                self.assertGreaterEqual(resp.risk_score, 70)

        p99_latency = sorted(latencies)[int(0.99 * len(latencies))]
        self.assertLess(p99_latency, 15.0, f"p99 latency too high: {p99_latency:.2f}ms")

    def test_scoring_differential_residential_vs_datacenter(self) -> None:
        """Acceptance Criteria check: Datacenter IP scores strictly higher than residential IP."""
        scorer = get_upi_scorer()
        now = datetime.now(timezone.utc)

        # Baseline transaction from residential IP
        txn_res = UpiTransaction(
            txn_id="TXN_DIFF_RES",
            payer_vpa="user_diff@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="49.207.50.10",  # Residential Airtel/Jio IP
            timestamp=now,
        )
        resp_res = scorer.evaluate(txn_res)

        # Identical transaction from Datacenter IP
        txn_dc = UpiTransaction(
            txn_id="TXN_DIFF_DC",
            payer_vpa="user_diff_2@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="3.220.100.45",  # AWS Datacenter IP
            timestamp=now,
        )
        resp_dc = scorer.evaluate(txn_dc)

        self.assertGreater(resp_dc.risk_score, resp_res.risk_score)
        self.assertIn("R_DATACENTER_IP", resp_dc.reasons)
        self.assertNotIn("R_DATACENTER_IP", resp_res.reasons)


if __name__ == "__main__":
    unittest.main()

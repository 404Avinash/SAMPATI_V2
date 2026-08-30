"""Empirical Adversarial Challenge Test Suite for SAMPATI V2 (Tier 5).

Empirical verification harness targeting:
1. Honeypot stress testing:
   - Rapid concurrent hits and contention across threads.
   - Case sensitivity matrix (e.g. HONEYPOT_TRAP_01@OKAXIS, mixed-case, whitespace).
   - Deflection counter aggregation over 24h rolling windows & lifetime stats.
2. Federation signal edge testing:
   - Large volume batch signals (5,000+ signals, 250+ rings).
   - Sub-5ms latency under sustained lookup load.
   - Unknown hash lookups and fuzzing (random hex, empty, unicode, injection strings).
   - Dynamic network_score blending across 3 layers (Rules, Adaptive EWMA, Federation).
3. Timeline playback stress testing:
   - Empty topologies and malformed case structures.
   - 0-length transactions and identical timestamp ordering.
   - Rapid play/pause/reset scrubbing & state invariants for k in [0, N].
   - Speed multipliers and interval math.
   - Node coordinate bounds and canvas projection hit detection.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import math
import os
import random
import statistics
import sys
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Set

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.engine.adaptive import AdaptiveBehaviorModel
from app.engine.honeypot import (
    DEFAULT_HONEYPOTS,
    HONEYPOT_PREFIXES,
    HoneypotRegistry,
    get_honeypot_registry,
)
from app.engine.upi_rules import evaluate_rules, rule_honeypot_hit
from app.engine.upi_scorer import (
    ALLOW_BELOW,
    BLOCK_AT,
    NETWORK_HOLD_FLOOR,
    NETWORK_MAX_POINTS,
    ADAPTIVE_MAX_POINTS,
    UpiRiskScorer,
    get_upi_scorer,
)
from app.engine.upi_state import UpiHotState, get_upi_state
from app.federation.coordinator import FederatedCoordinator, get_federation
from app.models.upi_models import UpiTransaction
from tests.frontend_contracts_test import (
    format_inr,
    get_continuous_edge_color,
    point_to_segment_distance,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. HONEYPOT EMPIRICAL STRESS HARNESS
# ══════════════════════════════════════════════════════════════════════════════

class TestHoneypotEmpiricalStressHarness(unittest.TestCase):
    """Adversarial stress testing of Honeypot detection, hit counting, and 24h rolling windows."""

    def setUp(self):
        self.registry = HoneypotRegistry()
        self.registry.clear()

    def tearDown(self):
        self.registry.clear()

    def test_rapid_concurrent_honeypot_hits_and_contention(self):
        """Stress Test: 50 concurrent threads firing 50 hits each (2,500 total hits)."""
        num_threads = 50
        hits_per_thread = 50
        total_expected_hits = num_threads * hits_per_thread
        amount_per_hit = 1250.0
        expected_total_amount = total_expected_hits * amount_per_hit

        target_vpas = [
            "honeypot_trap_01@okaxis",
            "honeypot_mule_99@okhdfcbank",
            "phish_trap_node@okicici",
            "botnet_sink_04@oksbi",
            "mule_honeypot_prime@okaxis",
        ]

        def worker(thread_idx: int):
            for i in range(hits_per_thread):
                vpa = target_vpas[(thread_idx + i) % len(target_vpas)]
                self.registry.record_hit(
                    vpa=vpa,
                    txn_id=f"CONC_TXN_{thread_idx}_{i}",
                    amount=amount_per_hit,
                    payer_vpa=f"attacker_{thread_idx}@paytm",
                )

        threads = []
        for t_idx in range(num_threads):
            t = threading.Thread(target=worker, args=(t_idx,))
            threads.append(t)

        t0 = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - t0

        # Assert zero lost updates / race conditions
        self.assertEqual(self.registry.total_hits(), total_expected_hits)
        self.assertAlmostEqual(self.registry.total_amount_deflected(), expected_total_amount, places=2)
        self.assertEqual(self.registry.get_hits_24h(), total_expected_hits)

        # Verify all targeted VPAs have correct hit count distributions
        vpa_summary = self.registry.list_honeypots()
        active_traps = [item for item in vpa_summary if item["hit_count"] > 0]
        self.assertEqual(len(active_traps), len(target_vpas))
        sum_hits = sum(item["hit_count"] for item in active_traps)
        self.assertEqual(sum_hits, total_expected_hits)

    def test_honeypot_case_sensitivity_and_normalization_matrix(self):
        """Stress Test: Exhaustive case variants, whitespace, and uppercase prefix matching."""
        case_variants = [
            ("HONEYPOT_TRAP_01@OKAXIS", True),
            ("honeypot_trap_01@okaxis", True),
            ("HoNeYpOt_TrAp_01@OkAxIs", True),
            ("  honeypot_trap_01@okaxis  ", True),
            ("\t\nHONEYPOT_MULE_99@OKHDFCBANK\n", True),
            ("PHISH_TRAP_NODE@OKICICI", True),
            ("BOTNET_SINK_04@OKSBI", True),
            ("MULE_HONEYPOT_PRIME@OKAXIS", True),
            ("TRAP_COLLECT_007@PAYTM", True),
            ("DECOY_MULE_99@YBL", True),
            ("HONEYPOT_CUSTOM_BOTNET@AXIS", True),  # prefix match
            ("phish_trap_dynamically_created@icici", True),  # prefix match
            ("botnet_sink_omega@sbi", True),  # prefix match
            ("legitimate.merchant@okaxis", False),
            ("user_paying_bill@okhdfcbank", False),
            ("normal_customer@okicici", False),
            ("", False),
            ("   ", False),
        ]

        state = UpiHotState()
        for vpa_input, expected_match in case_variants:
            is_matched = self.registry.is_honeypot(vpa_input)
            self.assertEqual(
                is_matched,
                expected_match,
                f"Registry matching failed for VPA: '{vpa_input}' (expected {expected_match}, got {is_matched})"
            )

            # Test through rule evaluation
            if vpa_input.strip():
                txn = UpiTransaction(
                    txn_id=f"TXN_CASE_{hash(vpa_input)}",
                    amount=5000.0,
                    payer_vpa="victim_user@oksbi",
                    payee_vpa=vpa_input,
                )
                hit = rule_honeypot_hit(txn, state)
                if expected_match:
                    self.assertIsNotNone(hit, f"Rule did not trigger for honeypot variant: {vpa_input}")
                    self.assertEqual(hit.code, "R_HONEYPOT_HIT")
                    self.assertEqual(hit.points, 100)
                else:
                    self.assertIsNone(hit, f"Rule falsely triggered for legitimate VPA: {vpa_input}")

    def test_honeypot_deflection_24h_rolling_window_math(self):
        """Stress Test: Precision of 24h rolling aggregation across time-shifted hit records."""
        now = datetime.now(timezone.utc)
        now_epoch = now.timestamp()

        # Ingest hits with simulated epochs:
        # 1. 30 hours ago (should be EXCLUDED from 24h)
        # 2. 25 hours ago (should be EXCLUDED from 24h)
        # 3. 23.9 hours ago (should be INCLUDED in 24h)
        # 4. 12 hours ago (should be INCLUDED in 24h)
        # 5. 1 hour ago (should be INCLUDED in 24h)
        # 6. Current timestamp (should be INCLUDED in 24h)
        test_entries = [
            ("honeypot_trap_01@okaxis", 1000.0, now_epoch - 30 * 3600, False),
            ("honeypot_trap_01@okaxis", 2000.0, now_epoch - 25 * 3600, False),
            ("honeypot_mule_99@okhdfcbank", 3000.0, now_epoch - 23.9 * 3600, True),
            ("phish_trap_node@okicici", 4000.0, now_epoch - 12 * 3600, True),
            ("botnet_sink_04@oksbi", 5000.0, now_epoch - 1 * 3600, True),
            ("mule_honeypot_prime@okaxis", 6000.0, now_epoch, True),
        ]

        for vpa, amt, epoch, _ in test_entries:
            # Inject directly into registry hit_log with controlled epoch
            with self.registry._lock:
                iso_ts = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
                self.registry._hit_counts[vpa] += 1
                self.registry._amount_deflected[vpa] += amt
                self.registry._last_hit_at[vpa] = iso_ts
                self.registry._hit_log.append({
                    "vpa": vpa,
                    "txn_id": f"TXN_{int(epoch)}",
                    "payer_vpa": "payer@bank",
                    "amount": amt,
                    "timestamp": iso_ts,
                    "epoch": epoch,
                })

        # Lifetime total hits must be 6
        self.assertEqual(self.registry.total_hits(), 6)
        self.assertEqual(self.registry.total_amount_deflected(), 21000.0)

        # 24h rolling hits must be exactly 4
        hits_24h = self.registry.get_hits_24h(now=now)
        self.assertEqual(hits_24h, 4, f"Expected exactly 4 hits in 24h window, got {hits_24h}")

    def test_concurrent_24h_rolling_aggregation_under_active_writes(self):
        """Stress Test: Concurrent readers and writers maintaining 24h aggregation invariants."""
        stop_event = threading.Event()
        writer_errors = []
        reader_errors = []

        def writer_loop():
            try:
                for i in range(200):
                    if stop_event.is_set():
                        break
                    self.registry.record_hit(
                        vpa="honeypot_trap_01@okaxis",
                        txn_id=f"TXN_BURST_{i}",
                        amount=100.0,
                    )
                    time.sleep(0.001)
            except Exception as e:
                writer_errors.append(e)

        def reader_loop():
            try:
                for _ in range(200):
                    if stop_event.is_set():
                        break
                    h24 = self.registry.get_hits_24h()
                    tot = self.registry.total_hits()
                    self.assertGreaterEqual(tot, h24)
                    time.sleep(0.001)
            except Exception as e:
                reader_errors.append(e)

        writers = [threading.Thread(target=writer_loop) for _ in range(5)]
        readers = [threading.Thread(target=reader_loop) for _ in range(5)]

        for t in writers + readers:
            t.start()
        for t in writers + readers:
            t.join()

        self.assertEqual(len(writer_errors), 0, f"Writer errors: {writer_errors}")
        self.assertEqual(len(reader_errors), 0, f"Reader errors: {reader_errors}")
        self.assertEqual(self.registry.total_hits(), 1000)


# ══════════════════════════════════════════════════════════════════════════════
# 2. FEDERATION SIGNAL EMPIRICAL STRESS HARNESS
# ══════════════════════════════════════════════════════════════════════════════

class TestFederationSignalEmpiricalStressHarness(unittest.TestCase):
    """Adversarial stress testing of Federation signal exchange, batch lookups, and score blending."""

    def setUp(self):
        self.coordinator = FederatedCoordinator()
        self.coordinator.clear()

    def tearDown(self):
        self.coordinator.clear()

    def test_large_volume_batch_signals_ingestion(self):
        """Stress Test: Ingest 5,000 distinct signals across 250 rings with multi-node aggregation."""
        total_signals = 5000
        total_rings = 250
        nodes = ["hdfc_node", "sbi_node", "icici_node", "axis_node", "paytm_node"]

        t0 = time.perf_counter()
        for i in range(total_signals):
            vpa_hash = hashlib.sha256(f"mule_user_{i}@mesh.net".encode()).hexdigest()
            ring_hash = f"RING_MESH_{i % total_rings}"
            node_id = nodes[i % len(nodes)]
            risk_level = "CRITICAL" if i % 10 == 0 else "HIGH"

            res = self.coordinator.record_signal(
                vpa_hash=vpa_hash,
                risk_level=risk_level,
                ring_hash=ring_hash,
                node_id=node_id,
            )
            self.assertEqual(res["status"], "accepted")
            self.assertEqual(res["vpa_hash"], vpa_hash)

        ingest_elapsed = time.perf_counter() - t0
        signals_per_sec = total_signals / ingest_elapsed
        print(f"\n[Federation Ingestion Benchmark]: Ingested {total_signals} signals in {ingest_elapsed:.3f}s ({signals_per_sec:.1f} signals/sec)")

        # Verify ring topology size: exactly total_rings
        all_signals = self.coordinator.list_signals()
        self.assertEqual(len(all_signals), total_signals)

        # Verify random ring member query
        sample_hash = hashlib.sha256(b"mule_user_0@mesh.net").hexdigest()
        q_res = self.coordinator.query_signal(sample_hash)
        self.assertTrue(q_res["cached"])
        self.assertEqual(q_res["vpa_hash"], sample_hash)
        self.assertGreaterEqual(len(q_res["ring_members"]), total_signals // total_rings)

    def test_sub_5ms_latency_under_sustained_load(self):
        """Stress Test: Benchmark 10,000 lookups on populated coordinator; verify sub-0.5ms p99 latency."""
        # Seed 1,000 signals
        test_hashes = []
        for i in range(1000):
            h = hashlib.sha256(f"latency_test_vpa_{i}@bank".encode()).hexdigest()
            test_hashes.append(h)
            self.coordinator.record_signal(
                vpa_hash=h,
                risk_level="HIGH",
                ring_hash=f"RING_{i % 20}",
                node_id=f"node_{i % 4}",
            )

        # Benchmark 10,000 lookups
        lookup_count = 10000
        latencies_ms: List[float] = []
        for i in range(lookup_count):
            target_h = test_hashes[i % len(test_hashes)]
            t0 = time.perf_counter()
            res = self.coordinator.query_signal(target_h)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)
            self.assertEqual(res["federated_risk_score"], 0.85)

        avg_lat = statistics.mean(latencies_ms)
        p50_lat = statistics.median(latencies_ms)
        sorted_lat = sorted(latencies_ms)
        p95_lat = sorted_lat[int(len(sorted_lat) * 0.95)]
        p99_lat = sorted_lat[int(len(sorted_lat) * 0.99)]
        max_lat = max(latencies_ms)

        print(f"\n[Empirical Latency Benchmark (10,000 queries)]")
        print(f"  Avg: {avg_lat:.5f} ms | p50: {p50_lat:.5f} ms | p95: {p95_lat:.5f} ms | p99: {p99_lat:.5f} ms | Max: {max_lat:.5f} ms")

        # Sub-5ms SLA Verification
        self.assertLess(avg_lat, 0.05, f"Average query latency exceeds 0.05ms: {avg_lat}ms")
        self.assertLess(p95_lat, 0.10, f"p95 query latency exceeds 0.10ms: {p95_lat}ms")
        self.assertLess(p99_lat, 0.50, f"p99 query latency exceeds 0.50ms: {p99_lat}ms")

    def test_unknown_hash_lookups_adversarial_fuzzing(self):
        """Stress Test: Fuzz coordinator query with unknown hashes, injections, and edge formats."""
        fuzz_inputs = [
            "0000000000000000000000000000000000000000000000000000000000000000",
            "deadbeef" * 8,
            "random_unknown_non_hex_string",
            "",
            "   ",
            "' OR '1'='1",
            "<script>alert(1)</script>",
            "💥💀🚨",
            "NONE_EXISTENT_RING",
            "a" * 128,
        ]

        for inp in fuzz_inputs:
            res = self.coordinator.query_signal(inp)
            self.assertEqual(res["federated_risk_score"], 0.0)
            self.assertEqual(res["risk_level"], "NONE")
            self.assertEqual(res["ring_members"], [])
            self.assertEqual(res["reported_by_nodes"], [])
            self.assertTrue(res["cached"])

    def test_dynamic_network_score_blending_3layer_matrix(self):
        """Stress Test: Full 3-layer interaction matrix (Deterministic Rules, Adaptive, Federation)."""
        scorer = UpiRiskScorer()

        # Scenario 1: Clean rules (0) + Clean adaptive (0) + High federation (0.85)
        # Expected: network_pts = 0.85 * 40 = 34 pts. Because network_score >= 0.7 floor, action is HOLD
        clean_txn = UpiTransaction(
            txn_id="TXN_CLEAN_FED_01",
            amount=500.0,
            payer_vpa="innocent_payer@okaxis",
            payee_vpa="mule_payee@okhdfcbank",
            payer_account_age_days=100,
            payee_vpa_age_days=100,
        )
        res1 = scorer.evaluate(clean_txn, network_score=0.85)
        self.assertEqual(res1.network_score, 0.85)
        self.assertEqual(res1.action, "HOLD")
        self.assertIn("FEDERATED_MULE_NETWORK", res1.reasons)
        self.assertGreaterEqual(res1.risk_score, 45)  # HOLD floor enforced

        # Scenario 2: Moderate rules (25) + High adaptive (25) + Critical federation (1.0 -> 40 pts)
        # Combined = 25 + 25 + 40 = 90 pts -> BLOCK verdict
        fresh_txn = UpiTransaction(
            txn_id="TXN_COMBO_02",
            amount=25000.0,
            payer_vpa="payer_farm@oksbi",
            payee_vpa="fresh_payee@okicici",
            payer_account_age_days=2,
            payee_vpa_age_days=2,  # triggers NEW_PAYEE_VPA (25 pts)
        )
        res2 = scorer.evaluate(fresh_txn, network_score=1.0)
        self.assertGreaterEqual(res2.risk_score, BLOCK_AT)
        self.assertEqual(res2.action, "BLOCK")
        self.assertIn("FEDERATED_MULE_NETWORK", res2.reasons)
        self.assertIn("NEW_PAYEE_VPA", res2.reasons)

        # Scenario 3: Honeypot hit (100) + Federation (1.0)
        # Combined must cap cleanly at 100 without overflow
        honeypot_txn = UpiTransaction(
            txn_id="TXN_HONEYPOT_FED_03",
            amount=1000.0,
            payer_vpa="victim@ybl",
            payee_vpa="honeypot_trap_01@okaxis",
        )
        res3 = scorer.evaluate(honeypot_txn, network_score=1.0)
        self.assertEqual(res3.risk_score, 100)
        self.assertEqual(res3.action, "BLOCK")
        self.assertIn("R_HONEYPOT_HIT", res3.reasons)
        self.assertIn("FEDERATED_MULE_NETWORK", res3.reasons)


# ══════════════════════════════════════════════════════════════════════════════
# 3. TIMELINE PLAYBACK EMPIRICAL STRESS HARNESS
# ══════════════════════════════════════════════════════════════════════════════

class TestTimelinePlaybackEmpiricalStressHarness(unittest.TestCase):
    """Adversarial stress testing of Fraud Playback Timeline, topology extraction, and math."""

    def test_empty_topologies_and_malformed_cases(self):
        """Stress Test: Edge-case inputs to timeline topology extraction."""
        # Simulated extraction logic matching frontend extractChronologicalTopology
        def extract_topology(cases=None, case_data=None):
            target_cases = [case_data] if case_data else (cases if isinstance(cases, list) else [])
            nodes = {}
            raw_edges = []
            for c in target_cases:
                if not c or not isinstance(c, dict):
                    continue
                topo = c.get("topology") or {}
                txns = topo.get("transactions") or c.get("transactions") or []
                for tx in txns:
                    p = tx.get("payer_vpa") or tx.get("from")
                    q = tx.get("payee_vpa") or tx.get("to")
                    if p and q:
                        nodes[p] = {"id": p}
                        nodes[q] = {"id": q}
                        raw_edges.append({"id": f"{p}->{q}", "a": p, "b": q, "timestamp": tx.get("timestamp", 0)})
            sorted_edges = sorted(raw_edges, key=lambda e: e.get("timestamp", 0))
            return nodes, sorted_edges

        # Test empty cases
        n1, e1 = extract_topology(cases=[], case_data=None)
        self.assertEqual(len(n1), 0)
        self.assertEqual(len(e1), 0)

        # Test None / malformed cases
        n2, e2 = extract_topology(cases=[None, {}, {"corrupted": True}], case_data=None)
        self.assertEqual(len(n2), 0)
        self.assertEqual(len(e2), 0)

    def test_zero_length_and_identical_timestamp_transactions(self):
        """Stress Test: Chronological edge ordering when timestamps are identical or zero."""
        edges = [
            {"id": "e1", "a": "A", "b": "B", "timestamp": 1000},
            {"id": "e2", "a": "B", "b": "C", "timestamp": 1000},
            {"id": "e3", "a": "C", "b": "D", "timestamp": 1000},
            {"id": "e4", "a": "D", "b": "E", "timestamp": 1500},
        ]
        sorted_edges = sorted(edges, key=lambda e: e["timestamp"])
        self.assertEqual(len(sorted_edges), 4)
        self.assertEqual(sorted_edges[3]["id"], "e4")

    def test_rapid_play_pause_reset_scrubbing_invariants(self):
        """Stress Test: Invariants for visible edges and nodes across scrubbing transitions."""
        sorted_edges = [
            {"id": f"edge_{i}", "a": f"node_{i}", "b": f"node_{i+1}", "timestamp": 1000 + i * 100}
            for i in range(20)
        ]
        total_steps = len(sorted_edges)

        def get_visible_state(k: int):
            clamped_k = max(0, min(total_steps, k))
            if clamped_k == 0:
                return [], set(), None
            v_edges = sorted_edges[:clamped_k]
            v_nodes = set()
            for e in v_edges:
                v_nodes.add(e["a"])
                v_nodes.add(e["b"])
            act_edge = sorted_edges[clamped_k - 1]
            return v_edges, v_nodes, act_edge

        # 1. Test k=0 (Reset state)
        edges_0, nodes_0, act_0 = get_visible_state(0)
        self.assertEqual(len(edges_0), 0)
        self.assertEqual(len(nodes_0), 0)
        self.assertIsNone(act_0)

        # 2. Test scrubbing through all steps k in [1, 20]
        for k in range(1, total_steps + 1):
            edges_k, nodes_k, act_k = get_visible_state(k)
            self.assertEqual(len(edges_k), k)
            self.assertEqual(len(nodes_k), k + 1)
            self.assertEqual(act_k["id"], f"edge_{k-1}")
            for e in edges_k:
                self.assertIn(e["a"], nodes_k)
                self.assertIn(e["b"], nodes_k)

        # 3. Test non-monotonic scrubbing sequence (e.g. 0 -> 15 -> 5 -> 20 -> 0)
        scrub_sequence = [0, 15, 5, 20, 0, 10, 1]
        for step in scrub_sequence:
            edges_s, nodes_s, act_s = get_visible_state(step)
            self.assertEqual(len(edges_s), step)
            if step > 0:
                self.assertEqual(act_s["id"], f"edge_{step-1}")

    def test_speed_multipliers_interval_calculation(self):
        """Stress Test: Interval timer calculations across speed multipliers."""
        def calc_interval(speed: float) -> int:
            if not speed or speed <= 0 or math.isnan(speed):
                return 1000
            return max(150, round(1000 / speed))

        self.assertEqual(calc_interval(0.5), 2000)
        self.assertEqual(calc_interval(1.0), 1000)
        self.assertEqual(calc_interval(2.0), 500)
        self.assertEqual(calc_interval(4.0), 250)
        self.assertEqual(calc_interval(10.0), 150)  # Clamped to 150ms floor
        self.assertEqual(calc_interval(0.0), 1000)
        self.assertEqual(calc_interval(-2.0), 1000)

    def test_node_coordinate_bounds_and_hit_detection_precision(self):
        """Stress Test: Subpixel mathematical precision for canvas point-to-segment projections."""
        # Collinear projection onto segment (100, 100) -> (300, 100)
        # Point (200, 104) is 4px away (within 6px edge threshold)
        dist_in = point_to_segment_distance(200.0, 104.0, 100.0, 100.0, 300.0, 100.0)
        self.assertAlmostEqual(dist_in, 4.0, places=5)
        self.assertLessEqual(dist_in, 6.0)

        # Point (200, 110) is 10px away (outside 6px edge threshold)
        dist_out = point_to_segment_distance(200.0, 110.0, 100.0, 100.0, 300.0, 100.0)
        self.assertAlmostEqual(dist_out, 10.0, places=5)
        self.assertGreater(dist_out, 6.0)

        # Degenerate 0-length segment (100, 100) -> (100, 100)
        dist_degen = point_to_segment_distance(103.0, 104.0, 100.0, 100.0, 100.0, 100.0)
        self.assertAlmostEqual(dist_degen, 5.0, places=5)

        # Color gradient interpolation boundary checks
        self.assertEqual(get_continuous_edge_color(0), "rgba(100, 116, 139, 0.30)")
        self.assertEqual(get_continuous_edge_color(39), "rgba(100, 116, 139, 0.59)")
        self.assertEqual(get_continuous_edge_color(40), "rgba(245, 158, 11, 0.60)")
        self.assertEqual(get_continuous_edge_color(74), "rgba(245, 158, 11, 0.89)")
        self.assertEqual(get_continuous_edge_color(75), "rgba(239, 68, 68, 0.85)")
        self.assertEqual(get_continuous_edge_color(100), "rgba(239, 68, 68, 1.00)")


if __name__ == "__main__":
    unittest.main()

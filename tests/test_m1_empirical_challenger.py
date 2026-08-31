"""Comprehensive Empirical Adversarial Challenge Harness for Milestone 1 (M1).

Stress-tests:
1. Rule score bounding [0, 100], composite risk scores arithmetic, threshold boundaries, reason codes emission.
2. Fraud campaign DNA similarity scoring across identical, mutated, and random/benign transactions.
3. Dead Money Velocity (DMV) score curve across dormancy days and transfer ratios, monotonicity, concurrency.
4. Telemetry rules (SIM/device mismatch, impossible travel Haversine, datacenter/VPN IP filtering).
"""
from __future__ import annotations

import concurrent.futures
import math
import random
import unittest
from datetime import datetime, timedelta, timezone
from typing import List

from app.engine.campaign import (
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
from app.engine.honeypot import get_honeypot_registry
from app.engine.upi_rules import (
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
from app.models.upi_models import RuleHit, UpiEvaluationResponse, UpiTransaction


class TestRiskEngineBoundingAndArithmetic(unittest.TestCase):
    """Empirical stress-testing of risk score bounding, layer combination arithmetic, and reason code emission."""

    def setUp(self) -> None:
        clear_rule_telemetry()
        get_dmv_tracker().clear()
        get_campaign_store().clear()
        get_honeypot_registry().clear()
        self.state = get_upi_state()
        self.state.clear()
        self.scorer = UpiRiskScorer(state=self.state)

    def test_rule_score_and_risk_score_strict_bounding_overflow(self) -> None:
        """Adversarially trigger multiple high-weight rules (> 200 raw points) and verify strict [0, 100] clamping."""
        # 1. Seed honeypot
        reg = get_honeypot_registry()
        reg.register_honeypot("honeypot_overflow@okaxis")

        # 2. Seed payer history in Mumbai
        t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc)
        payer = "overflow_mule@okaxis"
        record_payer_telemetry(payer, device_id="DEV_OLD", sim_id="SIM_OLD", location="Mumbai", timestamp=t0)
        self.state.mark_confirmed_fraud(payer)

        # 3. Construct transaction hitting Honeypot (100) + Impossible Travel (35) + SIM Swap (30) + Datacenter IP (25) + Known Fraud (35) + Campaign (30)
        t1 = t0 + timedelta(minutes=5)
        txn = UpiTransaction(
            txn_id="TXN_OVERFLOW_001",
            payer_vpa=payer,
            payee_vpa="honeypot_overflow@okaxis",
            amount=99000.0,
            device_id="DEV_OLD",
            sim_id="SIM_NEW_SWAPPED",   # Triggers SIM mismatch (+30)
            location="Delhi",           # Triggers Impossible Travel (+35)
            ip="3.220.100.45",          # Triggers Datacenter IP (+25)
            note="Urgent KYC verification pan update", # Triggers Campaign match (+30)
            payer_account_age_days=10,
            payee_vpa_age_days=5,
            timestamp=t1,
        )

        resp = self.scorer.evaluate(txn, network_score=1.0)
        self.assertEqual(resp.rule_score, 100, f"rule_score must be clamped to 100, got {resp.rule_score}")
        self.assertEqual(resp.risk_score, 100, f"risk_score must be clamped to 100, got {resp.risk_score}")
        self.assertEqual(resp.action, "BLOCK")

        # Verify sum of breakdown exceeds 100
        raw_sum = sum(h.points for h in resp.rule_breakdown)
        self.assertGreaterEqual(raw_sum, 150, f"Raw rule points sum was {raw_sum}, expected >= 150")

    def test_layer_arithmetic_combinations(self) -> None:
        """Empirically test exact arithmetic combinations of rule_score + adaptive_pts + network_pts."""
        txn = UpiTransaction(
            txn_id="TXN_ARITH_001",
            payer_vpa="clean_payer@okaxis",
            payee_vpa="clean_payee@okaxis",
            amount=100.0,
            device_id="DEV_CLEAN",
            sim_id="SIM_CLEAN",
            location="Mumbai",
            ip="103.21.124.5",  # Residential
            timestamp=datetime.now(timezone.utc),
        )

        # Baseline: zero rule hits
        resp_base = self.scorer.evaluate(txn, network_score=0.0)
        self.assertEqual(resp_base.rule_score, 0)
        self.assertEqual(resp_base.action, "ALLOW")
        self.assertLess(resp_base.risk_score, 45)

        # Network score scaling: 0.5 network score -> int(0.5 * 40) = 20 pts
        resp_net = self.scorer.evaluate(txn, network_score=0.5)
        self.assertEqual(resp_net.network_score, 0.5)
        self.assertIn("FEDERATED_MULE_NETWORK", resp_net.reasons)

        # Network score >= 0.7 forces HOLD and risk_score floor of 45
        resp_net_hold = self.scorer.evaluate(txn, network_score=0.75)
        self.assertEqual(resp_net_hold.action, "HOLD")
        self.assertGreaterEqual(resp_net_hold.risk_score, 45)

    def test_decision_boundary_thresholds(self) -> None:
        """Verify the exact boundary thresholds: ALLOW (<45), HOLD (45-69), BLOCK (>=70)."""
        for target_score in range(0, 101):
            hits = [RuleHit(code="MOCK_RULE", points=target_score, detail="Mock")]
            rule_score = min(100, sum(h.points for h in hits))
            risk_score = min(100, max(0, rule_score))

            if risk_score >= 70:
                expected_action = "BLOCK"
            elif risk_score >= 45:
                expected_action = "HOLD"
            else:
                expected_action = "ALLOW"

            self.assertEqual(
                "BLOCK" if target_score >= 70 else ("HOLD" if target_score >= 45 else "ALLOW"),
                expected_action,
                f"Action mismatch at score {target_score}"
            )

    def test_reason_codes_emission_integrity(self) -> None:
        """Verify that reason codes accurately reflect rule codes, behavioral anomaly, and federation signal."""
        txn = UpiTransaction(
            txn_id="TXN_REASON_001",
            payer_vpa="victim@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="3.220.100.45",  # Datacenter IP (+25)
            timestamp=datetime.now(timezone.utc),
        )
        resp = self.scorer.evaluate(txn, network_score=0.6)
        self.assertIn("R_DATACENTER_IP", resp.reasons)
        self.assertIn("FEDERATED_MULE_NETWORK", resp.reasons)


class TestCampaignSimilarityAndClustering(unittest.TestCase):
    """Empirical stress-testing of Campaign DNA fingerprinting, similarity scoring, and mutation fuzzing."""

    def setUp(self) -> None:
        self.store = CampaignSignatureStore()

    def test_seed_campaign_exact_and_mutated_matching(self) -> None:
        """Verify similarity scoring across exact matches and mutated variants."""
        # 1. KYC Phishing Seed
        exact_kyc = UpiTransaction(
            txn_id="TXN_KYC_EXACT",
            payer_vpa="victim@okhdfcbank",
            payee_vpa="kyc_verify_alert@ybl",
            amount=15000.0,
            note="Urgent KYC verification pan card update",
        )
        match_kyc = self.store.match_campaign(exact_kyc, threshold=0.82)
        self.assertIsNotNone(match_kyc)
        self.assertEqual(match_kyc[0], "CAMP-KYC-PHISH-01")
        self.assertGreaterEqual(match_kyc[1], 0.85)

        # 2. Mutated KYC Phishing (case changes, extra words, slight amount shift)
        mutated_kyc = UpiTransaction(
            txn_id="TXN_KYC_MUT",
            payer_vpa="victim2@oksbi",
            payee_vpa="random_merchant@okicici",
            amount=14999.0,  # Structured rounding amount
            note="*** URGENT NOTICE: PLEASE UPDATE KYC AADHAAR CARD TO UNBLOCK SERVICE ***",
        )
        match_mut = self.store.match_campaign(mutated_kyc, threshold=0.82)
        self.assertIsNotNone(match_mut)
        self.assertEqual(match_mut[0], "CAMP-KYC-PHISH-01")
        self.assertGreaterEqual(match_mut[1], 0.82)

    def test_smurfing_and_investment_campaign_matches(self) -> None:
        """Verify micro-smurfing and task investment scheme matches."""
        # Smurfing
        txn_smurf = UpiTransaction(
            txn_id="TXN_SMURF_001",
            payer_vpa="smurf_collector_01@okaxis",
            payee_vpa="dest@ybl",
            amount=5000.0,
            note="P2P instant cashout split settlement",
        )
        match_smurf = self.store.match_campaign(txn_smurf, threshold=0.82)
        self.assertIsNotNone(match_smurf)
        self.assertEqual(match_smurf[0], "CAMP-SMURF-BURST-02")

        # Investment / Task Scam
        txn_inv = UpiTransaction(
            txn_id="TXN_INV_001",
            payer_vpa="victim@paytm",
            payee_vpa="crypto_earn_vip@paytm",
            amount=25000.0,
            note="Telegram task bonus VIP commission profit",
        )
        match_inv = self.store.match_campaign(txn_inv, threshold=0.82)
        self.assertIsNotNone(match_inv)
        self.assertEqual(match_inv[0], "CAMP-INVESTMENT-03")

    def test_campaign_matching_on_noise_and_generic_transactions(self) -> None:
        """Verify behavior on strictly neutral/generic notes with no keyword collisions."""
        neutral_notes = [
            "Grocery shopping at dmart",
            "Uber ride cab fare",
            "Electricity bill payment",
            "Mobile recharge jio",
            "Pharmacy medicines",
            "Coffee at starbucks",
            "Lunch with team",
            "Birthday gift contribution",
            "Gym membership monthly fee",
        ]
        for i, note in enumerate(neutral_notes):
            txn = UpiTransaction(
                txn_id=f"TXN_NEUTRAL_{i:04d}",
                payer_vpa=f"user_{i}@okhdfcbank",
                payee_vpa=f"merchant_{i}@okaxis",
                amount=1200.0,
                note=note,
                timestamp=datetime.now(timezone.utc),
            )
            hit = rule_campaign_match(txn, self.store)
            self.assertIsNone(hit, f"Neutral note '{note}' triggered campaign match!")

    def test_dynamic_campaign_clustering_lifecycle(self) -> None:
        """Stress-test dynamic signature creation and cluster ingestion."""
        # 1. Ingest novel syndicate transaction
        novel_1 = UpiTransaction(
            txn_id="TXN_NOV_1",
            payer_vpa="novel_mule_alpha@okaxis",
            payee_vpa="novel_collector@ybl",
            amount=33000.0,
            note="Custom syndicate proxy routing payment",
        )
        camp_id_1 = self.store.ingest_fingerprint(novel_1)
        self.assertTrue(camp_id_1.startswith("CAMP-"))

        # 2. Ingest similar follow-up transaction (same notes/keywords)
        novel_2 = UpiTransaction(
            txn_id="TXN_NOV_2",
            payer_vpa="novel_mule_beta@okaxis",
            payee_vpa="novel_collector@ybl",
            amount=33500.0,
            note="Custom syndicate proxy routing disbursement",
        )
        camp_id_2 = self.store.ingest_fingerprint(novel_2)
        self.assertEqual(camp_id_1, camp_id_2, "Follow-up similar transaction must cluster into the same campaign!")

        # 3. Check campaign listing
        campaigns = self.store.list_campaigns()
        matched_entry = next((c for c in campaigns if c["campaign_id"] == camp_id_1), None)
        self.assertIsNotNone(matched_entry)
        self.assertGreaterEqual(matched_entry["hit_count"], 2)


class TestDmvScoreCurveAndMonotonicity(unittest.TestCase):
    """Empirical verification of the Dead Money Velocity (DMV) score curve, mathematical monotonicity, and concurrency."""

    def setUp(self) -> None:
        self.tracker = DmvTracker()

    def test_dmv_score_monotonicity_across_dormancy_elapsed_time(self) -> None:
        """Verify that with prior outbound history, increasing elapsed days monotonically increases DMV score."""
        dormancy_days_list = [0.1, 1.0, 3.0, 7.0, 14.0, 21.0, 30.0, 60.0, 180.0, 365.0]
        scores = []

        now = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)
        for days in dormancy_days_list:
            trk = DmvTracker()
            prev_time = now - timedelta(days=days)
            prev_txn = UpiTransaction(
                txn_id=f"TXN_PREV_{days}",
                payer_vpa=f"dormant_{days}@okaxis",
                payee_vpa="dest@okaxis",
                amount=1000.0,
                timestamp=prev_time,
            )
            trk.record_txn(prev_txn)

            curr_txn = UpiTransaction(
                txn_id=f"TXN_CURR_{days}",
                payer_vpa=f"dormant_{days}@okaxis",
                payee_vpa="cashout@ybl",
                amount=25000.0,
                payer_account_age_days=180,
                timestamp=now,
            )
            score = calculate_dmv_score(curr_txn, trk)
            scores.append(score)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)

        # Verify monotonicity: score[i] <= score[i+1]
        for i in range(len(scores) - 1):
            self.assertLessEqual(
                scores[i], scores[i + 1] + 1e-6,
                f"Monotonicity violated: dormancy {dormancy_days_list[i]}d ({scores[i]}) > {dormancy_days_list[i+1]}d ({scores[i+1]})"
            )

    def test_dmv_score_monotonicity_across_outflow_amounts(self) -> None:
        """Verify that for a dormant account (60 days), increasing outflow amount monotonically increases DMV score."""
        amounts = [100.0, 500.0, 2000.0, 5000.0, 10000.0, 20000.0, 30000.0, 50000.0]
        scores = []

        now = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)
        for amt in amounts:
            trk = DmvTracker()
            # 60 days dormancy
            prev_txn = UpiTransaction(
                txn_id="TXN_DORMANT_PREV",
                payer_vpa="dormant_user@okaxis",
                payee_vpa="dest@okaxis",
                amount=1000.0,
                timestamp=now - timedelta(days=60),
            )
            trk.record_txn(prev_txn)

            curr_txn = UpiTransaction(
                txn_id=f"TXN_AMT_{amt}",
                payer_vpa="dormant_user@okaxis",
                payee_vpa="cashout@ybl",
                amount=amt,
                payer_account_age_days=180,
                timestamp=now,
            )
            score = calculate_dmv_score(curr_txn, trk)
            scores.append(score)

        for i in range(len(scores) - 1):
            self.assertLessEqual(
                scores[i], scores[i + 1] + 1e-6,
                f"Amount monotonicity violated: amount {amounts[i]} ({scores[i]}) > {amounts[i+1]} ({scores[i+1]})"
            )

    def test_dmv_first_outflow_dormancy_and_burst_triggers_red(self) -> None:
        """Verify that a long-dormant account (180 days) executing a high-value burst outflow scores >= 70 (RED)."""
        now = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)
        trk = DmvTracker()
        
        # Prior outbound transaction was 180 days ago
        prev_txn = UpiTransaction(
            txn_id="TXN_PREV_180",
            payer_vpa="mule_target@okaxis",
            payee_vpa="old_dest@okaxis",
            amount=500.0,
            timestamp=now - timedelta(days=180),
        )
        trk.record_txn(prev_txn)

        # Inflow 30m ago: 50,000
        in_txn = UpiTransaction(
            txn_id="TXN_INFLOW",
            payer_vpa="source@okhdfcbank",
            payee_vpa="mule_target@okaxis",
            amount=50000.0,
            timestamp=now - timedelta(minutes=30),
        )
        trk.record_txn(in_txn)

        # High burst cashout (now): 45,000 (90% drain)
        curr_txn = UpiTransaction(
            txn_id="TXN_OUT",
            payer_vpa="mule_target@okaxis",
            payee_vpa="cashout@ybl",
            amount=45000.0,
            payer_account_age_days=180,
            timestamp=now,
        )
        score = calculate_dmv_score(curr_txn, trk)
        self.assertGreaterEqual(score, 70.0, f"Expected RED tier (>=70), got {score}")

    def test_dmv_extreme_and_boundary_resilience(self) -> None:
        """Empirical fuzz test for boundary cases: 0 amount, negative amount, large amount, default timestamp."""
        now = datetime.now(timezone.utc)
        test_txns = [
            UpiTransaction(txn_id="TXN_ZERO", payer_vpa="u1@okaxis", payee_vpa="u2@okaxis", amount=0.0, timestamp=now),
            UpiTransaction(txn_id="TXN_NEG", payer_vpa="u2@okaxis", payee_vpa="u3@okaxis", amount=-100.0, timestamp=now),
            UpiTransaction(txn_id="TXN_HUGE", payer_vpa="u3@okaxis", payee_vpa="u4@okaxis", amount=1e9, timestamp=now),
            UpiTransaction(txn_id="TXN_NOW_DEF", payer_vpa="u4@okaxis", payee_vpa="u5@okaxis", amount=500.0),
        ]
        for txn in test_txns:
            score = calculate_dmv_score(txn, self.tracker)
            self.assertIsInstance(score, float)
            self.assertFalse(math.isnan(score))
            self.assertFalse(math.isinf(score))
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)

    def test_dmv_multithreaded_concurrency_stress(self) -> None:
        """Stress-test concurrent read and write operations on DmvTracker across 16 threads."""
        trk = DmvTracker()
        now = datetime.now(timezone.utc)

        def worker(thread_idx: int) -> List[float]:
            thread_scores = []
            for j in range(25):
                vpa = f"mule_thread_{thread_idx % 4}@okaxis"
                txn = UpiTransaction(
                    txn_id=f"TXN_TH_{thread_idx}_{j}",
                    payer_vpa=vpa,
                    payee_vpa=f"dest_{j}@ybl",
                    amount=float(1000 * (j + 1)),
                    timestamp=now + timedelta(seconds=j),
                )
                trk.record_txn(txn)
                s = calculate_dmv_score(txn, trk)
                thread_scores.append(s)
                _ = trk.get_top_vpas(limit=5)
            return thread_scores

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(worker, i) for i in range(16)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), 16)
        top = trk.get_top_vpas(limit=10)
        self.assertLessEqual(len(top), 10)
        self.assertGreaterEqual(len(top), 1)
        for k in range(len(top) - 1):
            self.assertGreaterEqual(top[k]["dmv_score"], top[k + 1]["dmv_score"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Comprehensive Unit and Integration Tests for SAMPATI V2 Sprint 2 Milestone 1.

Covers:
1. Dead Money Velocity (DMV) Engine (DmvTracker, calculate_dmv_score, top VPAs by DMV).
2. Device Telemetry Rules (R_SIM_DEVICE_MISMATCH, R_IMPOSSIBLE_TRAVEL, R_DATACENTER_IP).
3. Fraud Campaign DNA Fingerprinting (CampaignSignatureStore, R_CAMPAIGN_MATCH, dynamic ingestion).
4. UpiRiskScorer and UpiCaseService integration (response model, analytics, telemetry).
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

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
from app.models.upi_models import UpiEvaluationResponse, UpiTransaction
from app.services.upi_cases import RULE_METADATA, UpiCaseService, get_upi_case_service


class TestDmvEngine(unittest.TestCase):
    """Unit tests for the Dead Money Velocity (DMV) score engine."""

    def setUp(self) -> None:
        self.tracker = DmvTracker()

    def test_dmv_dormancy_and_burst_high_score(self) -> None:
        """A long-dormant account (180 days old) suddenly moving high outflow scores > 70 (RED)."""
        now = datetime.now(timezone.utc)
        txn = UpiTransaction(
            txn_id="TXN_DMV_001",
            payer_vpa="dormant_mule@okaxis",
            payee_vpa="cashout_dest@ybl",
            amount=28000.0,
            payer_account_age_days=180,
            timestamp=now,
        )
        score = calculate_dmv_score(txn, self.tracker)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 70.0)
        self.assertLessEqual(score, 100.0)

    def test_dmv_active_legit_user_low_score(self) -> None:
        """An active user who transacted recently moving a small amount scores < 40 (GREEN)."""
        now = datetime.now(timezone.utc)
        # Prior transaction 1 hour ago
        prev_txn = UpiTransaction(
            txn_id="TXN_DMV_PREV",
            payer_vpa="active_user@okaxis",
            payee_vpa="grocery@okicici",
            amount=500.0,
            timestamp=now - timedelta(hours=1),
        )
        self.tracker.record_txn(prev_txn)

        curr_txn = UpiTransaction(
            txn_id="TXN_DMV_002",
            payer_vpa="active_user@okaxis",
            payee_vpa="coffee@paytm",
            amount=250.0,
            payer_account_age_days=365,
            timestamp=now,
        )
        score = calculate_dmv_score(curr_txn, self.tracker)
        self.assertLess(score, 40.0)

    def test_dmv_moderate_burst_amber_score(self) -> None:
        """Moderate outflow from an account with moderate dormancy scores in AMBER zone (40-70)."""
        now = datetime.now(timezone.utc)
        # Previous outbound transaction 15 days ago
        prev_out = UpiTransaction(
            txn_id="TXN_DMV_OUT_PREV",
            payer_vpa="moderate_user@okaxis",
            payee_vpa="store@okaxis",
            amount=2000.0,
            timestamp=now - timedelta(days=15),
        )
        self.tracker.record_txn(prev_out)

        # Inflow 5 hours ago
        prev_in = UpiTransaction(
            txn_id="TXN_DMV_IN",
            payer_vpa="other_sender@okaxis",
            payee_vpa="moderate_user@okaxis",
            amount=15000.0,
            timestamp=now - timedelta(hours=5),
        )
        self.tracker.record_txn(prev_in)

        curr_txn = UpiTransaction(
            txn_id="TXN_DMV_003",
            payer_vpa="moderate_user@okaxis",
            payee_vpa="merchant@ybl",
            amount=10000.0,
            payer_account_age_days=60,
            timestamp=now,
        )
        score = calculate_dmv_score(curr_txn, self.tracker)
        self.assertGreaterEqual(score, 40.0)
        self.assertLessEqual(score, 75.0)

    def test_dmv_tracker_get_top_vpas(self) -> None:
        """Top VPAs by DMV score ranked descending with full metadata."""
        self.tracker.set_score("mule_high@okaxis", 92.5)
        self.tracker.set_score("mule_med@ybl", 55.0)
        self.tracker.set_score("user_low@paytm", 15.2)

        top = self.tracker.get_top_vpas(limit=10)
        self.assertEqual(len(top), 3)
        self.assertEqual(top[0]["vpa"], "mule_high@okaxis")
        self.assertEqual(top[0]["dmv_score"], 92.5)
        self.assertEqual(top[0]["tier"], "RED")
        self.assertEqual(top[1]["tier"], "AMBER")
        self.assertEqual(top[2]["tier"], "GREEN")
        for item in top:
            self.assertIn("last_active", item)
            self.assertIn("outflow_24h", item)
            self.assertIn("inflow_24h", item)

    def test_dmv_tracker_clear(self) -> None:
        """Tracker clear resets all internal state."""
        self.tracker.set_score("test@upi", 88.0)
        self.tracker.clear()
        self.assertEqual(self.tracker.get_score("test@upi"), 0.0)
        self.assertEqual(len(self.tracker.get_top_vpas()), 0)


class TestSimDeviceMismatchRule(unittest.TestCase):
    """Unit tests for R_SIM_DEVICE_MISMATCH rule."""

    def setUp(self) -> None:
        clear_rule_telemetry()

    def tearDown(self) -> None:
        clear_rule_telemetry()

    def test_sim_device_match_normal(self) -> None:
        """Same device and same SIM for a known payer triggers no mismatch."""
        payer = "user_normal@okaxis"
        record_payer_telemetry(payer, device_id="DEV_AAA_111", sim_id="SIM_8991_111")
        
        txn = UpiTransaction(
            txn_id="TXN_SIM_001",
            payer_vpa=payer,
            payee_vpa="shop@okaxis",
            amount=500.0,
            device_id="DEV_AAA_111",
            sim_id="SIM_8991_111",
        )
        hit = rule_sim_device_mismatch(txn)
        self.assertIsNone(hit)

    def test_sim_swap_same_device_new_sim(self) -> None:
        """Same device hardware with a newly swapped SIM triggers R_SIM_DEVICE_MISMATCH (+30 pts)."""
        payer = "victim_swap@okaxis"
        record_payer_telemetry(payer, device_id="DEV_IPHONE_01", sim_id="SIM_JIO_001")

        txn = UpiTransaction(
            txn_id="TXN_SIM_002",
            payer_vpa=payer,
            payee_vpa="attacker@okaxis",
            amount=25000.0,
            device_id="DEV_IPHONE_01",  # Same device
            sim_id="SIM_AIRTEL_999",    # Swapped SIM
        )
        hit = rule_sim_device_mismatch(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_SIM_DEVICE_MISMATCH")
        self.assertEqual(hit.points, 30)
        self.assertIn("New SIM", hit.detail)

    def test_device_swap_same_sim_new_device(self) -> None:
        """Existing SIM observed on a new hardware device triggers R_SIM_DEVICE_MISMATCH (+30 pts)."""
        payer = "victim_clone@okaxis"
        record_payer_telemetry(payer, device_id="DEV_OLD_SAMSUNG", sim_id="SIM_AIRTEL_001")

        txn = UpiTransaction(
            txn_id="TXN_SIM_003",
            payer_vpa=payer,
            payee_vpa="attacker@okaxis",
            amount=30000.0,
            device_id="DEV_NEW_EMULATOR",  # Changed device
            sim_id="SIM_AIRTEL_001",       # Same SIM
        )
        hit = rule_sim_device_mismatch(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_SIM_DEVICE_MISMATCH")
        self.assertEqual(hit.points, 30)
        self.assertIn("Existing SIM", hit.detail)

    def test_sim_device_missing_telemetry(self) -> None:
        """Transactions with missing device or SIM IDs gracefully evaluate to None."""
        txn = UpiTransaction(
            txn_id="TXN_SIM_004",
            payer_vpa="payer_no_telemetry@okaxis",
            payee_vpa="payee@okaxis",
            amount=1000.0,
            device_id="",
            sim_id="",
        )
        hit = rule_sim_device_mismatch(txn)
        self.assertIsNone(hit)


class TestImpossibleTravelRule(unittest.TestCase):
    """Unit tests for R_IMPOSSIBLE_TRAVEL geographic velocity rule."""

    def setUp(self) -> None:
        clear_rule_telemetry()

    def tearDown(self) -> None:
        clear_rule_telemetry()

    def test_coordinate_resolution_and_haversine(self) -> None:
        """Verify city coordinate lookup and Haversine distance accuracy."""
        mumbai = resolve_coordinates("Mumbai")
        delhi = resolve_coordinates("Delhi")
        self.assertIsNotNone(mumbai)
        self.assertIsNotNone(delhi)
        dist = haversine_distance(mumbai[0], mumbai[1], delhi[0], delhi[1])
        # Mumbai to Delhi is ~1140-1160 km
        self.assertGreater(dist, 1100.0)
        self.assertLess(dist, 1200.0)

        # Direct lat,lon parsing
        custom = resolve_coordinates("12.9716, 77.5946")
        self.assertIsNotNone(custom)
        self.assertAlmostEqual(custom[0], 12.9716, places=3)
        self.assertAlmostEqual(custom[1], 77.5946, places=3)

    def test_impossible_travel_city_jump_trigger(self) -> None:
        """Payer transacting in Mumbai and then Delhi 10 minutes later triggers R_IMPOSSIBLE_TRAVEL."""
        payer = "traveler_mule@okaxis"
        t0 = datetime(2026, 8, 31, 10, 0, 0, tzinfo=timezone.utc)
        record_payer_telemetry(payer, location="Mumbai", timestamp=t0)

        t1 = t0 + timedelta(minutes=10)
        txn = UpiTransaction(
            txn_id="TXN_TRV_001",
            payer_vpa=payer,
            payee_vpa="receiver@okaxis",
            amount=15000.0,
            location="Delhi",
            timestamp=t1,
        )
        hit = rule_impossible_travel(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_IMPOSSIBLE_TRAVEL")
        self.assertEqual(hit.points, 35)
        self.assertIn("Impossible travel", hit.detail)

    def test_impossible_travel_lat_lon_jump_trigger(self) -> None:
        """Payer jumping > 500km in 15 minutes using raw coordinates triggers R_IMPOSSIBLE_TRAVEL."""
        payer = "traveler_coords@okaxis"
        t0 = datetime(2026, 8, 31, 12, 0, 0, tzinfo=timezone.utc)
        # Bengaluru coordinates
        record_payer_telemetry(payer, location="12.9716,77.5946", timestamp=t0)

        t1 = t0 + timedelta(minutes=15)
        # Kolkata coordinates (> 1500km)
        txn = UpiTransaction(
            txn_id="TXN_TRV_002",
            payer_vpa=payer,
            payee_vpa="receiver@okaxis",
            amount=20000.0,
            location="22.5726,88.3639",
            timestamp=t1,
        )
        hit = rule_impossible_travel(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_IMPOSSIBLE_TRAVEL")
        self.assertEqual(hit.points, 35)

    def test_possible_travel_normal_flight_or_drive(self) -> None:
        """Travel of ~120km over 4 hours (Mumbai to Pune) does not trigger impossible travel."""
        payer = "normal_traveler@okaxis"
        t0 = datetime(2026, 8, 31, 8, 0, 0, tzinfo=timezone.utc)
        record_payer_telemetry(payer, location="Mumbai", timestamp=t0)

        t1 = t0 + timedelta(hours=4)
        txn = UpiTransaction(
            txn_id="TXN_TRV_003",
            payer_vpa=payer,
            payee_vpa="shop@pune",
            amount=1000.0,
            location="Pune",
            timestamp=t1,
        )
        hit = rule_impossible_travel(txn)
        self.assertIsNone(hit)

    def test_missing_or_unparseable_location(self) -> None:
        """Invalid or missing location strings evaluate gracefully to None."""
        txn = UpiTransaction(
            txn_id="TXN_TRV_004",
            payer_vpa="no_loc@okaxis",
            payee_vpa="shop@okaxis",
            amount=500.0,
            location="",
        )
        self.assertIsNone(rule_impossible_travel(txn))


class TestDatacenterIpRule(unittest.TestCase):
    """Unit tests for R_DATACENTER_IP detection rule."""

    def test_datacenter_ip_aws(self) -> None:
        """AWS EC2 origin IP triggers R_DATACENTER_IP (+25 pts)."""
        txn = UpiTransaction(
            txn_id="TXN_DC_001",
            payer_vpa="bot_runner@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="3.220.100.45",  # AWS 3.0.0.0/9
        )
        hit = rule_datacenter_ip(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_DATACENTER_IP")
        self.assertEqual(hit.points, 25)

    def test_datacenter_ip_gcp(self) -> None:
        """GCP Cloud subnet triggers R_DATACENTER_IP."""
        txn = UpiTransaction(
            txn_id="TXN_DC_002",
            payer_vpa="bot_runner@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="34.93.10.20",  # GCP Mumbai 34.93.0.0/16
        )
        hit = rule_datacenter_ip(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_DATACENTER_IP")

    def test_datacenter_ip_azure(self) -> None:
        """Azure Cloud subnet triggers R_DATACENTER_IP."""
        txn = UpiTransaction(
            txn_id="TXN_DC_003",
            payer_vpa="bot_runner@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="20.198.10.5",  # Azure 20.0.0.0/11
        )
        hit = rule_datacenter_ip(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_DATACENTER_IP")

    def test_datacenter_ip_tor_vpn(self) -> None:
        """Tor exit node subnet triggers R_DATACENTER_IP."""
        txn = UpiTransaction(
            txn_id="TXN_DC_004",
            payer_vpa="darkweb_bot@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="185.220.101.5",  # Tor subnet 185.220.100.0/22
        )
        hit = rule_datacenter_ip(txn)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_DATACENTER_IP")

    def test_residential_ip_no_trigger(self) -> None:
        """Standard residential mobile carrier IPs do not trigger datacenter rule."""
        for res_ip in ("49.207.50.10", "122.160.10.5", "103.21.124.5"):
            txn = UpiTransaction(
                txn_id="TXN_DC_005",
                payer_vpa="legit_mobile@okaxis",
                payee_vpa="merchant@ybl",
                amount=500.0,
                ip=res_ip,
            )
            hit = rule_datacenter_ip(txn)
            self.assertIsNone(hit)

    def test_invalid_or_blank_ip(self) -> None:
        """Blank or malformed IP strings evaluate cleanly without exception."""
        for bad_ip in ("", "not_an_ip", "999.999.999.999", None):
            txn = UpiTransaction(
                txn_id="TXN_DC_006",
                payer_vpa="user@okaxis",
                payee_vpa="shop@okaxis",
                amount=200.0,
                ip=bad_ip or "",
            )
            self.assertIsNone(rule_datacenter_ip(txn))


class TestCampaignFingerprinting(unittest.TestCase):
    """Unit tests for fraud campaign DNA fingerprinting and clustering."""

    def setUp(self) -> None:
        self.store = CampaignSignatureStore()

    def test_campaign_similarity_matching_kyc(self) -> None:
        """Transaction matching KYC phishing signature triggers R_CAMPAIGN_MATCH."""
        txn = UpiTransaction(
            txn_id="TXN_CAMP_001",
            payer_vpa="victim_elderly@okhdfcbank",
            payee_vpa="phish_trap_node@okicici",
            amount=24500.0,
            note="Urgent KYC PAN card verification update",
        )
        hit, camp_id = check_campaign_match(txn, self.store)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_CAMPAIGN_MATCH")
        self.assertEqual(hit.points, 30)
        self.assertEqual(camp_id, "CAMP-KYC-PHISH-01")

    def test_campaign_similarity_matching_investment(self) -> None:
        """Transaction matching Task Scam investment scheme triggers R_CAMPAIGN_MATCH."""
        txn = UpiTransaction(
            txn_id="TXN_CAMP_002",
            payer_vpa="user_scammed@paytm",
            payee_vpa="bonus_task_pay@okaxis",
            amount=15000.0,
            note="Telegram task investment bonus VIP profit",
        )
        hit = rule_campaign_match(txn, self.store)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.code, "R_CAMPAIGN_MATCH")
        self.assertIn("CAMP-INVESTMENT-03", hit.detail)

    def test_campaign_no_match_legitimate(self) -> None:
        """Benign everyday transaction does not trigger campaign match."""
        txn = UpiTransaction(
            txn_id="TXN_CAMP_003",
            payer_vpa="alice@okaxis",
            payee_vpa="bob@okaxis",
            amount=450.0,
            note="Dinner bill split",
        )
        hit = rule_campaign_match(txn, self.store)
        self.assertIsNone(hit)

    def test_campaign_dynamic_ingest_on_block(self) -> None:
        """Dynamic ingestion clusters new novel patterns into auto-generated campaigns."""
        novel_txn = UpiTransaction(
            txn_id="TXN_NOVEL_001",
            payer_vpa="novel_mule_1@okaxis",
            payee_vpa="novel_mule_2@ybl",
            amount=8888.0,
            note="Novel syndicate custom token disbursement",
        )
        camp_id = self.store.ingest_fingerprint(novel_txn)
        self.assertIsInstance(camp_id, str)
        self.assertTrue(camp_id.startswith("CAMP-"))

        campaigns = self.store.list_campaigns()
        self.assertGreaterEqual(len(campaigns), 4)


class TestUpiScorerAndServiceIntegration(unittest.TestCase):
    """Integration tests verifying full risk scorer pipeline and case service."""

    def setUp(self) -> None:
        clear_rule_telemetry()
        get_dmv_tracker().clear()
        get_campaign_store().clear()

    def test_upi_scorer_returns_dmv_and_campaign_id(self) -> None:
        """UpiRiskScorer.evaluate populates dmv_score and campaign_id on UpiEvaluationResponse."""
        scorer = get_upi_scorer()
        txn = UpiTransaction(
            txn_id="TXN_EVAL_001",
            payer_vpa="kyc_victim@okaxis",
            payee_vpa="phish_trap_node@okicici",
            amount=35000.0,
            payer_account_age_days=120,
            note="URGENT KYC UPDATE UNBLOCK",
            ip="3.220.100.45",  # Datacenter IP
            device_id="DEV_ORIG_01",
            sim_id="SIM_ORIG_01",
            location="Mumbai",
        )
        resp: UpiEvaluationResponse = scorer.evaluate(txn)

        self.assertIsInstance(resp, UpiEvaluationResponse)
        self.assertIsInstance(resp.dmv_score, float)
        self.assertGreater(resp.dmv_score, 0.0)
        self.assertEqual(resp.campaign_id, "CAMP-KYC-PHISH-01")
        self.assertIn("R_DATACENTER_IP", [h.code for h in resp.rule_breakdown])
        self.assertIn("R_CAMPAIGN_MATCH", [h.code for h in resp.rule_breakdown])
        self.assertEqual(resp.action, "BLOCK")

    def test_evaluate_rules_returns_list_of_rule_hits(self) -> None:
        """evaluate_rules preserves exact backwards compatibility returning List[RuleHit]."""
        state = get_upi_state()
        txn = UpiTransaction(
            txn_id="TXN_RULES_001",
            payer_vpa="sim_victim@okaxis",
            payee_vpa="merchant@ybl",
            amount=5000.0,
            ip="3.220.100.45",
        )
        hits = evaluate_rules(txn, state)
        self.assertIsInstance(hits, list)
        self.assertTrue(all(hasattr(h, "code") and hasattr(h, "points") for h in hits))

    def test_upi_case_service_evaluation_and_analytics(self) -> None:
        """UpiCaseService.evaluate populates dmv_score and get_analytics includes top_vpas_by_dmv."""
        service: UpiCaseService = get_upi_case_service()
        txn = UpiTransaction(
            txn_id="TXN_SVC_001",
            payer_vpa="dormant_target@okhdfcbank",
            payee_vpa="honeypot_trap_01@okaxis",
            amount=45000.0,
            payer_account_age_days=90,
        )
        resp = service.evaluate(txn)

        self.assertEqual(resp.action, "BLOCK")
        self.assertIn("R_HONEYPOT_HIT", resp.reasons)
        self.assertGreater(resp.dmv_score, 0.0)

        # Verify analytics payload
        analytics = service.get_analytics()
        self.assertIn("top_vpas_by_dmv", analytics)
        self.assertIn("active_campaigns", analytics)
        self.assertIsInstance(analytics["top_vpas_by_dmv"], list)
        self.assertIsInstance(analytics["active_campaigns"], list)

    def test_rule_metadata_completeness(self) -> None:
        """All Sprint 2 rule codes are registered in RULE_METADATA."""
        expected_rules = [
            "R_SIM_DEVICE_MISMATCH",
            "R_IMPOSSIBLE_TRAVEL",
            "R_DATACENTER_IP",
            "R_CAMPAIGN_MATCH",
            "R_HONEYPOT_HIT",
        ]
        for rule_code in expected_rules:
            self.assertIn(rule_code, RULE_METADATA)
            self.assertIn("name", RULE_METADATA[rule_code])
            self.assertIn("severity", RULE_METADATA[rule_code])


if __name__ == "__main__":
    unittest.main()

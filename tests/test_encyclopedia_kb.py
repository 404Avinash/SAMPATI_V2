"""Comprehensive Unit Test Suite for Encyclopedia Knowledge Base (`app/engine/encyclopedia_kb.py`).

Verifies:
1. Retrieval of all 19 canonical rule explanations and mathematical definitions.
2. Case-insensitive alias normalization (e.g., 'dmv', 'DMV', 'mule', 'structuring', 'ewma', etc.).
3. Resilient fallback for unknown, empty, or malformed rule codes.
4. Scalar metric interpolation (e.g., value=0.92, value=82.5, value=49990).
5. Rich context dictionary interpolation (inflow, outflow, speed_kmh, distance, device IDs).
6. Markdown prompt context builder layout (summary table + detailed algorithmic breakdowns).
7. Pydantic `RuleHit` object compatibility and deduplication.
8. In-memory keyword and conceptual search precision, scoring, and limit handling.
9. Resilience against NaN, Inf, None, empty lists, and invalid types.
10. Sub-millisecond performance benchmark (< 1ms per context build).
"""
from __future__ import annotations

import math
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.engine.encyclopedia_kb import (
    RULE_DEFINITIONS,
    build_case_encyclopedia_context,
    get_all_rule_codes,
    get_all_rule_definitions,
    get_rule_explanation,
    normalize_rule_code,
    search_encyclopedia,
)
from app.models.upi_models import RuleHit


class TestEncyclopediaKB(unittest.TestCase):
    """Unit test suite for Encyclopedia Knowledge Base with 30+ comprehensive test cases."""

    # ── Group 1: Canonical Rule Inventory & Schema ────────────────────────────

    def test_canonical_rule_coverage(self):
        """Verify all core platform rules exist and return required dictionary schema."""
        expected_rules = [
            "DMV_RAPID_DRAIN",
            "R_HONEYPOT_HIT",
            "R_SIM_DEVICE_MISMATCH",
            "R_IMPOSSIBLE_TRAVEL",
            "R_DATACENTER_IP",
            "R_CAMPAIGN_MATCH",
            "PASS_THROUGH_CONDUIT",
            "FAN_IN_BURST",
            "FAN_OUT_DISPERSAL",
            "DEVICE_FARM",
            "NEW_ACCOUNT_HIGH_VALUE",
            "LIMIT_SKIRTING",
            "NEW_PAYEE_VPA",
            "KNOWN_FRAUD_ENTITY",
            "BEHAVIORAL_ANOMALY",
            "FEDERATED_MULE_NETWORK",
            "DPIP_BLACKLIST",
            "GINI_INEQUALITY",
            "GRAPH_ML_ROLE",
        ]

        indexed_codes = get_all_rule_codes()
        self.assertGreaterEqual(len(indexed_codes), 19)

        for rule in expected_rules:
            self.assertIn(rule, indexed_codes, f"Rule '{rule}' missing from encyclopedia index")
            exp = get_rule_explanation(rule)
            self.assertIsInstance(exp, dict)
            self.assertEqual(exp["rule_code"], rule)
            self.assertTrue(len(exp["name"]) > 3)
            self.assertTrue(len(exp["mathematical_definition"]) > 5)
            self.assertTrue(len(exp["plain_english_explanation"]) > 10)
            self.assertIn(exp["severity"], ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"])
            self.assertIsInstance(exp["default_points"], int)
            self.assertIn("regulatory_typology", exp)
            self.assertIn("recommended_action", exp)
            self.assertIn("detection_mechanism", exp)

    def test_get_all_rule_definitions(self):
        """Verify get_all_rule_definitions returns complete rule definitions list."""
        defs = get_all_rule_definitions()
        self.assertIsInstance(defs, list)
        self.assertEqual(len(defs), len(RULE_DEFINITIONS))
        for d in defs:
            self.assertIn("canonical_code", d)
            self.assertIn("name", d)
            self.assertIn("mathematical_definition", d)
            self.assertIn("plain_english_explanation", d)
            self.assertIn("category", d)

    def test_get_all_rule_codes(self):
        """Verify get_all_rule_codes returns sorted or full list of canonical codes."""
        codes = get_all_rule_codes()
        self.assertIsInstance(codes, list)
        self.assertEqual(len(codes), len(RULE_DEFINITIONS))
        self.assertIn("DMV_RAPID_DRAIN", codes)
        self.assertIn("R_HONEYPOT_HIT", codes)

    # ── Group 2: Alias Normalization Matrix ───────────────────────────────────

    def test_alias_normalization_dmv(self):
        """Verify DMV rule variants normalize to DMV_RAPID_DRAIN."""
        for code in ["dmv", "DMV", "RULE_DMV_VELOCITY", "dead_money_velocity", "DMV_BURST", "DEAD_MONEY"]:
            self.assertEqual(normalize_rule_code(code), "DMV_RAPID_DRAIN")

    def test_alias_normalization_honeypot(self):
        """Verify Honeypot rule variants normalize to R_HONEYPOT_HIT."""
        for code in ["honeypot", "HONEYPOT", "r_honeypot_hit", "synthetic_trap", "HONEYPOT_TRAP", "HONEYPOT_PROBE"]:
            self.assertEqual(normalize_rule_code(code), "R_HONEYPOT_HIT")

    def test_alias_normalization_sim_device(self):
        """Verify SIM/Device mismatch variants normalize to R_SIM_DEVICE_MISMATCH."""
        for code in ["sim_swap", "SIM_SWAP", "device_mismatch", "sim_device_mismatch", "TELEMETRY_MISMATCH"]:
            self.assertEqual(normalize_rule_code(code), "R_SIM_DEVICE_MISMATCH")

    def test_alias_normalization_travel(self):
        """Verify Travel velocity variants normalize to R_IMPOSSIBLE_TRAVEL."""
        for code in ["impossible_travel", "TRAVEL_VELOCITY", "GEO_VELOCITY", "travel_speed", "geo_jump"]:
            self.assertEqual(normalize_rule_code(code), "R_IMPOSSIBLE_TRAVEL")

    def test_alias_normalization_datacenter(self):
        """Verify Datacenter/VPN variants normalize to R_DATACENTER_IP."""
        for code in ["datacenter_ip", "VPN_IP", "tor_ip", "cloud_ip", "DATACENTER_ORIGIN", "datacenter"]:
            self.assertEqual(normalize_rule_code(code), "R_DATACENTER_IP")

    def test_alias_normalization_campaign(self):
        """Verify Campaign DNA variants normalize to R_CAMPAIGN_MATCH."""
        for code in ["campaign_dna", "CAMPAIGN_MATCH", "fraud_campaign", "campaign_fingerprint", "campaign"]:
            self.assertEqual(normalize_rule_code(code), "R_CAMPAIGN_MATCH")

    def test_alias_normalization_conduit_and_flows(self):
        """Verify Flow and conduit variants normalize properly."""
        self.assertEqual(normalize_rule_code("conduit"), "PASS_THROUGH_CONDUIT")
        self.assertEqual(normalize_rule_code("pass_through"), "PASS_THROUGH_CONDUIT")
        self.assertEqual(normalize_rule_code("fan_in"), "FAN_IN_BURST")
        self.assertEqual(normalize_rule_code("collector_hub"), "FAN_IN_BURST")
        self.assertEqual(normalize_rule_code("fan_out"), "FAN_OUT_DISPERSAL")
        self.assertEqual(normalize_rule_code("cashout_dispersal"), "FAN_OUT_DISPERSAL")
        self.assertEqual(normalize_rule_code("device_farm"), "DEVICE_FARM")
        self.assertEqual(normalize_rule_code("mule_farm"), "DEVICE_FARM")

    def test_alias_normalization_structuring(self):
        """Verify Structuring / Smurfing variants normalize to LIMIT_SKIRTING."""
        for code in ["structuring", "smurfing", "structuring_burst", "caution_threshold", "limit_skirting"]:
            self.assertEqual(normalize_rule_code(code), "LIMIT_SKIRTING")

    def test_alias_normalization_federation_and_dpip(self):
        """Verify Federation and DPIP variants normalize properly."""
        self.assertEqual(normalize_rule_code("mule"), "FEDERATED_MULE_NETWORK")
        self.assertEqual(normalize_rule_code("mule_ring"), "FEDERATED_MULE_NETWORK")
        self.assertEqual(normalize_rule_code("federation_risk"), "FEDERATED_MULE_NETWORK")
        self.assertEqual(normalize_rule_code("dpip_feed"), "DPIP_BLACKLIST")
        self.assertEqual(normalize_rule_code("dpip_intelligence"), "DPIP_BLACKLIST")
        self.assertEqual(normalize_rule_code("dpip"), "DPIP_BLACKLIST")

    def test_alias_normalization_gini_and_graph(self):
        """Verify Gini and Graph ML variants normalize properly."""
        self.assertEqual(normalize_rule_code("gini"), "GINI_INEQUALITY")
        self.assertEqual(normalize_rule_code("gini_coefficient"), "GINI_INEQUALITY")
        self.assertEqual(normalize_rule_code("node_role"), "GRAPH_ML_ROLE")
        self.assertEqual(normalize_rule_code("graph_role_classification"), "GRAPH_ML_ROLE")
        self.assertEqual(normalize_rule_code("graph_ml"), "GRAPH_ML_ROLE")

    # ── Group 3: Fallback & Edge Case Normalization ───────────────────────────

    def test_unknown_rule_fallback_preserves_code(self):
        """Verify unindexed custom rule codes return valid fallback without crashing."""
        exp = get_rule_explanation("CUSTOM_EXPERIMENTAL_RULE_XYZ")
        self.assertEqual(exp["rule_code"], "CUSTOM_EXPERIMENTAL_RULE_XYZ")
        self.assertEqual(exp["category"], "CUSTOM")
        self.assertEqual(exp["severity"], "INFO")
        self.assertIn("Custom", exp["name"])

    def test_none_and_empty_rule_codes(self):
        """Verify None, empty string, and whitespace rule codes return safe fallback."""
        for bad in [None, "", "   "]:
            exp = get_rule_explanation(bad)
            self.assertEqual(exp["rule_code"], "UNKNOWN_RULE")
            self.assertIsInstance(exp["name"], str)

    def test_non_string_rule_codes(self):
        """Verify non-string types (int, float) are handled safely."""
        exp_int = get_rule_explanation(999)
        self.assertEqual(exp_int["rule_code"], "999")
        self.assertIsInstance(exp_int["mathematical_definition"], str)

    def test_custom_rule_with_metadata_enrichment(self):
        """Verify custom rules incorporate provided metadata for detail and points."""
        exp = get_rule_explanation(
            "CUSTOM_BURST_RATE",
            metadata={"detail": "Over 20 requests per second", "points": 50, "severity": "CRITICAL"}
        )
        self.assertEqual(exp["points"], 50)
        self.assertEqual(exp["severity"], "CRITICAL")
        self.assertIn("Over 20 requests per second", exp["plain_english_explanation"])

    # ── Group 4: Dynamic Metric Interpolation ─────────────────────────────────

    def test_scalar_interpolation_dmv_score(self):
        """Verify DMV score interpolation at CRITICAL, ELEVATED, and NORMAL levels."""
        # Critical DMV
        exp_crit = get_rule_explanation("DMV_RAPID_DRAIN", value=85.5)
        self.assertIn("85.5", exp_crit["plain_english_explanation"])
        self.assertIn("CRITICAL", exp_crit["plain_english_explanation"])

        # Elevated DMV
        exp_elev = get_rule_explanation("DMV_RAPID_DRAIN", value=55.0)
        self.assertIn("55.0", exp_elev["plain_english_explanation"])
        self.assertIn("ELEVATED", exp_elev["plain_english_explanation"])

    def test_scalar_interpolation_ewma_score(self):
        """Verify EWMA / Behavioral anomaly metric interpolation."""
        exp = get_rule_explanation("BEHAVIORAL_ANOMALY", metric_value=0.94, context={"z_score": 3.75})
        self.assertIn("0.94", exp["plain_english_explanation"])
        self.assertIn("3.75", exp["plain_english_explanation"])

    def test_scalar_interpolation_structuring_amount(self):
        """Verify structuring amount currency formatting."""
        exp = get_rule_explanation("LIMIT_SKIRTING", metric_value=49990.0, context={"threshold": 50000.0})
        self.assertTrue("49,990" in exp["plain_english_explanation"] or "49990" in exp["plain_english_explanation"])
        self.assertTrue("50,000" in exp["plain_english_explanation"] or "50000" in exp["plain_english_explanation"])

    def test_scalar_interpolation_high_value_amount(self):
        """Verify high value fresh account metric interpolation."""
        exp = get_rule_explanation("NEW_ACCOUNT_HIGH_VALUE", metric_value=75000.0, context={"age_days": 4})
        self.assertTrue("75,000" in exp["plain_english_explanation"] or "75000" in exp["plain_english_explanation"])
        self.assertIn("4", exp["plain_english_explanation"])

    def test_scalar_interpolation_honeypot_string(self):
        """Verify honeypot trap address string interpolation."""
        exp = get_rule_explanation("R_HONEYPOT_HIT", metric_value="honeypot_trap_01@okaxis")
        self.assertIn("honeypot_trap_01@okaxis", exp["plain_english_explanation"])

    # ── Group 5: Context Dict Unpacking ───────────────────────────────────────

    def test_context_dict_interpolation_conduit(self):
        """Verify pass-through conduit flow metrics interpolation."""
        conduit_ctx = {
            "inflow": 120000.0,
            "outflow": 115000.0,
            "ratio": 0.958,
            "window_minutes": 45,
        }
        exp = get_rule_explanation("PASS_THROUGH_CONDUIT", context=conduit_ctx)
        self.assertTrue("95.8%" in exp["plain_english_explanation"] or "96%" in exp["plain_english_explanation"])
        self.assertTrue("120,000" in exp["plain_english_explanation"] or "120000" in exp["plain_english_explanation"])
        self.assertIn("45", exp["plain_english_explanation"])

    def test_context_dict_interpolation_travel(self):
        """Verify impossible travel distance, speed, and cities interpolation."""
        travel_ctx = {
            "speed_kmh": 1420.0,
            "distance_km": 710.0,
            "time_minutes": 30.0,
            "from_city": "Bengaluru",
            "to_city": "Delhi",
        }
        exp = get_rule_explanation("R_IMPOSSIBLE_TRAVEL", context=travel_ctx)
        self.assertIn("1,420", exp["plain_english_explanation"])
        self.assertIn("Bengaluru", exp["plain_english_explanation"])
        self.assertIn("Delhi", exp["plain_english_explanation"])

    def test_context_dict_interpolation_sim_swap(self):
        """Verify SIM / device IDs unpacked in telemetry mismatch rule."""
        sim_ctx = {
            "device_id": "hw_pixel7_9981",
            "sim_id": "sim_airtel_5541",
            "payer_vpa": "victim@okhdfcbank",
            "payee_vpa": "mule@okaxis",
        }
        exp = get_rule_explanation("R_SIM_DEVICE_MISMATCH", context=sim_ctx)
        self.assertIn("hw_pixel7_9981", exp["plain_english_explanation"])
        self.assertIn("sim_airtel_5541", exp["plain_english_explanation"])
        self.assertIn("victim@okhdfcbank", exp["plain_english_explanation"])

    def test_context_dict_interpolation_entity_pairs(self):
        """Verify payer and payee entities attached to contextual narrative."""
        exp = get_rule_explanation(
            "KNOWN_FRAUD_ENTITY",
            metadata={"payer_vpa": "alice@okaxis", "payee_vpa": "fraudster@paytm", "detail": "Prior SAR filing"}
        )
        self.assertIn("alice@okaxis", exp["contextual_narrative"])
        self.assertIn("fraudster@paytm", exp["contextual_narrative"])
        self.assertIn("Prior SAR filing", exp["contextual_narrative"])

    # ── Group 6: Prompt Context Builder (Tier-1 Table + Tier-2 Sections) ──────

    def test_build_context_markdown_table_and_sections(self):
        """Verify build_case_encyclopedia_context produces markdown table and deep sections."""
        evaluated_rules = [
            "DMV_RAPID_DRAIN",
            {"code": "R_HONEYPOT_HIT", "points": 100, "detail": "Direct hit on trap"},
            RuleHit(code="R_SIM_DEVICE_MISMATCH", points=30, detail="SIM swap detected"),
        ]
        metrics = {
            "dmv_score": 88.0,
            "risk_score": 95,
            "amount": 50000.0,
        }

        context_md = build_case_encyclopedia_context(evaluated_rules, metrics)
        self.assertIsInstance(context_md, str)
        self.assertIn("### 📚 SAMPATI ENCYCLOPEDIA ALGORITHMIC KNOWLEDGE BASE", context_md)
        self.assertIn("| Rule Code | Rule Name | Evaluated Metric | Severity | Detection Summary |", context_md)
        self.assertIn("`DMV_RAPID_DRAIN`", context_md)
        self.assertIn("`R_HONEYPOT_HIT`", context_md)
        self.assertIn("`R_SIM_DEVICE_MISMATCH`", context_md)
        self.assertIn("Mathematical Formula", context_md)
        self.assertIn("Forensic Rationale", context_md)
        self.assertIn("Regulatory Typology", context_md)
        self.assertIn("Recommended Compliance Action", context_md)

    def test_build_context_with_rulehit_pydantic_objects(self):
        """Verify context builder handles Pydantic RuleHit objects seamlessly."""
        hits = [
            RuleHit(code="PASS_THROUGH_CONDUIT", points=30, detail="Forwarding 95% of Rs 80k"),
            RuleHit(code="FAN_IN_BURST", points=25, detail="6 distinct payers"),
        ]
        ctx_md = build_case_encyclopedia_context(hits)
        self.assertIn("`PASS_THROUGH_CONDUIT`", ctx_md)
        self.assertIn("`FAN_IN_BURST`", ctx_md)
        self.assertIn("Forwarding 95% of Rs 80k", ctx_md)

    def test_build_context_empty_rules_and_none_metrics(self):
        """Verify context builder produces clean baseline output for empty inputs."""
        empty_ctx = build_case_encyclopedia_context([], None)
        self.assertIn("No specific high-risk deterministic rules triggered", empty_ctx)

    def test_build_context_dmv_overlay_when_not_in_rules(self):
        """Verify DMV is rendered in table and section when in metrics but not in evaluated_rules."""
        ctx_md = build_case_encyclopedia_context(["R_DATACENTER_IP"], metrics={"dmv_score": 92.4})
        self.assertIn("`R_DATACENTER_IP`", ctx_md)
        self.assertIn("`DMV_RAPID_DRAIN`", ctx_md)
        self.assertIn("92.4/100", ctx_md)

    def test_build_context_deduplicates_aliases(self):
        """Verify duplicate rules or alias forms only appear once in markdown."""
        rules = ["DMV_RAPID_DRAIN", "dmv", "RULE_DMV_VELOCITY", "DMV"]
        ctx_md = build_case_encyclopedia_context(rules)
        self.assertEqual(ctx_md.count("`DMV_RAPID_DRAIN` — Dead Money Velocity"), 1)

    # ── Group 7: Fast In-Memory Search Engine ─────────────────────────────────

    def test_search_encyclopedia_exact_and_alias(self):
        """Verify search_encyclopedia returns top ranked match for exact code and alias."""
        res_exact = search_encyclopedia("DMV_RAPID_DRAIN")
        self.assertTrue(len(res_exact) > 0)
        self.assertEqual(res_exact[0]["canonical_code"], "DMV_RAPID_DRAIN")

        res_alias = search_encyclopedia("sim_swap")
        self.assertTrue(len(res_alias) > 0)
        self.assertEqual(res_alias[0]["canonical_code"], "R_SIM_DEVICE_MISMATCH")

    def test_search_encyclopedia_concept_keywords(self):
        """Verify search_encyclopedia matches concept keywords correctly."""
        res_dormancy = search_encyclopedia("dormancy")
        self.assertTrue(any(r["canonical_code"] == "DMV_RAPID_DRAIN" for r in res_dormancy))

        res_honeypot = search_encyclopedia("synthetic darknet botnet")
        self.assertTrue(any(r["canonical_code"] == "R_HONEYPOT_HIT" for r in res_honeypot))

        res_structuring = search_encyclopedia("smurfing structuring")
        self.assertTrue(any(r["canonical_code"] == "LIMIT_SKIRTING" for r in res_structuring))

        res_gini = search_encyclopedia("gini dispersion")
        self.assertTrue(any(r["canonical_code"] == "GINI_INEQUALITY" for r in res_gini))

    def test_search_encyclopedia_limit_and_empty(self):
        """Verify search limits and empty search handling."""
        self.assertEqual(search_encyclopedia(""), [])
        self.assertEqual(search_encyclopedia("   "), [])
        self.assertEqual(search_encyclopedia(None), [])  # type: ignore

        res = search_encyclopedia("fraud", limit=3)
        self.assertLessEqual(len(res), 3)

    # ── Group 8: Resilience & Edge Cases ──────────────────────────────────────

    def test_resilience_to_nan_inf_and_malformed(self):
        """Verify engine does not crash on NaN, Inf, non-string codes, or malformed dicts."""
        cases = [
            get_rule_explanation("DMV_RAPID_DRAIN", metric_value=float("nan")),
            get_rule_explanation("DMV_RAPID_DRAIN", metric_value=float("inf")),
            get_rule_explanation("BEHAVIORAL_ANOMALY", metric_value=-100.0),
            get_rule_explanation(12345),
            build_case_encyclopedia_context([None, 123, {"invalid": "dict"}]),  # type: ignore
        ]
        for item in cases:
            self.assertIsNotNone(item)

    # ── Group 9: Performance Benchmark ────────────────────────────────────────

    def test_performance_submillisecond_latency(self):
        """Verify get_rule_explanation and build_case_encyclopedia_context execute in < 1ms."""
        rules = ["DMV_RAPID_DRAIN", "R_HONEYPOT_HIT", "PASS_THROUGH_CONDUIT", "BEHAVIORAL_ANOMALY"]
        metrics = {"dmv_score": 85.0, "adaptive_score": 0.88, "amount": 75000.0}

        # Warmup
        for _ in range(50):
            build_case_encyclopedia_context(rules, metrics)

        t0 = time.perf_counter()
        iterations = 500
        for _ in range(iterations):
            build_case_encyclopedia_context(rules, metrics)
        elapsed_total_ms = (time.perf_counter() - t0) * 1000.0
        avg_latency_ms = elapsed_total_ms / iterations

        self.assertLess(avg_latency_ms, 1.0, f"Average context building latency {avg_latency_ms:.4f}ms exceeded 1.0ms limit")


if __name__ == "__main__":
    unittest.main()

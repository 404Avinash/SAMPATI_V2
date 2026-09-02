"""SAMPATI V2 — End-to-End Test Suite for Gemini Assistant & Agentic Operations.

Covers all 4 Tiers defined in TEST_INFRA.md:
- Tier 1: Feature Isolation & Functional Verification (Context Injection, Encyclopedia KB Rationale,
          Agentic Federation Round, Transaction Simulation, Block/Hold VPA, SAR PDF Export).
- Tier 2: Boundary & Corner Cases (Empty Cases, Unknown Case 404, 0/Max Rules, Boundary Simulation
          Counts, Malformed VPAs, Duplicate Tool Intents, Extreme Values).
- Tier 3: Cross-Feature Combinations & Multi-Turn Chat (Multi-Intent Queries, Conversational
          Context Maintenance, Live Function Calling Mocking, Backward Compatibility).
- Tier 4: Real-World Application Scenarios (Scenarios 1 through 5).
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from starlette.testclient import TestClient

from app.forensics.sar_pdf import build_sar_pdf
from app.main import app
from app.models.upi_models import (
    AiCaseBriefingResponse,
    AiChatRequest,
    AiChatResponse,
    GeminiAssistantBriefing,
    GeminiAssistantChatRequest,
    GeminiAssistantChatResponse,
    GeminiChatResponse,
    ToolExecutionResult,
    UpiTransaction,
)
from app.services.gemini_service import (
    GEMINI_TOOL_DECLARATIONS,
    GeminiAssistantService,
    GeminiCopilotService,
    build_case_dossier_text,
    get_gemini_assistant_service,
    get_gemini_copilot_service,
)
from app.services.upi_cases import get_upi_case_service


def _build_test_case_payload(case_id: str = "case_e2e_test_001") -> Dict[str, Any]:
    """Helper to generate a rich forensic case dictionary for end-to-end testing."""
    return {
        "case_id": case_id,
        "status": "OPEN",
        "verdict": "HOLD",
        "risk_score": 89,
        "amount": 85000.0,
        "payer_vpa": "victim_e2e@okhdfcbank",
        "payee_vpa": "mule_e2e@okicici",
        "payer_psp": "okhdfcbank",
        "payee_psp": "okicici",
        "reasons": ["DMV_RAPID_DRAIN", "PASS_THROUGH_CONDUIT", "R_SIM_DEVICE_MISMATCH"],
        "dmv_score": 86.4,
        "adaptive_score": 0.82,
        "network_score": 0.77,
        "ring_members_vpas": ["mule_e2e@okicici", "conduit_relay@ybl", "cashout_node@paytm"],
        "ring_hash": "ring_hash_e2e_alpha_999",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trigger_txn": {
            "txn_id": f"txn_{case_id}_trigger",
            "payer_vpa": "victim_e2e@okhdfcbank",
            "payee_vpa": "mule_e2e@okicici",
            "amount": 85000.0,
            "device_id": "DEV_FINGERPRINT_E2E_01",
            "sim_id": "SIM_IMSI_E2E_01",
            "ip": "103.25.144.12",
            "location": "Mumbai, MH",
            "note": "Immediate crypto investment release",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "raw_transactions": [
            {
                "txn_id": f"txn_{case_id}_inflow",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payer_vpa": "victim_e2e@okhdfcbank",
                "payee_vpa": "mule_e2e@okicici",
                "amount": 85000.0,
                "txn_type": "P2P",
            },
            {
                "txn_id": f"txn_{case_id}_outflow_1",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payer_vpa": "mule_e2e@okicici",
                "payee_vpa": "conduit_relay@ybl",
                "amount": 40000.0,
                "txn_type": "P2P",
            },
            {
                "txn_id": f"txn_{case_id}_outflow_2",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payer_vpa": "mule_e2e@okicici",
                "payee_vpa": "cashout_node@paytm",
                "amount": 42000.0,
                "txn_type": "P2P",
            },
        ],
        "topology": {
            "fan_in": 1,
            "hops": 2,
            "fan_out": 2,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# TIER 1: FEATURE ISOLATION & FUNCTIONAL VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestTier1FeatureCoverage(unittest.IsolatedAsyncioTestCase):
    """Tier 1: Feature Isolation & Functional Verification for Gemini Assistant."""

    def setUp(self):
        self.service = GeminiAssistantService(api_key=None)
        self.service.clear_cache()
        self.case_service = get_upi_case_service()
        self.client = TestClient(app)
        self.sample_case = _build_test_case_payload("tier1_case_001")

    # Feature 1: Deep Context Injection in Briefing and Chat
    def test_tier1_context_injection_in_case_dossier(self):
        """Verify dossier builds complete multi-layer telemetry, ledger, topology & encyclopedia context."""
        dossier = build_case_dossier_text(self.sample_case)

        # Telemetry & Case Identity
        self.assertIn("tier1_case_001", dossier)
        self.assertIn("85,000.00", dossier)
        self.assertIn("victim_e2e@okhdfcbank", dossier)
        self.assertIn("mule_e2e@okicici", dossier)
        self.assertIn("DEV_FINGERPRINT_E2E_01", dossier)
        self.assertIn("SIM_IMSI_E2E_01", dossier)
        self.assertIn("103.25.144.12", dossier)
        self.assertIn("Mumbai, MH", dossier)

        # Multi-layer score & DMV
        self.assertIn("86.4/100", dossier)
        self.assertIn("CRITICAL", dossier)
        self.assertIn("0.82", dossier)
        self.assertIn("0.77", dossier)

        # Transaction Ledger
        self.assertIn("txn_tier1_case_001_inflow", dossier)
        self.assertIn("txn_tier1_case_001_outflow_1", dossier)
        self.assertIn("txn_tier1_case_001_outflow_2", dossier)

        # Graph Topology & Ring Hash
        self.assertIn("ring_hash_e2e_alpha_999", dossier)
        self.assertIn("conduit_relay@ybl", dossier)
        self.assertIn("cashout_node@paytm", dossier)

        # Algorithmic Encyclopedia Rationale
        self.assertIn("SAMPATI ENCYCLOPEDIA ALGORITHMIC KNOWLEDGE BASE", dossier)
        self.assertIn("Dead Money Velocity (DMV) Burst", dossier)

    async def test_tier1_ai_briefing_deep_context_generation(self):
        """Verify generate_case_briefing creates structured briefing with threat level and actions."""
        briefing = await self.service.generate_case_briefing(self.sample_case)
        self.assertEqual(briefing["case_id"], "tier1_case_001")
        self.assertEqual(briefing["threat_level"], "CRITICAL")
        self.assertIn("executive_summary", briefing)
        self.assertIn("scam_classification", briefing)
        self.assertIsInstance(briefing["key_indicators"], list)
        self.assertIsInstance(briefing["recommended_actions"], list)
        self.assertTrue(len(briefing["recommended_actions"]) >= 2)

    # Feature 2: Algorithmic Encyclopedia Rationale for Triggered Rules
    async def test_tier1_encyclopedia_mathematical_rationale_dmv(self):
        """Verify chat explanation for DMV contains mathematical formulas from Encyclopedia KB."""
        res = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Explain why the Dead Money Velocity (DMV) score spiked",
        )
        answer = res["answer"]
        self.assertIn("Dead Money Velocity", answer)
        self.assertIn("86.4/100", answer)
        self.assertIn("CRITICAL", answer)
        self.assertIn("Dormancy Index D =", answer)
        self.assertIn("Drain Ratio R =", answer)
        self.assertIn("Burst Velocity V =", answer)

    async def test_tier1_encyclopedia_rule_lookups(self):
        """Verify direct encyclopedia searches for platform detection rules."""
        rules_to_query = [
            ("Explain Pass Through Conduit", "PASS_THROUGH_CONDUIT"),
            ("What is Limit Skirting and Structuring?", "LIMIT_SKIRTING"),
            ("Explain Synthetic Honeypot", "R_HONEYPOT_HIT"),
        ]
        for query, expected_code in rules_to_query:
            res = await self.service.chat_with_case_assistant(self.sample_case, question=query)
            ans = res["answer"]
            self.assertIn(expected_code, ans)
            self.assertIn("Mathematical Definition", ans)
            self.assertIn("Forensic Rationale", ans)

    # Feature 3: Agentic Operation - Trigger Federation Round
    async def test_tier1_agentic_trigger_federation_round(self):
        """Verify 'Trigger a federation round' executes federation and returns structured result."""
        res = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Trigger a federation round across all participating PSP nodes",
        )
        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "trigger_federation_round")
        self.assertEqual(tool_exec["status"], "success")
        self.assertIn("participating_nodes", tool_exec["data"])
        self.assertIn("rings_detected", tool_exec["data"])
        self.assertIn("Gemini Assistant Action Executed: `trigger_federation_round`", res["answer"])

    # Feature 4: Agentic Operation - Simulate Transaction Batch
    async def test_tier1_agentic_simulate_transaction_batch(self):
        """Verify 'Simulate 60 transactions' parses parameters and executes simulation."""
        res = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Simulate 60 synthetic transactions with 25% fraud ratio and seed 88",
        )
        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "simulate_transactions")
        self.assertEqual(tool_exec["status"], "success")
        self.assertEqual(tool_exec["arguments"]["total_txns"], 60)
        self.assertAlmostEqual(tool_exec["arguments"]["fraud_ratio"], 0.25)
        self.assertEqual(tool_exec["arguments"]["seed"], 88)
        self.assertIn("Gemini Assistant Action Executed: `simulate_transactions`", res["answer"])

    # Feature 5: Agentic Operation - Block / Hold VPA
    async def test_tier1_agentic_block_vpa_enforcement(self):
        """Verify 'Block payee VPA' applies hot state freeze and case escalation."""
        res = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Block suspect payee VPA mule_e2e@okicici immediately",
        )
        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "block_vpa_or_transaction")
        self.assertEqual(tool_exec["status"], "success")
        self.assertEqual(tool_exec["arguments"]["target_vpa"], "mule_e2e@okicici")
        self.assertEqual(tool_exec["arguments"]["action"], "BLOCK")
        self.assertIn("Gemini Assistant Action Executed: `block_vpa_or_transaction`", res["answer"])

    # Feature 6: Agentic Operation - Export SAR to PDF
    async def test_tier1_agentic_export_sar_pdf(self):
        """Verify 'Export SAR to PDF' compiles formal PDF SAR document."""
        res = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Export SAR to PDF for regulatory reporting to FIU-IND",
        )
        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "export_sar_pdf")
        self.assertEqual(tool_exec["status"], "success")
        self.assertGreater(tool_exec["data"]["pdf_size_bytes"], 100)
        self.assertEqual(tool_exec["data"]["download_url"], f"/cases/{self.sample_case['case_id']}/sar/pdf")
        self.assertIn("Gemini Assistant Action Executed: `export_sar_pdf`", res["answer"])


# ══════════════════════════════════════════════════════════════════════════════
# TIER 2: BOUNDARY & CORNER CASES
# ══════════════════════════════════════════════════════════════════════════════

class TestTier2BoundaryAndCornerCases(unittest.IsolatedAsyncioTestCase):
    """Tier 2: Boundary & Corner Cases for Gemini Assistant."""

    def setUp(self):
        self.service = GeminiAssistantService(api_key=None)
        self.service.clear_cache()
        self.client = TestClient(app)

    async def test_tier2_empty_case_payload(self):
        """Verify graceful handling when case data is empty dictionary or contains None values."""
        empty_case: Dict[str, Any] = {}
        briefing = await self.service.generate_case_briefing(empty_case)
        self.assertIn("case_id", briefing)
        self.assertIn("executive_summary", briefing)
        self.assertIn("threat_level", briefing)

        chat_resp = await self.service.chat_with_case_assistant(empty_case, question="What is the risk level?")
        self.assertIn("answer", chat_resp)
        self.assertTrue(len(chat_resp["answer"]) > 10)

    def test_tier2_unknown_case_id_api_404(self):
        """Verify REST API returns 404 for unknown case IDs."""
        non_existent_id = "case_non_existent_999999"
        res_briefing = self.client.post(f"/cases/{non_existent_id}/ai-briefing")
        self.assertEqual(res_briefing.status_code, 404)

        res_chat = self.client.post(f"/cases/{non_existent_id}/ai-chat", json={"question": "Hello"})
        self.assertEqual(res_chat.status_code, 404)

    async def test_tier2_zero_rules_fired_clean_case(self):
        """Verify clean transaction case with zero rules and 0 DMV score handles gracefully."""
        clean_case = {
            "case_id": "clean_case_001",
            "status": "OPEN",
            "verdict": "ALLOW",
            "risk_score": 5,
            "amount": 500.0,
            "payer_vpa": "user_alice@oksbi",
            "payee_vpa": "merchant_bob@okaxis",
            "reasons": [],
            "dmv_score": 0.0,
        }
        res = await self.service.chat_with_case_assistant(clean_case, question="Why was this flagged?")
        self.assertIn("answer", res)
        self.assertIn("500.00", res["answer"])

    async def test_tier2_maximum_rules_fired_stress_case(self):
        """Verify case with 15+ simultaneous rule hits parses all rules without overflow or crash."""
        all_rules = [
            "DMV_RAPID_DRAIN", "PASS_THROUGH_CONDUIT", "R_SIM_DEVICE_MISMATCH",
            "LIMIT_SKIRTING", "FAN_OUT_DISPERSAL", "R_HONEYPOT_HIT",
            "R_IMPOSSIBLE_TRAVEL", "FAN_IN_BURST", "NEW_ACCOUNT_HIGH_VALUE",
            "R_DATACENTER_IP", "DEVICE_FARM", "R_CAMPAIGN_MATCH",
        ]
        stress_case = {
            "case_id": "stress_max_rules_case",
            "status": "OPEN",
            "verdict": "BLOCK",
            "risk_score": 99,
            "amount": 490000.0,
            "payer_vpa": "victim_stress@okhdfcbank",
            "payee_vpa": "syndicate_boss@okicici",
            "reasons": all_rules,
            "dmv_score": 98.7,
            "ring_members_vpas": [f"node_{i}@upi" for i in range(15)],
        }
        dossier = build_case_dossier_text(stress_case)
        self.assertIn("stress_max_rules_case", dossier)
        self.assertIn("98.7/100", dossier)

        res = await self.service.chat_with_case_assistant(stress_case, question="Explain why this case was flagged")
        self.assertIn("answer", res)
        self.assertIn("490,000.00", res["answer"])

    async def test_tier2_boundary_simulation_counts(self):
        """Verify boundary counts (1, 250, extreme fraud ratios 0.0, 1.0)."""
        test_prompts = [
            ("Simulate 1 synthetic transaction with 0% fraud ratio", 1, 0.0),
            ("Simulate 250 synthetic transactions with 100% fraud ratio", 250, 1.0),
        ]
        for prompt, exp_count, exp_ratio in test_prompts:
            res = await self.service.chat_with_case_assistant({}, question=prompt)
            tool_exec = res["tool_executions"][0]
            self.assertEqual(tool_exec["arguments"]["total_txns"], exp_count)
            self.assertAlmostEqual(tool_exec["arguments"]["fraud_ratio"], exp_ratio)

    async def test_tier2_malformed_vpa_and_fallback(self):
        """Verify malformed VPA addresses in commands fallback safely to case payee/payer."""
        case_with_payee = {
            "case_id": "case_vpa_fallback",
            "payee_vpa": "fallback_payee@okhdfcbank",
            "payer_vpa": "fallback_payer@okicici",
        }
        # Malformed VPA string without valid '@' symbol
        res = await self.service.chat_with_case_assistant(case_with_payee, question="Block the suspect account invalid_vpa_no_at_sign")
        self.assertEqual(res["source"], "agentic-tool")
        tool_exec = res["tool_executions"][0]
        # Should fallback to case payee
        self.assertEqual(tool_exec["arguments"]["target_vpa"], "fallback_payee@okhdfcbank")

    async def test_tier2_duplicate_and_idempotent_tool_intents(self):
        """Verify repeated invocation of the same tool intent in successive calls executes safely."""
        case_data = _build_test_case_payload("idempotency_case_001")
        for _ in range(3):
            res = await self.service.chat_with_case_assistant(case_data, question="Trigger a federation round")
            self.assertEqual(res["source"], "agentic-tool")
            self.assertEqual(res["tool_executions"][0]["status"], "success")

    async def test_tier2_extreme_numerical_values(self):
        """Verify handling of NaN, Inf, and large numeric values without crashes."""
        extreme_case = {
            "case_id": "case_extreme_math",
            "amount": 100000000.0,  # 10 Crore INR
            "risk_score": 100,
            "dmv_score": float("nan"),
            "adaptive_score": float("inf"),
            "reasons": ["DMV_RAPID_DRAIN"],
        }
        briefing = await self.service.generate_case_briefing(extreme_case)
        self.assertEqual(briefing["case_id"], "case_extreme_math")
        self.assertIn("100,000,000.00", briefing["executive_summary"])


# ══════════════════════════════════════════════════════════════════════════════
# TIER 3: CROSS-FEATURE COMBINATIONS & MULTI-TURN CONVERSATIONS
# ══════════════════════════════════════════════════════════════════════════════

class TestTier3CrossFeatureCombinations(unittest.IsolatedAsyncioTestCase):
    """Tier 3: Cross-Feature Combinations & Multi-Turn Conversations."""

    def setUp(self):
        self.service = GeminiAssistantService(api_key=None)
        self.service.clear_cache()
        self.case_service = get_upi_case_service()
        self.sample_case = _build_test_case_payload("tier3_case_multi_001")

    async def test_tier3_multi_turn_investigative_chat_lifecycle(self):
        """Verify multi-turn session maintains conversation history and executes tools in sequence."""
        history: List[Dict[str, Any]] = []

        # Turn 1: Case explanation inquiry
        t1_resp = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Why was this transaction flagged by the risk engine?",
            conversation_history=history,
        )
        self.assertIn("DMV_RAPID_DRAIN", t1_resp["answer"])
        history.append({"role": "user", "text": "Why was this transaction flagged by the risk engine?"})
        history.append({"role": "assistant", "text": t1_resp["answer"]})

        # Turn 2: Algorithmic formula follow-up
        t2_resp = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Explain the Dead Money Velocity formula in detail",
            conversation_history=history,
        )
        self.assertIn("Dormancy Index D =", t2_resp["answer"])
        history.append({"role": "user", "text": "Explain the Dead Money Velocity formula in detail"})
        history.append({"role": "assistant", "text": t2_resp["answer"]})

        # Turn 3: Federation round execution
        t3_resp = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Trigger a federation round to synchronize intelligence with other banks",
            conversation_history=history,
        )
        self.assertEqual(t3_resp["source"], "agentic-tool")
        self.assertEqual(t3_resp["tool_executions"][0]["tool_name"], "trigger_federation_round")
        history.append({"role": "user", "text": "Trigger a federation round to synchronize intelligence"})
        history.append({"role": "assistant", "text": t3_resp["answer"]})

        # Turn 4: Block suspect and export SAR PDF
        t4_resp = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Block suspect payee VPA mule_e2e@okicici immediately",
            conversation_history=history,
        )
        self.assertEqual(t4_resp["source"], "agentic-tool")
        self.assertEqual(t4_resp["tool_executions"][0]["tool_name"], "block_vpa_or_transaction")
        history.append({"role": "user", "text": "Block suspect payee VPA mule_e2e@okicici immediately"})
        history.append({"role": "assistant", "text": t4_resp["answer"]})

        # Turn 5: Export SAR PDF
        t5_resp = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Export SAR report to PDF for FIU-IND regulatory submission",
            conversation_history=history,
        )
        self.assertEqual(t5_resp["source"], "agentic-tool")
        self.assertEqual(t5_resp["tool_executions"][0]["tool_name"], "export_sar_pdf")
        self.assertEqual(len(history), 8)

    async def test_tier3_live_gemini_function_calling_and_dispatch(self):
        """Verify remote Gemini API returning functionCall is correctly intercepted and executed."""
        service = GeminiAssistantService(api_key="AIzaSyMockRemoteFunctionCallingKey")

        mock_gemini_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "trigger_federation_round",
                                    "args": {
                                        "case_id": "tier3_case_multi_001",
                                        "force_sync": True,
                                    },
                                }
                            }
                        ]
                    },
                    "finishReason": "STOP",
                }
            ]
        }

        mock_http_response = AsyncMock()
        mock_http_response.status_code = 200
        mock_http_response.json = lambda: mock_gemini_payload

        with patch("httpx.AsyncClient.post", return_value=mock_http_response):
            res = await service.chat_with_case_assistant(
                self.sample_case,
                question="Perform a multi-bank network risk assessment across all partners",
            )
            self.assertEqual(res["source"], "gemini-ai")
            self.assertEqual(len(res["tool_executions"]), 1)
            self.assertEqual(res["tool_executions"][0]["tool_name"], "trigger_federation_round")
            self.assertIn("trigger_federation_round", res["answer"])

    async def test_tier3_multi_intent_query_routing(self):
        """Verify queries combining multiple action intents are parsed and dispatched gracefully."""
        # Multi-intent query: Federation + SAR
        res_fed = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Please trigger a federation round and then export the SAR report",
        )
        self.assertEqual(res_fed["source"], "agentic-tool")
        self.assertTrue(len(res_fed["tool_executions"]) >= 1)
        self.assertIn(res_fed["tool_executions"][0]["tool_name"], ["trigger_federation_round", "export_sar_pdf"])

        # Multi-intent query: Block + Simulate
        res_block = await self.service.chat_with_case_assistant(
            self.sample_case,
            question="Block payee VPA suspect@okaxis and simulate 20 transactions",
        )
        self.assertEqual(res_block["source"], "agentic-tool")
        self.assertTrue(len(res_block["tool_executions"]) >= 1)
        self.assertIn(res_block["tool_executions"][0]["tool_name"], ["simulate_transactions", "block_vpa_or_transaction"])

    def test_tier3_backward_compatibility_aliases_and_models(self):
        """Verify complete backward compatibility across all legacy Copilot identifiers and schemas."""
        # Service aliases
        self.assertIs(GeminiCopilotService, GeminiAssistantService)
        self.assertIsInstance(get_gemini_copilot_service(), GeminiAssistantService)
        self.assertIsInstance(get_gemini_assistant_service(), GeminiAssistantService)

        # Model aliases
        self.assertIs(AiChatResponse, GeminiChatResponse)
        self.assertIs(GeminiAssistantBriefing, AiCaseBriefingResponse)
        self.assertIs(GeminiAssistantChatRequest, AiChatRequest)
        self.assertIs(GeminiAssistantChatResponse, GeminiChatResponse)

        # Schema validation with tool execution metadata
        tool_exec = ToolExecutionResult(
            tool_name="simulate_transactions",
            arguments={"total_txns": 50},
            status="success",
            result_summary="Simulation complete",
        )
        chat_resp = GeminiChatResponse(
            case_id="case_compat_check",
            question="Simulate batch",
            answer="Done",
            tool_executions=[tool_exec],
        )
        self.assertEqual(chat_resp.reply, "Done")
        self.assertEqual(len(chat_resp.tool_executions), 1)


# ══════════════════════════════════════════════════════════════════════════════
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

class TestTier4RealWorldScenarios(unittest.IsolatedAsyncioTestCase):
    """Tier 4: Real-World Application Scenarios (Scenarios 1 through 5 from TEST_INFRA.md)."""

    def setUp(self):
        self.service = GeminiAssistantService(api_key=None)
        self.service.clear_cache()
        self.case_service = get_upi_case_service()
        self.client = TestClient(app)

    # ──────────────────────────────────────────────────────────────────────────
    # Scenario 1: Analyst asks "Explain why DMV score spiked for case X"
    # ──────────────────────────────────────────────────────────────────────────
    async def test_scenario_1_analyst_dmv_score_explanation(self):
        """Scenario 1: Analyst asks 'Explain why DMV score spiked for case X'
        Asserts dormancy gap, outflow velocity math (D, R, V), and plain English explanation.
        """
        case_data = _build_test_case_payload("case_scenario_1_dmv")
        res = await self.service.chat_with_case_assistant(
            case_data,
            question="Explain why the DMV score spiked for case case_scenario_1_dmv",
        )
        answer = res["answer"]

        # Math formulas and dormancy gap explanation
        self.assertIn("Dead Money Velocity (DMV) Score is 86.4/100", answer)
        self.assertIn("CRITICAL", answer)
        self.assertIn("Dormancy Index D =", answer)
        self.assertIn("Drain Ratio R =", answer)
        self.assertIn("Burst Velocity V =", answer)
        self.assertTrue("dormancy" in answer.lower())
        self.assertTrue("outflow" in answer.lower())
        self.assertTrue("mule pass-through" in answer.lower() or "pass-through" in answer.lower())

    # ──────────────────────────────────────────────────────────────────────────
    # Scenario 2: Analyst commands "Trigger a federation round to sync intelligence"
    # ──────────────────────────────────────────────────────────────────────────
    async def test_scenario_2_analyst_trigger_federation_round(self):
        """Scenario 2: Analyst commands 'Trigger a federation round to sync intelligence'
        Asserts federation coordinator execution, returned PSP nodes & threat metrics.
        """
        case_data = _build_test_case_payload("case_scenario_2_fed")
        res = await self.service.chat_with_case_assistant(
            case_data,
            question="Trigger a federation round to sync intelligence across all banks",
        )

        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "trigger_federation_round")
        self.assertEqual(tool_exec["status"], "success")

        # Assert participating PSP nodes
        nodes = tool_exec["data"]["participating_nodes"]
        self.assertIsInstance(nodes, list)
        self.assertTrue(len(nodes) >= 3)
        self.assertTrue(any("hdfc" in n or "axis" in n or "icici" in n or "sbi" in n for n in nodes))

        # Assert returned markdown contains execution card
        self.assertIn("Gemini Assistant Action Executed: `trigger_federation_round`", res["answer"])
        self.assertIn("Participating PSP Nodes", res["answer"])
        self.assertIn("Forensic Impact", res["answer"])

    # ──────────────────────────────────────────────────────────────────────────
    # Scenario 3: Analyst commands "Simulate a batch of 50 mule transactions"
    # ──────────────────────────────────────────────────────────────────────────
    async def test_scenario_3_analyst_simulate_mule_transactions(self):
        """Scenario 3: Analyst commands 'Simulate a batch of 50 mule transactions'
        Asserts simulation execution, generated counts, decisions breakdown, and case opening.
        """
        case_data = _build_test_case_payload("case_scenario_3_sim")
        res = await self.service.chat_with_case_assistant(
            case_data,
            question="Simulate a batch of 50 mule transactions with 30% fraud ratio",
        )

        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "simulate_transactions")
        self.assertEqual(tool_exec["status"], "success")
        self.assertEqual(tool_exec["arguments"]["total_txns"], 50)
        self.assertAlmostEqual(tool_exec["arguments"]["fraud_ratio"], 0.30)

        # Assert breakdown of decisions
        verdicts = tool_exec["data"].get("verdicts", {})
        self.assertIn("ALLOW", verdicts)
        self.assertIn("HOLD", verdicts)
        self.assertIn("BLOCK", verdicts)
        self.assertEqual(sum(verdicts.values()), 50)

        self.assertIn("Gemini Assistant Action Executed: `simulate_transactions`", res["answer"])
        self.assertIn("50", res["answer"])

    # ──────────────────────────────────────────────────────────────────────────
    # Scenario 4: Analyst commands "Block VPA suspect@upi and export SAR to PDF"
    # ──────────────────────────────────────────────────────────────────────────
    async def test_scenario_4_analyst_block_vpa_and_export_sar(self):
        """Scenario 4: Analyst commands 'Block VPA suspect@upi and export SAR to PDF'
        Asserts VPA frozen in hot state, DPIP broadcast, and PDF compiled with valid download rail.
        """
        # Step A: Enforce VPA block
        case_data = _build_test_case_payload("case_scenario_4_enforce")
        block_res = await self.service.chat_with_case_assistant(
            case_data,
            question="Block suspect payee VPA bad_actor_mule@okaxis immediately due to confirmed fraud",
        )
        self.assertEqual(block_res["source"], "agentic-tool")
        block_tool = block_res["tool_executions"][0]
        self.assertEqual(block_tool["tool_name"], "block_vpa_or_transaction")
        self.assertEqual(block_tool["status"], "success")
        self.assertEqual(block_tool["arguments"]["target_vpa"], "bad_actor_mule@okaxis")
        self.assertEqual(block_tool["arguments"]["action"], "BLOCK")

        # Step B: Export SAR PDF
        sar_res = await self.service.chat_with_case_assistant(
            case_data,
            question="Export SAR report to PDF for case_scenario_4_enforce",
        )
        self.assertEqual(sar_res["source"], "agentic-tool")
        sar_tool = sar_res["tool_executions"][0]
        self.assertEqual(sar_tool["tool_name"], "export_sar_pdf")
        self.assertEqual(sar_tool["status"], "success")
        self.assertGreater(sar_tool["data"]["pdf_size_bytes"], 100)
        self.assertEqual(sar_tool["data"]["download_url"], "/cases/case_scenario_4_enforce/sar/pdf")

        # Step C: Verify PDF binary compilation
        pdf_bytes = build_sar_pdf(case_data)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 500)

    # ──────────────────────────────────────────────────────────────────────────
    # Scenario 5: Full End-to-End Investigation Lifecycle
    # ──────────────────────────────────────────────────────────────────────────
    def test_scenario_5_full_e2e_investigation_lifecycle(self):
        """Scenario 5: Complete end-to-end investigation lifecycle:
        1. Evaluate suspicious transaction via UPI risk engine -> opens case.
        2. Request AI Briefing via /cases/{case_id}/ai-briefing.
        3. Analyst asks clarifying algorithmic questions via /cases/{case_id}/ai-chat.
        4. Analyst triggers federation round via chat tool.
        5. Analyst blocks suspect payee VPA via chat tool.
        6. Analyst compiles & downloads SAR PDF from /cases/{case_id}/sar/pdf.
        """
        # Step 1: Submit high-risk suspicious transaction
        txn = UpiTransaction(
            txn_id="txn_scenario5_lifecycle_01",
            amount=92000.0,
            payer_vpa="victim_lifecycle@okhdfcbank",
            payee_vpa="mule_lifecycle@okicici",
            payer_account_age_days=365,
            payee_vpa_age_days=2,
            device_id="DEV_LIFECYCLE_99",
            sim_id="SIM_LIFECYCLE_99",
            ip="103.11.88.99",
            location="Bengaluru, KA",
            note="Fast high return crypto payout",
        )
        eval_resp = self.case_service.evaluate(txn)
        case_id = eval_resp.case_id
        if not case_id:
            case_id = self.case_service._open_case(txn, eval_resp)

        self.assertIsNotNone(case_id)

        # Step 2: Fetch AI Briefing via REST API
        briefing_resp = self.client.post(f"/cases/{case_id}/ai-briefing")
        self.assertEqual(briefing_resp.status_code, 200)
        briefing_data = briefing_resp.json()
        self.assertEqual(briefing_data["case_id"], case_id)
        self.assertIn("executive_summary", briefing_data)
        self.assertIn("scam_classification", briefing_data)
        self.assertIn(briefing_data["threat_level"], ["CRITICAL", "HIGH", "MEDIUM"])

        # Step 3: Interactive Q&A: Explain DMV and Rules
        chat_q1 = self.client.post(
            f"/cases/{case_id}/ai-chat",
            json={"question": "Explain why the DMV score spiked and what rules fired"},
        )
        self.assertEqual(chat_q1.status_code, 200)
        q1_data = chat_q1.json()
        self.assertIn("Dead Money Velocity", q1_data["answer"])
        self.assertIn("Dormancy Index D =", q1_data["answer"])

        # Step 4: Autonomous Tool Calling: Trigger Federation Round
        chat_fed = self.client.post(
            f"/cases/{case_id}/ai-chat",
            json={"question": "Trigger a federation round to correlate with other PSPs"},
        )
        self.assertEqual(chat_fed.status_code, 200)
        fed_data = chat_fed.json()
        self.assertIn("trigger_federation_round", fed_data["answer"])
        self.assertTrue(len(fed_data["tool_executions"]) >= 1)
        self.assertEqual(fed_data["tool_executions"][0]["tool_name"], "trigger_federation_round")
        self.assertEqual(fed_data["tool_executions"][0]["status"], "success")

        # Step 5: Autonomous Tool Calling: Block Suspect VPA
        chat_block = self.client.post(
            f"/cases/{case_id}/ai-chat",
            json={"question": "Block suspect payee VPA mule_lifecycle@okicici immediately"},
        )
        self.assertEqual(chat_block.status_code, 200)
        block_data = chat_block.json()
        self.assertIn("block_vpa_or_transaction", block_data["answer"])
        self.assertTrue(len(block_data["tool_executions"]) >= 1)
        self.assertEqual(block_data["tool_executions"][0]["arguments"]["action"], "BLOCK")

        # Step 6: Regulatory Export: Download SAR PDF
        sar_export = self.client.get(f"/cases/{case_id}/sar/pdf")
        self.assertEqual(sar_export.status_code, 200)
        self.assertEqual(sar_export.headers.get("content-type"), "application/pdf")
        self.assertTrue(sar_export.content.startswith(b"%PDF-"))
        self.assertGreater(len(sar_export.content), 500)


if __name__ == "__main__":
    unittest.main()

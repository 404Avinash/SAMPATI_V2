"""Comprehensive Unit & Integration Test Suite for Gemini Assistant & Agentic Operations.

Verifies:
1. Deep Context Injection in System & User Prompts (Telemetry, Ledger, Graph Topology, Encyclopedia KB).
2. Algorithmic Explanation of Dead Money Velocity (DMV) with Mathematical Formulas from ENCYCLOPEDIA.md.
3. Autonomous Intent Routing & Dispatch for Platform Operations:
   - trigger_federation_round (Consensus round execution, cross-PSP rings, SAR attachment)
   - simulate_transactions (Synthetic batch injection, scoring, parameter extraction)
   - block_vpa_or_transaction (Hot state memory update, DPIP signal mesh, case escalation)
   - export_sar_pdf (Dynamic SAR PDF compilation, download URL resolution)
4. Mocked Live Gemini Function Calling Response Parsing & Execution Loop.
5. Error Handling & Graceful Recovery during Tool Executions.
6. 100% Backward Compatibility of Class Names, Function Signatures, and Pydantic Model Aliases.
7. FastAPI HTTP Endpoints (/cases/{case_id}/ai-briefing, /cases/{case_id}/ai-chat).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from starlette.testclient import TestClient

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


class TestGeminiAssistantAgentic(unittest.IsolatedAsyncioTestCase):
    """Unit tests for Gemini Assistant deep context injection and agentic tool operations."""

    def setUp(self):
        self.service = GeminiAssistantService(api_key=None)
        self.service.clear_cache()
        self.sample_case = {
            "case_id": "upi_case_agentic_001",
            "status": "OPEN",
            "verdict": "HOLD",
            "risk_score": 88,
            "amount": 95000.0,
            "payer_vpa": "victim_agentic@okhdfcbank",
            "payee_vpa": "mule_agentic@okicici",
            "payer_psp": "okhdfcbank",
            "payee_psp": "okicici",
            "reasons": ["DMV_RAPID_DRAIN", "PASS_THROUGH_CONDUIT", "R_SIM_DEVICE_MISMATCH"],
            "dmv_score": 88.5,
            "adaptive_score": 0.85,
            "network_score": 0.75,
            "ring_members_vpas": ["mule_agentic@okicici", "conduit_99@ybl", "cashout_88@paytm"],
            "ring_hash": "ring_hash_agentic_test_1234",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "trigger_txn": {
                "txn_id": "txn_agentic_trigger_01",
                "payer_vpa": "victim_agentic@okhdfcbank",
                "payee_vpa": "mule_agentic@okicici",
                "amount": 95000.0,
                "device_id": "DEV_FINGERPRINT_9988",
                "sim_id": "SIM_IMSI_123456789",
                "ip": "103.21.244.0",
                "location": "Mumbai, India",
                "note": "Urgent crypto release",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "raw_transactions": [
                {
                    "txn_id": "txn_agentic_trigger_01",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payer_vpa": "victim_agentic@okhdfcbank",
                    "payee_vpa": "mule_agentic@okicici",
                    "amount": 95000.0,
                    "txn_type": "P2P",
                },
                {
                    "txn_id": "txn_agentic_conduit_02",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payer_vpa": "mule_agentic@okicici",
                    "payee_vpa": "conduit_99@ybl",
                    "amount": 90000.0,
                    "txn_type": "P2P",
                },
            ],
            "topology": {
                "fan_in": 1,
                "hops": 2,
                "fan_out": 3,
            },
        }

    # ── Group 1: Deep Context Injection Verification ──────────────────────────

    def test_build_case_dossier_text_completeness(self):
        """Verify build_case_dossier_text aggregates telemetry, ledger, topology, and Encyclopedia KB."""
        dossier = build_case_dossier_text(self.sample_case)

        # Overview & Telemetry checks
        self.assertIn("upi_case_agentic_001", dossier)
        self.assertIn("95,000.00", dossier)
        self.assertIn("victim_agentic@okhdfcbank", dossier)
        self.assertIn("mule_agentic@okicici", dossier)
        self.assertIn("DEV_FINGERPRINT_9988", dossier)
        self.assertIn("SIM_IMSI_123456789", dossier)
        self.assertIn("103.21.244.0", dossier)
        self.assertIn("Urgent crypto release", dossier)

        # Multi-layer score & DMV
        self.assertIn("88.5/100", dossier)
        self.assertIn("CRITICAL", dossier)
        self.assertIn("0.85", dossier)
        self.assertIn("0.75", dossier)

        # Transaction ledger table
        self.assertIn("txn_agentic_trigger_01", dossier)
        self.assertIn("txn_agentic_conduit_02", dossier)
        self.assertIn("P2P", dossier)

        # Topology & Ring
        self.assertIn("ring_hash_agentic_test_1234", dossier)
        self.assertIn("conduit_99@ybl", dossier)
        self.assertIn("cashout_88@paytm", dossier)

        # Encyclopedia Knowledge Base injection
        self.assertIn("SAMPATI ENCYCLOPEDIA ALGORITHMIC KNOWLEDGE BASE", dossier)
        self.assertIn("Dead Money Velocity (DMV) Burst", dossier)
        self.assertIn("Dormancy Index D =", dossier)
        self.assertIn("Drain Ratio R =", dossier)
        self.assertIn("Burst Velocity V =", dossier)

    async def test_offline_dmv_score_explanation_with_encyclopedia_math(self):
        """Verify chat reply explains DMV with exact mathematical formulas in offline mode."""
        questions = [
            "Explain why the DMV score spiked for this case",
            "What is the mathematical formula for Dead Money Velocity?",
            "Why did the velocity score increase?",
        ]

        for q in questions:
            res = await self.service.chat_with_case_assistant(self.sample_case, question=q)
            ans = res["answer"]
            self.assertIn("Dead Money Velocity", ans)
            self.assertIn("88.5/100", ans)
            self.assertIn("CRITICAL", ans)
            self.assertIn("Dormancy Index D =", ans)
            self.assertIn("Drain Ratio R =", ans)
            self.assertIn("Burst Velocity V =", ans)
            self.assertEqual(res["source"], "heuristic-fallback")

    async def test_offline_encyclopedia_concept_search(self):
        """Verify queries regarding platform concepts return Encyclopedia definition & formula."""
        res = await self.service.chat_with_case_assistant(self.sample_case, question="Explain Synthetic Honeypot")
        ans = res["answer"]
        self.assertIn("Synthetic Honeypot Trap Hit", ans)
        self.assertIn("R_HONEYPOT_HIT", ans)
        self.assertIn("Mathematical Definition", ans)
        self.assertIn("Forensic Rationale", ans)

    # ── Group 2: Autonomous Tool Calling: Federation Round ────────────────────

    async def test_intent_routing_trigger_federation_round(self):
        """Verify 'Trigger a federation round' executes federation and returns structured tool results."""
        prompts = [
            "Trigger a federation round",
            "Please run a federated intelligence consensus round",
            "Execute federation sync across PSP nodes",
        ]

        for prompt in prompts:
            res = await self.service.chat_with_case_assistant(self.sample_case, question=prompt)
            self.assertEqual(res["source"], "agentic-tool")
            self.assertTrue(len(res["tool_executions"]) >= 1)

            tool_exec = res["tool_executions"][0]
            self.assertEqual(tool_exec["tool_name"], "trigger_federation_round")
            self.assertEqual(tool_exec["status"], "success")
            self.assertIn("Federation intelligence consensus round completed", tool_exec["result_summary"])

            # Verify markdown synthesis
            ans = res["answer"]
            self.assertIn("Gemini Assistant Action Executed: `trigger_federation_round`", ans)
            self.assertIn("Participating PSP Nodes", ans)
            self.assertIn("Forensic Impact", ans)

    # ── Group 3: Autonomous Tool Calling: Transaction Simulation ──────────────

    async def test_intent_routing_simulate_transactions_custom_parameters(self):
        """Verify simulation prompt parses count, fraud ratio, seed, and executes simulation."""
        prompt = "Simulate 120 synthetic transactions with 25% fraud ratio and seed 99"
        res = await self.service.chat_with_case_assistant(self.sample_case, question=prompt)

        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "simulate_transactions")
        self.assertEqual(tool_exec["status"], "success")
        self.assertEqual(tool_exec["arguments"]["total_txns"], 120)
        self.assertAlmostEqual(tool_exec["arguments"]["fraud_ratio"], 0.25)
        self.assertEqual(tool_exec["arguments"]["seed"], 99)
        self.assertIn("Generated and scored synthetic batch of 120 transactions", tool_exec["result_summary"])

        ans = res["answer"]
        self.assertIn("Gemini Assistant Action Executed: `simulate_transactions`", ans)
        self.assertIn("120", ans)
        self.assertIn("25%", ans)

    # ── Group 4: Autonomous Tool Calling: Block / Hold VPA ────────────────────

    async def test_intent_routing_block_vpa_enforcement(self):
        """Verify 'Block payee VPA' applies hot state freeze, DPIP broadcast, and case escalation."""
        prompt = "Block suspect payee VPA bad_actor_99@okicici immediately due to high fraud risk"
        res = await self.service.chat_with_case_assistant(self.sample_case, question=prompt)

        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "block_vpa_or_transaction")
        self.assertEqual(tool_exec["status"], "success")
        self.assertEqual(tool_exec["arguments"]["target_vpa"], "bad_actor_99@okicici")
        self.assertEqual(tool_exec["arguments"]["action"], "BLOCK")

        ans = res["answer"]
        self.assertIn("Gemini Assistant Action Executed: `block_vpa_or_transaction`", ans)
        self.assertIn("bad_actor_99@okicici", ans)
        self.assertIn("Digital Payments Intelligence Platform (DPIP)", ans)

    # ── Group 5: Autonomous Tool Calling: SAR PDF Export ──────────────────────

    async def test_intent_routing_export_sar_pdf(self):
        """Verify 'Export SAR to PDF' compiles formal SAR document and provides download rail."""
        prompt = "Export SAR report to PDF for regulatory filing"
        res = await self.service.chat_with_case_assistant(self.sample_case, question=prompt)

        self.assertEqual(res["source"], "agentic-tool")
        self.assertTrue(len(res["tool_executions"]) >= 1)

        tool_exec = res["tool_executions"][0]
        self.assertEqual(tool_exec["tool_name"], "export_sar_pdf")
        self.assertEqual(tool_exec["status"], "success")
        self.assertGreater(tool_exec["data"]["pdf_size_bytes"], 100)
        self.assertEqual(tool_exec["data"]["download_url"], f"/cases/{self.sample_case['case_id']}/sar/pdf")

        ans = res["answer"]
        self.assertIn("Gemini Assistant Action Executed: `export_sar_pdf`", ans)
        self.assertIn("SAR_upi_case_agentic_001.pdf", tool_exec["data"]["filename"])

    # ── Group 6: Live Gemini Function Calling Mocking ─────────────────────────

    async def test_mocked_gemini_remote_function_calling_round(self):
        """Verify remote Gemini API returning functionCall is correctly intercepted, dispatched, and reported."""
        service = GeminiAssistantService(api_key="AIzaSyDummyKeyForLiveFunctionCallingTest")

        mock_gemini_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "trigger_federation_round",
                                    "args": {
                                        "case_id": "upi_case_agentic_001",
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
        mock_http_response.json = lambda: mock_gemini_response

        with patch("httpx.AsyncClient.post", return_value=mock_http_response):
            res = await service.chat_with_case_assistant(
                self.sample_case,
                question="Perform a cross-PSP consensus check with other banks",
            )

            self.assertEqual(res["source"], "gemini-ai")
            self.assertTrue(len(res["tool_executions"]) >= 1)
            self.assertEqual(res["tool_executions"][0]["tool_name"], "trigger_federation_round")
            self.assertIn("trigger_federation_round", res["answer"])

    # ── Group 7: Tool Execution Error Recovery ────────────────────────────────

    def test_tool_dispatch_error_recovery(self):
        """Verify _dispatch_tool handles unexpected runtime exceptions gracefully."""
        with patch.object(self.service, "_execute_simulate_transactions", side_effect=RuntimeError("Simulation hardware crash")):
            result = self.service._dispatch_tool("simulate_transactions", {}, self.sample_case)
            self.assertEqual(result.status, "error")
            self.assertIn("Tool execution failed: Simulation hardware crash", result.result_summary)
            self.assertEqual(result.data, {"error": "Simulation hardware crash"})

    # ── Group 8: Backward Compatibility Invariants ───────────────────────────

    def test_backward_compatibility_aliases_and_signatures(self):
        """Verify 100% backward compatibility for all prior Copilot identifiers and aliases."""
        # Class alias
        self.assertIs(GeminiCopilotService, GeminiAssistantService)

        # Singleton helper
        copilot_svc = get_gemini_copilot_service()
        assistant_svc = get_gemini_assistant_service()
        self.assertIsInstance(copilot_svc, GeminiAssistantService)
        self.assertIsInstance(assistant_svc, GeminiAssistantService)

        # Model aliases
        self.assertIs(AiChatResponse, GeminiChatResponse)
        self.assertIs(GeminiAssistantBriefing, AiCaseBriefingResponse)
        self.assertIs(GeminiAssistantChatRequest, AiChatRequest)
        self.assertIs(GeminiAssistantChatResponse, GeminiChatResponse)

        # Model instantiation with tool_executions
        chat_resp = GeminiChatResponse(
            case_id="case_compat_01",
            question="What is the verdict?",
            answer="Transaction is on HOLD.",
            tool_executions=[
                ToolExecutionResult(
                    tool_name="test_tool",
                    arguments={"arg1": "val1"},
                    status="success",
                    result_summary="Completed",
                )
            ],
        )
        self.assertEqual(chat_resp.reply, "Transaction is on HOLD.")
        self.assertEqual(len(chat_resp.tool_executions), 1)

    # ── Group 9: GEMINI_TOOL_DECLARATIONS Schema Invariants ───────────────────

    def test_gemini_tool_declarations_schema_integrity(self):
        """Verify OpenAPI tool declarations schema syntax and parameters."""
        self.assertEqual(len(GEMINI_TOOL_DECLARATIONS), 4)
        tool_names = [t["name"] for t in GEMINI_TOOL_DECLARATIONS]
        self.assertIn("block_vpa_or_transaction", tool_names)
        self.assertIn("trigger_federation_round", tool_names)
        self.assertIn("export_sar_pdf", tool_names)
        self.assertIn("simulate_transactions", tool_names)

        for decl in GEMINI_TOOL_DECLARATIONS:
            self.assertIn("name", decl)
            self.assertIn("description", decl)
            self.assertIn("parameters", decl)
            self.assertEqual(decl["parameters"]["type"], "OBJECT")
            self.assertIn("properties", decl["parameters"])


class TestGeminiAssistantFastApiEndpoints(unittest.TestCase):
    """Integration tests for FastAPI REST routes invoking Gemini Assistant & Tools."""

    def setUp(self):
        self.client = TestClient(app)
        self.case_service = get_upi_case_service()

        # Seed an investigative case
        txn = UpiTransaction(
            txn_id="txn_api_agentic_test_01",
            amount=88000.0,
            payer_vpa="victim_api@okhdfcbank",
            payee_vpa="mule_api@okicici",
            payer_account_age_days=300,
            payee_vpa_age_days=4,
            device_id="DEV_API_1122",
            sim_id="SIM_API_3344",
            ip="103.11.22.33",
            note="Quick payment",
        )
        resp = self.case_service.evaluate(txn)
        self.case_id = resp.case_id or "upi_case_default_test"
        if not resp.case_id:
            # Manually ensure case exists
            self.case_id = self.case_service._open_case(txn, resp)

    def test_post_ai_chat_intent_execution_endpoint(self):
        """Verify POST /cases/{case_id}/ai-chat executes federation tool and returns tool_executions."""
        payload = {"question": "Trigger a federation round"}
        response = self.client.post(f"/cases/{self.case_id}/ai-chat", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["case_id"], self.case_id)
        self.assertEqual(data["question"], "Trigger a federation round")
        self.assertIn("Gemini Assistant Action Executed: `trigger_federation_round`", data["answer"])
        self.assertIn("tool_executions", data)
        self.assertIsInstance(data["tool_executions"], list)
        self.assertTrue(len(data["tool_executions"]) >= 1)
        self.assertEqual(data["tool_executions"][0]["tool_name"], "trigger_federation_round")

    def test_post_ai_chat_dmv_algorithmic_explanation_endpoint(self):
        """Verify POST /cases/{case_id}/ai-chat returns Encyclopedia mathematical formulas for DMV questions."""
        payload = {"question": "Explain why the DMV score spiked"}
        response = self.client.post(f"/cases/{self.case_id}/ai-chat", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("Dead Money Velocity", data["answer"])
        self.assertIn("Dormancy Index D =", data["answer"])
        self.assertIn("Drain Ratio R =", data["answer"])

    def test_post_ai_briefing_deep_context_endpoint(self):
        """Verify POST /cases/{case_id}/ai-briefing generates structured briefing."""
        response = self.client.post(f"/cases/{self.case_id}/ai-briefing")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["case_id"], self.case_id)
        self.assertIn("executive_summary", data)
        self.assertIn("scam_classification", data)
        self.assertIn("confidence_score", data)
        self.assertIn("threat_level", data)
        self.assertIn("recommended_actions", data)


if __name__ == "__main__":
    unittest.main()

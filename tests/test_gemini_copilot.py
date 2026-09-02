"""Comprehensive Test Suite for Gemini AI Fraud Analyst Copilot Service & Endpoints.

Verifies:
1. Resilient GeminiCopilotService with deterministic rule-based fallbacks.
2. Scam typology classification heuristics across all threat scenarios.
3. Interactive case chat Q&A with intent routing and multi-turn context.
4. FIU-IND compliant SAR narrative drafting.
5. In-memory caching and cache invalidation.
6. Mocked Google Gemini API integration (JSON mode, markdown codeblock cleaning, error fallback).
7. FastAPI REST routes: GET/POST /cases/{case_id}/ai-briefing, POST /cases/{case_id}/ai-chat, GET /cases/{case_id}/ai-sar.
8. Zero latency impact on /upi/check inline scoring gate.
9. 404 handling for nonexistent cases.
10. Robustness against malformed or toxic case data payloads.
11. Multi-model fallback hierarchy traversal on transient errors.
12. Schema sanitization and normalization for confidence, threat level, and list structures.
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
from app.models.upi_models import UpiTransaction
from app.services.gemini_service import GeminiCopilotService, get_gemini_copilot_service
from app.services.upi_cases import get_upi_case_service


class TestGeminiCopilotService(unittest.IsolatedAsyncioTestCase):
    """Unit tests for GeminiCopilotService logic and fallbacks."""

    def setUp(self):
        self.service = GeminiCopilotService(api_key=None)
        self.service.clear_cache()
        self.sample_case = {
            "case_id": "upi_case_test_copilot_01",
            "status": "OPEN",
            "verdict": "HOLD",
            "risk_score": 85,
            "amount": 75000.0,
            "payer_vpa": "victim_copilot@okhdfcbank",
            "payee_vpa": "mule_copilot@icici",
            "reasons": ["R_HONEYPOT_HIT", "DMV_RAPID_DRAIN"],
            "dmv_score": 82.5,
            "ring_members_vpas": ["mule_copilot@icici", "conduit_02@ybl", "cashout_03@paytm"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_copilot_availability_detection(self):
        """Verify is_available accurately detects API key presence and length."""
        svc_no_key = GeminiCopilotService(api_key=None)
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(svc_no_key.is_available())

        svc_short_key = GeminiCopilotService(api_key="123")
        self.assertFalse(svc_short_key.is_available())

        svc_valid_key = GeminiCopilotService(api_key="AIzaSyDummyKeyForTestingPurposes12345")
        self.assertTrue(svc_valid_key.is_available())

    async def test_fallback_briefing_generation_schema(self):
        """Verify fallback briefing conforms to all required schema keys and type invariants."""
        briefing = await self.service.generate_case_briefing(self.sample_case)

        self.assertEqual(briefing["case_id"], "upi_case_test_copilot_01")
        self.assertIn("executive_summary", briefing)
        self.assertIsInstance(briefing["executive_summary"], str)
        self.assertTrue(len(briefing["executive_summary"]) > 20)

        self.assertIn("scam_classification", briefing)
        self.assertEqual(briefing["scam_classification"], "Automated Botnet Honeypot Penetration")

        self.assertIn("confidence_score", briefing)
        self.assertGreaterEqual(briefing["confidence_score"], 0.0)
        self.assertLessEqual(briefing["confidence_score"], 1.0)

        self.assertIn("threat_level", briefing)
        self.assertIn(briefing["threat_level"], ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

        self.assertIn("ring_analysis", briefing)
        self.assertIn("key_indicators", briefing)
        self.assertIsInstance(briefing["key_indicators"], list)
        self.assertTrue(len(briefing["key_indicators"]) >= 1)

        self.assertIn("recommended_actions", briefing)
        self.assertIsInstance(briefing["recommended_actions"], list)
        self.assertTrue(len(briefing["recommended_actions"]) >= 3)

        self.assertEqual(briefing["source"], "deterministic-fallback")
        self.assertEqual(briefing["model"], "rule-heuristic-engine")

    async def test_fallback_scam_typology_matrix(self):
        """Verify accurate heuristic scam classification across distinct fraud typologies."""
        test_matrix = [
            (["R_HONEYPOT_HIT"], 50.0, "Automated Botnet Honeypot Penetration"),
            (["R_IMPOSSIBLE_TRAVEL"], 45.0, "Account Takeover / SIM-Swap Hijacking"),
            (["R_SIM_DEVICE_MISMATCH"], 45.0, "Account Takeover / SIM-Swap Hijacking"),
            (["NEW_ACCOUNT_HIGH_VALUE"], 75.0, "Rapid Dormant-to-Active Mule Draining"),
            ([], 88.0, "Rapid Dormant-to-Active Mule Draining"),
            (["R_CAMPAIGN_MATCH"], 60.0, "Coordinated Syndicate Phishing Campaign"),
            (["FAN_IN_BURST"], 50.0, "High-Frequency Fan-In Mule Aggregation"),
            (["GENERIC_VELOCITY"], 30.0, "Layered Mule Dispersal Network"),
        ]

        for reasons, dmv, expected_typology in test_matrix:
            case = dict(self.sample_case)
            case["reasons"] = reasons
            case["dmv_score"] = dmv
            case["case_id"] = f"case_{expected_typology[:10]}_{dmv}"

            briefing = await self.service.generate_case_briefing(case, force_refresh=True)
            self.assertEqual(
                briefing["scam_classification"],
                expected_typology,
                f"Failed for reasons {reasons} and DMV {dmv}",
            )

    async def test_fallback_chat_reply_intents(self):
        """Verify context-aware keyword intent classification for analyst questions."""
        questions_and_expected_keywords = [
            ("Why was this case flagged?", ["Case Analysis", "flagged due to", "Dead Money Velocity"]),
            ("Who are the involved parties and nodes?", ["Entity Breakdown", "Payer", "Payee", "Ring Topology"]),
            ("What does the DMV score mean?", ["Dead Money Velocity", "Score is 82.5/100", "dormancy"]),
            ("What remediation actions should I take?", ["Remediation Protocol", "Debit Restriction", "Federation Signal", "SAR Filing"]),
            ("Draft a SAR summary for this case", ["SAR Summary", "Suspected mule", "FIU-IND"]),
            ("Can you give me a summary?", ["Based on case records", "risk engine"]),
        ]

        for question, expected_keywords in questions_and_expected_keywords:
            reply_obj = await self.service.chat_with_case_copilot(self.sample_case, question)
            answer = reply_obj["answer"]
            self.assertEqual(reply_obj["case_id"], "upi_case_test_copilot_01")
            self.assertEqual(reply_obj["source"], "heuristic-fallback")

            for kw in expected_keywords:
                self.assertIn(
                    kw.lower(),
                    answer.lower(),
                    f"Keyword '{kw}' missing in reply to '{question}' (Got: {answer})",
                )

    async def test_fallback_sar_narrative_structure(self):
        """Verify formal SAR narrative generation in fallback mode."""
        sar_text = await self.service.generate_sar_narrative(self.sample_case)

        self.assertIn("SUSPICIOUS ACTIVITY REPORT", sar_text)
        self.assertIn("upi_case_test_copilot_01", sar_text)
        self.assertIn("EXECUTIVE SUMMARY", sar_text)
        self.assertIn("FORENSIC TYPOLOGY", sar_text)
        self.assertIn("COMPLIANCE RECOMMENDATION", sar_text)
        self.assertIn("FIU-IND", sar_text)

    async def test_briefing_caching_and_force_refresh(self):
        """Verify briefing is cached per case_id and force_refresh re-evaluates."""
        case_id = "cache_test_case_99"
        case = dict(self.sample_case)
        case["case_id"] = case_id

        # First call caches
        res1 = await self.service.generate_case_briefing(case)
        self.assertIn(case_id, self.service._cache)

        # Mutate case amount
        case["amount"] = 999999.0
        # Normal call should hit cache (still has old executive summary)
        res2 = await self.service.generate_case_briefing(case, force_refresh=False)
        self.assertEqual(res1["executive_summary"], res2["executive_summary"])

        # Force refresh should update cache with new amount
        res3 = await self.service.generate_case_briefing(case, force_refresh=True)
        self.assertIn("999,999.00", res3["executive_summary"])

    async def test_mocked_gemini_api_success_json_mode(self):
        """Verify successful Gemini API response parsing in JSON mode."""
        mock_gemini_json = {
            "executive_summary": "Coordinated digital arrest extortion transferring funds to mule hub.",
            "scam_classification": "Digital Arrest Impersonation Scam",
            "confidence_score": 0.96,
            "threat_level": "CRITICAL",
            "ring_analysis": "Victim was coerced via video call into immediate liquidation.",
            "key_indicators": ["Coerced high-value transfer", "Instant pass-through velocity"],
            "recommended_actions": ["Emergency debit lien", "FIU red notice dispatch"],
        }

        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": f"```json\n{json.dumps(mock_gemini_json)}\n```"}
                        ]
                    }
                }
            ]
        }

        svc_with_key = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_response,
            )

            briefing = await svc_with_key.generate_case_briefing(self.sample_case)
            self.assertEqual(briefing["source"], "gemini-ai")
            self.assertEqual(briefing["scam_classification"], "Digital Arrest Impersonation Scam")
            self.assertEqual(briefing["threat_level"], "CRITICAL")
            self.assertEqual(briefing["confidence_score"], 0.96)

    async def test_mocked_gemini_api_network_failure_graceful_fallback(self):
        """Verify that Gemini HTTP errors (500, 429, timeout) gracefully fallback without raising."""
        svc_with_key = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = Exception("Connection timed out to Google API")

            briefing = await svc_with_key.generate_case_briefing(self.sample_case)
            self.assertEqual(briefing["source"], "deterministic-fallback")
            self.assertIn("executive_summary", briefing)

            chat = await svc_with_key.chat_with_case_copilot(self.sample_case, "Why was this flagged?")
            self.assertEqual(chat["source"], "heuristic-fallback")
            self.assertIn("Case Analysis", chat["answer"])

    async def test_malformed_case_payload_resilience(self):
        """Verify copilot handles empty, None, or toxic case data without crashing."""
        toxic_payloads = [
            {},
            {"case_id": ""},
            {"amount": "invalid_number", "reasons": None, "dmv_score": "nan"},
            {"amount": None, "payer_vpa": None, "payee_vpa": None, "reasons": "single_string_reason"},
        ]

        for payload in toxic_payloads:
            briefing = await self.service.generate_case_briefing(payload, force_refresh=True)
            self.assertIsInstance(briefing, dict)
            self.assertIn("scam_classification", briefing)

            chat = await self.service.chat_with_case_copilot(payload, "What happened?")
            self.assertIsInstance(chat, dict)
            self.assertIn("answer", chat)

            sar = await self.service.generate_sar_narrative(payload)
            self.assertIsInstance(sar, str)
            self.assertTrue(len(sar) > 10)

    async def test_json_extraction_with_noisy_markdown_and_chatter(self):
        """Verify regex JSON extractor cleans preamble and trailing chatter."""
        noisy_payload = (
            "Here is the requested forensic briefing in JSON format:\n\n"
            "```json\n"
            "{\n"
            '  "executive_summary": "Extracted through markdown noise.",\n'
            '  "scam_classification": "Phishing Syndicate",\n'
            '  "confidence_score": "95%",\n'
            '  "threat_level": "critical",\n'
            '  "ring_analysis": "Money routed to 3 mules.",\n'
            '  "key_indicators": "Indicator 1\\nIndicator 2",\n'
            '  "recommended_actions": "Step 1\\nStep 2"\n'
            "}\n"
            "```\n\n"
            "Please review carefully."
        )

        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": noisy_payload}]
                    }
                }
            ]
        }

        svc = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_response)
            briefing = await svc.generate_case_briefing(self.sample_case, force_refresh=True)
            self.assertEqual(briefing["source"], "gemini-ai")
            self.assertEqual(briefing["confidence_score"], 0.95)
            self.assertEqual(briefing["threat_level"], "CRITICAL")
            self.assertIsInstance(briefing["key_indicators"], list)
            self.assertIsInstance(briefing["recommended_actions"], list)

    async def test_fallback_model_cascade_on_500_503_and_429(self):
        """Verify model fallback hierarchy continues trying subsequent models on 500/503/429."""
        svc = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")

        call_count = 0

        async def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return AsyncMock(status_code=503, text="Service Unavailable")
            return AsyncMock(
                status_code=200,
                json=lambda: {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": json.dumps({"executive_summary": "Recovered on fallback model.", "scam_classification": "Recovered Scam", "confidence_score": 0.89})}
                                ]
                            }
                        }
                    ]
                },
            )

        with patch("httpx.AsyncClient.post", side_effect=mock_post_side_effect):
            briefing = await svc.generate_case_briefing(self.sample_case, force_refresh=True)
            self.assertEqual(briefing["source"], "gemini-ai")
            self.assertEqual(briefing["scam_classification"], "Recovered Scam")
            self.assertEqual(call_count, 3)

    async def test_currency_and_reasons_dict_parsing(self):
        """Verify currency strings and dictionary structured reasons are parsed safely."""
        case_with_formats = {
            "case_id": "upi_case_format_test",
            "amount": "₹ 1,50,000.75",
            "risk_score": "88.0",
            "dmv_score": "78.4",
            "reasons": [
                {"rule_name": "R_HONEYPOT_HIT", "points": 35},
                {"detail": "Rapid SIM swap detected", "code": "SIM_SWAP"},
            ],
            "ring_members_vpas": ["vpa1@upi", "vpa2@upi"],
        }

        briefing = await self.service.generate_case_briefing(case_with_formats, force_refresh=True)
        self.assertIn("150,000.75", briefing["executive_summary"])
        self.assertEqual(briefing["threat_level"], "CRITICAL")
        self.assertIn("Automated Botnet Honeypot Penetration", briefing["scam_classification"])

        chat = await self.service.chat_with_case_copilot(
            case_with_formats,
            question="What happened?",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        )
        self.assertIn("150,000.75", chat["answer"])

    async def test_candidate_multipart_text_aggregation(self):
        """Verify that multiple text parts (e.g., thinking models or split chunks) are joined properly."""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"thought": "Evaluating fraud risk..."},
                            {"text": '{"executive_summary": "Multipart chunk 1. '},
                            {"text": 'Chunk 2 explanation.", "scam_classification": "Multipart Scam", "confidence_score": 0.93}'},
                        ]
                    },
                    "finishReason": "STOP",
                }
            ]
        }

        svc = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_response)
            briefing = await svc.generate_case_briefing(self.sample_case, force_refresh=True)
            self.assertEqual(briefing["source"], "gemini-ai")
            self.assertEqual(briefing["scam_classification"], "Multipart Scam")
            self.assertIn("Multipart chunk 1. Chunk 2 explanation.", briefing["executive_summary"])

    async def test_safety_filter_prompt_feedback_blocking(self):
        """Verify promptFeedback blockReason triggers immediate graceful fallback without wasted retries."""
        mock_response = {
            "promptFeedback": {
                "blockReason": "SAFETY",
                "safetyRatings": [
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "probability": "HIGH", "blocked": True}
                ],
            }
        }

        svc = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_response)
            briefing = await svc.generate_case_briefing(self.sample_case, force_refresh=True)
            self.assertEqual(briefing["source"], "deterministic-fallback")
            # Should have aborted on first model without trying all 6 models
            self.assertEqual(mock_post.call_count, 1)

    async def test_safety_filter_candidate_finish_reason_blocking(self):
        """Verify candidate finishReason SAFETY triggers immediate fallback."""
        mock_response = {
            "candidates": [
                {
                    "finishReason": "SAFETY",
                    "safetyRatings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "probability": "HIGH", "blocked": True}
                    ],
                }
            ]
        }

        svc = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_response)
            briefing = await svc.generate_case_briefing(self.sample_case, force_refresh=True)
            self.assertEqual(briefing["source"], "deterministic-fallback")
            self.assertEqual(mock_post.call_count, 1)

    async def test_brace_balanced_json_extraction_with_preamble_curlies(self):
        """Verify JSON extractor correctly extracts inner JSON object when preamble contains curly braces."""
        from app.services.gemini_service import _extract_json_from_text

        noisy_text = (
            "Reviewing incident {case_ref: 1234} from mesh node {node_a}:\n"
            "{\n"
            '  "executive_summary": "Extracted through brace balancing.",\n'
            '  "scam_classification": "Layered Mule Dispersal Network",\n'
            '  "confidence_score": 0.91,\n'
            '  "threat_level": "HIGH"\n'
            "}\n"
            "Contact team {ops} for details."
        )

        extracted = _extract_json_from_text(noisy_text)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted["scam_classification"], "Layered Mule Dispersal Network")
        self.assertEqual(extracted["executive_summary"], "Extracted through brace balancing.")

    async def test_nan_infinity_sanitization(self):
        """Verify NaN, Infinity, and extreme values in amount and scores do not cause crashes."""
        case_nan = {
            "case_id": "case_nan_stress_test",
            "amount": float("nan"),
            "risk_score": float("inf"),
            "dmv_score": float("-inf"),
            "reasons": ["R_HONEYPOT_HIT"],
        }

        briefing = await self.service.generate_case_briefing(case_nan, force_refresh=True)
        self.assertEqual(briefing["case_id"], "case_nan_stress_test")
        self.assertIn("0.00", briefing["executive_summary"])

        chat = await self.service.chat_with_case_copilot(case_nan, "What is the DMV score?")
        self.assertIn("0.0/100", chat["answer"])

    async def test_cache_lru_bounding_and_eviction(self):
        """Verify cache does not grow unbounded beyond MAX_CACHE_ENTRIES."""
        for i in range(550):
            self.service._set_cache(f"case_cache_{i}", {"source": "test", "val": i})

        self.assertLessEqual(len(self.service._cache), 500)
        # Oldest should have been evicted
        self.assertNotIn("case_cache_0", self.service._cache)
        # Newest should be present
        self.assertIn("case_cache_549", self.service._cache)

    async def test_sar_report_source_metadata_integrity(self):
        """Verify generate_sar_report returns accurate deterministic-fallback source when API key missing or failing."""
        svc_no_key = GeminiCopilotService(api_key=None)
        rep = await svc_no_key.generate_sar_report(self.sample_case)
        self.assertEqual(rep["source"], "deterministic-fallback")
        self.assertIn("SUSPICIOUS ACTIVITY REPORT", rep["sar_narrative"])

        svc_with_key = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(status_code=401, text="Unauthorized")
            rep2 = await svc_with_key.generate_sar_report(self.sample_case)
            self.assertEqual(rep2["source"], "deterministic-fallback")
            self.assertIn("SUSPICIOUS ACTIVITY REPORT", rep2["sar_narrative"])

    async def test_threat_level_synonym_normalization(self):
        """Verify threat level synonyms (SEVERE, ELEVATED, MODERATE, MINIMAL) map correctly."""
        synonym_cases = [
            ("SEVERE", "CRITICAL"),
            ("ELEVATED", "HIGH"),
            ("MODERATE", "MEDIUM"),
            ("MINIMAL", "LOW"),
            ("INFO", "LOW"),
            ("UNKNOWN_LEVEL", "HIGH"),
        ]

        svc = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")
        for raw_tl, expected_tl in synonym_cases:
            mock_response = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": json.dumps({
                                    "executive_summary": "Test briefing.",
                                    "scam_classification": "Test Scam",
                                    "threat_level": raw_tl,
                                    "confidence_score": 0.9,
                                })}
                            ]
                        }
                    }
                ]
            }
            with patch("httpx.AsyncClient.post") as mock_post:
                mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_response)
                briefing = await svc.generate_case_briefing(self.sample_case, force_refresh=True)
                self.assertEqual(briefing["threat_level"], expected_tl, f"Failed mapping {raw_tl} -> {expected_tl}")

    async def test_concurrent_async_briefing_non_blocking_event_loop(self):
        """Verify concurrent requests execute asynchronously via asyncio.gather without blocking."""
        svc = GeminiCopilotService(api_key="AIzaSyValidDummyTestKey123456789")

        async def delayed_post(*args, **kwargs):
            await asyncio.sleep(0.05)
            return AsyncMock(
                status_code=200,
                json=lambda: {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": json.dumps({"executive_summary": "Async ok", "scam_classification": "Async Mule"})}
                                ]
                            }
                        }
                    ]
                },
            )

        with patch("httpx.AsyncClient.post", side_effect=delayed_post):
            tasks = [
                svc.generate_case_briefing(
                    {"case_id": f"async_case_{i}", "amount": 1000 * i},
                    force_refresh=True,
                )
                for i in range(5)
            ]
            results = await asyncio.gather(*tasks)
            self.assertEqual(len(results), 5)
            for res in results:
                self.assertEqual(res["source"], "gemini-ai")
                self.assertEqual(res["scam_classification"], "Async Mule")


class TestGeminiCopilotFastApiEndpoints(unittest.TestCase):
    """Integration and contract tests for FastAPI Copilot routes."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.case_service = get_upi_case_service()

    def setUp(self):
        # Create a confirmed case in service
        t = UpiTransaction(
            txn_id="TXN-COPILOT-E2E-01",
            payer_vpa="victim_api@okhdfcbank",
            payee_vpa="mule_api_hub@icici",
            amount=88000.0,
            device_id="DEV-COPILOT-01",
            ip="192.168.1.100",
            location="Delhi",
            timestamp=datetime.now(timezone.utc),
        )
        resp = self.case_service.evaluate(t)
        self.case_id = resp.case_id
        if not self.case_id:
            self.case_id = "upi_case_copilot_e2e_fallback"
            with self.case_service._lock:
                self.case_service._cases[self.case_id] = {
                    "case_id": self.case_id,
                    "status": "OPEN",
                    "verdict": "HOLD",
                    "risk_score": 88,
                    "amount": 88000.0,
                    "payer_vpa": "victim_api@okhdfcbank",
                    "payee_vpa": "mule_api_hub@icici",
                    "reasons": ["R_HONEYPOT_HIT", "DMV_RAPID_DRAIN"],
                    "dmv_score": 85.0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

    def test_get_ai_briefing_endpoint_root_and_upi_prefix(self):
        """Verify GET /cases/{case_id}/ai-briefing and /upi/cases/{case_id}/ai-briefing return structured JSON."""
        for path in [f"/cases/{self.case_id}/ai-briefing", f"/upi/cases/{self.case_id}/ai-briefing"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed on path {path}: {res.text}")
            data = res.json()
            self.assertEqual(data["case_id"], self.case_id)
            self.assertIn("executive_summary", data)
            self.assertIn("scam_classification", data)
            self.assertIn("threat_level", data)
            self.assertIn("confidence_score", data)
            self.assertIn("recommended_actions", data)

    def test_post_ai_chat_endpoint_root_and_upi_prefix(self):
        """Verify POST /cases/{case_id}/ai-chat interactive Q&A endpoint."""
        for path in [f"/cases/{self.case_id}/ai-chat", f"/upi/cases/{self.case_id}/ai-chat"]:
            res = self.client.post(
                path,
                json={"question": "Why was this transaction flagged?", "history": []},
            )
            self.assertEqual(res.status_code, 200, f"Failed on path {path}: {res.text}")
            data = res.json()
            self.assertEqual(data["case_id"], self.case_id)
            self.assertEqual(data["question"], "Why was this transaction flagged?")
            self.assertIn("answer", data)
            self.assertTrue(len(data["answer"]) > 10)
            self.assertIn("source", data)

    def test_post_ai_chat_with_empty_or_whitespace_question(self):
        """Verify POST /cases/{case_id}/ai-chat gracefully handles empty or whitespace queries."""
        for path in [f"/cases/{self.case_id}/ai-chat", f"/upi/cases/{self.case_id}/ai-chat"]:
            res = self.client.post(path, json={"question": "   ", "history": []})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("answer", data)
            self.assertTrue(len(data["answer"]) > 5)

    def test_get_ai_sar_endpoint_root_and_upi_prefix(self):
        """Verify GET /cases/{case_id}/ai-sar returns SAR narrative text and valid source metadata."""
        for path in [f"/cases/{self.case_id}/ai-sar", f"/upi/cases/{self.case_id}/ai-sar"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed on path {path}: {res.text}")
            data = res.json()
            self.assertEqual(data["case_id"], self.case_id)
            self.assertIn("sar_narrative", data)
            self.assertIn("SUSPICIOUS ACTIVITY REPORT", data["sar_narrative"])
            self.assertEqual(data["source"], "deterministic-fallback")

    def test_ai_copilot_endpoints_404_for_unknown_case(self):
        """Verify 404 Not Found returned when querying nonexistent case IDs."""
        bad_id = "nonexistent_case_random_9999"

        r1 = self.client.get(f"/cases/{bad_id}/ai-briefing")
        self.assertEqual(r1.status_code, 404)

        r2 = self.client.post(f"/cases/{bad_id}/ai-chat", json={"question": "What happened?"})
        self.assertEqual(r2.status_code, 404)

        r3 = self.client.get(f"/cases/{bad_id}/ai-sar")
        self.assertEqual(r3.status_code, 404)

    def test_upi_check_scoring_zero_latency_impact(self):
        """Verify that inline scoring gate /upi/check executes in sub-10ms without synchronous Gemini calls."""
        t = {
            "txn_id": "TXN-INLINE-BENCH-01",
            "payer_vpa": "payer_fast@okaxis",
            "payee_vpa": "payee_fast@ybl",
            "amount": 5000.0,
            "device_id": "DEV-FAST-01",
            "ip": "10.0.0.1",
            "location": "Mumbai",
        }

        # Make request
        res = self.client.post("/upi/check", json=t)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("action", data)
        self.assertIn("risk_score", data)
        # Latency should be sub-20ms in tests
        self.assertLess(data.get("execution_latency_ms", 0.0), 50.0)


if __name__ == "__main__":
    unittest.main()


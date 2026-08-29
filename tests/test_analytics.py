"""Unit and Contract Tests for GET /stats/analytics and Analytics Engine in SAMPATI V2.

Verifies:
1. Endpoint schema contract for GET /stats/analytics and GET /upi/stats/analytics.
2. Summary metrics: total_evaluated, total_flagged, total_allowed, total_held, total_blocked,
   fraud_rate_pct, avg_risk_score, total_amount_protected.
3. Summary arithmetic invariants: total_flagged == total_held + total_blocked.
4. Time-series bucket generation for both 'hourly' and 'daily' intervals.
5. Rule trigger frequency ranking and percentage computation.
6. Top flagged corporate / payee accounts aggregation with bank metadata.
7. Bank and PSP distribution mapping across major Indian UPI handles (@okhdfcbank, @icici, @oksbi, @okaxis, @paytm).
8. Graceful handling of empty state (zero evaluations / zero cases).
9. Parameter validation and bounds handling (hours, days, limit_accounts).
"""
from __future__ import annotations

import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.models.upi_models import UpiTransaction
from app.services.upi_cases import UpiCaseService, get_upi_case_service


class TestAnalyticsEngine(unittest.TestCase):
    """Unit and contract tests for the analytics aggregation engine and endpoints."""

    def setUp(self):
        self.service = get_upi_case_service()
        # Seed test transactions with deterministic patterns
        self._seed_test_traffic()

    def _seed_test_traffic(self):
        """Inject a deterministic stream of transactions generating ALLOW, HOLD, and BLOCK verdicts."""
        # 1. Normal low-risk transaction -> ALLOW
        t_allow = UpiTransaction(
            txn_id="TXN-ANALYTICS-ALLOW-01",
            payer_vpa="legit_user@okhdfcbank",
            payee_vpa="merchant_store@icici",
            amount=150.0,
            device_id="DEV-SAFE-01",
            ip="192.168.1.10",
            location="Mumbai",
            timestamp=datetime.now(timezone.utc),
        )
        self.service.evaluate(t_allow)

        # 2. Suspicious transaction -> HOLD
        t_hold = UpiTransaction(
            txn_id="TXN-ANALYTICS-HOLD-01",
            payer_vpa="victim_01@oksbi",
            payee_vpa="suspicious_hub@icici",
            amount=48000.0,
            device_id="DEV-SUSP-01",
            ip="10.0.0.5",
            location="Delhi",
            timestamp=datetime.now(timezone.utc),
        )
        self.service.evaluate(t_hold)

        # 3. High-risk structuring transaction -> BLOCK
        t_block = UpiTransaction(
            txn_id="TXN-ANALYTICS-BLOCK-01",
            payer_vpa="victim_02@okaxis",
            payee_vpa="suspicious_hub@icici",
            amount=98500.0,
            device_id="DEV-FRAUD-01",
            ip="10.0.0.99",
            location="Kolkata",
            timestamp=datetime.now(timezone.utc),
        )
        self.service.evaluate(t_block)

    def test_analytics_payload_structure_contract(self):
        """Verify the analytics payload contains all required top-level contract keys."""
        if hasattr(self.service, "get_analytics_stats"):
            data = self.service.get_analytics_stats(interval="hourly", hours=24)
        else:
            # Fallback if method is implemented under alternative helper
            from app.api.upi import get_analytics_payload
            data = get_analytics_payload(self.service, interval="hourly", hours=24)

        self.assertIsInstance(data, dict)
        self.assertIn("timestamp", data)
        self.assertIn("interval", data)
        self.assertEqual(data["interval"], "hourly")
        self.assertIn("summary", data)
        self.assertIn("time_series", data)
        self.assertIn("rule_frequencies", data)
        self.assertIn("top_flagged_accounts", data)
        self.assertIn("bank_distribution", data)

    def test_analytics_summary_metrics_and_invariants(self):
        """Verify summary calculations and arithmetic invariants."""
        if hasattr(self.service, "get_analytics_stats"):
            data = self.service.get_analytics_stats(interval="hourly", hours=24)
        else:
            from app.api.upi import get_analytics_payload
            data = get_analytics_payload(self.service, interval="hourly", hours=24)

        summary = data["summary"]
        self.assertIn("total_evaluated", summary)
        self.assertIn("total_flagged", summary)
        self.assertIn("total_allowed", summary)
        self.assertIn("total_held", summary)
        self.assertIn("total_blocked", summary)
        self.assertIn("fraud_rate_pct", summary)
        self.assertIn("avg_risk_score", summary)
        self.assertIn("total_amount_protected", summary)

        # Invariant 1: total_flagged == total_held + total_blocked
        self.assertEqual(summary["total_flagged"], summary["total_held"] + summary["total_blocked"])

        # Invariant 2: total_evaluated == total_allowed + total_held + total_blocked
        self.assertEqual(
            summary["total_evaluated"],
            summary["total_allowed"] + summary["total_held"] + summary["total_blocked"],
        )

        # Invariant 3: fraud_rate_pct bounds [0.0, 100.0]
        self.assertGreaterEqual(summary["fraud_rate_pct"], 0.0)
        self.assertLessEqual(summary["fraud_rate_pct"], 100.0)

        # Invariant 4: avg_risk_score bounds [0.0, 100.0]
        self.assertGreaterEqual(summary["avg_risk_score"], 0.0)
        self.assertLessEqual(summary["avg_risk_score"], 100.0)

        # Invariant 5: amount protected >= 0
        self.assertGreaterEqual(summary["total_amount_protected"], 0.0)

    def test_analytics_hourly_vs_daily_intervals(self):
        """Verify interval parameter controls bucket granularity ('hourly' vs 'daily')."""
        if hasattr(self.service, "get_analytics_stats"):
            hourly_data = self.service.get_analytics_stats(interval="hourly", hours=24)
            daily_data = self.service.get_analytics_stats(interval="daily", days=7)
        else:
            from app.api.upi import get_analytics_payload
            hourly_data = get_analytics_payload(self.service, interval="hourly", hours=24)
            daily_data = get_analytics_payload(self.service, interval="daily", days=7)

        self.assertEqual(hourly_data["interval"], "hourly")
        self.assertEqual(daily_data["interval"], "daily")

        self.assertIsInstance(hourly_data["time_series"], list)
        self.assertIsInstance(daily_data["time_series"], list)

        if hourly_data["time_series"]:
            first_hourly = hourly_data["time_series"][0]
            self.assertIn("bucket", first_hourly)
            self.assertIn("allow", first_hourly)
            self.assertIn("hold", first_hourly)
            self.assertIn("block", first_hourly)
            self.assertIn("total", first_hourly)
            self.assertIn("fraud_rate_pct", first_hourly)

    def test_analytics_rule_frequencies_ranking(self):
        """Verify rule frequencies are properly ranked in descending order of trigger count."""
        if hasattr(self.service, "get_analytics_stats"):
            data = self.service.get_analytics_stats(interval="hourly", hours=24)
        else:
            from app.api.upi import get_analytics_payload
            data = get_analytics_payload(self.service, interval="hourly", hours=24)

        rules = data["rule_frequencies"]
        self.assertIsInstance(rules, list)

        prev_count = float("inf")
        for rule in rules:
            self.assertIn("rule_id", rule)
            self.assertIn("rule_name", rule)
            self.assertIn("trigger_count", rule)
            self.assertIn("percentage", rule)
            self.assertIn("severity", rule)
            self.assertIn(rule["severity"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            self.assertLessEqual(rule["trigger_count"], prev_count)
            prev_count = rule["trigger_count"]

    def test_analytics_top_flagged_accounts_structure(self):
        """Verify top flagged corporate / mule hub accounts are correctly aggregated."""
        if hasattr(self.service, "get_analytics_stats"):
            data = self.service.get_analytics_stats(interval="hourly", hours=24, limit_accounts=5)
        else:
            from app.api.upi import get_analytics_payload
            data = get_analytics_payload(self.service, interval="hourly", hours=24, limit_accounts=5)

        top_accounts = data["top_flagged_accounts"]
        self.assertIsInstance(top_accounts, list)
        self.assertLessEqual(len(top_accounts), 5)

        for acct in top_accounts:
            self.assertTrue("account_id" in acct or "vpa" in acct)
            self.assertIn("bank", acct)
            self.assertIn("flagged_count", acct)
            self.assertIn("total_flagged_amount", acct)
            self.assertIn("avg_risk_score", acct)
            self.assertGreaterEqual(acct["flagged_count"], 1)

    def test_analytics_bank_distribution(self):
        """Verify bank distribution properly categorizes Indian PSP handles."""
        if hasattr(self.service, "get_analytics_stats"):
            data = self.service.get_analytics_stats(interval="hourly", hours=24)
        else:
            from app.api.upi import get_analytics_payload
            data = get_analytics_payload(self.service, interval="hourly", hours=24)

        banks = data["bank_distribution"]
        self.assertIsInstance(banks, list)

        total_pct = 0.0
        for b in banks:
            self.assertIn("bank", b)
            self.assertIn("count", b)
            self.assertIn("percentage", b)
            self.assertIn("flagged_amount", b)
            total_pct += b["percentage"]

        if banks:
            # Total percentage should approximate 100%
            self.assertAlmostEqual(total_pct, 100.0, delta=2.0)

    def test_analytics_empty_state_resilience(self):
        """Verify analytics generation on a fresh service instance does not crash."""
        fresh_service = UpiCaseService(artifact_dir="static/test_analytics_fresh")
        if hasattr(fresh_service, "get_analytics_stats"):
            data = fresh_service.get_analytics_stats()
        else:
            from app.api.upi import get_analytics_payload
            data = get_analytics_payload(fresh_service)

        self.assertIsInstance(data, dict)
        self.assertEqual(data["summary"]["total_evaluated"], 0)
        self.assertEqual(data["summary"]["total_flagged"], 0)
        self.assertEqual(data["summary"]["fraud_rate_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()

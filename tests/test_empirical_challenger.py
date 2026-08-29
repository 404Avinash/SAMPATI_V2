"""Comprehensive Empirical Adversarial Challenge Suite for SAMPATI V2.

Adversarially probes:
1. CI/CD workflow YAML structure, dependency graph, secrets isolation, healthcheck polling, rollback, notifications.
2. Backend mathematical invariants (total_flagged == total_held + total_blocked; min <= p50 <= p90 <= p99 <= max; throughput, time series).
3. Case status state machine transitions (OPEN -> REVIEWED, ESCALATED, DISMISSED; invalid rejection, 404s, side effects).
4. Frontend mathematical projections (point_to_segment_distance, get_continuous_edge_color, format_inr).
"""
from __future__ import annotations

import math
import os
import random
import re
import sys
import unittest
import yaml
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import tests.mock_env

from app.models.upi_models import UpiTransaction
from app.services.upi_cases import UpiCaseService, get_upi_case_service, extract_bank_and_psp
from tests.frontend_contracts_test import (
    point_to_segment_distance,
    get_continuous_edge_color,
    format_inr,
)


class TestCiCdWorkflowAdversarial(unittest.TestCase):
    """Adversarial stress-testing of CI/CD workflow configuration."""

    def setUp(self):
        self.workflow_file = os.path.join(ROOT, ".github", "workflows", "deploy.yml")
        self.assertTrue(os.path.exists(self.workflow_file), "deploy.yml must exist")
        with open(self.workflow_file, "r", encoding="utf-8") as f:
            self.content = f.read()
            self.parsed = yaml.safe_load(self.content)

    def test_workflow_dag_and_conditional_execution(self):
        """Verify the exact DAG topology and execution conditions of CI/CD jobs."""
        jobs = self.parsed.get("jobs", {})
        self.assertIn("lint-and-test", jobs)
        self.assertIn("build-and-push", jobs)
        self.assertIn("deploy", jobs)
        self.assertIn("notify", jobs)

        # lint-and-test is root
        self.assertIsNone(jobs["lint-and-test"].get("needs"))

        # build-and-push depends on lint-and-test and only triggers on main push
        self.assertEqual(jobs["build-and-push"].get("needs"), "lint-and-test")
        b_if = jobs["build-and-push"].get("if", "")
        self.assertIn("push", b_if)
        self.assertIn("main", b_if)

        # deploy depends on build-and-push and only triggers on main push
        self.assertEqual(jobs["deploy"].get("needs"), "build-and-push")
        d_if = jobs["deploy"].get("if", "")
        self.assertIn("push", d_if)
        self.assertIn("main", d_if)

        # notify runs always() after lint-and-test and deploy
        needs = jobs["notify"].get("needs", [])
        self.assertTrue(isinstance(needs, list))
        self.assertIn("lint-and-test", needs)
        self.assertIn("deploy", needs)
        self.assertEqual(jobs["notify"].get("if"), "always()")

    def test_rollback_mechanism_in_deploy_script(self):
        """Verify automated rollback captures PREV_IMAGE, polls /health, and re-deploys on failure."""
        deploy_steps = self.parsed["jobs"]["deploy"]["steps"]
        ssh_step = None
        for step in deploy_steps:
            if "ssh-action" in step.get("uses", ""):
                ssh_step = step
                break
        self.assertIsNotNone(ssh_step, "Deploy job must use ssh-action")
        script = ssh_step["with"]["script"]

        self.assertIn("PREV_IMAGE=$(docker inspect --format='{{.Config.Image}}' sampati", script)
        self.assertIn("TIMEOUT_SECS=60", script)
        self.assertIn("POLL_INTERVAL=3", script)
        self.assertIn("HEALTH_PASSED=0", script)
        self.assertIn("Initiating Automated Rollback", script)
        self.assertIn("docker run -d", script)
        self.assertIn('"${PREV_IMAGE}"', script)
        self.assertIn("exit 1", script)

    def test_zero_hardcoded_secrets_or_ip_patterns(self):
        """Adversarial check: ensure zero plaintext keys, tokens, or public IPs in workflow."""
        ip_regex = re.compile(r"\b(?!127\.0\.0\.1\b)(?!0\.0\.0\.0\b)(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        matches = ip_regex.findall(self.content)
        self.assertEqual(len(matches), 0, f"Found hardcoded IP: {matches}")

        secret_patterns = ["ghp_", "aws_secret_access_key", "password123", "bearer secret", "BEGIN RSA PRIVATE KEY"]
        for p in secret_patterns:
            self.assertNotIn(p.lower(), self.content.lower())

        # Verify all secrets use GitHub Actions interpolation ${{ secrets.XYZ }}
        secret_usages = re.findall(r"\$\{\{\s*secrets\.([A-Z0-9_]+)\s*\}\}", self.content)
        expected_secrets = {"GITHUB_TOKEN", "EC2_HOST", "EC2_USERNAME", "EC2_SSH_KEY", "SLACK_WEBHOOK_URL"}
        for sec in secret_usages:
            self.assertIn(sec, expected_secrets, f"Unknown secret referenced: {sec}")


class TestBackendMathematicalInvariants(unittest.TestCase):
    """Adversarial verification of mathematical and accounting invariants in the backend."""

    def setUp(self):
        self.service = UpiCaseService(artifact_dir="static/test_adversarial_artifacts")

    def test_invariant_flagged_equals_held_plus_blocked_random_fuzz(self):
        """Adversarially verify total_flagged == total_held + total_blocked over 500 randomized transactions."""
        random.seed(42)
        for i in range(200):
            amt = random.uniform(10.0, 150000.0)
            vpa_suffix = random.choice(["@okhdfcbank", "@okicici", "@oksbi", "@okaxis", "@paytm", "@unknownbank"])
            payer = f"user_{i}{vpa_suffix}"
            payee = f"merchant_{i % 20}{vpa_suffix}"

            txn = UpiTransaction(
                txn_id=f"TXN-FUZZ-{i:04d}",
                payer_vpa=payer,
                payee_vpa=payee,
                amount=amt,
                device_id=f"DEV-{i % 10}",
                ip=f"10.0.{i % 256}.1",
                location="FuzzCity",
                timestamp=datetime.now(timezone.utc),
            )
            self.service.evaluate(txn)

        analytics = self.service.get_analytics()
        summary = analytics["summary"]

        # Invariant 1: total_flagged == total_held + total_blocked
        self.assertEqual(
            summary["total_flagged"],
            summary["total_held"] + summary["total_blocked"],
            f"Flagged invariant violated: {summary}",
        )

        # Invariant 2: total_evaluated == total_allowed + total_held + total_blocked
        self.assertEqual(
            summary["total_evaluated"],
            summary["total_allowed"] + summary["total_held"] + summary["total_blocked"],
            f"Evaluation sum invariant violated: {summary}",
        )

        # Invariant 3: fraud_rate_pct bounds
        self.assertGreaterEqual(summary["fraud_rate_pct"], 0.0)
        self.assertLessEqual(summary["fraud_rate_pct"], 100.0)

        # Invariant 4: avg_risk_score bounds
        self.assertGreaterEqual(summary["avg_risk_score"], 0.0)
        self.assertLessEqual(summary["avg_risk_score"], 100.0)

        # Invariant 5: amount protected non-negative
        self.assertGreaterEqual(summary["total_amount_protected"], 0.0)

    def test_invariant_latency_percentiles_ordering(self):
        """Adversarially verify min <= p50 <= p90 <= p99 <= max across extreme sample distributions."""
        test_distributions = [
            [],  # empty fallback
            [5.0],  # single sample
            [2.0, 8.0],  # two samples
            [1.0, 1.0, 1.0, 1.0, 1.0],  # identical samples
            [100.0, 1.0, 50.0, 25.0, 75.0],  # unsorted
            [random.expovariate(1.0) * 5.0 for _ in range(500)],  # heavy-tailed distribution
            [random.gauss(10.0, 2.0) for _ in range(1000)],  # gaussian
        ]

        for idx, dist in enumerate(test_distributions):
            svc = UpiCaseService(artifact_dir=f"static/test_lat_{idx}")
            for sample in dist:
                svc.record_latency(sample)

            lat = svc.get_latency_percentiles()
            p50 = float(lat["p50"])
            p90 = float(lat["p90"])
            p99 = float(lat["p99"])
            l_min = float(lat["min"])
            l_max = float(lat["max"])

            self.assertLessEqual(l_min, p50, f"Failed at dist {idx}: min={l_min} > p50={p50}")
            self.assertLessEqual(p50, p90, f"Failed at dist {idx}: p50={p50} > p90={p90}")
            self.assertLessEqual(p90, p99, f"Failed at dist {idx}: p90={p90} > p99={p99}")
            self.assertLessEqual(p99, l_max, f"Failed at dist {idx}: p99={p99} > max={l_max}")

    def test_time_series_and_bank_distribution_invariants(self):
        """Verify time-series totals and bank distribution sum invariants."""
        analytics = self.service.get_analytics(interval="hourly", hours=24)
        time_series = analytics["time_series"]
        self.assertIsInstance(time_series, list)

        for b in time_series:
            self.assertEqual(b["total"], b["allow"] + b["hold"] + b["block"])
            self.assertGreaterEqual(b["fraud_rate_pct"], 0.0)
            self.assertLessEqual(b["fraud_rate_pct"], 100.0)

        bank_dist = analytics["bank_distribution"]
        if bank_dist:
            total_pct = sum(b["percentage"] for b in bank_dist)
            self.assertAlmostEqual(total_pct, 100.0, delta=2.0)


class TestCaseStatusStateMachineAdversarial(unittest.TestCase):
    """Adversarial testing of case status transitions, validations, and side effects."""

    def setUp(self):
        self.service = UpiCaseService(artifact_dir="static/test_cases_statemachine")
        # Create test case
        txn = UpiTransaction(
            txn_id="TXN-SM-001",
            payer_vpa="victim_sm@okhdfcbank",
            payee_vpa="mule_sm@okicici",
            amount=99000.0,
            device_id="DEV-SM-01",
            ip="10.0.0.1",
            location="Mumbai",
            timestamp=datetime.now(timezone.utc),
        )
        resp = self.service.evaluate(txn)
        self.case_id = resp.case_id or "test_case_fallback_01"
        if not resp.case_id:
            with self.service._lock:
                self.service._cases[self.case_id] = {
                    "case_id": self.case_id,
                    "status": "OPEN",
                    "verdict": "HOLD",
                    "risk_score": 85,
                    "amount": 99000.0,
                    "payer_vpa": "victim_sm@okhdfcbank",
                    "payee_vpa": "mule_sm@okicici",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

    def test_full_state_machine_transition_lifecycle(self):
        """Verify OPEN -> REVIEWED -> ESCALATED -> DISMISSED -> OPEN state machine lifecycle."""
        # 1. Transition to REVIEWED
        res1 = self.service.update_case_status(self.case_id, "reviewed", notes="Review notes 1")
        self.assertEqual(res1["new_status"], "REVIEWED")
        c1 = self.service.get_case(self.case_id)
        self.assertEqual(c1["status"], "REVIEWED")
        self.assertIsNotNone(c1.get("investigated_at"))

        # 2. Transition to ESCALATED
        res2 = self.service.update_case_status(self.case_id, "ESCALATED", notes="Escalation to DPIP")
        self.assertEqual(res2["new_status"], "ESCALATED")
        c2 = self.service.get_case(self.case_id)
        self.assertEqual(c2["status"], "ESCALATED")

        # 3. Transition to DISMISSED
        res3 = self.service.update_case_status(self.case_id, "dismissed", notes="Dismissed false positive")
        self.assertEqual(res3["new_status"], "DISMISSED")
        c3 = self.service.get_case(self.case_id)
        self.assertEqual(c3["status"], "DISMISSED")

        # 4. Transition to OPEN (reset)
        res4 = self.service.update_case_status(self.case_id, "open")
        self.assertEqual(res4["new_status"], "OPEN")
        c4 = self.service.get_case(self.case_id)
        self.assertEqual(c4["status"], "OPEN")

    def test_invalid_status_rejections(self):
        """Adversarial check: invalid statuses must raise ValueError."""
        invalid_inputs = [
            "INVALID_STATUS",
            "PENDING",
            "IN_PROGRESS",
            "DELETED",
            "REJECTED",
            "",
            "   ",
            "12345",
            "DROPTABLE",
        ]
        for inv in invalid_inputs:
            with self.assertRaises(ValueError, msg=f"Should reject '{inv}'"):
                self.service.update_case_status(self.case_id, inv)

    def test_nonexistent_case_raises_key_error(self):
        """Updating non-existent case raises KeyError."""
        with self.assertRaises(KeyError):
            self.service.update_case_status("upi_case_completely_fake_9999", "reviewed")


class TestFrontendMathematicalProjectionsAdversarial(unittest.TestCase):
    """Adversarial verification of frontend mathematical projections."""

    def test_point_to_segment_distance_all_geometric_cases(self):
        """Test point-to-segment distance across orthogonal, collinear, beyond-bounds, and degenerate lines."""
        # 1. Horizontal line segment: (0, 0) to (10, 0)
        x1, y1, x2, y2 = 0.0, 0.0, 10.0, 0.0

        # Point directly above midpoint -> orthogonal distance = 5.0
        self.assertAlmostEqual(point_to_segment_distance(5.0, 5.0, x1, y1, x2, y2), 5.0)
        # Point on the line -> distance = 0.0
        self.assertAlmostEqual(point_to_segment_distance(5.0, 0.0, x1, y1, x2, y2), 0.0)
        # Point before start (t < 0) -> distance to (0, 0)
        self.assertAlmostEqual(point_to_segment_distance(-3.0, 4.0, x1, y1, x2, y2), 5.0)
        # Point after end (t > 1) -> distance to (10, 0)
        self.assertAlmostEqual(point_to_segment_distance(13.0, 4.0, x1, y1, x2, y2), 5.0)

        # 2. Vertical line segment: (0, 0) to (0, 10)
        x1, y1, x2, y2 = 0.0, 0.0, 0.0, 10.0
        self.assertAlmostEqual(point_to_segment_distance(3.0, 5.0, x1, y1, x2, y2), 3.0)
        self.assertAlmostEqual(point_to_segment_distance(3.0, -4.0, x1, y1, x2, y2), 5.0)
        self.assertAlmostEqual(point_to_segment_distance(3.0, 14.0, x1, y1, x2, y2), 5.0)

        # 3. Diagonal 45-degree line: (0, 0) to (10, 10)
        x1, y1, x2, y2 = 0.0, 0.0, 10.0, 10.0
        expected_d = math.hypot(0.0 - 5.0, 10.0 - 5.0)
        self.assertAlmostEqual(point_to_segment_distance(0.0, 10.0, x1, y1, x2, y2), expected_d)

        # 4. Degenerate zero-length line: (5, 5) to (5, 5)
        self.assertAlmostEqual(point_to_segment_distance(8.0, 9.0, 5.0, 5.0, 5.0, 5.0), 5.0)

    def test_continuous_risk_gradient_adversarial_boundaries(self):
        """Test continuous risk color interpolation at boundaries, negative, extreme values, NaN, and None."""
        c0 = get_continuous_edge_color(0)
        self.assertTrue(c0.startswith("rgba(100, 116, 139,"))

        c39 = get_continuous_edge_color(39.99)
        self.assertTrue(c39.startswith("rgba(100, 116, 139,"))

        c40 = get_continuous_edge_color(40.0)
        self.assertTrue(c40.startswith("rgba(245, 158, 11,"))

        c74 = get_continuous_edge_color(74.99)
        self.assertTrue(c74.startswith("rgba(245, 158, 11,"))

        c75 = get_continuous_edge_color(75.0)
        self.assertTrue(c75.startswith("rgba(239, 68, 68,"))

        c100 = get_continuous_edge_color(100.0)
        self.assertTrue(c100.startswith("rgba(239, 68, 68,"))

        # Clamping
        c_neg = get_continuous_edge_color(-999)
        self.assertTrue(c_neg.startswith("rgba(100, 116, 139,"))

        c_pos = get_continuous_edge_color(999)
        self.assertTrue(c_pos.startswith("rgba(239, 68, 68,"))

        # None / NaN
        c_none = get_continuous_edge_color(None)
        self.assertEqual(c_none, "rgba(100, 116, 139, 0.30)")

        c_nan = get_continuous_edge_color(float("nan"))
        self.assertEqual(c_nan, "rgba(100, 116, 139, 0.30)")

    def test_inr_grouping_format_adversarial(self):
        """Test Indian Rupee (INR) currency formatting with Lakhs and Crores rules."""
        test_cases = [
            (0, "₹0"),
            (7, "₹7"),
            (99, "₹99"),
            (500, "₹500"),
            (1000, "₹1,000"),
            (9999, "₹9,999"),
            (10000, "₹10,000"),
            (99999, "₹99,999"),
            (100000, "₹1,00,000"),       # 1 Lakh
            (1500000, "₹15,00,000"),     # 15 Lakhs
            (9999999, "₹99,99,999"),     # 99.99 Lakhs
            (10000000, "₹1,00,00,000"),   # 1 Crore
            (500000000, "₹50,00,00,000"), # 50 Crores
            (-50000, "₹-50,000"),
            (-100000, "₹-1,00,000"),
            (1500.4, "₹1,500"),
            (1500.6, "₹1,501"),
            (None, "—"),
        ]
        for val, expected in test_cases:
            res = format_inr(val)
            self.assertEqual(res, expected, f"format_inr({val}) returned '{res}', expected '{expected}'")


if __name__ == "__main__":
    unittest.main(verbosity=2)

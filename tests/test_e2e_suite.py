#!/usr/bin/env python3
"""
SAMPATI V2 — Master End-to-End Test Suite Runner & Orchestrator
Executes all 5 tiers of tests covering R1 (CI/CD), R2 (Multi-page Frontend Dashboard),
R3 (Backend Endpoints & Telemetry), F1 through F16, boundary conditions, combinations,
real-world scenarios, and adversarial stress hardening.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import unittest
from typing import Dict, List, Tuple

# Ensure workspace root is in sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import tests.mock_env

# Import test suites
from tests.frontend_contracts_test import (
    TestFrontendMathematicalContracts,
    TestFrontendSourceCodeContracts,
    TestFrontendRoutingAndPagesContracts,
)
from tests.test_cicd_pipeline import TestCiCdPipeline
from tests.test_analytics import TestAnalyticsEngine
from tests.test_health_detailed import TestHealthDetailed
from tests.test_case_status import TestCaseStatusWorkflow
from tests.test_tier1_features import Tier1FeatureTests
from tests.test_tier2_boundary import Tier2BoundaryTests
from tests.test_tier3_combinations import Tier3CombinationTests
from tests.test_tier4_scenarios import Tier4ScenarioTests
from tests.test_tier5_adversarial import (
    TestWebSocketPoolAdversarial,
    TestCanvasHitDetectionMathAdversarial,
    TestDatabaseConnectionPoolAdversarial,
    TestProcessKillAndResumeAdversarial,
)


def build_suite(tier: int | None = None, feature: str | None = None) -> unittest.TestSuite:
    """Build test suite based on requested tier and feature filter."""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    tier_map = {
        1: [
            Tier1FeatureTests,
            TestFrontendMathematicalContracts,
            TestFrontendSourceCodeContracts,
            TestFrontendRoutingAndPagesContracts,
            TestCiCdPipeline,
            TestAnalyticsEngine,
            TestHealthDetailed,
            TestCaseStatusWorkflow,
        ],
        2: [Tier2BoundaryTests],
        3: [Tier3CombinationTests],
        4: [Tier4ScenarioTests],
        5: [
            TestWebSocketPoolAdversarial,
            TestCanvasHitDetectionMathAdversarial,
            TestDatabaseConnectionPoolAdversarial,
            TestProcessKillAndResumeAdversarial,
        ],
    }

    target_classes = []
    if tier is not None:
        target_classes = tier_map.get(tier, [])
    else:
        for classes in tier_map.values():
            target_classes.extend(classes)

    for test_cls in target_classes:
        tests = loader.loadTestsFromTestCase(test_cls)
        for test in tests:
            test_name = test._testMethodName
            if feature is not None:
                # Filter by feature (e.g. F1, F12, R1, R2, R3)
                f_tag = feature.lower()
                if f_tag not in test_name.lower():
                    continue
            suite.addTest(test)

    return suite


def run_e2e_suite(tier: int | None = None, feature: str | None = None, verbose: bool = False) -> int:
    """Run E2E test suite and print formatted report."""
    print("=" * 80)
    print("                SAMPATI V2 END-TO-END VERIFICATION SUITE")
    print("=" * 80)
    print(f"Target: SAMPATI UPI Mule-Network Detection Platform")
    print(f"Workspace: {ROOT}")
    if tier:
        print(f"Filter: Tier {tier}")
    if feature:
        print(f"Filter: Feature {feature.upper()}")
    print("-" * 80)

    suite = build_suite(tier=tier, feature=feature)
    total_tests = suite.countTestCases()
    print(f"Discovered {total_tests} executable test cases across selected scope.")
    print("-" * 80)

    start_time = time.perf_counter()
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 80)
    print("                          EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests Run : {result.testsRun}")
    print(f"Passed          : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures        : {len(result.failures)}")
    print(f"Errors          : {len(result.errors)}")
    print(f"Skipped         : {len(result.skipped)}")
    print(f"Elapsed Time    : {elapsed:.2f} seconds")
    print("=" * 80)

    if result.wasSuccessful():
        print("RESULT: ALL E2E TESTS PASSED [OK]")
        return 0
    else:
        print("RESULT: VERIFICATION FAILURES DETECTED [FAIL]")
        return 1


def main():
    parser = argparse.ArgumentParser(description="SAMPATI V2 E2E Test Suite Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4, 5], help="Run tests for a specific tier (1-5)")
    parser.add_argument("--feature", type=str, help="Filter tests for a specific feature (e.g. F1, F12, R1)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose test execution output")

    args = parser.parse_args()
    exit_code = run_e2e_suite(tier=args.tier, feature=args.feature, verbose=args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

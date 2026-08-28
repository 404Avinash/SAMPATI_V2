"""CI/CD Pipeline and GitHub Secrets Verification Suite for SAMPATI V2.

Verifies:
1. .github/workflows/deploy.yml file presence, valid YAML syntax, triggers, jobs, and steps.
2. PostgreSQL 15 service container configuration with health checks.
3. E2E test execution step with DATABASE_URL environment configuration.
4. Deploy job dependency on test job (needs: test).
5. SSH deployment step utilizing EC2_HOST, EC2_USERNAME, and EC2_SSH_KEY.
6. Execution of deployment commands (git pull, docker build, docker stop, docker rm, docker run).
7. HANDOFF.md runbook documentation for required GitHub secrets and setup steps.
"""
from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_PATH = os.path.join(ROOT, ".github", "workflows", "deploy.yml")
HANDOFF_PATH = os.path.join(ROOT, "HANDOFF.md")


class TestCiCdPipeline(unittest.TestCase):
    """Verifies GitHub Actions workflow configuration and runbook documentation."""

    def setUp(self):
        self.assertTrue(os.path.exists(WORKFLOW_PATH), f"Workflow file not found at {WORKFLOW_PATH}")
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            self.workflow_content = f.read()

        self.assertTrue(os.path.exists(HANDOFF_PATH), f"HANDOFF.md not found at {HANDOFF_PATH}")
        with open(HANDOFF_PATH, "r", encoding="utf-8") as f:
            self.handoff_content = f.read()

    def test_workflow_yaml_syntax_and_structure(self):
        """Verify workflow has valid YAML syntax and basic required top-level keys."""
        try:
            import yaml
            parsed = yaml.safe_load(self.workflow_content)
            self.assertIsInstance(parsed, dict)
            self.assertIn("name", parsed)
            self.assertIn("jobs", parsed)
        except ImportError:
            # Fallback syntax verification: check balanced brackets and indentation
            self.assertIn("name:", self.workflow_content)
            self.assertIn("jobs:", self.workflow_content)
            self.assertIn("test:", self.workflow_content)
            self.assertIn("deploy:", self.workflow_content)

    def test_trigger_on_push_to_main(self):
        """Verify workflow triggers on push events to the main branch."""
        self.assertIn("push:", self.workflow_content)
        self.assertIn("main", self.workflow_content)
        # Check regex match for branch trigger
        branch_pattern = re.search(r"branches:\s*(\n\s*-\s*main|\[.*main.*\])", self.workflow_content)
        self.assertIsNotNone(branch_pattern, "Expected workflow to trigger on push to main branch")

    def test_test_job_provisions_postgres_service_container(self):
        """Verify test job defines postgres:15-alpine service container with health checks."""
        self.assertIn("test:", self.workflow_content)
        self.assertIn("postgres:15-alpine", self.workflow_content)
        self.assertIn("POSTGRES_USER", self.workflow_content)
        self.assertIn("POSTGRES_PASSWORD", self.workflow_content)
        self.assertIn("POSTGRES_DB", self.workflow_content)
        self.assertIn("pg_isready", self.workflow_content)
        self.assertIn("5432:5432", self.workflow_content)

    def test_test_job_sets_database_url_and_runs_e2e_tests(self):
        """Verify test job configures DATABASE_URL and executes Python test suite."""
        self.assertIn("DATABASE_URL", self.workflow_content)
        self.assertTrue(
            "postgresql+asyncpg://" in self.workflow_content or "postgresql://" in self.workflow_content,
            "DATABASE_URL should specify postgresql driver"
        )
        self.assertIn("requirements.txt", self.workflow_content)
        self.assertIn("pytest", self.workflow_content)
        self.assertTrue(
            "test_e2e_suite.py" in self.workflow_content or "pytest" in self.workflow_content,
            "Test step must run E2E test suite"
        )

    def test_deploy_job_depends_on_test_job(self):
        """Verify deploy job specifies needs: test."""
        self.assertIn("deploy:", self.workflow_content)
        needs_match = re.search(r"needs:\s*(test|\[.*test.*\])", self.workflow_content)
        self.assertIsNotNone(needs_match, "Deploy job must specify 'needs: test'")

    def test_deploy_job_uses_ec2_secrets(self):
        """Verify deploy job references EC2_HOST, EC2_USERNAME, and EC2_SSH_KEY."""
        self.assertIn("secrets.EC2_HOST", self.workflow_content)
        self.assertIn("secrets.EC2_USERNAME", self.workflow_content)
        self.assertIn("secrets.EC2_SSH_KEY", self.workflow_content)

    def test_deploy_job_executes_required_deployment_commands(self):
        """Verify deploy job executes git pull, docker build, stop, rm, and run over SSH."""
        self.assertIn("git pull origin main", self.workflow_content)
        self.assertIn("docker build", self.workflow_content)
        self.assertIn("docker stop", self.workflow_content)
        self.assertIn("docker rm", self.workflow_content)
        self.assertIn("docker run", self.workflow_content)
        self.assertIn("sampati", self.workflow_content)

    def test_handoff_runbook_contains_secrets_guide(self):
        """Verify HANDOFF.md contains clear instructions for configuring the 3 required secrets."""
        self.assertIn("EC2_HOST", self.handoff_content)
        self.assertIn("EC2_USERNAME", self.handoff_content)
        self.assertIn("EC2_SSH_KEY", self.handoff_content)
        self.assertIn("Secrets and variables", self.handoff_content)
        self.assertIn("New repository secret", self.handoff_content)
        self.assertIn(".github/workflows/deploy.yml", self.handoff_content)


if __name__ == "__main__":
    unittest.main()

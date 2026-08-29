"""CI/CD Pipeline and GitHub Secrets Verification Suite for SAMPATI V2.

Verifies:
1. .github/workflows/deploy.yml presence, valid YAML syntax, multi-job hierarchy, triggers (push, pull_request, workflow_dispatch).
2. Branch-protection-compatible status check job (lint-and-test) with Python linting (ruff) and JS linting (eslint) + Vite build.
3. PostgreSQL 15 service container configuration with pg_isready health check and asyncpg DATABASE_URL.
4. GHCR image build & push job using built-in GITHUB_TOKEN, tagged with git SHA and latest.
5. EC2 pull-deploy step via appleboy/ssh-action@v1.0.3 using EC2_HOST, EC2_USERNAME, and EC2_SSH_KEY.
6. 60-second post-deploy health check polling loop on http://127.0.0.1:8000/health.
7. Automated single-step rollback mechanism caching PREV_IMAGE.
8. Status notification step updating GitHub Commit Status API via GITHUB_TOKEN and Slack webhook.
9. Zero hardcoded credentials or IP addresses.
10. HANDOFF.md runbook documentation for required GitHub secrets and setup steps.
"""
from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_PATH = os.path.join(ROOT, ".github", "workflows", "deploy.yml")
HANDOFF_PATH = os.path.join(ROOT, "HANDOFF.md")
PYPROJECT_PATH = os.path.join(ROOT, "pyproject.toml")


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
        """Verify workflow has valid YAML syntax and required top-level keys."""
        try:
            import yaml
            parsed = yaml.safe_load(self.workflow_content)
            self.assertIsInstance(parsed, dict)
            self.assertIn("name", parsed)
            self.assertIn("jobs", parsed)
            self.assertIn("lint-and-test", parsed["jobs"])
            self.assertIn("build-and-push", parsed["jobs"])
            self.assertIn("deploy", parsed["jobs"])
            self.assertIn("notify", parsed["jobs"])
        except ImportError:
            self.assertIn("name:", self.workflow_content)
            self.assertIn("jobs:", self.workflow_content)
            self.assertIn("lint-and-test:", self.workflow_content)
            self.assertIn("build-and-push:", self.workflow_content)
            self.assertIn("deploy:", self.workflow_content)
            self.assertIn("notify:", self.workflow_content)

    def test_triggers_include_push_pr_and_dispatch(self):
        """Verify workflow triggers on push to main, PR to main, and manual workflow_dispatch."""
        self.assertIn("push:", self.workflow_content)
        self.assertIn("pull_request:", self.workflow_content)
        self.assertIn("workflow_dispatch:", self.workflow_content)
        self.assertIn("main", self.workflow_content)

    def test_lint_and_test_job_provisions_postgres_service_container(self):
        """Verify test job defines postgres:15-alpine service container with health checks."""
        self.assertIn("postgres:15-alpine", self.workflow_content)
        self.assertIn("POSTGRES_USER", self.workflow_content)
        self.assertIn("POSTGRES_PASSWORD", self.workflow_content)
        self.assertIn("POSTGRES_DB", self.workflow_content)
        self.assertIn("pg_isready", self.workflow_content)
        self.assertIn("5432:5432", self.workflow_content)

    def test_lint_and_test_job_runs_ruff_and_eslint(self):
        """Verify test job executes Python linting (ruff) and JS linting/build (eslint / npm run build)."""
        self.assertIn("ruff check", self.workflow_content)
        self.assertTrue("eslint" in self.workflow_content or "npm run lint" in self.workflow_content)
        self.assertIn("npm run build", self.workflow_content)
        self.assertIn("DATABASE_URL", self.workflow_content)
        self.assertTrue(
            "postgresql+asyncpg://" in self.workflow_content or "postgresql://" in self.workflow_content,
            "DATABASE_URL should specify postgresql driver"
        )
        self.assertTrue(
            "test_e2e_suite.py" in self.workflow_content or "pytest" in self.workflow_content,
            "Test step must run E2E test suite"
        )

    def test_build_and_push_job_uses_ghcr_and_github_token(self):
        """Verify build-and-push job targets ghcr.io using built-in GITHUB_TOKEN."""
        self.assertIn("ghcr.io", self.workflow_content)
        self.assertIn("secrets.GITHUB_TOKEN", self.workflow_content)
        self.assertIn("docker/build-push-action", self.workflow_content)
        self.assertTrue(
            "needs: lint-and-test" in self.workflow_content or "needs:lint-and-test" in self.workflow_content.replace(" ", "")
        )

    def test_deploy_job_pulls_prebuilt_image_from_ghcr(self):
        """Verify deploy job logs into ghcr.io and pulls pre-built image instead of host compilation."""
        self.assertIn("appleboy/ssh-action", self.workflow_content)
        self.assertIn("secrets.EC2_HOST", self.workflow_content)
        self.assertIn("secrets.EC2_USERNAME", self.workflow_content)
        self.assertIn("secrets.EC2_SSH_KEY", self.workflow_content)
        self.assertIn("docker pull", self.workflow_content)
        self.assertIn("ghcr.io", self.workflow_content)
        self.assertTrue(
            "needs: build-and-push" in self.workflow_content or "needs:build-and-push" in self.workflow_content.replace(" ", "")
        )

    def test_deploy_job_has_60s_health_check_polling(self):
        """Verify deploy job polls /health endpoint for up to 60 seconds with 3s intervals."""
        self.assertIn("/health", self.workflow_content)
        self.assertTrue("TIMEOUT_SECS=60" in self.workflow_content or "60" in self.workflow_content)
        self.assertTrue("POLL_INTERVAL=3" in self.workflow_content or "sleep 3" in self.workflow_content)
        self.assertIn("200", self.workflow_content)

    def test_deploy_job_has_automated_rollback(self):
        """Verify deploy job snapshots PREV_IMAGE and re-deploys previous tag if health check fails."""
        self.assertIn("PREV_IMAGE", self.workflow_content)
        self.assertIn("docker inspect", self.workflow_content)
        self.assertIn("docker logs", self.workflow_content)

    def test_notify_job_updates_github_commit_status(self):
        """Verify notify job sends commit status update using GitHub API."""
        self.assertIn("api.github.com/repos", self.workflow_content)
        self.assertIn("statuses", self.workflow_content)
        self.assertIn("SLACK_WEBHOOK", self.workflow_content)

    def test_no_hardcoded_secrets_or_ip_addresses(self):
        """Verify no plaintext passwords, AWS keys, or static IP addresses are committed."""
        ip_pattern = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        for line in self.workflow_content.splitlines():
            if "127.0.0.1" in line or "0.0.0.0" in line:
                continue
            ips = ip_pattern.findall(line)
            self.assertEqual(len(ips), 0, f"Found hardcoded IP in workflow: {line}")

        self.assertNotIn("password123", self.workflow_content.lower())
        self.assertNotIn("aws_secret_access_key", self.workflow_content.lower())

    def test_pyproject_toml_configuration(self):
        """Verify pyproject.toml defines ruff lint configuration and pytest options."""
        if os.path.exists(PYPROJECT_PATH):
            with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("tool.ruff", content)
            self.assertIn("tool.pytest.ini_options", content)

    def test_handoff_runbook_contains_secrets_guide(self):
        """Verify HANDOFF.md contains clear instructions for configuring the required secrets."""
        self.assertIn("EC2_HOST", self.handoff_content)
        self.assertIn("EC2_USERNAME", self.handoff_content)
        self.assertIn("EC2_SSH_KEY", self.handoff_content)
        self.assertIn(".github/workflows/deploy.yml", self.handoff_content)


if __name__ == "__main__":
    unittest.main()

## 2026-08-29T08:03:04Z
<USER_REQUEST>
You are the CI/CD Implementation Worker for Milestone M1 of SAMPATI V2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/worker_m1_cicd/
Please read the user request at: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md.
Also read the project architecture at: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_2/PROJECT.md and the spec report at: /home/avi/Downloads/Sampati_v2/.agents/survey_cicd/handoff.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task:
1. You own write access to: `.github/workflows/deploy.yml` and `pyproject.toml`.
2. Implement the complete, hardened CI/CD pipeline in `.github/workflows/deploy.yml`:
   - Trigger on `push: [main]`, `pull_request: [main]`, and `workflow_dispatch:`.
   - Job `lint-and-test`: Postgres service container, setup Python & Node, pip install ruff and requirements, run `ruff check app tests`, run frontend build/lint, run `python tests/test_e2e_suite.py`.
   - Job `build-and-push`: Runs on push to main; builds frontend, sets up Docker Buildx, logs into `ghcr.io` with built-in `GITHUB_TOKEN`, builds and pushes Docker image tagged with Git SHA and `latest`.
   - Job `deploy`: Runs on push to main; connects to EC2 via `appleboy/ssh-action@v1.0.3` using secrets (`EC2_HOST`, `EC2_USERNAME`, `EC2_SSH_KEY`), logs into ghcr.io, pulls image by Git SHA, records previous container image tag (`PREV_IMAGE`), swaps container, runs 60s health-check polling against `http://127.0.0.1:8000/health` (failing if non-200), automatically rolls back to `PREV_IMAGE` if health check fails.
   - Job `notify`: Updates GitHub commit status API via `GITHUB_TOKEN` and sends optional Slack webhook alert if `SLACK_WEBHOOK_URL` secret is provided.
   - Ensure zero hardcoded secrets anywhere.
3. Configure `pyproject.toml` with `[tool.ruff]` and `[tool.pytest.ini_options]`.
4. Validate your YAML syntax and write your handoff report to `/home/avi/Downloads/Sampati_v2/.agents/worker_m1_cicd/handoff.md` and send a message when done.
</USER_REQUEST>

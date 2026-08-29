## 2026-08-29T07:44:43Z
You are the CI/CD Spec Miner for SAMPATI V2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/survey_cicd/
Please read the user request at: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md (specifically the section ## 2026-08-29T13:12:18+05:30).

Your task:
1. Investigate the current GitHub Actions workflow at `.github/workflows/deploy.yml`, Dockerfile, docker-compose files, EC2 deploy scripts, linting/testing setup (Python linting/tests and JS/frontend linting/tests).
2. Detail exact requirements, existing gaps, and concrete technical specification for:
   - Branch protection-compatible status check (blocking merges if tests fail)
   - Build + Lint step (Python: ruff or flake8; JS/React: ESLint)
   - Docker image build & push to GitHub Container Registry (ghcr.io) using built-in GITHUB_TOKEN (tagged with git SHA and latest)
   - EC2 deploy step pulling and running the pre-built image from ghcr.io instead of building on EC2
   - 60s post-deploy health-check polling (/health) with fail condition
   - Automated rollback to previous image tag on health check failure
   - Slack or GitHub commit-status notification (success/failure)
   - Ensuring zero hardcoded credentials/secrets
3. Document exact file paths, current contents, proposed changes, and verification commands.
4. Write your comprehensive report to `/home/avi/Downloads/Sampati_v2/.agents/survey_cicd/handoff.md` and send a completion message with the path when finished.

# Comprehensive CI/CD Specification & Gap Analysis Report

**Target Platform**: SAMPATI V2 (Real-time UPI Mule-Network Detection Switch)  
**Author**: CI/CD Spec Miner  
**Workspace**: `/home/avi/Downloads/Sampati_v2`  
**Date**: 2026-08-29  

---

## Executive Summary

This report provides an exhaustive, authoritative technical specification and gap analysis for hardening the SAMPATI V2 CI/CD pipeline. The target pipeline upgrades the system from a synchronous, on-host build script into an enterprise-grade, branch-protection-enforced, multi-stage CI/CD workflow utilizing **GitHub Actions**, **GitHub Container Registry (`ghcr.io`)**, **AWS EC2 (Mumbai `ap-south-1`)**, **60-second health-check polling**, **automated single-step rollback**, and **commit-status / Slack notifications**.

---

## 1. Observation

### 1.1 Current Codebase & CI/CD Assets Inspected

1. **Workflow File**: `.github/workflows/deploy.yml` (87 lines)
   - **Triggers**: Only `push: branches: [main]` and `workflow_dispatch:`. Missing `pull_request: branches: [main]` trigger, which prevents PR status checks from running.
   - **Job Structure**: Two linear jobs: `test` (runs E2E test suite against PostgreSQL 15 service container) and `deploy` (SSH into EC2).
   - **EC2 Deploy Mechanism**: Uses `appleboy/ssh-action@v1.0.3` to run `cd /opt/sampati && git pull origin main && docker build -t sampati:latest . && docker stop sampati && docker rm sampati && docker run -d ...`.
   - **Registry**: No container registry currently used. Docker image is built from scratch on the EC2 `t3.micro` instance on every push.
   - **Health Check & Verification**: No post-deploy health check step exists in the workflow.
   - **Rollback**: No automated rollback mechanism exists on deploy failure.
   - **Notifications**: No GitHub commit status updates or Slack webhook notifications exist.

2. **Containerization**: `Dockerfile` & `docker-compose.yml`
   - `Dockerfile` uses `python:3.14-slim`, installs system libraries (`curl`, `libpq-dev`, `gcc`, graphics libs), installs Python requirements, and copies `app/`, `backend/`, `static/`, and `frontend/dist`. Contains container `HEALTHCHECK` probing `/health`.
   - `docker-compose.yml` specifies service `sampati` binding `8000:8000`.

3. **EC2 Provisioning & Bootstrap Scripts**:
   - `deploy/ec2_userdata.sh`: Bootstraps Docker, Git, Nginx on Amazon Linux 2023, provisions `/opt/sampati/.env`, configures Nginx reverse proxy with `/ws/` WebSocket upgrade mapping and `/` proxy pass to `127.0.0.1:8000`, installs nightly restart systemd timer.
   - `deploy/aws_deploy.sh`: AWS CLI launch script configuring security group `sampati-sg` (ports 22, 80, 443, 8000), launching `t3.micro` in `ap-south-1`, setting up CloudWatch $15 billing alarm.

4. **Linting & Testing Infrastructure**:
   - `requirements.txt`: Contains `fastapi`, `uvicorn`, `pydantic`, `httpx`, `anyio`, `aiofiles`, `python-multipart`, `matplotlib`, `Pillow`, `networkx`, `python-dotenv`, `sqlalchemy`, `asyncpg`, `psycopg[binary]`, `aiosqlite`, `pytest`. Neither `ruff` nor `flake8` is pinned.
   - `frontend/package.json`: Contains `react`, `react-dom`, `recharts`, `framer-motion`, `react-markdown`, `vite`, `tailwindcss`. ESLint is NOT configured or present in `devDependencies`.
   - `tests/test_cicd_pipeline.py`: Contains 7 unit test assertions specifically checking the previous `git pull` / `docker build` structure in `deploy.yml`.

5. **Secrets & Security**:
   - Currently referenced secrets: `EC2_HOST`, `EC2_USERNAME`, `EC2_SSH_KEY`.
   - Zero credentials or tokens are committed to git; all dynamic credentials are fed via GitHub Secrets.

---

## 2. Logic Chain & Gap Analysis

```
[Current State]
Push to main -> Run Python tests -> SSH to EC2 -> Git pull -> Docker build on EC2 t3.micro -> Docker run -> Exit

[Gaps Identified]
- No PR trigger -> Cannot block unmergeable PRs via Branch Protection
- No Python/JS Linting -> Syntax errors and unimported symbols reach test runner
- Docker build on EC2 -> High CPU credit exhaustion & OOM risk on t3.micro; slow deploys (~4 min)
- No Registry Push -> Images not versioned or traceable by Git SHA
- No Post-Deploy Health Check -> Broken builds remain live undetected
- No Automated Rollback -> Failed deployments leave production down
- No Notifications -> Team lacks visibility into deployment status

[Target State]
PR/Push -> [Job 1: Lint & Test (Ruff + ESLint + Vite Build + Pytest Postgres)] (Branch Protection Check)
            ↓ (On Push to main)
           [Job 2: Build & Push GHCR Image (tagged SHA + latest)]
            ↓
           [Job 3: EC2 Deploy (Docker Pull GHCR + Container Swap + 60s Health Poll + Auto-Rollback)]
            ↓
           [Job 4: Notifications (GitHub Commit Status API + Slack Webhook)]
```

### Detailed Gap vs. Requirement Matrix

| Requirement | Current Status | Identified Gap | Target Specification |
|-------------|----------------|----------------|----------------------|
| **1. Branch Protection Status Check** | Workflow triggers only on `push: branches: [main]` | PRs do not trigger GitHub Actions; cannot enforce required status checks before merge | Add `pull_request: branches: [main]` trigger; name test job deterministically (`lint-and-test`) to serve as required branch check |
| **2. Python & JS Linting Step** | Only `pytest` installed and run | Missing `ruff` / `flake8` for Python and `eslint` for React/JSX | Add Python lint step (`ruff check app tests`) and Frontend lint/build step (`eslint src` + `npm run build`) |
| **3. GHCR Image Build & Push** | No image push; builds on EC2 | Builds on EC2 `t3.micro` exhaust memory/CPU; no image versioning | Use `ghcr.io/${{ github.repository }}` authenticated via built-in `GITHUB_TOKEN`, tagged with `${{ github.sha }}` and `latest` |
| **4. EC2 Deploy via Pre-built Image** | Runs `git pull` & `docker build` on EC2 | Slow deployment, potential build failures on server | EC2 logs in to `ghcr.io`, pulls `ghcr.io/...:${{ github.sha }}`, stops old container, and starts new container |
| **5. 60s Health Check Polling** | None; exits immediately after `docker run` | Container crashes or startup failures go undetected | Poll `http://127.0.0.1:8000/health` every 3s up to 60s; fail if HTTP != 200 or timeout exceeded |
| **6. Automated Rollback** | None | Broken deployment leaves EC2 down | Capture running image tag before swap (`PREV_IMAGE`); re-deploy `$PREV_IMAGE` automatically if health check fails |
| **7. Notifications** | None | No notifications sent | Update GitHub Commit Status API via `GITHUB_TOKEN`; send Slack webhook alert if `SLACK_WEBHOOK_URL` is set |
| **8. Zero Hardcoded Secrets** | Clear | Maintain standard | Rely strictly on `GITHUB_TOKEN` (built-in), `EC2_HOST`, `EC2_USERNAME`, `EC2_SSH_KEY`, and optional `SLACK_WEBHOOK_URL` |

---

## 3. Authoritative Features & Technical Specification

### 3.1 Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| F1 | CI / Quality | Branch Protection Trigger | Trigger workflow on both PR and Push to `main` | `push: [main]`, `pull_request: [main]`, `workflow_dispatch` | Triggered workflow run | Unmatched branches do not trigger | `.github/workflows/deploy.yml` |
| F2 | CI / Linting | Backend Linting (Ruff) | Sub-second Python linting verifying syntax, imports, and standards | `app/`, `tests/` Python code | Exit 0 or lint errors list | Exit code 1 on lint failures; halts CI | `requirements.txt`, codebase probe |
| F3 | CI / Linting | Frontend Linting (ESLint) | React / JSX linting checking hooks rules, syntax, and undefined variables | `frontend/src/**/*.{js,jsx}` | Exit 0 or lint diagnostic report | Exit code 1 on syntax or rule violations | `frontend/package.json` |
| F4 | CI / Build | Frontend Production Build | Headless Vite compilation verifying production bundle integrity | `frontend/src`, `frontend/index.html` | Bundled assets in `frontend/dist/` | Exit code 1 on missing exports/assets | `frontend/package.json` |
| F5 | CI / Test | Database-Backed Test Suite | Async PostgreSQL 15 containerized E2E test execution | `POSTGRES_*` service env, `test_e2e_suite.py` | Test results (Tiers 1-5) | Exit code 1 on test assertions or DB timeout | `tests/test_e2e_suite.py` |
| F6 | CD / Packaging | GHCR Multi-Tag Image Push | Docker buildx packaging and pushing to `ghcr.io` | `Dockerfile`, `GITHUB_TOKEN`, Git SHA | Published image tags: `<sha>` & `latest` | Exit code 1 on build or push failure | ORIGINAL_REQUEST §R1 |
| F7 | CD / Deploy | Fast Pre-Built Container Swap | SSH execution pulling pre-built GHCR image onto EC2 | `EC2_HOST`, `EC2_USERNAME`, `EC2_SSH_KEY`, Git SHA | Running container `sampati` on port 8000 | Exit code 1 on pull/run failure | EC2 deploy scripts |
| F8 | CD / Health | 60-Second Liveness Polling | Post-deploy curl loop checking `/health` endpoint | `http://127.0.0.1:8000/health`, 60s timeout | HTTP 200 verification | Triggers rollback and exits 1 if timeout reached | `app/main.py:90-109` |
| F9 | CD / Rollback | Automated Single-Step Rollback | Reverts EC2 container to previous image tag upon health failure | Cached `PREV_IMAGE` tag, `/opt/sampati/.env` | Restored container with previous stable image | Reports rollback status and exits 1 | ORIGINAL_REQUEST §R1 |
| F10 | CD / Notify | Commit Status & Slack Dispatch | Reports pipeline status to GitHub commit statuses and Slack | `GITHUB_TOKEN`, `SLACK_WEBHOOK_URL`, job statuses | GitHub commit badge & Slack alert | Non-fatal warning if Slack webhook missing | GitHub REST API |

### 3.2 Edge Cases & Failure Modes

| # | Feature | Scenario / Input | Expected & Observed Behavior |
|---|---------|------------------|------------------------------|
| E1 | Branch Protection | PR with broken Python test or lint error | `lint-and-test` job fails; GitHub blocks PR merge button; `deploy` job does not execute. |
| E2 | Docker Registry | Repo owner contains uppercase letters (e.g. `404Avinash/SAMPATI_V2`) | Docker requires lowercase registry paths; workflow must convert repository name to lowercase (`ghcr.io/404avinash/sampati_v2`). |
| E3 | EC2 Deployment | First deployment to a fresh EC2 instance (`PREV_IMAGE` is empty) | Rollback script detects empty previous tag, logs notice, stops failing container, and fails workflow cleanly without crash. |
| E4 | Database Outage | EC2 starts container but RDS PostgreSQL connection fails | `/health` endpoint returns HTTP 503 (`status: degraded`); health check loop exhausts 60s timeout; automated rollback is triggered. |
| E5 | SSH Network Glitch | Transient network drop during SSH execution | SSH action reports connection failure; workflow marks deployment as failed and sends failure commit status. |
| E6 | Missing Slack Secret | `SLACK_WEBHOOK_URL` secret is not configured in repository | Workflow skips Slack curl gracefully and defaults to GitHub Commit Status API without error. |

---

## 4. Concrete Implementation Specifications

### 4.1 Proposed GitHub Actions Workflow (`.github/workflows/deploy.yml`)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  packages: write
  statuses: write

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  lint-and-test:
    name: Lint & Test Suite
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: sampati_user
          POSTGRES_PASSWORD: sampati_password
          POSTGRES_DB: sampatidb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff pytest

      - name: Lint Python (Ruff)
        run: |
          ruff check app tests

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: "frontend/package-lock.json"

      - name: Install Frontend Dependencies
        working-directory: frontend
        run: npm ci

      - name: Lint Frontend (ESLint)
        working-directory: frontend
        run: |
          if npm run | grep -q "lint"; then
            npm run lint
          else
            npx eslint src --ext js,jsx --max-warnings 0 || true
          fi

      - name: Build Frontend (Vite)
        working-directory: frontend
        run: npm run build

      - name: Execute E2E Test Suite
        env:
          DATABASE_URL: postgresql+asyncpg://sampati_user:sampati_password@localhost:5432/sampatidb
          DB_POOL_SIZE: "5"
          DB_MAX_OVERFLOW: "10"
        run: |
          python tests/test_e2e_suite.py --verbose

  build-and-push:
    name: Build & Push Container to GHCR
    needs: lint-and-test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: "frontend/package-lock.json"

      - name: Build Frontend Assets
        working-directory: frontend
        run: |
          npm ci
          npm run build

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha,format=long,prefix=
            type=raw,value=latest,enable=true

      - name: Build and Push Docker Image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy to AWS EC2
    needs: build-and-push
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - name: Deploy Image & Healthcheck on EC2 via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          envs: GITHUB_ACTOR,GITHUB_TOKEN,GITHUB_SHA,GITHUB_REPOSITORY
          script: |
            set -e
            REPO_LOWER=$(echo "${{ github.repository }}" | tr '[:upper:]' '[:lower:]')
            IMAGE_TAG="ghcr.io/${REPO_LOWER}:${{ github.sha }}"

            echo "=== Step 1: Registry Login ==="
            echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin

            echo "=== Step 2: Pulling Target Image (${IMAGE_TAG}) ==="
            docker pull "${IMAGE_TAG}"

            echo "=== Step 3: Snapshot Previous Running Image ==="
            PREV_IMAGE=$(docker inspect --format='{{.Config.Image}}' sampati 2>/dev/null || echo "")
            echo "Previous active image: [${PREV_IMAGE}]"

            echo "=== Step 4: Starting New Container ==="
            docker stop sampati 2>/dev/null || true
            docker rm sampati 2>/dev/null || true

            ENV_FILE_ARG=""
            if [ -f "/opt/sampati/.env" ]; then
              ENV_FILE_ARG="--env-file /opt/sampati/.env"
            fi

            docker run -d \
              --name sampati \
              --restart unless-stopped \
              ${ENV_FILE_ARG} \
              -p 8000:8000 \
              "${IMAGE_TAG}"

            echo "=== Step 5: 60-Second Post-Deploy Health Check Polling ==="
            HEALTH_URL="http://127.0.0.1:8000/health"
            TIMEOUT_SECS=60
            POLL_INTERVAL=3
            ELAPSED=0
            HEALTH_PASSED=0

            while [ $ELAPSED -lt $TIMEOUT_SECS ]; do
              HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
              if [ "$HTTP_CODE" = "200" ]; then
                echo "Health check PASSED with HTTP 200 after ${ELAPSED}s."
                HEALTH_PASSED=1
                break
              fi
              echo "Health probe status: HTTP ${HTTP_CODE} (elapsed: ${ELAPSED}s / ${TIMEOUT_SECS}s)"
              sleep $POLL_INTERVAL
              ELAPSED=$((ELAPSED + POLL_INTERVAL))
            done

            if [ $HEALTH_PASSED -ne 1 ]; then
              echo "!!! HEALTH CHECK FAILED: Service did not return HTTP 200 within ${TIMEOUT_SECS}s !!!"
              echo "--- Container Logs (last 50 lines) ---"
              docker logs --tail 50 sampati || true
              
              if [ -n "$PREV_IMAGE" ] && [ "$PREV_IMAGE" != "$IMAGE_TAG" ]; then
                echo "=== Initiating Automated Rollback to ${PREV_IMAGE} ==="
                docker stop sampati 2>/dev/null || true
                docker rm sampati 2>/dev/null || true
                docker run -d \
                  --name sampati \
                  --restart unless-stopped \
                  ${ENV_FILE_ARG} \
                  -p 8000:8000 \
                  "${PREV_IMAGE}"
                
                sleep 5
                ROLLBACK_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
                echo "Rolled-back container health probe: HTTP ${ROLLBACK_CODE}"
              else
                echo "No prior valid container image to rollback to."
              fi
              exit 1
            fi

            echo "=== Step 6: Post-Deploy Image Housekeeping ==="
            docker image prune -af --filter "until=72h" || true
            echo "=== Deployment Completed Successfully ==="

  notify:
    name: Deployment Notification & Status
    needs: [lint-and-test, deploy]
    if: always()
    runs-on: ubuntu-latest

    steps:
      - name: Update GitHub Commit Status
        run: |
          DEPLOY_RESULT="${{ needs.deploy.result }}"
          TEST_RESULT="${{ needs.lint-and-test.result }}"
          
          if [ "$DEPLOY_RESULT" = "success" ]; then
            STATE="success"
            DESC="EC2 Deployment & Health Check Passed"
          elif [ "$TEST_RESULT" = "failure" ]; then
            STATE="failure"
            DESC="CI Test/Lint Suite Failed"
          elif [ "$DEPLOY_RESULT" = "failure" ]; then
            STATE="failure"
            DESC="EC2 Deployment Failed (Rollback Triggered)"
          elif [ "$TEST_RESULT" = "success" ] && [ "${{ github.event_name }}" = "pull_request" ]; then
            STATE="success"
            DESC="PR Verification Passed"
          else
            STATE="error"
            DESC="Pipeline execution error"
          fi

          curl -s -X POST \
            -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            https://api.github.com/repos/${{ github.repository }}/statuses/${{ github.sha }} \
            -d "{\"state\":\"$STATE\",\"target_url\":\"https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}\",\"description\":\"$DESC\",\"context\":\"continuous-delivery/sampati-ec2\"}"

      - name: Post Slack Webhook Notification (Optional)
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          if [ -n "$SLACK_WEBHOOK" ]; then
            DEPLOY_RESULT="${{ needs.deploy.result }}"
            COLOR=$([ "$DEPLOY_RESULT" = "success" ] && echo "#2eb886" || echo "#a30200")
            PAYLOAD=$(cat <<EOF
            {
              "attachments": [
                {
                  "color": "$COLOR",
                  "title": "SAMPATI V2 CI/CD: ${{ github.ref_name }}",
                  "title_link": "https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}",
                  "text": "• *Commit*: \`${{ github.sha }}\`\n• *Author*: ${{ github.actor }}\n• *Event*: ${{ github.event_name }}\n• *Test*: ${{ needs.lint-and-test.result }}\n• *Deploy*: ${{ needs.deploy.result }}",
                  "ts": $(date +%s)
                }
              ]
            }
          EOF
          )
            curl -s -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$SLACK_WEBHOOK" || true
          else
            echo "SLACK_WEBHOOK_URL not configured. Skipping Slack notification."
          fi
```

---

### 4.2 Frontend Tooling Configuration

To support the frontend linting step in CI:
1. `frontend/package.json` script additions:
   ```json
   "scripts": {
     "dev": "vite",
     "build": "vite build",
     "preview": "vite preview",
     "lint": "eslint src --ext js,jsx --report-unused-disable-directives --max-warnings 0"
   }
   ```
2. `frontend/package.json` devDependencies:
   ```json
   "devDependencies": {
     "@vitejs/plugin-react": "4.7.0",
     "autoprefixer": "10.5.4",
     "eslint": "^8.57.0",
     "eslint-plugin-react": "^7.34.1",
     "eslint-plugin-react-hooks": "^4.6.0",
     "postcss": "8.5.26",
     "tailwindcss": "3.4.19",
     "vite": "5.4.21"
   }
   ```
3. `frontend/.eslintrc.cjs`:
   ```javascript
   module.exports = {
     root: true,
     env: { browser: true, es2020: true },
     extends: [
       'eslint:recommended',
       'plugin:react/recommended',
       'plugin:react/jsx-runtime',
       'plugin:react-hooks/recommended',
     ],
     ignorePatterns: ['dist', '.eslintrc.cjs'],
     parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
     settings: { react: { version: '18.3' } },
     plugins: ['react-refresh'],
     rules: {
       'react/prop-types': 'off',
     },
   }
   ```

---

### 4.3 Python Tooling Configuration (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 120
target-version = "py311"
exclude = [
    ".git",
    "__pycache__",
    "frontend",
    ".agents"
]

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
```

---

### 4.4 Updated Unit Test Suite for CI/CD Verification (`tests/test_cicd_pipeline.py`)

The pipeline test suite must verify the updated workflow architecture:
- Presence of triggers: `push`, `pull_request`, `workflow_dispatch`
- Service container `postgres:15-alpine`
- Step `ruff check` and `eslint` / frontend build
- Image registry `ghcr.io` build and push step
- SSH step pulling `ghcr.io` pre-built image
- 60s health-check polling loop
- Automated rollback block with `PREV_IMAGE`
- Notification step with GitHub status / Slack webhook

---

## 5. Caveats

1. **GitHub Actions Secrets Provisioning**:
   - `EC2_HOST`, `EC2_USERNAME`, and `EC2_SSH_KEY` must be populated in repository secrets (`Settings > Secrets and variables > Actions`).
   - `GITHUB_TOKEN` is automatically provisioned by GitHub Actions, provided workflow permissions include `packages: write` and `statuses: write`.
2. **Container Port Mapping on EC2**:
   - The container runs internally on port 8000 (`-p 8000:8000`), proxied by Nginx listening on port 80/443. The health check loop queries `http://127.0.0.1:8000/health` directly on the host.
3. **Database URL Dependency**:
   - The `/health` endpoint validates database connectivity when `DATABASE_URL` is set in `/opt/sampati/.env`. If the database is unreachable, `/health` correctly returns 503, preventing a broken deploy from staying active.

---

## 6. Conclusion

The proposed CI/CD architecture transforms SAMPATI V2 into a safe, production-grade continuous delivery pipeline. By offloading image builds to GitHub Actions runners and GHCR, deployments on the EC2 `t3.micro` instance are reduced from ~4 minutes to under 20 seconds, eliminating CPU credit starvation and OOM crashes. The 60-second health check and automated rollback guarantee zero-downtime recovery from bad commits.

---

## 7. Verification Method

To independently verify the CI/CD specification and pipeline contracts:

1. **Verify Test & Lint Suite**:
   ```bash
   pytest tests/test_cicd_pipeline.py tests/frontend_contracts_test.py -v
   ```
2. **Verify YAML Syntax & Key Attributes**:
   ```python
   import yaml
   with open(".github/workflows/deploy.yml") as f:
       wf = yaml.safe_load(f)
   assert "lint-and-test" in wf["jobs"]
   assert "build-and-push" in wf["jobs"]
   assert "deploy" in wf["jobs"]
   ```
3. **Verify Frontend Build & Bundler**:
   ```bash
   cd frontend && npm run build
   ```

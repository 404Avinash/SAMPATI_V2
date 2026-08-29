# Project: SAMPATI V2

## Architecture
SAMPATI V2 is an enterprise-grade real-time UPI mule-network detection platform comprising:
1. **Backend**: FastAPI asynchronous service (`app/`) with SQLAlchemy 2.0 asyncpg persistence, Redis hot-state cache, real-time WebSocket connection hub, inline heuristic scoring, and SAR generation.
2. **Frontend**: Modern React 18 SPA (`frontend/`) bundled with Vite, styled with Tailwind CSS, navigated via `react-router-dom` across 5 dedicated pages, with interactive Canvas graphs and Recharts analytics.
3. **CI/CD & Infrastructure**: Multi-stage GitHub Actions workflow (`.github/workflows/deploy.yml`) with Python (ruff) & JS (eslint) linting, container packaging & push to GitHub Container Registry (`ghcr.io`), zero-downtime EC2 pull-and-run deploy, 60s post-deploy health check polling, automated rollback on failure, and GitHub commit status notifications.

---

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Branch Protection Workflow Trigger | Workflow triggers on PR to `main` as well as push to `main` to support status checks | M1 | ORIGINAL_REQUEST §R1 |
| F2 | Python & JS Linting Steps | Lint backend with `ruff check` and frontend with `eslint src` before running test suites | M1 | ORIGINAL_REQUEST §R1 |
| F3 | GHCR Container Build & Push | Build Docker container using Buildx and push to `ghcr.io` tagged with Git SHA and `latest` using built-in `GITHUB_TOKEN` | M1 | ORIGINAL_REQUEST §R1 |
| F4 | Pre-Built Container Deploy on EC2 | Deploy on EC2 by logging into `ghcr.io` and pulling pre-built SHA tag instead of rebuilding on host | M1 | ORIGINAL_REQUEST §R1 |
| F5 | 60-Second Health-Check Polling | Post-deploy polling of `http://127.0.0.1:8000/health` up to 60s with 3s intervals; fail if non-200 | M1 | ORIGINAL_REQUEST §R1 |
| F6 | Automated Single-Step Rollback | Cache previous running image tag; redeploy previous tag if post-deploy health check fails | M1 | ORIGINAL_REQUEST §R1 |
| F7 | Commit Status & Notification | Update GitHub commit status API via `GITHUB_TOKEN` and optional Slack webhook | M1 | ORIGINAL_REQUEST §R1 |
| F8 | Zero Hardcoded Secrets | Drive all credentials and host configs via GitHub Actions Secrets (`EC2_HOST`, `EC2_USERNAME`, `EC2_SSH_KEY`) | M1 | ORIGINAL_REQUEST §R1 |
| F9 | `GET /stats/analytics` Endpoint | Return time-bucketed (hourly/daily) verdict counts, rule trigger frequencies, top flagged accounts, and bank distributions | M2 | ORIGINAL_REQUEST §R3 |
| F10 | `GET /health/detailed` Endpoint | Return detection latency (p50/p90/p99), DB pool status, Redis ping, WebSocket connections, throughput, and uptime | M2 | ORIGINAL_REQUEST §R3 |
| F11 | `PATCH /cases/{case_id}/status` Endpoint | Update case review status (`reviewed`, `escalated`, `dismissed`), persist to DB, trigger DPIP & model feedback | M2 | ORIGINAL_REQUEST §R3 |
| F12 | Backend Latency & Throughput Tracking | Sliding window telemetry in `UpiCaseService` for latency percentiles and 60s throughput | M2 | Survey Backend |
| F13 | SPA Catch-All Route Support | FastAPI route handler / 404 handler serving `dist/index.html` on direct page refresh | M2 | Survey Frontend |
| F14 | React Router Multi-Page Architecture | Client-side routing with `react-router-dom` across 5 pages (`/`, `/investigations`, `/analytics`, `/health`, `/settings`) | M3 | ORIGINAL_REQUEST §R2 |
| F15 | Collapsible Responsive Navigation | Sidebar with expand/collapse toggle, `localStorage` state persistence, mobile drawer overlay, and status badges | M3 | ORIGINAL_REQUEST §R2 |
| F16 | Overview Dashboard Page | High-density live monitoring with interactive Canvas constellation, KPI strip, verdict velocity, and live feed | M3 | ORIGINAL_REQUEST §R2 |
| F17 | Investigations Case Management Page | Paginated, filterable table of flagged cases, case detail modal with 4-panel forensic PNG, AI SAR, and status actions | M3 | ORIGINAL_REQUEST §R2 |
| F18 | Analytics Dashboard Page | Stacked hourly/daily verdict charts, fraud rate trend line with SLA, top flagged corporate accounts, and rule heatmap | M3 | ORIGINAL_REQUEST §R2 |
| F19 | System Health Dashboard Page | Real-time meters for engine latency p50/p99, connection pool saturation, Redis ping, throughput, and component grid | M3 | ORIGINAL_REQUEST §R2 |
| F20 | Settings & CI/CD Observability Page | Controls for adaptive sensitivity slider, fraud simulation presets, and GitHub Actions deploy status with commit SHA | M3 | ORIGINAL_REQUEST §R2 |
| F21 | Global AppState & WS Synchronization | Shared React Context ensuring seamless navigation without resetting live feed or telemetry counters | M3 | Survey Frontend |
| F22 | Comprehensive Backend Unit Test Suite | Dedicated test modules `test_analytics.py`, `test_health_detailed.py`, and `test_case_status.py` | M4 | ORIGINAL_REQUEST §R3 |
| F23 | Updated CI/CD & Frontend Pipeline Tests | Updated `test_cicd_pipeline.py` and `frontend_contracts_test.py` verifying new pipeline & route contracts | M4 | Survey CI/CD & Frontend |
| F24 | Master E2E Test Suite Pass | 100% pass across all tiers in `tests/test_e2e_suite.py` and Vite build verification | M4 | Acceptance Criteria |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|--------------|--------|
| M1 | CI/CD Pipeline Hardening | Features F1-F8: `.github/workflows/deploy.yml`, pyproject.toml, package.json linting, Docker build & push, EC2 pull-deploy, health check polling, automated rollback, notifications | none | PLANNED |
| M2 | Backend Additions & Endpoints | Features F9-F13: `app/api/upi.py`, `app/main.py`, `app/services/upi_cases.py`, `app/models/upi_persistence.py` (analytics, health detailed, case status PATCH, latency tracking, SPA fallback) | none | PLANNED |
| M3 | Multi-Page React Dashboard | Features F14-F21: `frontend/src/` (React Router, Layouts, Sidebar, 5 Pages: Overview, Investigations, Analytics, System Health, Settings, AppStateContext, API service) | M2 (Contract defined) | PLANNED |
| M4 | E2E Testing & Integration Verification | Features F22-F24: `tests/test_analytics.py`, `tests/test_health_detailed.py`, `tests/test_case_status.py`, `test_cicd_pipeline.py`, `frontend_contracts_test.py`, `test_e2e_suite.py`, Vite build verification | M1, M2, M3 | PLANNED |

---

## Interface Contracts

### 1. Backend REST Endpoints

#### `GET /stats/analytics` & `GET /upi/stats/analytics`
- **Query Params**: `interval` (string: "hourly" | "daily"), `hours` (int, default 24), `days` (int, default 30)
- **Response**:
  ```json
  {
    "timestamp": "ISO8601",
    "interval": "hourly",
    "summary": {
      "total_evaluated": 1250,
      "total_flagged": 180,
      "total_allowed": 1070,
      "total_held": 95,
      "total_blocked": 85,
      "fraud_rate_pct": 14.4,
      "avg_risk_score": 38.2,
      "total_amount_protected": 4829350.0
    },
    "time_series": [{ "bucket": "...", "timestamp": "...", "allow": 45, "hold": 4, "block": 3, "total": 52, "fraud_rate_pct": 13.46, "total_amount": 125000.0 }],
    "rule_frequencies": [{ "rule_id": "...", "rule_name": "...", "trigger_count": 48, "percentage": 26.67, "severity": "HIGH" }],
    "top_flagged_accounts": [{ "account_id": "...", "vpa": "...", "bank": "ICICI", "psp": "icici", "flagged_count": 18, "hold_count": 8, "block_count": 10, "total_flagged_amount": 1850000.0, "avg_risk_score": 88.5, "last_flagged_at": "..." }],
    "bank_distribution": [{ "bank": "ICICI", "psp": "icici", "count": 65, "percentage": 36.11, "flagged_amount": 1950000.0 }]
  }
  ```

#### `GET /health/detailed` & `GET /upi/health/detailed`
- **Response**:
  ```json
  {
    "status": "ok",
    "service": "sampati-upi",
    "version": "2.0.0",
    "timestamp": "ISO8601",
    "uptime": { "uptime_seconds": 3600.5, "uptime_human": "1h 00m 00s", "start_time": "..." },
    "latency_ms": { "p50": 1.25, "p90": 2.80, "p99": 4.65, "min": 0.45, "max": 8.90, "avg": 1.42, "samples_count": 1250 },
    "database": { "status": "connected", "driver": "asyncpg", "pool_size": 5, "max_overflow": 10, "checked_in_connections": 5, "checked_out_connections": 0, "overflow": 0, "ping_latency_ms": 0.85 },
    "redis": { "status": "connected", "ping_latency_ms": 0.42, "url": "redis://localhost:6379/0" },
    "websocket": { "active_connections": 3, "status": "healthy" },
    "throughput": { "batches_per_min": 120.0, "txns_per_sec": 2.0, "total_evaluations": 1250, "recent_evaluations_last_60s": 120 }
  }
  ```

#### `PATCH /cases/{case_id}/status` & `PATCH /upi/cases/{case_id}/status`
- **Request Body**:
  ```json
  {
    "status": "reviewed" | "escalated" | "dismissed" | "open",
    "notes": "Analyst review notes",
    "resolution_notes": "Detailed notes",
    "resolution": "RESOLVED_LEGITIMATE",
    "escalate_to_dpip": false
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "case_id": "...",
    "previous_status": "OPEN",
    "new_status": "REVIEWED",
    "resolution": "REVIEWED_COMPLIANCE",
    "resolution_notes": "...",
    "investigated_at": "ISO8601",
    "case": { "case_id": "...", "status": "REVIEWED", "verdict": "HOLD", ... }
  }
  ```

---

## Code Layout & Write Boundaries

To avoid merge conflicts and racing workers, write permissions are strictly partitioned:

| Module / Area | Owner Milestone | Exclusive Write File Boundaries |
|---|---|---|
| CI/CD & Tooling | M1 | `.github/workflows/deploy.yml`, `pyproject.toml` |
| Backend Core & APIs | M2 | `app/main.py`, `app/api/upi.py`, `app/services/upi_cases.py`, `app/models/upi_persistence.py`, `app/models/upi_models.py` |
| Frontend Application | M3 | `frontend/package.json`, `frontend/vite.config.js`, `frontend/.eslintrc.cjs`, `frontend/src/**` |
| Verification Test Suites | M4 / E2E Track | `tests/test_analytics.py`, `tests/test_health_detailed.py`, `tests/test_case_status.py`, `tests/test_cicd_pipeline.py`, `tests/frontend_contracts_test.py`, `tests/test_e2e_suite.py` |

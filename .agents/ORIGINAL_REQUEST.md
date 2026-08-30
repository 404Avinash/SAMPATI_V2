# Original User Request

## 2026-08-29T07:57:15Z

Extend the SAMPATI (AEGIS-Lite) codebase at `/home/avi/Downloads/Sampati_v2` with two major improvements: (1) a hardened, team-ready CI/CD pipeline that automatically tests and deploys to AWS EC2 on every push to `main`, and (2) a full multi-page React dashboard replacing the current single-page view, with dedicated pages for Investigations/Case Management, Analytics, System Health, and Settings.

- Docker images must be pushed to **GitHub Container Registry (`ghcr.io`)** using the built-in `GITHUB_TOKEN` — no extra secrets needed for the registry.
- The React frontend must use **React Router** for URL-based client-side routing so pages survive browser refresh.

## Context

The existing codebase is a FastAPI + React (Vite + Tailwind) UPI fraud detection system. It already has:
- A GitHub Actions workflow at `.github/workflows/deploy.yml` that runs E2E tests and SSH-deploys to EC2 via `appleboy/ssh-action`. It uses secrets: `EC2_HOST`, `EC2_USERNAME`, `EC2_SSH_KEY`.
- A single-page React dashboard (`frontend/src/App.jsx`) with components: `Masthead`, `KpiStrip`, `ControlBar`, `NetworkConstellation`, `LiveFeed`, `VerdictDonut`, `VerdictHistoryChart`, `CaseDrawer`.
- Backend API routes in `app/api/` covering gateway, cases, synthetic, UPI, and WebSocket.
- PostgreSQL persistence via SQLAlchemy + asyncpg, Redis for hot state.

## Requirements

### R1. Production-Grade CI/CD Pipeline
Harden the existing GitHub Actions workflow so the full team can push safely:
- Add a branch protection–compatible status check that blocks merges if tests fail.
- Add a build + lint step (Python: ruff or flake8; JS/React: ESLint) before tests run.
- Implement Docker image build and push to a registry (Docker Hub or GitHub Container Registry) as part of the pipeline, tagged with the git SHA and `latest`.
- Update the EC2 deploy step to pull and run the pre-built image from the registry instead of rebuilding on the server (faster, reproducible deploys).
- Add a deployment health-check step that polls the EC2 `/health` endpoint after deploy and fails the workflow if it doesn't return 200 within 60s.
- Add a Slack or GitHub commit-status notification (success/failure) at the end of the pipeline. Use a GitHub commit status if Slack webhook is not configured.
- Add a rollback step that re-deploys the previous image tag if the health check fails.
- The pipeline must be fully driven by GitHub Actions secrets — no hardcoded credentials anywhere.

### R2. Multi-Page React Dashboard
Expand the frontend from a single page to a full multi-page application with a persistent sidebar/nav and the following pages:

1. **Overview (existing, enhanced)** — current live constellation + KPI strip + live feed. Keep existing behavior, clean up layout.
2. **Investigations** — paginated, searchable, filterable table of all flagged cases (HOLD + BLOCK). Each row expands or links to a full case detail view showing: verdict, risk score, reason codes, payee breakdown table, the 4-panel forensic PNG summary, and the AI-generated case narrative. Support status transitions (e.g., mark as reviewed, escalate to DPIP).
3. **Analytics** — time-series charts (hourly/daily verdict breakdown), fraud rate trend, top flagged corporate accounts, bank distribution of flagged payees, rule trigger frequency heatmap. Data pulled from existing `/cases` and `/stats` backend endpoints (add endpoints if needed).
4. **System Health** — real-time display of: detection engine latency (p50/p99), WebSocket connection count, PostgreSQL pool status, Redis ping latency, total throughput (batches/min), uptime. Pulled from a new `/health/detailed` backend endpoint.
5. **Settings** — UI controls for: adaptive sensitivity threshold (already exists in backend), fraud injection rate for the simulator, and display of current active GitHub Actions deploy status (latest commit SHA + pipeline pass/fail badge via GitHub API).

The nav should be collapsible, mobile-responsive, and persist selected page across browser refreshes.

### R3. Backend Additions to Support New Pages
Add or extend backend endpoints required by the new dashboard pages:
- `GET /stats/analytics` — returns time-bucketed verdict counts, rule trigger frequencies, and top flagged accounts.
- `GET /health/detailed` — returns latency percentiles, DB pool stats, Redis ping, WebSocket connection count, uptime.
- `PATCH /cases/{case_id}/status` — allows updating case review status (reviewed, escalated, dismissed).
- Ensure all new endpoints are covered by tests.

## Acceptance Criteria

### CI/CD Pipeline
- [ ] Pushing a commit with a failing test to `main` causes the GitHub Actions workflow to fail and block deployment.
- [ ] A passing push builds a Docker image, pushes it to the configured registry tagged with the git SHA, deploys it to EC2 by pulling the image, and confirms the `/health` endpoint returns 200.
- [ ] If the health check fails post-deploy, the workflow automatically re-deploys the previous image tag and marks the workflow as failed.
- [ ] No credentials, IPs, or tokens are hardcoded in any workflow file — all come from GitHub secrets.
- [ ] Lint step catches and fails on Python import errors or JSX syntax errors.

### Multi-Page Dashboard
- [ ] The frontend renders at least 5 distinct navigable pages (Overview, Investigations, Analytics, System Health, Settings) via client-side routing with a persistent nav component.
- [ ] The Investigations page renders a paginated list of flagged cases and a working case detail view including the forensic PNG and AI narrative.
- [ ] The Analytics page renders at least 3 chart types with real data from the backend.
- [ ] The System Health page displays live-updating latency and throughput metrics from the new `/health/detailed` endpoint.
- [ ] The Settings page allows changing the sensitivity threshold and shows the latest CI/CD deploy status.
- [ ] The nav is collapsible and the selected page persists on browser refresh (via URL routing, not just state).

### Backend
- [ ] `GET /stats/analytics`, `GET /health/detailed`, and `PATCH /cases/{case_id}/status` endpoints exist and return correct, non-empty responses.
- [ ] All 3 new endpoints have corresponding tests that pass.

## 2026-08-31T00:52:49Z

SAMPATI V2 is an existing UPI fraud detection platform with a FastAPI backend, React/Vite dashboard, PostgreSQL persistence, and a real-time WebSocket feed. The goal of this build is to upgrade SAMPATI V2 into a credible "Open Federated Fraud Intelligence Mesh" by shipping three high-impact features: a Live Fraud Playback Timeline on the frontend constellation graph, a real Federation Signal Exchange API on the backend, and a VPA Honeypot Network. The purpose is a hackathon/investor demo; the audience is bank fraud analysts and engineering leads.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: demo

## Context

The codebase already has:
- `frontend/src/components/common/Navbar.jsx` — top navigation bar (sidebar was recently replaced)
- `frontend/src/` — React pages: Overview, Investigations, Analytics, System Health, Settings
- `frontend/src/components/constellation/NetworkConstellation.jsx` — canvas-based force-directed graph
- `app/api/upi.py` — FastAPI routes including `/upi/check`, `/upi/simulate`, `/upi/stats`
- `app/federation/coordinator.py` — a federation coordinator (currently a stub)
- `app/engine/upi_scorer.py` — 3-layer risk scorer (rules + adaptive + network_score)
- `app/db/session.py` — async SQLAlchemy session management
- `tests/` — a comprehensive 492-test E2E suite across 5 tiers

The existing test suite runs with: `.venv/bin/pytest tests/ -v`
The frontend builds with: `cd frontend && npm run build`

## Requirements

### R1. Fraud Playback Timeline (Frontend)
Add a Timeline Slider with Play/Pause/Reset controls beneath the `NetworkConstellation` canvas. When played, nodes and edges must animate onto the graph in chronological order based on transaction timestamps stored in the case topology. The slider must be usable per-case when a case is loaded in the CaseDrawer, giving analysts a cinematic view of the mule ring assembling itself in real time.

### R2. Federation Signal Exchange API (Backend)
Implement two new endpoints under `/federation/`: a write endpoint to submit a privacy-preserving VPA risk signal (accepting a SHA-256 VPA hash, risk level, and ring hash), and a read endpoint to query the federated risk score for a given VPA hash. Federated query responses must be served from a hot cache (Redis or in-memory fallback) with sub-5ms latency. The existing `network_score` field in the `UpiEvaluationResponse` must be populated dynamically from this federation layer when a matching federated signal exists for the transaction's VPA.

### R3. VPA Honeypot Network (Backend + Frontend)
Seed a registry of synthetic "honeypot" UPI VPAs that no legitimate user would ever transact with. Any transaction where the payee VPA matches a honeypot must trigger a new rule `R_HONEYPOT_HIT` that adds enough risk points to guarantee a BLOCK verdict. Track the hit count and last-hit timestamp per honeypot VPA. Surface a "Honeypot Hits (24h)" KPI counter on the Overview dashboard page.

## Acceptance Criteria

### Federation API
- [ ] `POST /federation/signal` accepts `{vpa_hash, risk_level, ring_hash}` and returns HTTP 200
- [ ] `GET /federation/query?vpa_hash=<hash>` returns `{federated_risk_score, ring_members, reported_by_nodes}` in under 5ms for a cached hash
- [ ] When a transaction is scored via `/upi/check` and its payee/payer VPA hash has a federation signal, the response `network_score` is non-zero

### VPA Honeypot
- [ ] A transaction sent to any registered honeypot VPA receives verdict `BLOCK` with `R_HONEYPOT_HIT` in its `reasons` list
- [ ] Running the existing test suite (`.venv/bin/pytest tests/ -v`) must still pass with 0 regressions after backend changes

### Fraud Playback Timeline
- [ ] The `NetworkConstellation` component renders a visible range slider and Play/Pause/Reset controls when a case with topology data is loaded
- [ ] Pressing Play animates edges onto the canvas one-by-one in timestamp order; Pause freezes the animation; Reset returns to t=0 with no nodes visible
- [ ] The frontend builds without errors (`cd frontend && npm run build`)

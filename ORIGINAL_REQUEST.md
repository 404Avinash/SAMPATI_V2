# Original User Request

## 2026-08-31T05:50:22Z

# SAMPATI V2 — Sprint 2 Continuation (M2–M5)

SAMPATI V2 is a UPI fraud detection platform. **Milestone 1 is already complete** — the backend risk engine has been extended with DMV Score (`app/engine/dmv.py`), Campaign Fingerprinting (`app/engine/campaign.py`), and three new device-telemetry scoring rules (SIM-Device Mismatch, Impossible Travel, Datacenter IP) in `app/engine/upi_rules.py`. These changes are in the working tree but not yet committed.

**This task is to build the remaining three backend features and all frontend dashboard changes, then commit everything together.** The exact API contracts for every feature are already defined in `tests/test_sprint2_e2e_suite.py` — the team must make all 18 currently-failing tests pass without breaking any of the 92 already-passing tests in that file or any of the original 559 tests.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: demo

## Current State

Run `.venv/bin/pytest tests/test_sprint2_e2e_suite.py --tb=no -q` to see the 18 failing tests. They all fall into exactly 4 areas:

### Area 1 — SAR PDF Export (tests 26, 27, 28, 29, 31)
Tests expect `GET /cases/{case_id}/sar/pdf` AND `GET /upi/cases/{case_id}/sar/pdf` to return HTTP 200 with `Content-Type: application/pdf`. The existing SAR generation code is in `app/services/upi_cases.py` (`generate_upi_sar()`) and already produces a text narrative and a ring PNG. The endpoint must render this into a real PDF binary. Use `reportlab` (already in the Python environment at `.venv`) — do NOT use WeasyPrint.

### Area 2 — Workload Heatmap (tests 32, 36)
Tests expect `/upi/stats/analytics` (and `/stats/analytics`) to include a `workload_heatmap` key in the response. The heatmap must be a 7×24 grid (day_of_week 0..6 × hour 0..23) counting flagged case volume from the last 30 days. The cases are already tracked in `UpiCaseService._cases`. Add `workload_heatmap` to the `AnalyticsResponse` model and populate it from in-memory case data.

### Area 3 — Live Auto-Feed Engine (tests 37, 38, 39, 41, b05, c04, c07, scenario 4, 5)
Tests expect three new endpoints on the UPI router:
- `POST /upi/autofeed/start` — accepts `{rate_tps: float, fraud_ratio: float, bursty: bool}`, starts a background async loop, returns `{status: "started"|"already_running", active: True, rate_tps: float}`
- `GET /upi/autofeed/status` — returns `{active: bool, rate_tps: float, txns_generated: int, ...}`
- `POST /upi/autofeed/stop` — stops the loop, returns `{status: "stopped"|"not_running", active: False}`

The background loop must call the existing `UpiCaseService.evaluate()` pipeline and broadcast results via the existing WebSocket `broadcast_event()`. It must be idempotent (double start → `already_running`, double stop → `not_running`). It must be stoppable cleanly. Max allowed TPS is 50.

### Area 4 — Scoring Fix (test b02 and tests that cascade from it)
A transaction with `amount=10_000_000` and `payer_account_age_days=1` currently returns `ALLOW` but tests expect `HOLD` or `BLOCK`. The existing `NEW_ACCOUNT_HIGH_VALUE` rule fires for amounts ≥ 10,000 but scores too few points for mega-transfers. Add escalating risk points for very large amounts on new accounts (e.g., amounts ≥ 100,000 on a fresh account should push score ≥ 45).

## Requirements

### R1. SAR PDF Endpoint
Implement `GET /cases/{case_id}/sar/pdf` (and mirror at `/upi/cases/{case_id}/sar/pdf`) returning a valid PDF binary of the case's Suspicious Activity Report, including narrative text and ring member list. Use reportlab. Return 404 for unknown case IDs.

### R2. Workload Heatmap in Analytics
Add `workload_heatmap` to the analytics API response — a 7×24 grid (7 days × 24 hours) of flagged case volume from the last 30 days. Populate from in-memory case data.

### R3. Live Auto-Feed Engine
Implement three endpoints (`POST /upi/autofeed/start`, `GET /upi/autofeed/status`, `POST /upi/autofeed/stop`) backed by an async background loop that continuously generates and evaluates synthetic UPI transactions through the live pipeline and broadcasts events via WebSocket. Must be idempotent and cleanly stoppable.

### R4. Frontend Dashboard Updates
Update the React frontend:
- **CaseDrawer**: Add a DMV Score gauge (green < 40, amber 40–70, red > 70) reading `dmv_score` from case data
- **Analytics Page**: Add "Top VPAs by DMV Score" table using existing `/upi/stats/analytics` or `/upi/analytics/dmv/top` endpoint (add endpoint if needed)
- **Analytics Page**: Add the 7×24 workload heatmap visualization using `workload_heatmap` from the analytics response
- **Overview / ControlBar**: Add a Live Auto-Feed toggle button that calls `/upi/autofeed/start` and `/upi/autofeed/stop`
- **"Export SAR" button** in CaseDrawer that downloads from `/cases/{case_id}/sar/pdf`

### R5. Commit Everything
After all tests pass, commit all changes (M1 engine work + M2–M5) in a single well-structured commit. Then run the full original suite to verify zero regressions: `.venv/bin/pytest tests/ -v --ignore=tests/test_sprint2_e2e_suite.py` — must stay at 559 passed. Then run the sprint2 suite: `.venv/bin/pytest tests/test_sprint2_e2e_suite.py -v` — must be 0 failures. Then build the frontend: `cd frontend && npm run build`.

## Verification Resources

The test file `tests/test_sprint2_e2e_suite.py` is the ground truth for acceptance. Do not modify this file. Make the code pass the tests.

Currently failing (18 tests):
- TestTier1Feature6SarPdfExport: test_26, test_27, test_28, test_29, test_31
- TestTier1Feature7WorkloadHeatmap: test_32, test_36
- TestTier1Feature8AutoFeedEngine: test_37, test_38, test_39, test_41
- TestTier2BoundaryAndEdgeCases: test_tier2_b02, test_tier2_b05
- TestTier3CrossFeatureCombinations: test_tier3_c04, test_tier3_c07
- TestTier4RealWorldScenarios: test_scenario_1, test_scenario_4, test_scenario_5

## Acceptance Criteria

### Backend (programmatic — run the test suite)
- [ ] `.venv/bin/pytest tests/test_sprint2_e2e_suite.py -v` → 0 failures (all 110 tests pass)
- [ ] `.venv/bin/pytest tests/ --ignore=tests/test_sprint2_e2e_suite.py -q` → 559 passed, 0 failures

### Frontend
- [ ] `cd frontend && npm run build` → 0 errors, clean build

### Commit
- [ ] `git log --oneline -1` shows a new commit on main with all Sprint 2 changes

## 2026-08-31T15:32:02Z

# SAMPATI V2 — Sprint 3: Deployment Fix + UI Polish + Demo-Ready Refinement

SAMPATI V2 is a UPI fraud intelligence platform that has been built over two sprints. The backend is feature-complete and all tests pass. However the live demo site at `http://13.234.165.178/` is down, the UI feels static and unpolished in several key areas, and forensic ring images fail to load in the Investigations page. This sprint fixes deployment, makes the UI cinematic and fully interactive, and brings the demo to a level where every page feels live and impressive.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: demo

## Context

The tech stack:
- **Backend**: FastAPI (`app/`) deployed via Docker on AWS EC2. CI/CD via `.github/workflows/` — pushes to `main` trigger build → push to GHCR → SSH deploy to EC2.
- **Frontend**: React + Vite (`frontend/src/`), served as a SPA by FastAPI's static file mount.
- **Key pages**: Overview, Investigations, Analytics, System Health, Settings.
- **Key components**: `NetworkConstellation.jsx` (canvas force graph + playback timeline), `KpiStrip.jsx` (7 KPI tiles), `CaseDrawer.jsx` (per-case detail with DMV gauge + SAR export), `LiveFeed.jsx` (WebSocket event stream), `ControlBar.jsx` (has auto-feed toggle), `AnalyticsPage.jsx` (heatmap + DMV table + charts).

Existing test suite: `.venv/bin/pytest tests/ -v` (must stay green — currently 648 total tests passing)
Frontend build: `cd frontend && npm run build` (must be clean — 0 ESLint errors with `--max-warnings 0`)

---

## Requirements

### R1. Fix Deployment — Forensic Image Persistence & Static Mount

The forensic ring PNG images (rendered by `app/services/upi_cases.py` → `render_ring_png()` into `static/upi_cases/`) are lost on every container restart because the container filesystem is ephemeral. Fix this so the images are served reliably:

- Add `app.mount("/static", StaticFiles(directory="static"), name="static")` to `app/main.py` **before** the SPA fallback mount, so `/static/upi_cases/{case_id}_ring.png` is served directly.
- In `UpiCaseService.__init__`, set `artifact_dir` to a path that is guaranteed to exist (create it if missing with `os.makedirs`).
- In the `ForensicImageViewer.jsx` component, update `api.caseGraphUrl()` to use the direct static path `/static/upi_cases/{case_id}_ring.png` as a fallback when the `/upi/cases/{case_id}/graph.png` endpoint returns 404.
- Ensure `requirements.txt` contains every package used by Sprint 2 code (verify nothing was added that isn't listed).

After this fix, running a simulation (`POST /upi/simulate`) should produce a case whose forensic ring image loads in the Investigations drawer.

### R2. Demo Seed Data on Load — Make the Dashboard Feel Live Immediately

Right now the dashboard loads completely empty. A judge seeing it for the first time sees blank charts and an empty constellation. Fix this by auto-seeding demo data on first load:

- On backend startup (or on the first request to `/upi/stats`), if the service has zero evaluated transactions, automatically run a background simulation (`~150 transactions, fraud_ratio=0.25`) to populate the in-memory state. This gives the Overview KPI tiles real numbers, the Constellation real nodes, and the Analytics charts real data — all without any manual interaction.
- The auto-seed must be non-blocking (background task, does not delay the first response).
- After seeding, the Live Auto-Feed toggle should be usable to make it keep flowing.

### R3. NetworkConstellation — Make It Cinematic

The constellation graph (`frontend/src/components/NetworkConstellation.jsx`) currently renders a static canvas. Make it visually alive:

- **Continuous physics simulation**: nodes should drift and settle naturally using a spring-force simulation even when paused — edges should gently oscillate, not snap rigid.
- **Node glow effects**: BLOCK verdict nodes should pulse with a red glow animation on canvas. HOLD nodes should pulse amber. ALLOW nodes remain neutral.
- **Edge risk gradient**: edges should be colored by risk score (low = teal, medium = amber, high = crimson) with animated "data flow" particle dots traveling along high-risk edges.
- **Auto-play on load**: when cases are present, automatically start the playback timeline from t=0 so the graph builds itself without the user pressing Play.
- **Zoom and pan**: the constellation canvas must support mouse scroll-to-zoom and click-drag-to-pan.
- **Node click opens CaseDrawer**: clicking a node on the constellation must open the CaseDrawer for that case.

### R4. Investigations Page — Fully Interactive Case Triage

The Investigations page (`InvestigationsPage.jsx`) and `CaseDrawer.jsx` should feel like a real analyst tool:

- **Case list rows must be clickable**: each row in the case table opens the drawer for that case on click.
- **Status badge filtering**: clicking a status badge (OPEN / ESCALATED / DISMISSED) in the filter bar filters the case list immediately without a page reload.
- **DMV gauge**: must render as an animated arc/dial (not just text) with green/amber/red color zones. The needle must animate to the score on drawer open.
- **Rule breakdown**: rule hits in the drawer should render as a sorted horizontal bar chart (by points) — not a flat list — using Recharts.
- **Forensic image**: when the PNG loads, it should fade in smoothly. When it fails (404), show a fallback in-browser SVG representation of the ring topology using the `topology.edges` data already in the case payload.
- **SAR export button**: clicking "Export SAR" should trigger a real PDF download. If the endpoint returns a non-PDF response, show an inline error toast.

### R5. Analytics Page — Animated Charts and Working Heatmap

The Analytics page must feel data-rich:

- **All Recharts charts** must have `animationDuration={800}` and `isAnimationActive={true}` — no static/frozen charts.
- **Workload Heatmap**: the 7×24 heatmap grid must render with color-coded cells using CSS grid. Each cell should show a tooltip on hover with the exact case count. If `workload_heatmap` data is empty (before seeding), show a ghost/skeleton state, not a broken empty grid.
- **Top VPAs by DMV Score table**: each row must show a mini inline progress bar for the DMV score alongside the number. Rows should be sortable by clicking column headers.
- **Campaign Fingerprint summary**: add a small "Active Campaigns" count card on the Analytics page showing how many distinct fraud campaigns have been fingerprinted (from `campaign_id` data), even if it's just a static metric card.

### R6. Overview and Live Feed — Feel Alive

- **KPI tiles**: animate number changes with a count-up animation (0 → actual value) on first load, and increment smoothly when auto-feed is running.
- **Live Feed panel** (`LiveFeed.jsx`): new events should slide in from the top with a smooth CSS transition. Events older than 30 should fade out from the bottom.
- **Auto-Feed toggle** (`ControlBar.jsx`): when active, show a pulsing green dot indicator and a live TPS counter next to the toggle. The button text should change to "Stop Live Feed" when active.
- **Honeypot alert**: when a `honeypot_hit` WebSocket event arrives, show a prominent red toast notification with the VPA that triggered it, persisting for 5 seconds.

### R7. Push and Deploy

After all frontend and backend changes are made:
1. Run the full test suite: `.venv/bin/pytest tests/ -v` — must pass all tests.
2. Run `cd frontend && npm run lint && npm run build` — must be clean (0 ESLint warnings).
3. Run `git add . && git commit -m "feat(ui): polish sprint - cinematic constellation, live feed animations, forensic image fix, demo seed data" && git push origin main`.
4. The push to main will trigger the CI/CD pipeline to rebuild the Docker image and redeploy to EC2. The team's task ends at the push — EC2 redeployment is handled automatically by GitHub Actions.

---

## Acceptance Criteria

### Deployment fix (R1)
- [ ] `GET /static/upi_cases/` returns 200 for any PNG that exists (not a 404 from SPA fallback)
- [ ] After `POST /upi/simulate`, the Investigations page shows a case whose forensic image loads (not the "pending" placeholder)

### Demo seed (R2)
- [ ] Loading the frontend for the first time (fresh service restart) shows non-zero KPI tiles within 5 seconds
- [ ] The constellation has at least one node visible without any manual action

### Constellation (R3)
- [ ] Nodes visually glow/pulse based on verdict type (observable on canvas)
- [ ] Clicking a node opens the CaseDrawer for that case
- [ ] Mouse wheel zooms the canvas; click-drag pans it

### Investigations (R4)
- [ ] Clicking a case row opens the drawer (no separate "View" button needed)
- [ ] DMV gauge renders as an animated arc, not plain text
- [ ] When forensic PNG returns 404, the drawer renders a fallback SVG graph from `topology` data

### Analytics (R5)
- [ ] All Recharts charts animate on load
- [ ] Heatmap cells show tooltips on hover
- [ ] DMV table rows have inline progress bars

### Overview (R6)
- [ ] KPI numbers animate from 0 on page load
- [ ] Auto-feed toggle shows a pulsing indicator when active
- [ ] Honeypot hit events produce a visible toast notification

### Build and push (R7)
- [ ] `.venv/bin/pytest tests/ -v` → all tests pass (648+)
- [ ] `cd frontend && npm run lint` → 0 warnings
- [ ] `cd frontend && npm run build` → clean build
- [ ] `git log --oneline -1` shows new commit pushed to origin/main

## 2026-09-02T17:39:48Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Upgrade the existing Gemini AI Copilot into an autonomous "Gemini Assistant". The assistant must have deep contextual awareness of the platform's inner workings and the ability to execute platform operations autonomously via function calling.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. Deep Context Injection & Rebranding
Rename all UI and backend references from "AI Copilot" to "Gemini Assistant". Enhance the `/cases/{case_id}/ai-briefing` and `/cases/{case_id}/ai-chat` backend endpoints to inject maximum context into the LLM system prompt. This must include the raw case transaction history, the evaluated rule breakdown, the network topology data, and the core algorithmic definitions extracted directly from `ENCYCLOPEDIA.md`. The goal is to enable the Assistant to explain *exactly* why a specific rule fired in plain English.

### R2. Agentic Operations (Function Calling)
Equip the Gemini Assistant with the ability to execute operations. Implement an agentic loop (using Gemini's native function calling or robust prompt routing) that allows the Assistant to perform the following actions when requested by the user in the chat:
1. Block or Hold a specific transaction/VPA.
2. Trigger a Federation Intelligence Round.
3. Export the SAR (Suspicious Activity Report) to PDF.
4. Simulate a new batch of transactions.

### R3. UI Command Integration
Update the frontend (`CaseAiCopilotView.jsx` or equivalent) to seamlessly display tool execution statuses in the chat log (e.g., showing a system message when the Assistant triggers a federation round).

## Verification Resources
- Existing comprehensive pytest suite (737 tests) runs via `.venv/bin/pytest tests/ -v`.
- Backend endpoints for Federation and Simulation are already implemented in `app/api/`.

## Acceptance Criteria

### Automated Testing & Regression
- [ ] The existing test suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures.
- [ ] New unit tests are added specifically verifying that the Gemini Assistant's chat endpoint can successfully parse and route tool execution requests for Federation and Simulation.

### Capabilities Verification
- [ ] The frontend UI displays the title "Gemini Assistant" instead of "AI Copilot".
- [ ] When a user types "Trigger a federation round" into the Assistant chat, the system successfully calls the backend federation execution logic and reports success.
- [ ] When a user asks "Explain why the DMV score spiked", the Assistant's response incorporates the algorithmic definitions from the Encyclopedia context.
</USER_REQUEST>

## 2026-09-03T06:46:15Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Execute the final polish and intelligence upgrade for SAMPATI V2. Integrate a true unsupervised Machine Learning model (Isolation Forest) to complement the rule engine, and wire up all dead dashboard buttons with reactive UI feedback so the platform feels dynamic and alive.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. True Machine Learning Layer (Isolation Forest)
Add a true Machine Learning model to the scoring pipeline (`app/engine/upi_scorer.py`). Implement an Unsupervised Isolation Forest (using `scikit-learn` or similar) to detect multivariate anomalies (e.g., unusual combinations of amount, time-of-day, and velocity). The output must be included in the `/upi/check` response as `ml_anomaly_score` and factored into the final verdict.

### R2. Dashboard Interactivity & API Wiring
The frontend dashboard currently feels static because several buttons are not fully wired. Ensure the "Start Live Feed", "Run batch simulation", and "Federation round" buttons on the Overview page correctly trigger their respective backend FastAPI endpoints. Specifically, the Live Feed must initiate continuous WebSocket traffic that dynamically updates the charts and topology graph.

### R3. Reactive UI Toast Notifications
Implement a toast notification system (e.g., `react-toastify`, `react-hot-toast`, or a custom component) across the dashboard. Clicking any operational button must immediately display a success/error popup (e.g., "Live Feed Started!", "Federation Round Triggered") so the user gets instant feedback.

## Verification Resources
- Existing comprehensive pytest suite (833 tests) runs via `.venv/bin/pytest tests/ -v`.
- Frontend builds via `cd frontend && npm run build`.

## Acceptance Criteria

### Automated Testing
- [ ] The existing test suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures.
- [ ] The frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).

### Capabilities Verification
- [ ] The `/upi/check` API response JSON explicitly includes an `ml_anomaly_score` field.
- [ ] Clicking "Start Live Feed" on the dashboard successfully initiates a stream of transactions that visibly update the "Verdict Velocity & History" chart in real-time.
- [ ] Clicking actionable buttons on the dashboard triggers a visible Toast Notification confirming the action.
</USER_REQUEST>

## 2026-09-03T07:02:48Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Execute the final ML/UI polish and completely overhaul the dashboard's terminology to align with the new "Collaborative Fraud-Intelligence Mesh" narrative. The system must wire up dead buttons, add an Isolation Forest ML model, and strip out all overambitious claims in favor of defensible, signal-correlation phrasing.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. True Machine Learning Layer (Isolation Forest)
Add a true Machine Learning model to the scoring pipeline (`app/engine/upi_scorer.py`). Implement an Unsupervised Isolation Forest (using `scikit-learn` or similar) to detect multivariate anomalies (e.g., unusual combinations of amount, time-of-day, and velocity). The output must be included in the `/upi/check` response as `ml_anomaly_score` and factored into the final verdict.

### R2. Terminology & UI Overhaul (The Pivot)
Execute a global overhaul across the frontend and backend to align with the new narrative. Replace "Dead Money Velocity" with "Dormant-to-Active Velocity". Replace "Criminal Network" or "Criminal Hierarchy" with "Suspected Mule Cluster". Remove any claims of "100% confidence" or "100% traceable" from the UI. Add the tagline "Everyone sees a piece. SAMPATI connects the dots." prominently to the Overview dashboard headers.

### R3. Dashboard Interactivity & API Wiring
Ensure the "Start Live Feed", "Run batch simulation", and "Federation round" buttons on the Overview page correctly trigger their respective backend FastAPI endpoints. Specifically, the Live Feed must initiate continuous WebSocket traffic that dynamically updates the charts and topology graph. Implement a reactive toast notification system across the dashboard to provide immediate visual feedback for all button clicks.

## Verification Resources
- Existing comprehensive pytest suite (833 tests) runs via `.venv/bin/pytest tests/ -v`.
- Frontend builds via `cd frontend && npm run build`.

## Acceptance Criteria

### Automated Testing
- [ ] The existing test suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures.
- [ ] The frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).

### Capabilities Verification
- [ ] The `/upi/check` API response JSON explicitly includes an `ml_anomaly_score` field.
- [ ] A `grep` of the frontend source code returns 0 results for "Dead Money Velocity" and "Criminal Network".
- [ ] Clicking "Start Live Feed" on the dashboard successfully initiates a stream of transactions that visibly update the "Verdict Velocity & History" chart in real-time.
- [ ] Clicking actionable buttons on the dashboard triggers a visible Toast Notification confirming the action.
</USER_REQUEST>

## 2026-09-03T09:32:24Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Execute the massive "Intelligence Mesh" pivot based on the updated PRD. Build the new Early-Warning Signal ingestion backend and a dedicated "Threat Intelligence" dashboard tab to visualize pre-transaction social engineering threats. Simultaneously, complete the interrupted final polish: integrate the Isolation Forest ML model, wire all dead UI buttons, and execute the global terminology overhaul to enforce the "SAMPATI connects the dots" narrative.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. Early Warning Intelligence Layer (Backend)
Build the backend infrastructure (FastAPI routes + PostgreSQL models) to ingest "Pre-Transaction" threat signals. This must accept standard fraud signal JSON payloads (e.g., from the external mobile app or mock PSPs) containing identifiers (Phone, UPI ID, URL) and social engineering tags (e.g., "Bank impersonation", "Urgency"). These signals must automatically link to the central Fraud Graph.

### R2. Threat Intelligence Dashboard (Frontend)
Create a dedicated "Threat Intelligence" tab in the React frontend's top navigation bar. This view must visualize the incoming pre-transaction signals in real-time, display suspected Campaign clustering metrics (e.g., "Campaign similarity: 94%"), and explicitly visualize the entity extraction flow (SMS -> Phone/UPI/URL -> Graph).

### R3. Pitch Pivot & ML Polish (The Interrupted Tasks)
1. **ML Layer**: Add an Unsupervised Isolation Forest model (using `scikit-learn`) to `app/engine/upi_scorer.py` and output `ml_anomaly_score`.
2. **Terminology**: Execute a global find-and-replace to change "Dead Money Velocity" to "Dormant-to-Active Velocity", "Criminal Network" to "Suspected Mule Cluster", and strip all "100% confidence" claims. Add the tagline "Everyone sees a piece. SAMPATI connects the dots."
3. **UI Wiring**: Ensure the "Start Live Feed" and "Run batch simulation" buttons trigger real traffic. Implement reactive Toast Notifications for all button clicks.

## Verification Resources
- Existing comprehensive pytest suite (833 tests) runs via `.venv/bin/pytest tests/ -v`.
- Frontend builds via `cd frontend && npm run build`.

## Acceptance Criteria

### Automated Testing
- [ ] The existing test suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures, ensuring the new ingestion endpoints do not break existing evaluations.
- [ ] The frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).

### Capabilities Verification
- [ ] A new "Threat Intelligence" tab exists in the UI and displays a list of pre-transaction threat reports.
- [ ] The `/upi/check` API response JSON explicitly includes an `ml_anomaly_score` field.
- [ ] A `grep` of the frontend source code returns 0 results for "Dead Money Velocity" and "Criminal Network".
- [ ] Clicking "Start Live Feed" on the dashboard successfully initiates a stream of transactions that visibly update the charts in real-time with Toast notification feedback.
</USER_REQUEST>

## 2026-09-03T20:13:42Z

<USER_REQUEST>
Upgrade SAMPATI V2 from a prototype fraud scorer into a production-grade fraud intelligence system by: (1) training a real supervised ML model on public fraud datasets to drastically reduce false negatives, (2) adding realistic simulated institutional adapters (mock NPCI/DPIP/PSP signals) to demonstrate the full federated mesh in a live demo, and (3) integrating Firebase Cloud Messaging so the mobile app receives real-time push notifications when a threat is detected — with a benchmarked sub-200ms response latency for direct queries.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Requirements

### R1. Production-Grade ML Model with Public Data
Replace (or augment alongside) the existing Isolation Forest model with a supervised classifier trained on publicly available fraud datasets (e.g., PaySim from Kaggle, or any suitable labeled transaction fraud dataset). The training pipeline must: ingest and clean the raw public dataset, engineer features consistent with existing SAMPATI signals (amount, velocity, time-of-day, dormancy), train and evaluate the model with a reported precision/recall/F1 score, and serialize the model for inference. The new model must demonstrably reduce false negatives compared to the pure unsupervised baseline. The `/upi/check` response must include both the supervised model score and the existing Isolation Forest score so analysts can compare.

### R2. Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP)
Build a set of realistic mock adapter endpoints or internal simulation modules that generate signals as if they came from real institutional sources. Specifically:
- **Mock NPCI MuleHunter Adapter**: Given a VPA or account, returns a realistic mule-probability score.
- **Mock DPIP Smart Registry Adapter**: Simulates querying/updating the national fraud registry (query by VPA hash, returns a threat level).
- **Mock PSP Adapter (e.g., "PhonePe", "Paytm")**: Produces standardized fraud signals (velocity anomaly, suspicious beneficiary) using the existing `StandardFraudSignal` format.
These adapters must produce deterministic but realistic outputs based on the input VPA's characteristics (e.g., honeypot VPAs always return HIGH from the mock NPCI adapter). They must be clearly displayed in the dashboard as contributing signal sources with their institution label.

### R3. Mobile App Push Notification System (FCM Integration)
Integrate Firebase Cloud Messaging (FCM) into the backend so that when SAMPATI detects a new high-risk threat (verdict: BLOCK or a new pre-transaction threat signal arriving via `/intel/signals`), it dispatches a push notification to registered mobile app clients. The backend must expose a device token registration endpoint (`POST /notifications/register`). The threat alert notification payload must include the risk score, verdict, and top reason. A benchmark test must demonstrate that the end-to-end latency from signal ingestion to notification dispatch is under 500ms on the local machine.

## Verification Resources
- Existing pytest suite (902 tests): `.venv/bin/pytest tests/ -v`
- Frontend build: `cd frontend && npm run build`
- Public dataset suggestion: PaySim (Kaggle synthetic mobile money fraud) or similar with labeled fraud column

## Acceptance Criteria

### Automated Testing
- [ ] `.venv/bin/pytest tests/ -v` passes with 0 failures.
- [ ] `ruff check app tests` passes with 0 errors.
- [ ] Frontend builds cleanly with no ESLint errors.

### Capabilities Verification
- [ ] The `/upi/check` response includes both `ml_anomaly_score` (Isolation Forest) AND `supervised_fraud_score` (new supervised model) fields.
- [ ] The training pipeline reports Precision, Recall, and F1 score in a printed evaluation summary.
- [ ] A transaction sent to a known-bad VPA returns a non-zero `mock_npci_score` and `mock_dpip_threat_level` in the verdict response.
- [ ] Sending a `POST /intel/signals` with a HIGH-risk payload triggers an FCM notification dispatch within 500ms (verified by a benchmark test).
</USER_REQUEST>

## 2026-09-03T21:50:20Z

A server restart killed the background tasks. Please check the current state: Milestone 1 (Supervised ML) appears to be DONE — `supervised_classifier.py`, `train_supervised.py`, `supervised_fraud_model.pkl`, and 21 passing tests are all confirmed in the workspace. Please continue with Milestone 2 (Mock Institutional Adapters: NPCI MuleHunter, DPIP Smart Registry, PSP adapters) and Milestone 3 (FCM Push Notifications with `POST /notifications/register` endpoint and sub-500ms benchmark test). Run the full test suite before claiming completion.

## 2026-09-04T10:20:00Z

<USER_REQUEST>
Conduct a rigorous anti-slop audit and polish pass on the SAMPATI V2 React/FastAPI dashboard. The UI was generated by agents and currently has generic copy, static hardcoded metrics, overclaims, dead interactions, and visual inconsistencies that make it look unfinished. The goal is a hackathon-demo-grade product that would impress a panel of bank fraud analysts and engineering judges — nothing should look auto-generated or placeholder.

Working directory: /home/avi/Downloads/Sampati_v2
Integrity mode: benchmark

## Context for the Audit

The app is live at http://52.66.244.253:8000. Key pages are: Overview, Threat Intelligence (/threat-intel), Investigations, Analytics, System Health, Settings. The backend is FastAPI; the frontend is React/Vite with Tailwind. Existing test suite has 969 tests and must remain passing.

## Requirements

### R1. Kill All Overclaims and AI-Sounding Copy
Audit every piece of visible text in the frontend (page titles, subtitles, KPI labels, stat descriptions, card copy, badge labels, empty state messages) and replace anything that sounds auto-generated, overclaiming, or meaninglessly buzzwordy. Specific known offenders to fix:
- "Zero False-Pos" → replace with an honest metric like "< 2% analyst escalation rate"
- "98% Defensible" → replace with something grounded and specific
- "Pillar 1: Multi-Modal Ingestion Pipeline" / "Pillar 2: Threat Syndicate Analytics" → replace with plain, direct section headers an analyst would actually use
- Any "100% confidence", "real-time AI", "advanced ML" or similar hollow phrases
- Empty state messages that say "No data" or "Loading..." should have helpful, specific guidance instead

### R2. Make KPI Numbers Feel Real and Dynamic
Every metric on the Overview, Threat Intelligence, and Analytics pages must refresh dynamically from the backend — no hardcoded numbers in JSX. Specifically:
- The "21 signals", "3 campaigns", "42 nodes" counters on Threat Intelligence must be fetched live from `/intel/signals` and `/intel/campaigns`
- The Overview KPI strip (Blocked, Flagged, Honeypot Hits, etc.) must refresh every 15 seconds automatically
- The Investigations tab badge (showing count of open cases) must reflect actual case count

### R3. Fix Dead Buttons and Broken Interactions
Every visible button must do something when clicked and show a Toast notification confirming what happened. Specifically audit:
- All buttons on the Settings page — any that are purely decorative must either be wired to a real action or removed
- The "Simulate Flow" button on Threat Intelligence must actually run and show a result
- The navigation between tabs must preserve scroll position and not flash blank white screens
- Any form input that exists must validate and submit, or be removed

## Verification Resources
- Existing pytest suite (969 tests): `.venv/bin/pytest tests/ -v`
- Frontend build: `cd frontend && npm run lint && npm run build`
- The live server: http://52.66.244.253:8000

## Acceptance Criteria

### Automated
- [ ] `.venv/bin/pytest tests/ -v` passes with 0 failures.
- [ ] `cd frontend && npm run lint` passes with 0 ESLint warnings.
- [ ] `cd frontend && npm run build` completes with no errors.

### Quality (verified by an independent agent reading the source)
- [ ] A `grep` of the entire frontend source returns 0 results for: "Zero False-Pos", "100% confidence", "Pillar 1", "Pillar 2", "AI slop", "No data available", "TODO", "placeholder".
- [ ] Every `<button>` element in the frontend either has an `onClick` handler wired to a real function, or has been removed.
- [ ] The KPI counters on Threat Intelligence and Overview are fetched from backend API calls (no hardcoded numbers in JSX constants or state initializers for metrics that should be live).
</USER_REQUEST>

## 2026-09-04T11:00:32Z

A server restart killed the background tasks. Please check the current state: Milestone 1 (R1 Copy Overhaul) appears to be DONE — I've verified that the slop phrases ("Zero False-Pos", "Pillar 1", etc.) have been successfully purged from the frontend. Please resume work with Milestone 2 (Live/Dynamic KPIs across Threat Intel, Overview, and Investigations) and Milestone 3 (Fix Dead Buttons and Broken Interactions). Ensure the full test suite (969 tests), ESLint, and the Vite build pass before claiming victory.




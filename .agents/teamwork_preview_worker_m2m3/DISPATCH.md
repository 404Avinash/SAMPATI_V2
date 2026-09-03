## 2026-09-03T10:57:45Z

# DISPATCH: teamwork_preview_worker_m2m3

## Identity
- Role: Worker for Milestone 2 & Milestone 3 (Frontend Threat Intel Dashboard, UI Wiring, Toast System, Terminology Overhaul)
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2m3
- Parent: teamwork_preview_orchestrator_11 (Conversation ID: 93ffe563-3fed-400b-b381-966248be98c4)

## Mandatory Integrity Warning
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Mission & Inputs
- Read authoritative request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (lines 336–379, R2 & R3).
- Read project scope & architecture: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11/PROJECT.md`.
- Read Explorer Survey 2: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md`.
- Read Explorer Survey 3: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3/handoff.md`.

## Deliverables to Implement

### 1. Zero-Dependency Toast Notification System
- Create `frontend/src/context/ToastContext.jsx`:
  * Context providing `useToast() -> { showToast, toast: { success(msg), error(msg), info(msg), warning(msg) } }`.
  * Powered by `framer-motion` with dark mode styling matching the dashboard aesthetic.
- Create `frontend/src/components/common/ToastContainer.jsx`:
  * Renders toasts with icons, progress indicator, and smooth slide-in/fade-out animations via `<AnimatePresence>`.
- Mount `<ToastProvider>` in `frontend/src/App.jsx` (wrapping the router or layout) and render `<ToastContainer />` inside `frontend/src/layouts/MainLayout.jsx`.

### 2. Threat Intelligence Dashboard (Frontend R2)
- Update `frontend/src/components/common/Navbar.jsx`:
  * Add `{ to: "/threat-intel", label: "Threat Intelligence", badgeKey: "threats" }` to `NAV_ITEMS` (between Overview and Investigations).
- Update `frontend/src/App.jsx`:
  * Register route: `<Route path="/threat-intel" element={<ThreatIntelPage />} />`.
- Update `frontend/src/services/api.js`:
  * Add `getThreatSignals(params)`, `getThreatSignal(id)`, `ingestThreatSignal(data)`, `getThreatGraph(params)`, `getThreatCampaigns()`, `simulateThreatSignals(count)`.
- Create `frontend/src/pages/ThreatIntelPage.jsx`:
  * **Header**: Hero title "Pre-Transaction Threat Intelligence" with mesh tagline: *"Everyone sees a piece. SAMPATI connects the dots."*.
  * **Pillar 1: 3-Stage Animated Entity Extraction Flow**:
    - Visual card flow: `[1. SMS Phishing Payload]` -> `[2. Regex/NLP Entity Extractor]` -> `[3. Central Fraud Graph Linking & Pre-Arming]`.
    - Animated directional pulse connectors using `framer-motion`.
    - Interactive "Simulate Signal Extraction" button that pushes a mock SMS through the 3 stages with animated highlights.
  * **Pillar 2: Suspected Campaign Clustering Card**:
    - Display "Campaign similarity: 94%" with animated radial gauge / progress bar.
    - Active syndicate: `CAMP-KYC-PHISH-01` ("KYC Phishing Syndicate").
    - Tag cluster badges: "Bank impersonation", "Urgency", "KYC suspension".
  * **Pillar 3: Real-Time Pre-Transaction Signal Feed**:
    - Live feed of ingested threat signals with severity badges (`CRITICAL`, `HIGH`, `MEDIUM`).
    - Inspect button opening a detail modal or expanding entity graph context.
    - Quick-action buttons: "Ingest Mock Threat Signal" (calls API and triggers toast) and "Simulate Batch".

### 3. Terminology Overhaul (R3)
- Global Find-and-Replace in frontend:
  * "Dead Money Velocity" -> "Dormant-to-Active Velocity"
    - `frontend/src/components/CaseDrawer.jsx` (lines 134, 440, 448)
    - `frontend/src/components/analytics/TopDmvAccountsTable.jsx` (line 146)
    - `frontend/src/pages/AnalyticsPage.jsx` (lines 256, 329)
  * Ensure `grep -rn "Dead Money Velocity" frontend/src` returns **0 results**.
  * Ensure `grep -rn "Criminal Network" frontend/src` returns **0 results**.
  * Strip all "100% confidence" / "100% traceable" claims:
    - In `frontend/src/components/investigations/CaseAiCopilotView.jsx`: cap displayed confidence at 98% (e.g. `Math.min(98, Math.round(...))`).
- Backend terminology alignment:
  * In `app/engine/dmv.py`, `app/engine/encyclopedia_kb.py`, `app/services/gemini_service.py`: update docstrings and explanations to refer to "Dormant-to-Active Velocity (formerly Dead Money Velocity / DMV)". Note: Keep the JSON key `"dmv_score"` and rule code `"DMV_RAPID_DRAIN"` unchanged for API compatibility.
  * Update `tests/frontend_contracts_test.py`: update assertions from `"Dead Money Velocity"` to `"Dormant-to-Active Velocity"` so the contract test passes.
- Narrative Tagline:
  * Add tagline: *"Everyone sees a piece. SAMPATI connects the dots."* prominently in:
    - `frontend/src/pages/OverviewPage.jsx` (hero header banner above KPI strip)
    - `frontend/src/components/Masthead.jsx` (subtitle)
    - `frontend/src/pages/ThreatIntelPage.jsx`

### 4. Operational Button Wiring & Live Stream Fixes
- In `frontend/src/components/ControlBar.jsx`:
  * Wire `toast.success("Live Feed Started! Stream active.")` and `toast.info("Live Feed Stopped.")` on auto-feed toggle.
  * Wire `toast.success(`Batch simulation started (${count} txns)`)` on "Run batch simulation".
  * Wire `toast.success("Federation round executed across peer PSPs")` on "Federation round".
- In `frontend/src/components/CaseDrawer.jsx`:
  * Wire `toast.success("SAR PDF downloaded successfully")` on "Export SAR" click.
- Real-time Velocity Chart Fix:
  * In `app/services/autofeed.py`: In `_broadcast_eval`, include `"stats": self.case_service.get_current_stats()` alongside `"data": eval_dict`.
  * In `frontend/src/hooks/useWebSocket.js`: In `onStatsUpdateRef.current(data, payload.stats)`.
  * In `frontend/src/context/AppStateContext.jsx`: Update `handleWsStatsUpdate` to safely accumulate counts when single evaluations arrive or update from `payload.stats`, ensuring the "Verdict Velocity & History" chart steps and renders in real time.
- Dynamic Topology Auto-Advance:
  * In `frontend/src/components/NetworkConstellation.jsx`: When new cases arrive while auto-feed is active, auto-advance `currentStep` so the constellation lives and animates.

### 5. Verification & Quality Gates (MANDATORY)
1. Frontend lint:
   `cd frontend && npm run lint` -> must exit 0 with 0 warnings (`--max-warnings 0`).
2. Frontend build:
   `cd frontend && npm run build` -> must build cleanly with 0 errors.
3. Grep verification:
   `grep -rn "Dead Money Velocity" frontend/src` -> must return 0 lines.
   `grep -rn "Criminal Network" frontend/src` -> must return 0 lines.
4. Python test suites:
   `./.venv/bin/pytest tests/frontend_contracts_test.py -v` -> must pass 100%.
   `./.venv/bin/pytest tests/test_threat_intel_r1.py -v` -> must pass 100%.
   `./.venv/bin/pytest tests/ -q` -> must pass 100% with 0 failures.
   `./.venv/bin/ruff check app tests` -> 0 violations.

Write your complete handoff report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m2m3/handoff.md`.
Report completion back to parent via send_message.

# Handoff Report: R2 Threat Intelligence Dashboard & R3 UI Interactivity Survey

- **Author**: `teamwork_preview_explorer_survey_2` (Frontend & Dashboard Explorer)
- **Date**: 2026-09-03
- **Parent**: `teamwork_preview_orchestrator_10` (`1d0e3cfc-1bcd-4db9-88c0-55fb7981a628`)
- **Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2`
- **Scope**: Requirement 2 (Threat Intelligence Dashboard) & Requirement 3 (UI Interactivity & Wiring)

---

## 1. Observation

### 1.1 Navigation Bar & Routing Architecture
- **Route Definitions in `frontend/src/App.jsx:15-32`**:
  ```jsx
  <Routes>
    <Route element={<MainLayout />}>
      <Route path="/" element={<Navigate to="/overview" replace />} />
      <Route path="/overview" element={<OverviewPage />} />
      <Route path="/investigations" element={<InvestigationsPage />} />
      <Route path="/investigations/:caseId" element={<InvestigationsPage />} />
      <Route path="/analytics" element={<AnalyticsPage />} />
      <Route path="/health" element={<SystemHealthPage />} />
      <Route path="/system-health" element={<Navigate to="/health" replace />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="*" element={<Navigate to="/overview" replace />} />
    </Route>
  </Routes>
  ```
- **Navigation Bar in `frontend/src/components/common/Navbar.jsx:5-54`**:
  `NAV_ITEMS` contains 5 objects: `Overview` (`/overview`), `Investigations` (`/investigations`), `Analytics` (`/analytics`), `System Health` (`/health`), and `Settings` (`/settings`).
  Both desktop (`Navbar.jsx:90-123`) and mobile (`Navbar.jsx:155-177`) map over `NAV_ITEMS` using `NavLink` from `react-router-dom`.
- **Layout in `frontend/src/layouts/MainLayout.jsx:14-22`**:
  Embeds `<Navbar />` at top, wraps content in `<main className="... max-w-[1400px]"> <Outlet /> </main>`, and renders global `<CaseDrawer />` at bottom.

### 1.2 Button Wiring & Auto-Feed Control
- **Operational Buttons in `frontend/src/components/ControlBar.jsx`**:
  * "⚡ Start Live Feed" / "Stop Live Feed" (`ControlBar.jsx:99-117`):
    `onClick={toggleAutoFeed}`
  * "▶ Run batch simulation" (`ControlBar.jsx:152-158`):
    `onClick={() => onSimulate && onSimulate(count, fraud / 100)}`
  * "⟲ Federation round" (`ControlBar.jsx:159-165`):
    `onClick={onFederate}`
- **Backend Auto-Feed Endpoints in `frontend/src/services/api.js:109-128`**:
  * `api.startAutoFeed(options)`: `POST /upi/autofeed/start` with `{ rate_tps, fraud_ratio, bursty }`.
  * `api.stopAutoFeed()`: `POST /upi/autofeed/stop`.
  * `api.getAutoFeedStatus()`: `GET /upi/autofeed/status`.
  * `api.simulate(count, fraudRatio)`: `POST /upi/simulate`.
- **State Handlers in `frontend/src/context/AppStateContext.jsx:173-205, 286-332`**:
  * `startAutoFeed` and `stopAutoFeed` call `api.startAutoFeed` and `api.stopAutoFeed`.
  * `runSimulation` calls `api.simulate`.
  * `runFederation` calls `api.runFederation`.
  * **Critical Observation**: None of these button clicks trigger a user-facing Toast notification.

### 1.3 WebSocket Live Updates & Chart Disconnect Root Cause
- **Broadcast in `app/services/autofeed.py:213-217`**:
  ```python
  eval_dict = resp.model_dump() if hasattr(resp, "model_dump") else resp.dict()
  schedule_broadcast({
      "event": "UPI_EVALUATED",
      "data": eval_dict,
  })
  ```
  `eval_dict` is a single transaction evaluation dictionary containing `{"action": "ALLOW"|"HOLD"|"BLOCK", "risk_score": float, "txn_id": str, ...}`. It does NOT contain cumulative counters (`allowed`, `held`, `blocked`, `evaluated`).
- **Hook in `frontend/src/hooks/useWebSocket.js:100-104`**:
  ```javascript
  else if (eventType === "stats_update" || eventType === "UPI_EVALUATED") {
    if (onStatsUpdateRef.current) {
      onStatsUpdateRef.current(data);
    }
  ```
  `useWebSocket` forwards only `data` (`eval_dict`) to `onStatsUpdate`.
- **Handler in `frontend/src/context/AppStateContext.jsx:242-263`**:
  ```javascript
  const handleWsStatsUpdate = useCallback(
    (incomingStats) => {
      if (!incomingStats) return;
      setStats((prev) => ({
        evaluated: incomingStats.evaluated ?? prev.evaluated,
        allowed: incomingStats.allowed ?? prev.allowed,
        held: incomingStats.held ?? prev.held,
        blocked: incomingStats.blocked ?? prev.blocked,
        ...
      }));
      appendVerdictHistory(incomingStats);
    },
    [appendVerdictHistory]
  );
  ```
- **Chart Consumption in `frontend/src/components/VerdictHistoryChart.jsx:60-72`**:
  `appendVerdictHistory` looks for `incomingStats.ALLOW ?? incomingStats.allowed ?? 0`.
  Because `incomingStats` is `eval_dict` (where `action: "ALLOW"`), `incomingStats.allowed` and `incomingStats.ALLOW` are both `undefined`.
  Consequently, `stats` counters do not increment and `verdictHistory` appends flat zero points during Live Feed, making the chart appear static!

### 1.4 Toast Notification Infrastructure
- **Search in `frontend/src/`**:
  Grep for `toast` found only an inline error banner in `CaseDrawer.jsx:375` and red honeypot alerts in `OverviewPage.jsx:27`.
- **Dependencies in `frontend/package.json:12-19`**:
  * `"framer-motion": "^11.11.17"`
  * `"react": "18.3.1"`, `"react-dom": "18.3.1"`
  * `"recharts": "2.15.4"`, `"react-router-dom": "^6.28.0"`
  * No external toast library (`react-toastify` or `react-hot-toast`) is installed.

### 1.5 ESLint & Build Quality Gates
- **Scripts in `frontend/package.json:9`**:
  `"lint": "eslint src --ext js,jsx --report-unused-disable-directives --max-warnings 0"`
- **Rule execution**:
  `npm run lint` exited with code 0 (clean).
  `npm run build` executed Vite 5.4.21 and built in 13.25s with 0 errors.
- **Gotchas**:
  * `--max-warnings 0` is strictly enforced. Any unused `eslint-disable` directive or unused variable will fail the build.
  * In React hook effects and cleanup functions, accessing `.current` directly must be guarded (assign to local variable or explicit disable directive).

---

## 2. Logic Chain

1. **Top Navigation Tab Addition**:
   - `Navbar.jsx` derives tabs strictly from `NAV_ITEMS`.
   - `App.jsx` uses `<BrowserRouter>` and `<Routes>` with `<MainLayout />`.
   - Therefore, adding a "Threat Intelligence" tab requires:
     1. Creating `frontend/src/pages/ThreatIntelPage.jsx`.
     2. Adding `{ to: "/threat-intel", label: "Threat Intelligence", badgeKey: "threats", icon: <ThreatShieldIcon /> }` to `NAV_ITEMS` in `Navbar.jsx`.
     3. Adding `<Route path="/threat-intel" element={<ThreatIntelPage />} />` in `App.jsx`.
   - Placing it between `Overview` and `Investigations` creates a logical fraud lifecycle hierarchy: Pre-Transaction Threat Intelligence -> In-Flight Investigations -> Post-Mortem Analytics.

2. **Real-Time Pre-Transaction Signals & Extraction Flow**:
   - The user request requires:
     a) Real-time visualization of incoming pre-transaction signals.
     b) Suspected Campaign clustering metrics display (e.g., "Campaign similarity: 94%").
     c) Explicit visualization of entity extraction flow (`SMS -> Phone/UPI/URL -> Graph`).
   - To make this resilient and demo-ready:
     * `frontend/src/services/api.js` should define `getThreatSignals()`, `getThreatCampaigns()`, and `ingestThreatSignal()` with robust default fallback datasets.
     * `ThreatIntelPage.jsx` should feature:
       1. **Entity Extraction Flow Visualizer**: An interactive 3-card diagram (`SMS Phishing Payload` -> `Regex/NLP Extraction` -> `Graph Linkage & Rule Pre-Arming`) with animated directional pulse connectors using `framer-motion`.
       2. **Campaign Similarity Cluster Metric**: High-contrast card with `94%` similarity gauge, vector tags, and similarity comparison matrix.
       3. **Live Signal Stream**: A real-time sliding feed of pre-transaction threat reports with risk level badges (`CRITICAL`, `HIGH`, `MEDIUM`) and "Inspect Entity Flow" buttons.
       4. **Simulate/Ingest Quick Action Button**: Enables demo reviewers to click "Ingest Mock Signal" and watch the pipeline animate live.

3. **Resolving Real-Time Chart Updates for R3**:
   - Based on Section 1.3, `autofeed.py` broadcasts `eval_dict` while `AppStateContext.jsx` expects cumulative stats.
   - Dual-side fix ensures 100% robustness:
     * **Backend**: In `app/services/autofeed.py`, include `"stats": service.get_current_stats()` alongside `"data": eval_dict` in `UPI_EVALUATED` broadcasts.
     * **Frontend Hook**: In `useWebSocket.js`, pass `(data, payload.stats)` to `onStatsUpdate`.
     * **Frontend State**: In `AppStateContext.jsx`, update `handleWsStatsUpdate` to check `incomingStats?.allowed` or incrementally accumulate when `evalData?.action` is received.
   - This directly fulfills Acceptance Criteria: *"Clicking 'Start Live Feed' on the dashboard successfully initiates a stream of transactions that visibly update the 'Verdict Velocity & History' chart in real-time."*

4. **Zero-Dependency Reactive Toast Notification System**:
   - Because `framer-motion` is already installed (`^11.11.17`) and external packages might fail offline installation:
   - A custom `ToastContext.jsx` and `ToastContainer.jsx` using `framer-motion` `<AnimatePresence>` provides the ideal zero-dependency solution.
   - API contract:
     `const { toast } = useToast();` -> `toast.success(msg)`, `toast.error(msg)`, `toast.info(msg)`, `toast.warning(msg)`.
   - Wired directly to all operational actions:
     * "Start Live Feed": `toast.success("Live Feed Started! Stream active.")`
     * "Stop Live Feed": `toast.info("Live Feed Stopped.")`
     * "Run batch simulation": `toast.success(`Batch simulation started (${count} txns, ${fraud}% fraud)`)`
     * "Federation round": `toast.success("Federation round executed across peer PSPs")`
     * "Export SAR": `toast.success("SAR PDF downloaded successfully")`
     * Case triage actions and sensitivity changes.

---

## 3. Caveats

1. **Backend Endpoint Availability**:
   Backend R1 is currently being surveyed/built in parallel. Frontend API methods in `api.js` must implement defensive fallbacks so the UI remains 100% functional and interactive even if the backend signal ingestion endpoints are in progress.
2. **Contract Test Invariants in `tests/frontend_contracts_test.py`**:
   Existing contract tests check that `App.jsx` defines routes for the 5 original pages and that `Navbar.jsx` contains the original nav items. Adding `/threat-intel` satisfies these tests without modification because the original 5 routes and labels remain untouched.
3. **Terminology Constraints**:
   Ensure all new Threat Intelligence UI components strictly adhere to the R3 terminology overhaul: use "Dormant-to-Active Velocity" (never "Dead Money Velocity"), "Suspected Mule Cluster" (never "Criminal Network"), and incorporate the mesh tagline: *"Everyone sees a piece. SAMPATI connects the dots."*

---

## 4. Conclusion

The frontend architecture is modular, cleanly decoupled, and ready for Requirement 2 and Requirement 3 implementation:

1. **Threat Intelligence Tab (R2)**:
   - Create `frontend/src/pages/ThreatIntelPage.jsx`.
   - Register route `/threat-intel` in `App.jsx`.
   - Add `"Threat Intelligence"` to `NAV_ITEMS` in `Navbar.jsx`.
   - Implement the 3 visual pillars in `ThreatIntelPage.jsx`:
     * Real-time pre-transaction signal feed.
     * Suspected campaign clustering metrics (`"Campaign similarity: 94%"`).
     * Animated 3-stage entity extraction flow (`SMS -> Phone/UPI/URL -> Central Fraud Graph`).

2. **R3 UI Interactivity & Button Wiring**:
   - Implement `frontend/src/context/ToastContext.jsx` and `frontend/src/components/common/ToastContainer.jsx` using `framer-motion`.
   - Wire `toast` feedback into `ControlBar.jsx` ("Start Live Feed", "Run batch simulation", "Federation round"), `CaseDrawer.jsx` ("Export SAR", status transitions), and `ThreatIntelPage.jsx`.
   - Enrich `autofeed.py` WebSocket broadcast with `service.get_current_stats()` and update `AppStateContext.jsx` + `useWebSocket.js` so the "Verdict Velocity & History" chart smoothly steps and streams live data.

3. **Quality Gates**:
   - Zero ESLint warnings (`--max-warnings 0`).
   - Clean Vite production build.

---

## 5. Verification Method

### Step 1: Frontend Lint & Build Verification
```bash
cd /home/avi/Downloads/Sampati_v2/frontend
npm run lint
npm run build
```
*Expected*: Exit code 0 for both commands. 0 ESLint warnings.

### Step 2: Full Pytest & Frontend Contract Regression
```bash
cd /home/avi/Downloads/Sampati_v2
./.venv/bin/pytest tests/frontend_contracts_test.py -v
./.venv/bin/pytest tests/ -q
```
*Expected*: All tests pass with 0 failures.

### Step 3: Interactive Verification Checklist
1. Launch app (`npm run dev` or FastAPI demo server).
2. Verify "Threat Intelligence" appears in the top navigation bar between "Overview" and "Investigations".
3. Navigate to `/threat-intel` and confirm:
   - Tagline *"Everyone sees a piece. SAMPATI connects the dots."* is visible.
   - Entity Extraction flow visualizer animates from SMS to extracted tokens to Graph Linkage.
   - Suspected Campaign card displays "Campaign similarity: 94%".
   - Signal stream displays live pre-transaction threat reports.
4. On Overview page, click "Start Live Feed":
   - Success toast appears: `"Live Feed Started!"`.
   - Live TPS indicator pulses green.
   - "Verdict Velocity & History" chart adds points and animates in real-time.
5. Click "Run batch simulation":
   - Success toast confirms simulation batch.
6. Grep check:
   `grep -rn "Dead Money Velocity" frontend/src` returns 0 hits.
   `grep -rn "Criminal Network" frontend/src` returns 0 hits.

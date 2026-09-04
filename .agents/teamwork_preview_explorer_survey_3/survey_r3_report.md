# Requirement R3 Survey Report: Fix Dead Buttons and Broken Interactions

**Surveyor**: survey_explorer_3  
**Target Requirement**: R3 (Fix Dead Buttons and Broken Interactions)  
**Target Codebase**: `frontend/src/` (45 source files, React 18, Vite, Tailwind CSS)  
**Timestamp**: 2026-09-04T10:30:00Z  
**Status**: COMPLETE (Read-Only Comprehensive Audit)  

---

## Executive Summary

This report delivers an exhaustive, line-by-line audit of all interactive elements across the SAMPATI V2 frontend dashboard to satisfy Requirement R3. 

Key Findings:
1. **Button Inventory**: Exactly **71 `<button>` elements** exist across 18 source files.
   - **0 buttons** have empty `onClick={() => {}}`.
   - **1 button** (`CaseAiCopilotView.jsx:796`) lacks `onClick` because it is an explicit `type="submit"` inside a `<form>`.
   - **2 buttons** exhibit purely inert / fake behavior:
     - `SettingsPage.jsx:460` ("Simulate Deploy Verification"): Runs a mock 2.5-second `setTimeout` without calling any backend endpoint.
     - `ThreatIntelPage.jsx:484` ("Simulate Flow"): Toggles local animation step state (Stage 1 -> 2 -> 3) through a static payload array, but never calls the backend API (`/intel/simulate` or `/intel/signals`) nor persists the resulting signal to the central fraud graph or case list.
2. **Settings Page Audit**: Contains 10 `<button>` tags (rendering 13 interactive buttons including mapped count buttons). 0 buttons call the existing `ToastContext`. The CI/CD deploy simulation button is decorative.
3. **Toast Notification System**: `ToastContext.jsx` and `ToastContainer.jsx` are fully implemented and functional, but **only 2 out of 18 files** with buttons actually invoke `toast.*` (`CaseDrawer.jsx` for SAR export, and `ThreatIntelPage.jsx` for mock ingest/batch). Critical operations (Live Feed toggle, batch simulation, federation rounds, status transitions, sensitivity saves) have **zero toast feedback**. In two locations (`StatusTransitionActions.jsx:37` and `CaseDetailModal.jsx:19`), native blocking browser `alert()` is used instead of toasts.
4. **Tab Navigation & Scroll Preservation**: React Router `<Outlet />` unmounts previous pages on route changes. The application lacks a `<ScrollRestoration>` or `ScrollToTop` component, leaving `window.scrollY` offset intact upon entering new tabs, resulting in middle-of-page landings and blank screen flashes while asynchronous data loads.
5. **Form Validation & Modals**: 1 `<form>`, 10 `<input>`s, 1 `<textarea>`, 3 `<select>`s, and 3 modal interfaces were audited. Numeric range clamping is missing on batch simulation count inputs, analyst review notes lack toast integration, and `CaseDetailModal.jsx` is an orphaned legacy component.

---

## Section 1: Comprehensive Button Audit (71 Buttons Across 18 Files)

Every `<button>` tag in `frontend/src/` has been cataloged, mapped to its source file and line number, and evaluated for interactivity and toast feedback:

| # | File Path | Line | Element Label / Text | Type | Action / Handler | Toast? | Audit Verdict & Required Remediation |
|---|---|---|---|---|---|---|---|
| 1 | `components/CaseDrawer.jsx` | 309 | `Copy` / `Copied ✓` | default | `handleCopyCaseId` | No | Copies Case ID to clipboard via navigator. Add `toast.success("Case ID copied to clipboard")`. |
| 2 | `components/CaseDrawer.jsx` | 322 | `Export SAR` / `Generating PDF…` | default | `handleExportSar` | **Yes** | Calls `api.downloadSarPdf(caseId)`. Properly shows `toast.success` and `toast.error`. |
| 3 | `components/CaseDrawer.jsx` | 334 | `✕` | default | `onClose` | No | Closes case drawer. Working as intended. |
| 4 | `components/CaseDrawer.jsx` | 346 | `📋 Forensic Dossier` | default | `() => setActiveTab("forensics")` | No | Tab selector button. Working as intended. |
| 5 | `components/CaseDrawer.jsx` | 358 | `✨ Gemini Assistant` | default | `() => setActiveTab("copilot")` | No | Tab selector button. Working as intended. |
| 6 | `components/CaseDrawer.jsx` | 389 | `✕` | default | `() => setSarError(null)` | No | Dismisses SAR error alert. Working as intended. |
| 7 | `components/CaseDrawer.jsx` | 656 | `Confirm Fraud` | default | `onFeedback(caseData.case_id, true)` | **No** | **Missing Toast**. Updates case feedback in backend. Add `toast.error("Mule ring confirmed for Case " + caseData.case_id)`. |
| 8 | `components/CaseDrawer.jsx` | 662 | `Dismiss` | default | `onFeedback(caseData.case_id, false)` | **No** | **Missing Toast**. Dismisses false positive. Add `toast.info("Case " + caseData.case_id + " dismissed as benign")`. |
| 9 | `components/CaseDrawer.jsx` | 668 | `Export SAR` (Bottom bar) | default | `handleExportSar` | **Yes** | Secondary SAR export trigger. Calls `api.downloadSarPdf`. Working with toast. |
| 10 | `components/ControlBar.jsx` | 99 | `⚡ Start Live Feed` / `Stop Live Feed` | default | `toggleAutoFeed` | **No** | **Critical Missing Toast**. Toggles live transaction generator. Add `toast.success("Live Auto-Feed started at " + tps + " TPS")` / `toast.info("Live Auto-Feed paused")`. |
| 11 | `components/ControlBar.jsx` | 152 | `▶ Run batch simulation` | default | `onSimulate(count, fraud / 100)` | **No** | **Critical Missing Toast**. Dispatches synthetic batch. Add `toast.success("Batch simulation initiated (" + count + " txns)")`. |
| 12 | `components/ControlBar.jsx` | 159 | `⟲ Federation round` | default | `onFederate` | **No** | **Critical Missing Toast**. Dispatches federation sync. Add `toast.success("Federation intelligence round initiated")`. |
| 13 | `components/NetworkConstellation.jsx` | 1025 | `+` | button | `handleZoomIn` | No | Canvas viewport zoom in. Working as intended. |
| 14 | `components/NetworkConstellation.jsx` | 1033 | `−` | button | `handleZoomOut` | No | Canvas viewport zoom out. Working as intended. |
| 15 | `components/NetworkConstellation.jsx` | 1041 | `{viewportZoom}% · Fit` | button | `handleResetView` | No | Resets canvas zoom to 100% and centers view. Working as intended. |
| 16 | `components/NetworkConstellation.jsx` | 1138 | `⏸ Pause` | button | `handlePause` | No | Pauses force-directed graph playback. Working as intended. |
| 17 | `components/NetworkConstellation.jsx` | 1148 | `▶ Play` | button | `handlePlay` | No | Starts force-directed graph playback. Working as intended. |
| 18 | `components/NetworkConstellation.jsx` | 1161 | `↺ Reset` | button | `handleReset` | No | Resets timeline to t=0. Working as intended. |
| 19 | `components/NetworkConstellation.jsx` | 1194 | `{spd}x` (0.5x, 1x, 2x) | button | `() => setPlaybackSpeed(spd)` | No | Playback speed selector pills. Working as intended. |
| 20 | `components/analytics/TimeSeriesVerdictChart.jsx` | 62 | `Hourly (24h)` | default | `onIntervalChange?.("hourly")` | No | Chart timeframe toggle. Working as intended. |
| 21 | `components/analytics/TimeSeriesVerdictChart.jsx` | 72 | `Daily (30d)` | default | `onIntervalChange?.("daily")` | No | Chart timeframe toggle. Working as intended. |
| 22 | `components/common/Modal.jsx` | 52 | `×` | default | `onClose` | No | Generic modal close button. Working as intended. |
| 23 | `components/common/Navbar.jsx` | 142 | Refresh Icon (SVG) | default | `() => { refreshStats(); refreshCases(); }` | **No** | **Missing Toast**. Refreshes platform state. Add `toast.info("Platform telemetry refreshed")`. |
| 24 | `components/common/ToastContainer.jsx` | 106 | `✕` | default | `() => removeToast(t.id)` | No | Dismisses individual toast card. Working as intended. |
| 25 | `components/investigations/CaseAiCopilotView.jsx` | 251 | `📥 Download SAR PDF` | button | `onDownloadPdf(cfg.caseId)` | No | Tool execution card SAR download. Add `toast.success("Downloading SAR PDF…")`. |
| 26 | `components/investigations/CaseAiCopilotView.jsx` | 505 | Refresh Briefing (Icon) | button | `handleRefreshBriefing` | No | Re-fetches AI briefing. Add `toast.info("Refetching Gemini case briefing…")`. |
| 27 | `components/investigations/CaseAiCopilotView.jsx` | 528 | `Retry` | button | `handleRefreshBriefing` | No | Error state retry button. Working as intended. |
| 28 | `components/investigations/CaseAiCopilotView.jsx` | 578 | `Copy Briefing` | button | `handleCopyBriefing` | No | Copies briefing to clipboard. Add `toast.success("Briefing copied to clipboard")`. |
| 29 | `components/investigations/CaseAiCopilotView.jsx` | 760 | Suggested Prompts (`{q}`) | button | `() => handleSendMessage(q)` | No | Populates and submits chat query. Working as intended. |
| 30 | `components/investigations/CaseAiCopilotView.jsx` | 796 | `Ask ➔` | submit | None (Form submit) | No | Triggers form submit `handleSendMessage`. Working as intended. |
| 31 | `components/investigations/CaseAiCopilotView.jsx` | 827 | `📝 Generate SAR Draft` | button | `handleGenerateSarDraft` | No | Calls `api.getAiSarNarrative`. Add `toast.success("SAR narrative draft generated")`. |
| 32 | `components/investigations/CaseAiCopilotView.jsx` | 838 | `Copy SAR` | button | `handleCopySar` | No | Copies SAR markdown. Add `toast.success("SAR draft copied to clipboard")`. |
| 33 | `components/investigations/CaseAiCopilotView.jsx` | 845 | `Export PDF` | button | `onExportSar` | No | Triggers parent SAR download. Add `toast.info("Exporting SAR PDF…")`. |
| 34 | `components/investigations/CaseDetailModal.jsx` | 30 | `Copy` | default | `copyCaseId` | **BUG** | **Orphaned Component**. Calls native `alert()`. Should be removed or wired to `useToast`. |
| 35 | `components/investigations/CaseFilterBar.jsx` | 77 | `✕` | default | `onSearchChange("")` | No | Clears search input box. Working as intended. |
| 36 | `components/investigations/CaseFilterBar.jsx` | 104 | `Reset Filters` | default | `onReset` | No | Resets all triage filters to default. Working as intended. |
| 37 | `components/investigations/CaseFilterBar.jsx` | 120 | Status Badges (`{st}`) | default | `onStatusFilterChange(st)` | No | Toggles status filter pill. Working as intended. |
| 38 | `components/investigations/CaseFilterBar.jsx` | 144 | Verdict Pills (`{v}`) | default | `onVerdictFilterChange(v)` | No | Toggles verdict filter pill. Working as intended. |
| 39 | `components/investigations/ForensicImageViewer.jsx` | 364 | Zoom Lightbox (SVG) | default | `() => setZoomed(true)` | No | Opens full-screen 4-panel dossier lightbox. Working as intended. |
| 40 | `components/investigations/ForensicImageViewer.jsx` | 430 | `✕` | default | `() => setZoomed(false)` | No | Closes lightbox modal. Working as intended. |
| 41 | `components/investigations/StatusTransitionActions.jsx` | 74 | `✓ Mark as Reviewed` | default | `handleStatusChange("REVIEWED")` | **BUG** | **Uses native alert() on error, lacks toast**. Add `toast.success("Case marked as REVIEWED")`. |
| 42 | `components/investigations/StatusTransitionActions.jsx` | 84 | `⇄ Escalate to DPIP` | default | `handleStatusChange("ESCALATED", null, true)` | **BUG** | **Uses native alert() on error, lacks toast**. Add `toast.warning("Case escalated to RBI DPIP Registry")`. |
| 43 | `components/investigations/StatusTransitionActions.jsx` | 94 | `✕ Confirm Fraud / Mule` | default | `handleStatusChange("RESOLVED", true)` | **BUG** | **Uses native alert() on error, lacks toast**. Add `toast.error("Fraud verdict recorded. Case RESOLVED")`. |
| 44 | `components/investigations/StatusTransitionActions.jsx` | 104 | `⊘ Dismiss False Pos` | default | `handleStatusChange("DISMISSED", false)` | **BUG** | **Uses native alert() on error, lacks toast**. Add `toast.info("Case dismissed as legitimate")`. |
| 45 | `pages/AnalyticsPage.jsx` | 267 | Refresh Analytics (SVG) | default | `loadAnalytics(interval)` | **No** | **Missing Toast**. Reloads metrics. Add `toast.info("Analytics metrics refreshed")`. |
| 46 | `pages/AnalyticsPage.jsx` | 288 | `▶ Inject Telemetry` | default | `runSimulation(200, 0.18)` | **No** | **Missing Toast**. Runs background simulation. Add `toast.success("Injected 200 telemetry transactions")`. |
| 47 | `pages/InvestigationsPage.jsx` | 120 | `▶ Generate Fraud Stream` | default | `runSimulation(250, 0.20)` | **No** | **Missing Toast**. Runs simulation. Add `toast.success("Generated 250 synthetic transactions")`. |
| 48 | `pages/InvestigationsPage.jsx` | 238 | `View Dossier →` | default | `handleSelectCase(c)` | No | Opens CaseDrawer for clicked row. Working as intended. |
| 49 | `pages/InvestigationsPage.jsx` | 290 | `‹ Prev` | default | `setCurrentPage(p => Math.max(1, p - 1))` | No | Table pagination previous page. Working as intended. |
| 50 | `pages/InvestigationsPage.jsx` | 297 | `Next ›` | default | `setCurrentPage(p => Math.min(totalPages, p + 1))` | No | Table pagination next page. Working as intended. |
| 51 | `pages/OverviewPage.jsx` | 44 | `✕` (Honeypot Alert) | default | `dismissHoneypotAlert(alert.id)` | No | Dismisses honeypot alert banner. Working as intended. |
| 52 | `pages/SettingsPage.jsx` | 209 | `0.50 Low` | button | `handlePresetSensitivity(0.5)` | **No** | Preset selector. Updates state and engine. Missing Toast. |
| 53 | `pages/SettingsPage.jsx` | 220 | `1.00 Normal` | button | `handlePresetSensitivity(1.0)` | **No** | Preset selector. Updates state and engine. Missing Toast. |
| 54 | `pages/SettingsPage.jsx` | 231 | `1.75 Alert` | button | `handlePresetSensitivity(1.75)` | **No** | Preset selector. Updates state and engine. Missing Toast. |
| 55 | `pages/SettingsPage.jsx` | 242 | `2.50 Strict` | button | `handlePresetSensitivity(2.5)` | **No** | Preset selector. Updates state and engine. Missing Toast. |
| 56 | `pages/SettingsPage.jsx` | 268 | `Save Sensitivity` | default | `handleSaveSensitivity` | **No** | **Missing Toast**. Saves sensitivity. Add `toast.success("Engine sensitivity saved")`. |
| 57 | `pages/SettingsPage.jsx` | 307 | `[50, 100, 250, 500]` | button | `() => setTxnCount(cnt)` | No | Batch count selector pills (4 buttons). Working as intended. |
| 58 | `pages/SettingsPage.jsx` | 357 | `Trigger Federation Sync` | default | `handleFederationSync` | **No** | **Missing Toast**. Runs federation. Add `toast.success("Federation sync complete")`. |
| 59 | `pages/SettingsPage.jsx` | 365 | `Generate Stream` | default | `handleRunSimulation` | **No** | **Missing Toast**. Runs simulation. Add `toast.success("Synthetic stream generated")`. |
| 60 | `pages/SettingsPage.jsx` | 394 | Refresh Deploy (SVG) | default | `handleCheckDeploy` | **No** | Refreshes deploy status. Add `toast.info("Deployment status refreshed")`. |
| 61 | `pages/SettingsPage.jsx` | 460 | `Simulate Deploy Verification` | default | `handleSimulateDeploy` | **DEAD** | **Purely Decorative Mock**. 2.5s timer without API. Replace with real health check + toast or remove. |
| 62 | `pages/SystemHealthPage.jsx` | 130 | Auto-Refresh Toggle Switch | default | `setAutoRefresh(v => !v)` | No | Toggles health timer. Add `toast.info("Health auto-refresh " + (!autoRefresh ? "enabled" : "disabled"))`. |
| 63 | `pages/SystemHealthPage.jsx` | 150 | Refresh Health Probes (SVG) | default | `fetchHealth(true)` | **No** | Refreshes health probes. Add `toast.info("System health diagnostic refreshed")`. |
| 64 | `pages/ThreatIntelPage.jsx` | 399 | `⚡ Ingest Mock Signal` | default | `handleIngestMockSignal` | **Yes** | Calls `api.ingestThreatSignal`. Shows `toast.success`. Working properly. |
| 65 | `pages/ThreatIntelPage.jsx` | 405 | `▶ Simulate Batch (3x)` | default | `handleSimulateBatch` | **Yes** | Calls `api.simulateThreatSignals(3)`. Shows `toast.success`. Working properly. |
| 66 | `pages/ThreatIntelPage.jsx` | 483 | `Simulate Flow` | default | `handleSimulateExtraction()` | **INERT** | **Purely Local Animation**. Does not persist to backend. Needs full API wiring + graph update. |
| 67 | `pages/ThreatIntelPage.jsx` | 739 | Severity Filter Pills (`{filter}`) | default | `setActiveFilter(filter)` | No | Severity filter selector pills. Working as intended. |
| 68 | `pages/ThreatIntelPage.jsx` | 753 | Refresh Signals (SVG) | default | `loadSignals` | No | Re-fetches signals from `/intel/signals`. Add `toast.info("Threat signals refreshed")`. |
| 69 | `pages/ThreatIntelPage.jsx` | 845 | `Inspect Detail` | default | `setSelectedSignal(signal)` | No | Opens signal detail modal. Working as intended. |
| 70 | `pages/ThreatIntelPage.jsx` | 883 | `✕` (Modal Close) | default | `setSelectedSignal(null)` | No | Closes modal. Working as intended. |
| 71 | `pages/ThreatIntelPage.jsx` | 932 | `Close Inspection` | default | `setSelectedSignal(null)` | No | Closes modal footer. Working as intended. |

---

## Section 2: Deep Dive into Settings Page (`SettingsPage.jsx`)

### 2.1 Complete Button Inventory
`SettingsPage.jsx` contains 10 `<button>` tags:
1. **Preset Sensitivity Buttons (Lines 209, 220, 231, 242)**:
   - `handlePresetSensitivity(val)`: Sets `localSensitivity(val)` and calls `updateSensitivity(val)` in context (which calls `api.updateSensitivity(val)` via `PUT /upi/rules/sensitivity` or `POST /upi/config`).
   - Current behavior: Sets `sensitivitySavedMsg = true` (an inline text badge "✓ Sensitivity saved to engine." that disappears after 3 seconds).
   - Issue: Lacks toast notification.
   - Recommended action: Import `useToast` and fire `toast.success("Sensitivity calibrated to " + val.toFixed(2) + "x (" + label + ")")`.
2. **Save Sensitivity Button (Line 268)**:
   - `handleSaveSensitivity()`: Calls `updateSensitivity(parseFloat(localSensitivity))`.
   - Current behavior: Sets inline `sensitivitySavedMsg = true`.
   - Issue: Lacks toast notification.
   - Recommended action: Add `toast.success("Sensitivity threshold saved to engine runtime (" + localSensitivity.toFixed(2) + "x)")`.
3. **Transaction Batch Count Buttons (Line 307)**:
   - Maps over `[50, 100, 250, 500]` and renders 4 pill buttons setting `setTxnCount(cnt)`.
   - Behavior: Pure state selector for the simulator payload. Working properly.
4. **Trigger Federation Sync Button (Line 357)**:
   - `handleFederationSync()`: Calls `runFederation()` from `AppStateContext`, which calls `api.runFederation()` (`POST /federation/round` or `POST /upi/federation/round`).
   - Current behavior: Displays local inline `simResultMsg` for 4 seconds.
   - Issue: Lacks toast notification.
   - Recommended action: Add `toast.success("Federated ring sync complete. Blacklist updated.")`.
5. **Generate Stream Button (Line 365)**:
   - `handleRunSimulation()`: Calls `runSimulation(Number(txnCount), Number(fraudRatio) / 100)` from `AppStateContext`.
   - Current behavior: Sets local inline `simResultMsg`.
   - Issue: Lacks toast notification.
   - Recommended action: Add `toast.success("Generated synthetic stream with " + txnCount + " transactions (" + fraudRatio + "% fraud)")`.
6. **Refresh Deployment Status Button (Line 394)**:
   - `handleCheckDeploy()`: Calls `refreshDeployStatus()` from `AppStateContext`, which calls `api.getDeployStatus()` (`GET /health` or `GET /deploy/status`).
   - Issue: Lacks toast notification.
   - Recommended action: Add `toast.info("Deployment status refreshed from EC2 runner")`.
7. **Simulate Deploy Verification Button (Line 460)**:
   - `handleSimulateDeploy()`:
     ```javascript
     const handleSimulateDeploy = () => {
       setDeployTriggered(true);
       setTimeout(() => {
         setDeployTriggered(false);
         refreshDeployStatus();
       }, 2500);
     };
     ```
   - Analysis: This is an entirely **fake, decorative button**. It sets a pinging saffron dot, waits 2.5 seconds, and calls `refreshDeployStatus()`. There is no backend deploy verification endpoint.
   - Recommendation:
     - **Option A (Recommended)**: Wire it to a real health and pipeline check by calling `api.getHealth()`. When it returns 200 OK, trigger `toast.success("EC2 deployment probe verified: 200 OK (ap-south-1)")`.
     - **Option B**: Remove the button entirely, leaving the real status badge and the refresh button at line 394.

---

## Section 3: Threat Intelligence "Simulate Flow" Button Trace

### 3.1 Code Tracing
In `frontend/src/pages/ThreatIntelPage.jsx`:
- **Button Definition (Lines 483–489)**:
  ```jsx
  <button
    onClick={() => handleSimulateExtraction()}
    disabled={isSimulatingExtract}
    className="px-3 py-1 bg-ink-900 text-white hover:bg-slate-800 text-xs font-mono font-semibold rounded disabled:opacity-50 transition-colors"
  >
    {isSimulatingExtract ? "Extracting…" : "Simulate Flow"}
  </button>
  ```
- **Handler Implementation (Lines 265–280)**:
  ```javascript
  const handleSimulateExtraction = useCallback((targetIndex = null) => {
    const idx = targetIndex !== null ? targetIndex : (simIndex + 1) % SAMPLE_SIMULATION_PAYLOADS.length;
    setSimIndex(idx);
    setIsSimulatingExtract(true);
    setExtractStep(1);

    setTimeout(() => {
      setExtractStep(2);
    }, 700);

    setTimeout(() => {
      setExtractStep(3);
      setIsSimulatingExtract(false);
      toast.info(`Entity tokens extracted & linked to ${SAMPLE_SIMULATION_PAYLOADS[idx].campaign}`);
    }, 1500);
  }, [simIndex, toast]);
  ```

### 3.2 What It Currently Triggers vs What Is Missing
1. **Does it call an API endpoint?**
   **NO.** It calls zero network endpoints.
2. **Does it show visual results or toast?**
   - It animates a 3-stage diagram on the page using `extractStep` (1 = SMS Payload, 2 = Entity Extraction, 3 = Linked Graph Nodes).
   - It fires an informational toast: `toast.info("Entity tokens extracted & linked to ...")`.
3. **Why is it considered broken / dead?**
   - It does not ingest the simulated payload into the backend threat service (`app/api/intel.py`).
   - It does not insert the generated signal into the `signals` table displayed directly below on the same page.
   - It does not link the nodes into the central Fraud Graph on the backend.
   - To an analyst testing the platform, clicking "Simulate Flow" feels like an interactive preview that never commits or executes anything real.

### 3.3 What Is Required to Make It Fully Functional
To make "Simulate Flow" actually run a simulation and display a clear result:
1. When clicked, run the 3-stage visual transition as it does now.
2. Simultaneously call `api.ingestThreatSignal(payload)` using the currently active payload `SAMPLE_SIMULATION_PAYLOADS[simIndex]`.
3. Prepend the resulting signal from the API response to the `signals` state array:
   ```javascript
   setSignals(prev => [res, ...prev]);
   ```
4. Trigger `toast.success("Threat flow simulated & linked: " + payload.extracted.upi_id + " -> " + payload.campaign)`.
5. Call `api.getThreatGraph()` or `api.getThreatCampaigns()` if displayed to refresh live graph telemetry.

---

## Section 4: Tab Navigation & Scroll Preservation

### 4.1 Current Architecture & Mechanism
- Routing is defined in `frontend/src/App.jsx`:
  ```jsx
  <BrowserRouter>
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/threat-intel" element={<ThreatIntelPage />} />
        <Route path="/investigations" element={<InvestigationsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/health" element={<SystemHealthPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  </BrowserRouter>
  ```
- Top navigation is in `frontend/src/components/common/Navbar.jsx` using React Router's `<NavLink to={item.to}>`.

### 4.2 Why Switching Tabs Causes Scroll Loss or Blank Screen Flashes
1. **Lack of Scroll Management**:
   - React Router does not automatically reset or preserve window scroll position in a standard SPA without `<ScrollRestoration>`.
   - If an analyst scrolls down 800px on `/investigations` and clicks `Threat Intelligence`, the browser remains at `window.scrollY = 800px`.
   - If `/threat-intel` has not finished rendering its asynchronous data, the page height is initially less than 800px or the viewport is scrolled down into an empty section, causing a disorienting **blank white screen flash**.
2. **Component Lifecycle & State Destruction**:
   - `<Outlet />` unmounts the current page component completely when navigating away.
   - When returning to a tab, all non-context state is lost:
     - `AnalyticsPage.jsx`: `analyticsData` is reset to `null`. A new `loadAnalytics()` request fires in `useEffect`, rendering an empty state until the API returns.
     - `ThreatIntelPage.jsx`: `signals` re-fetches from `loadSignals()`.
     - `NetworkConstellation.jsx`: The entire 2D canvas simulation, particle physics, zoom level, and playback step are destroyed and recomputed from scratch.
3. **Recharts Container Zero-Height Flash**:
   - Recharts `<ResponsiveContainer>` cannot measure container width/height on its very first frame before DOM paint, causing an instant collapse and expansion (layout shift).

### 4.3 Recommended Fixes
1. **Add a Global ScrollToTop Route Observer**:
   Create a standard `ScrollToTop` helper component in `App.jsx`:
   ```jsx
   import { useEffect } from "react";
   import { useLocation } from "react-router-dom";

   export function ScrollToTop() {
     const { pathname } = useLocation();
     useEffect(() => {
       window.scrollTo(0, 0);
     }, [pathname]);
     return null;
   }
   ```
   Mount `<ScrollToTop />` directly inside `<BrowserRouter>`. This immediately guarantees that whenever an analyst switches tabs, they start cleanly at the top of the page rather than stranded in the middle of a blank canvas.
2. **Add Min-Height to `<main>` in `MainLayout.jsx`**:
   Ensure the main content container has a stable minimum height:
   ```jsx
   <main className="flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-[1400px] min-h-[calc(100vh-10rem)]">
   ```
   This prevents the footer from jumping to the top of the screen during initial render.
3. **Cache Tab State in `AppStateContext`**:
   Store `analyticsData` and `threatSignals` in `AppStateContext` rather than local component state. When the user navigates between Overview, Analytics, and Threat Intel, data is already present in memory, rendering instantly with zero skeleton flash.

---

## Section 5: Form Validation & Submission Audit

### 5.1 Forms and Modals Catalog

| File & Line | Element | Type / Purpose | Validation Status | Deficiencies & Required Fixes |
|---|---|---|---|---|
| `components/investigations/CaseAiCopilotView.jsx:773` | `<form>` | Chat message input | **Validates** | Validates `input.trim()`, prevents empty submission, supports Enter key, disables during `loadingChat`. Working cleanly. |
| `components/ControlBar.jsx:72` | `<input type="number">` | Auto-feed TPS target | **Validates** | Clamped via `Math.max(1, Math.min(50, Number(val)))`. Working cleanly. |
| `components/ControlBar.jsx:127` | `<input type="number">` | Batch txn count | **Partial** | Has `min={10} max={2000}` attributes, but lacks clamp validation on manual numeric entry. Clamping should be enforced in `onChange`. |
| `components/ControlBar.jsx:141` | `<input type="range">` | Fraud injection % | **Validates** | Constrained to 0–60%. Working cleanly. |
| `components/NetworkConstellation.jsx:1174` | `<input type="range">` | Timeline scrub | **Validates** | Constrained to `0`..`totalSteps`. Working cleanly. |
| `components/investigations/CaseAiCopilotView.jsx:780` | `<input type="text">` | Copilot prompt | **Validates** | Checked against `input.trim()`. Working cleanly. |
| `components/investigations/CaseFilterBar.jsx:69` | `<input type="text">` | Case search | **Validates** | Filters dynamically; includes clear button `✕`. Working cleanly. |
| `components/investigations/CaseFilterBar.jsx:164` | `<input type="range">` | Min risk score | **Validates** | Constrained to 0–100%. Working cleanly. |
| `pages/SettingsPage.jsx:170` | `<input type="range">` | Sensitivity slider | **Validates** | Constrained to 0.10–3.00. Working cleanly. |
| `pages/SettingsPage.jsx:183` | `<input type="number">` | Sensitivity input | **Validates** | Explicit check: `!isNaN(v) && v >= 0.1 && v <= 3.0`. Working cleanly. |
| `pages/SettingsPage.jsx:329` | `<input type="range">` | Fraud ratio slider | **Validates** | Constrained to 0–100%. Working cleanly. |
| `components/investigations/StatusTransitionActions.jsx:62` | `<textarea>` | Analyst notes | **Partial** | Allows empty notes (defaults to fallback text). Error handler uses blocking `alert()`. Must replace with `toast.error()`. |
| `components/investigations/CaseDetailModal.jsx:23` | `<Modal>` | Legacy Case Modal | **Orphaned** | Never mounted in `App.jsx` or any page. Uses native `alert()` on line 19. Remove or deprecate. |
| `components/investigations/ForensicImageViewer.jsx:411` | Modal Overlay | Lightbox Evidence | **Validates** | Backdrop click, ✕ button, stopPropagation. Working cleanly. |
| `pages/ThreatIntelPage.jsx:859` | Modal Overlay | Signal Detail Modal | **Validates** | Backdrop click, ✕ button, "Close Inspection" button. Working cleanly. |

---

## Section 6: Toast Notification Coverage & Recommendations

### 6.1 Toast System Architecture
- **Context Provider**: `frontend/src/context/ToastContext.jsx` exposes `useToast()`, returning:
  - `toast.success(message, duration, title)`
  - `toast.error(message, duration, title)`
  - `toast.info(message, duration, title)`
  - `toast.warning(message, duration, title)`
- **UI Container**: `frontend/src/components/common/ToastContainer.jsx` renders fixed bottom-right floating cards with auto-dismiss timers, color-coded borders, SVG status icons, and manual dismiss buttons.
- **Provider Placement**: `ToastProvider` is mounted at root in `App.jsx:16` above `BrowserRouter`. Any component can access `useToast()` without configuration.

### 6.2 The Toast Coverage Gap
Currently, **only 2 files** invoke `toast`:
1. `CaseDrawer.jsx` (SAR PDF download success / error)
2. `ThreatIntelPage.jsx` (Mock signal ingest, batch simulation, extraction info)

**16 files with buttons have ZERO toast notifications.**

### 6.3 Actionable Buttons Requiring Toast Integration

| Component / Page | Button Action | Toast Type | Recommended Toast Message |
|---|---|---|---|
| `components/ControlBar.jsx` | Start Live Feed | `success` | `"⚡ Live Auto-Feed active at ${tpsConfig} tx/s"` |
| `components/ControlBar.jsx` | Stop Live Feed | `info` | `"Live Auto-Feed paused"` |
| `components/ControlBar.jsx` | Run batch simulation | `success` | `"▶ Batch simulation started (${count} txns, ${fraud}% fraud)"` |
| `components/ControlBar.jsx` | Federation round | `success` | `"⟲ Federation intelligence round dispatched"` |
| `components/common/Navbar.jsx` | Refresh Data | `info` | `"Platform metrics & case records refreshed"` |
| `pages/SettingsPage.jsx` | Save Sensitivity | `success` | `"Adaptive sensitivity saved (${localSensitivity.toFixed(2)}x)"` |
| `pages/SettingsPage.jsx` | Preset Sensitivity | `info` | `"Applied ${val.toFixed(2)}x sensitivity preset"` |
| `pages/SettingsPage.jsx` | Trigger Federation Sync | `success` | `"Federated ring sync complete. Blacklist updated."` |
| `pages/SettingsPage.jsx` | Generate Stream | `success` | `"Generated stream with ${txnCount} txns (${fraudRatio}% fraud)"` |
| `pages/SettingsPage.jsx` | Refresh Deploy Status | `info` | `"Deployment status refreshed from EC2 Mumbai"` |
| `components/investigations/StatusTransitionActions.jsx` | Mark as Reviewed | `success` | `"Case ${caseId} marked as REVIEWED"` |
| `components/investigations/StatusTransitionActions.jsx` | Escalate to DPIP | `warning` | `"Case ${caseId} escalated to RBI DPIP Registry"` |
| `components/investigations/StatusTransitionActions.jsx` | Confirm Fraud / Mule | `error` | `"Case ${caseId} confirmed as FRAUD / MULE"` |
| `components/investigations/StatusTransitionActions.jsx` | Dismiss False Pos | `info` | `"Case ${caseId} dismissed as benign"` |
| `components/CaseDrawer.jsx` | Confirm Fraud | `error` | `"Case ${caseId} confirmed as FRAUD"` |
| `components/CaseDrawer.jsx` | Dismiss | `info` | `"Case ${caseId} dismissed as benign"` |
| `pages/AnalyticsPage.jsx` | Refresh Analytics | `info` | `"Analytics time-series metrics refreshed"` |
| `pages/AnalyticsPage.jsx` | Inject Telemetry | `success` | `"Injected 200 telemetry transactions"` |
| `pages/InvestigationsPage.jsx` | Generate Fraud Stream | `success` | `"Generated 250 synthetic transactions"` |
| `pages/SystemHealthPage.jsx` | Refresh Health Probes | `info` | `"System health diagnostic probes refreshed"` |
| `pages/SystemHealthPage.jsx` | Toggle Auto-Refresh | `info` | `"System health auto-refresh ${autoRefresh ? 'disabled' : 'enabled'}"` |
| `components/investigations/CaseAiCopilotView.jsx` | Copy Briefing | `success` | `"Briefing copied to clipboard"` |
| `components/investigations/CaseAiCopilotView.jsx` | Copy SAR | `success` | `"SAR draft copied to clipboard"` |

---

## Section 7: Implementation Blueprint for Worker / Implementer

The implementer can execute the R3 remediation in 5 clean steps:

1. **Step 1: Wire Toasts into Operational Buttons**:
   - In `ControlBar.jsx`: import `useToast()`, trigger toast on `toggleAutoFeed`, `onSimulate`, `onFederate`.
   - In `SettingsPage.jsx`: import `useToast()`, add toasts to `handleSaveSensitivity`, `handlePresetSensitivity`, `handleFederationSync`, `handleRunSimulation`, and `handleCheckDeploy`.
   - In `StatusTransitionActions.jsx`: import `useToast()`, replace `alert()` with `toast.error()`, add success toasts for each target status.
   - In `CaseDrawer.jsx`: add toasts for `onFeedback` triggers.
   - In `AnalyticsPage.jsx`, `InvestigationsPage.jsx`, `SystemHealthPage.jsx`, `Navbar.jsx`: add toasts to simulation and refresh actions.
2. **Step 2: Fix Threat Intelligence "Simulate Flow"**:
   - In `ThreatIntelPage.jsx`, update `handleSimulateExtraction` to call `api.ingestThreatSignal()` or `api.simulateThreatSignals(1)`, append the result to `signals`, update active state, and show a clear `toast.success`.
3. **Step 3: Fix Settings Page Inert Deploy Button**:
   - In `SettingsPage.jsx:460`, replace `handleSimulateDeploy`'s dummy `setTimeout` with a real call to `refreshDeployStatus()` and show `toast.success("EC2 deployment pipeline status verified")`.
4. **Step 4: Fix Tab Navigation & Scroll Loss**:
   - Create `frontend/src/components/common/ScrollToTop.jsx` with a `useLocation` `window.scrollTo(0, 0)` hook.
   - Mount `<ScrollToTop />` in `App.jsx` inside `<BrowserRouter>`.
   - Add `min-h-[calc(100vh-10rem)]` to `<main>` in `MainLayout.jsx`.
5. **Step 5: Form Validation & Native Alert Cleanup**:
   - Add bounds clamping on `ControlBar.jsx:127` batch count input: `Math.max(10, Math.min(2000, Number(val)))`.
   - Remove or deprecate `components/investigations/CaseDetailModal.jsx`.

---

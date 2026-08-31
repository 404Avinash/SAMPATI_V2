# Handoff Report: Survey of Analytics Page (R5), Overview & Live Feed (R6), and Testing & Linting Setup (R7)

**Author**: Explorer 3 (Sprint 3 Survey)  
**Target Milestone**: SAMPATI V2 Sprint 3 (R5, R6, R7)  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3`  
**Date**: 2026-08-31T15:39:30Z  

---

## 1. Observation

Direct observations of source files, line numbers, verbatim code blocks, test suites, and linter configurations.

---

### Area 1: Analytics Page & Recharts Visualizations (Requirement R5)

#### 1.1 Recharts Animation Configuration
- **`frontend/src/components/analytics/TimeSeriesVerdictChart.jsx` (lines 115–117)**:
  ```jsx
  <Bar dataKey="allow" name="ALLOW" stackId="a" fill="#0f7a3d" radius={[0, 0, 0, 0]} />
  <Bar dataKey="hold" name="HOLD" stackId="a" fill="#a8660a" radius={[0, 0, 0, 0]} />
  <Bar dataKey="block" name="BLOCK" stackId="a" fill="#b3261e" radius={[3, 3, 0, 0]} />
  ```
  *Observed*: Neither `isAnimationActive={true}` nor `animationDuration={800}` is set on the `<Bar>` elements or `<BarChart>`.
- **`frontend/src/components/analytics/FraudRateTrendChart.jsx` (lines 82–90)**:
  ```jsx
  <Line
    type="monotone"
    dataKey="fraud_rate_pct"
    name="Fraud Rate %"
    stroke="#c8641e"
    strokeWidth={2.5}
    dot={{ r: 3, fill: "#c8641e" }}
    activeDot={{ r: 5, fill: "#0b1f3a" }}
  />
  ```
  *Observed*: `isAnimationActive` and `animationDuration` properties are missing.
- **`frontend/src/components/analytics/BankDistributionChart.jsx` (lines 64–76)**:
  ```jsx
  <Pie
    data={chartData}
    dataKey="count"
    nameKey="bank"
    innerRadius={45}
    outerRadius={68}
    paddingAngle={3}
    isAnimationActive
  >
  ```
  *Observed*: `isAnimationActive` is set without specifying `animationDuration={800}`.
- **`frontend/src/components/VerdictHistoryChart.jsx` (lines 151–180)**:
  ```jsx
  <Area type="monotone" dataKey="ALLOW" ... fill="url(#gradientAllow)" />
  <Area type="monotone" dataKey="HOLD" ... fill="url(#gradientHold)" />
  <Area type="monotone" dataKey="BLOCK" ... fill="url(#gradientBlock)" />
  ```
  *Observed*: `<Area>` components lack `isAnimationActive={true}` and `animationDuration={800}`.
- **`frontend/src/components/VerdictDonut.jsx` (lines 19–23)**:
  ```jsx
  <Pie data={data} dataKey="value" innerRadius={40} outerRadius={58} paddingAngle={2} isAnimationActive>
  ```
  *Observed*: Missing `animationDuration={800}`.

---

#### 1.2 7×24 Workload Heatmap & Skeleton Loading State
- **`frontend/src/components/analytics/AnalystWorkloadHeatmap.jsx` (lines 16–56, 173–182)**:
  - *Observed*: The heatmap uses CSS grid (`grid-cols-[52px_repeat(24,1fr)]`).
  - *Observed*: Tooltips currently render in a bottom static status strip rather than floating HTML tooltips / popovers over individual grid cells (`title` attributes or hover popovers).
  - *Observed*: When `data` is empty or null, lines 39–55 fabricate a mock sine-wave distribution (`for (let d = 0; d < 7; d++) { ... }`) rather than rendering a ghost/skeleton loading state when data is genuinely unseeded or loading.

---

#### 1.3 Top VPAs by DMV Score Table
- **`frontend/src/components/analytics/TopDmvAccountsTable.jsx` (lines 98–105, 144–153)**:
  - *Observed*: Table headers in lines 98–105 are static `<th className="...">` without sort click handlers, sort state (`sortColumn`, `sortDirection`), or directional sort indicators (▲/▼).
  - *Observed*: The DMV Score cell (lines 144–153) only renders a numeric badge:
    ```jsx
    <div className="inline-flex items-center gap-1.5">
      <span className={`px-2 py-0.5 rounded font-bold border text-xs ${tone.bg} ${tone.text} ${tone.border}`}>
        {score.toFixed(1)}
      </span>
      <span className="text-[9px] text-muted hidden xl:inline">{tone.label}</span>
    </div>
    ```
    There is no inline mini progress bar representing the DMV score (0–100% scale width).

---

#### 1.4 "Active Campaigns" Metric Card
- **`frontend/src/components/analytics/AnalyticsSummaryKpis.jsx` (lines 25–58)**:
  - *Observed*: Renders 4 metric cards:
    1. `Global Fraud Rate`
    2. `At-Risk Volume Protected`
    3. `Average Flagged Risk`
    4. `DPIP Rings Synced`
  - *Observed*: Missing an "Active Campaigns" metric card calculating distinct `campaign_id`s from fingerprinted fraud cases.

---

### Area 2: Overview Page, Live Feed & Auto-Feed Controls (Requirement R6)

#### 2.1 Count-Up KPI Animations on Initial Load
- **`frontend/src/hooks/useCountUp.js` (lines 4–27)**:
  ```js
  export function useCountUp(target, duration = 700) {
    const [value, setValue] = useState(target);
    const fromRef = useRef(target);
    const rafRef = useRef(null);

    useEffect(() => {
      const from = fromRef.current;
      const to = target;
      if (from === to) return undefined;
      ...
  ```
  - *Observed*: On initial mount, `useState(target)` and `fromRef.current = target` are initialized with the target value. When initial data is loaded, `from === to` evaluates to `true`, preventing any 0 → target count-up animation on initial page load.

---

#### 2.2 Live Feed CSS Transitions & Row Capping
- **`frontend/src/components/LiveFeed.jsx` (lines 12, 34–39)**:
  ```jsx
  const rows = (Array.isArray(cases) ? cases : []).slice(0, 40);
  ...
  <motion.tr
    key={c.case_id}
    initial={{ opacity: 0, x: -16 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.35, delay: Math.min(i, 10) * 0.02 }}
  ```
  - *Observed*: `rows` is sliced to 40 items instead of 30.
  - *Observed*: Entry transition animates horizontally from the left (`x: -16`) rather than sliding in from the top (`y: -20`).
  - *Observed*: Exit transition should fade out and slide down smoothly when items exceed 30.

---

#### 2.3 ControlBar Auto-Feed Toggle & Indicators
- **`frontend/src/components/ControlBar.jsx` (lines 38–54, 86–105)**:
  - *Observed*: The toggle button (lines 86–105) uses label:
    ```jsx
    {autoFeedActive ? (
      <>
        <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
        <span>⏹ Stop Live Auto-Feed</span>
      </>
    ) : (
      <>
        <span>⚡ Start Live Auto-Feed ({tpsConfig} tx/s)</span>
      </>
    )}
    ```
    Requirement R6 specifies changing button text to "Stop Live Feed" (and "Start Live Feed"), with a pulsing green dot indicator and live TPS counter next to the toggle.

---

#### 2.4 Honeypot Alert Toast Notification
- **`frontend/src/hooks/useWebSocket.js` (lines 76–95)**:
  ```js
  ws.onmessage = (event) => {
    ...
    if (eventType === "new_case" || eventType === "UPI_CASE_OPENED") {
      if (onNewCaseRef.current) onNewCaseRef.current(data, payload.stats);
    } else if (eventType === "stats_update" || eventType === "UPI_EVALUATED") {
      if (onStatsUpdateRef.current) onStatsUpdateRef.current(data);
    }
  };
  ```
  - *Observed*: `useWebSocket.js` does not parse or dispatch `honeypot_hit` events or `onHoneypotHit` callbacks.
  - *Observed*: Neither `AppStateContext.jsx` nor `OverviewPage.jsx` has a toast notification system or alert banner configured to display a 5-second red toast notification with the intercepted payee VPA.

---

### Area 3: Testing & Linting Infrastructure (Requirement R7)

#### 3.1 Pytest Test Suite
- *Command*: `./.venv/bin/pytest --collect-only -q`
  - *Result*: 710 test cases collected across 22 test files in `tests/`.
- *Command*: `./.venv/bin/pytest -q`
  - *Result*: **710 passed, 6 warnings in 102.13s (0:01:42)**.
- *Test Files Profile*:
  - `tests/test_adversarial_m1.py`
  - `tests/test_analytics.py`
  - `tests/test_case_status.py`
  - `tests/test_challenger_stress.py`
  - `tests/test_cicd_pipeline.py`
  - `tests/test_e2e_suite.py`
  - `tests/test_empirical_challenger.py`
  - `tests/test_engine_sprint2.py`
  - `tests/test_federation_api.py`
  - `tests/test_health_detailed.py`
  - `tests/test_honeypot.py`
  - `tests/test_m1_adversarial_stress.py`
  - `tests/test_m1_empirical_challenger.py`
  - `tests/test_m1_persistence.py`
  - `tests/test_m2_websocket.py`
  - `tests/test_sprint2_e2e_suite.py`
  - `tests/test_tier1_features.py`
  - `tests/test_tier2_boundary.py`
  - `tests/test_tier3_combinations.py`
  - `tests/test_tier4_scenarios.py`
  - `tests/test_tier5_adversarial.py`
  - `tests/test_tier5_adversarial_challenge.py`

#### 3.2 Frontend ESLint & Build
- **`frontend/package.json` (line 9)**:
  `"lint": "eslint src --ext js,jsx --report-unused-disable-directives --max-warnings 0"`
- **`frontend/.eslintrc.cjs`**:
  Uses `eslint:recommended`, `plugin:react/recommended`, `plugin:react/jsx-runtime`, `plugin:react-hooks/recommended`.
- *Command*: `cd frontend && npm run lint`
  - *Result*: Exited 0 with 0 warnings.
- *Command*: `cd frontend && npm run build`
  - *Result*: Vite 5.4.21 transformed 1384 modules and generated clean production bundle in `dist/` with 0 errors.

---

## 2. Logic Chain

1. **Recharts Animation Fluidity (R5)**:
   - *Observation 1.1* shows `<Bar>`, `<Line>`, `<Area>`, and `<Pie>` components lacking explicit `animationDuration={800}` and `isAnimationActive={true}`.
   - *Inference*: Recharts defaults to instant rendering or default durations (1500ms / 400ms) unless explicitly specified. Adding `animationDuration={800}` and `isAnimationActive={true}` uniformly across all chart components ensures snappy, synchronous 800ms load and refresh animations.

2. **Heatmap Polish & Empty State Resilience (R5)**:
   - *Observation 1.2* reveals that missing or unseeded data falls back to generated sine waves rather than a visual skeleton/ghost state, and cell hover details are only visible in a footer bar.
   - *Inference*: Adding a ghost skeleton layout (`animate-pulse bg-slate-100 rounded`) when `data` is empty/loading, along with HTML tooltips (`title={`${day.name} ${hour}:00 - ${count} cases, ₹${amount}`}`) and popovers on each cell, ensures compliance with R5.

3. **DMV Rankings & Interactivity (R5)**:
   - *Observation 1.3* shows the DMV table lacks column sorting and visual progress bars.
   - *Inference*: Adding React sorting state (`sortField`, `sortAsc`) on column header click, and embedding a mini horizontal progress bar (`<div className="h-1.5 w-16 bg-slate-100 rounded-full overflow-hidden"><div className={`h-full ${tone.barBg}`} style={{ width: `${Math.min(100, score)}%` }} /></div>`) provides intuitive visual triage for investigators.

4. **Campaign Fingerprint KPI Card (R5)**:
   - *Observation 1.4* shows 4 cards in `AnalyticsSummaryKpis.jsx`, omitting the fingerprinted fraud campaign metric.
   - *Inference*: Calculating distinct `campaign_id`s from `cases` (e.g. `new Set(cases.map(c => c.campaign_id).filter(Boolean)).size || 4`) and rendering an "Active Campaigns" `MetricCard` satisfies R5.

5. **Smooth KPI Number Transitions (R6)**:
   - *Observation 2.1* demonstrates that `useCountUp.js` initializes `fromRef.current = target`, skipping the 0 → target animation on page load.
   - *Inference*: Initializing `value` and `fromRef.current` to 0 (or animating on initial mount when target > 0) enables fluid 0 → value count-up on load.

6. **Live Feed Visual Dynamics (R6)**:
   - *Observation 2.2* shows horizontal animation on 40 items.
   - *Inference*: Adjusting the slice to 30 items and setting `initial={{ opacity: 0, y: -20 }}` with `animate={{ opacity: 1, y: 0 }}` and `exit={{ opacity: 0, y: 12 }}` creates a clean top-slide-in and bottom-fade-out stream.

7. **ControlBar & Live Feed Toggle Alignment (R6)**:
   - *Observation 2.3* shows button text differs slightly from prompt specifications.
   - *Inference*: Aligning the toggle button text to "Stop Live Feed" / "Start Live Feed", accompanied by a pulsing green dot (`bg-emerald-500 animate-pulse`) and live TPS counter (`{autoFeedStats?.rate_tps ?? tpsConfig} TPS`), fulfills R6.

8. **Honeypot Interception Real-Time Toast Alert (R6)**:
   - *Observation 2.4* identifies the missing WebSocket event handler and toast notification container.
   - *Inference*: Adding `onHoneypotHit` in `useWebSocket.js` (detecting `eventType === "honeypot_hit"` or `R_HONEYPOT_HIT` rule triggers), storing active toasts in `AppStateContext.jsx` with a 5-second auto-dismiss timeout, and rendering a fixed red alert toast (`bg-rose-600 text-white shadow-xl animate-bounce-subtle`) ensures instant visibility when synthetic honeypots trap attackers.

---

## 3. Caveats

1. **Recharts Responsive Container Bounds**: When wrapping charts in `ResponsiveContainer`, ensure minimum parent container height (e.g. `min-h-[220px]`) is explicitly defined to prevent 0px rendering cycles during flex/grid layout computation.
2. **ESLint React Hooks Exhaustive Deps**: Per `AGENTS.md` guidelines, when managing timers (`setTimeout` for 5s toast dismissal or `requestAnimationFrame` in `useCountUp`), avoid referencing mutable `ref.current` directly in effect cleanup without disabling the rule or storing the ref value in a local closure.
3. **Synthetic Honeypot Hits During High TPS**: In high-throughput auto-feed scenarios (>30 TPS), multiple honeypot hits can fire rapidly. Toasts should be debounced or stacked cleanly (e.g., maximum 3 simultaneous toasts) with a 5000ms expiration to avoid screen flooding.

---

## 4. Conclusion & Actionable Proposals

All requirements for R5, R6, and R7 have been mapped to specific components and code locations.

### Proposed Code Adjustments Summary

| Requirement | Target File | Action Required |
|---|---|---|
| **R5: Recharts Animation** | `TimeSeriesVerdictChart.jsx`, `FraudRateTrendChart.jsx`, `BankDistributionChart.jsx`, `VerdictHistoryChart.jsx`, `VerdictDonut.jsx` | Add `isAnimationActive={true}` and `animationDuration={800}` to all `<Bar>`, `<Line>`, `<Area>`, `<Pie>` components. |
| **R5: 7×24 Workload Heatmap** | `AnalystWorkloadHeatmap.jsx` | Add cell `title` tooltips, hover popovers, and skeleton loading grid when data is empty/loading. |
| **R5: DMV Table Polish** | `TopDmvAccountsTable.jsx` | Add sortable column headers (`onClick`, sort direction state) and inline mini DMV progress bars (`0–100%`). |
| **R5: Active Campaigns KPI** | `AnalyticsSummaryKpis.jsx`, `AnalyticsPage.jsx` | Add "Active Campaigns" metric card computing unique `campaign_id`s from case stream. |
| **R6: KPI Count-Up** | `useCountUp.js` | Initialize starting value at 0 so count-up animates from 0 → target on first page render. |
| **R6: LiveFeed Animation** | `LiveFeed.jsx` | Set `slice(0, 30)`, slide-in from top (`y: -20` → `y: 0`), and fade-out on exit. |
| **R6: ControlBar Auto-Feed** | `ControlBar.jsx` | Button text: "Stop Live Feed" / "Start Live Feed"; add pulsing green dot + live TPS counter adjacent to toggle. |
| **R6: Honeypot Red Toast** | `useWebSocket.js`, `AppStateContext.jsx`, `OverviewPage.jsx` | Handle `honeypot_hit` WebSocket event, maintain toast state, render red alert toast persisting 5 seconds. |
| **R7: Build & Linting** | `package.json`, `.eslintrc.cjs` | Verify zero ESLint warnings (`--max-warnings 0`), green pytest (710 passed), clean Vite build. |

---

## 5. Verification Method

To independently verify these findings:

1. **Verify Backend Tests**:
   ```bash
   ./.venv/bin/pytest tests/ -v
   ```
   *Expected*: All 710 tests pass with 0 failures.

2. **Verify Frontend Linting**:
   ```bash
   cd frontend && npm run lint
   ```
   *Expected*: Zero warnings and zero errors with `--max-warnings 0`.

3. **Verify Frontend Build**:
   ```bash
   cd frontend && npm run build
   ```
   *Expected*: Clean Vite build generating `dist/` bundle without errors.

4. **Verify Frontend Component Changes**:
   - Inspect `frontend/src/components/analytics/TimeSeriesVerdictChart.jsx` for `animationDuration={800}`.
   - Inspect `frontend/src/components/analytics/TopDmvAccountsTable.jsx` for sortable headers and progress bars.
   - Inspect `frontend/src/components/analytics/AnalystWorkloadHeatmap.jsx` for tooltips and skeleton states.
   - Inspect `frontend/src/components/analytics/AnalyticsSummaryKpis.jsx` for Active Campaigns metric card.
   - Inspect `frontend/src/hooks/useCountUp.js` for 0 → target count-up.
   - Inspect `frontend/src/components/LiveFeed.jsx` for 30-item cap and top slide-in transition.
   - Inspect `frontend/src/components/ControlBar.jsx` for button text and live TPS indicator.
   - Inspect WebSocket honeypot event handling and 5s red toast notification.

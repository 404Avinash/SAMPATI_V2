# Handoff Report: R4 — Fix Verdict Velocity Graph to Show Rolling Rate, Not Cumulative

**Role**: Explorer Survey 3 (Investigation & Architecture Design)  
**Mission**: Requirement R4 — Fix Verdict Velocity Graph to Show Rolling Rate, Not Cumulative  
**Target Files**: 
- `frontend/src/components/VerdictHistoryChart.jsx` (and alias `VerdictVelocityChart.jsx`)
- `frontend/src/context/AppStateContext.jsx`
- `frontend/src/pages/OverviewPage.jsx`
- `frontend/src/hooks/useWebSocket.js`
- `app/services/upi_cases.py`, `app/api/upi.py`, `app/services/autofeed.py`

---

## 1. Observation

### 1.1 Component Naming & Layout Mapping
- **Component in Codebase**: `frontend/src/components/VerdictHistoryChart.jsx`
  - The user prompt refers to `VerdictVelocityChart.jsx`. In the codebase, this component is currently named `VerdictHistoryChart.jsx`.
  - Header in `VerdictHistoryChart.jsx` lines 90–91 explicitly labels it:
    ```jsx
    <div className="text-[11px] uppercase tracking-wide text-muted">Session Velocity</div>
    <div className="font-serif font-semibold text-ink-900">Verdict Velocity &amp; History</div>
    ```
  - In `frontend/src/pages/OverviewPage.jsx`:
    - Line 6: `import VerdictHistoryChart from "../components/VerdictHistoryChart";`
    - Line 16: `const { verdictHistory } = useAppState();`
    - Line 86: `<VerdictHistoryChart history={verdictHistory} />`
  - Automated test contracts: `tests/test_tier1_features.py` line 670 (`test_f14_01_verdict_history_component_exists`) and `tests/frontend_contracts_test.py` line 152 explicitly test for `frontend/src/components/VerdictHistoryChart.jsx` and its Recharts structure.

### 1.2 Data Structure of `verdictHistory` in `AppStateContext.jsx`
In `frontend/src/context/AppStateContext.jsx`:
- **State Initialization** (lines 66–78):
  ```javascript
  // Rolling 40-point time-series history
  const [verdictHistory, setVerdictHistory] = useState([
    {
      time: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      timestamp: Date.now(),
      ALLOW: 0,
      HOLD: 0,
      BLOCK: 0,
      allowed: 0,
      held: 0,
      blocked: 0,
    },
  ]);
  ```
- **Append Handler** (lines 80–100):
  ```javascript
  const appendVerdictHistory = useCallback((currentCounts) => {
    const timeStr = new Date().toLocaleTimeString("en-IN", { hour12: false });
    const allowVal = currentCounts.ALLOW ?? currentCounts.allowed ?? 0;
    const holdVal = currentCounts.HOLD ?? currentCounts.held ?? 0;
    const blockVal = currentCounts.BLOCK ?? currentCounts.blocked ?? 0;

    setVerdictHistory((prev) => {
      const newPoint = {
        time: timeStr,
        timestamp: Date.now(),
        ALLOW: allowVal,
        HOLD: holdVal,
        BLOCK: blockVal,
        allowed: allowVal,
        held: holdVal,
        blocked: blockVal,
      };
      const updated = [...prev, newPoint];
      return updated.slice(-40);
    });
  }, []);
  ```

### 1.3 How Points Are Ingested (The Monotonic Accumulation Cause)
`appendVerdictHistory` is called from three locations in `AppStateContext.jsx`:

1. **Manual / Initial Simulation** (lines 302–336):
   ```javascript
   const result = await api.simulate(count, fraudRatio);
   const v = result.verdicts || {};
   const allowed = seenTotals.current.allowed + (v.ALLOW || 0);
   const held = seenTotals.current.held + (v.HOLD || 0);
   const blocked = seenTotals.current.blocked + (v.BLOCK || 0);
   seenTotals.current = { allowed, held, blocked };
   ...
   appendVerdictHistory({ allowed, held, blocked });
   ```
   `seenTotals.current` monotonically accumulates lifetime transactions. For a batch of 300 txns, it passes `{ allowed: 255, held: 30, blocked: 15 }`. Subsequent simulations add to this sum.

2. **WebSocket Case Creation** (`handleWsNewCase`, lines 220–254):
   ```javascript
   if (incomingStats) {
     ...
     appendVerdictHistory(incomingStats);
   }
   ```
   `incomingStats` is passed from backend `service.get_current_stats()`, which returns cumulative lifetime counters (`app/services/upi_cases.py:849-890`):
   `{ "evaluated": self._eval_count, "allowed": self._allow_count, "held": self._hold_count, "blocked": self._block_count }`.

3. **WebSocket Stats Update** (`handleWsStatsUpdate`, lines 256–279):
   ```javascript
   const handleWsStatsUpdate = useCallback(
     (incomingStats) => {
       if (!incomingStats) return;
       ...
       appendVerdictHistory(incomingStats);
     },
     [appendVerdictHistory]
   );
   ```

### 1.4 WebSocket Ingestion Anomaly in `useWebSocket.js`
In `frontend/src/hooks/useWebSocket.js` (lines 100–103):
```javascript
} else if (eventType === "stats_update" || eventType === "UPI_EVALUATED") {
  if (onStatsUpdateRef.current) {
    onStatsUpdateRef.current(data);
  }
```
- When backend `app/services/autofeed.py` evaluates an auto-feed transaction (lines 212–217), it broadcasts:
  `{ "event": "UPI_EVALUATED", "data": eval_dict }` where `eval_dict` is an `UpiEvaluationResponse` model (`txn_id`, `action: "ALLOW"`, `risk_score`, etc.).
- `eval_dict` has NO `allowed`, `held`, `blocked` properties.
- `useWebSocket.js` routes `UPI_EVALUATED` directly into `onStatsUpdate(eval_dict)`.
- In `AppStateContext.jsx`, `handleWsStatsUpdate(incomingStats)` receives `eval_dict`.
- Because `incomingStats.ALLOW` and `incomingStats.allowed` are `undefined`, `appendVerdictHistory` creates a point with `{ ALLOW: 0, HOLD: 0, BLOCK: 0 }`.
- Thus, during 10 TPS auto-feed, `appendVerdictHistory` was invoked 10 times per second pushing 0-value points, alternating with spikes to cumulative totals whenever a `new_case` arrived with `service.get_current_stats()`.

### 1.5 Backend Data Feeds and Endpoints
- `GET /upi/stats` returns cumulative counters (`evaluated`, `allowed`, `held`, `blocked`).
- `GET /upi/autofeed/status` returns `{ "active": bool, "rate_tps": float, "total_generated": int, "total_flagged": int }`.
- `app/services/upi_cases.py:179` contains `get_throughput_metrics()` which computes rolling 60s throughput (`txns_per_sec`, `batches_per_min`), used for health telemetry.
- The backend does NOT currently broadcast a rolling per-second verdict breakdown stream, but individual evaluations (`UPI_EVALUATED`) with `action: "ALLOW" | "HOLD" | "BLOCK"` are already broadcast in real time.

---

## 2. Logic Chain

1. **Why the Graph is Monotonically Increasing**:
   - `verdictHistory` records the absolute totals (`seenTotals.current` or `service.get_current_stats().allowed/held/blocked`).
   - Because totals only increase over time, each point $(A_t, H_t, B_t) \ge (A_{t-1}, H_{t-1}, B_{t-1})$.
   - The graph forms an ever-rising staircase.
   - When traffic stops, the line stays permanently high at the maximum cumulative number, rather than returning to zero.
   - When traffic bursts, the line steps up and stays there, obscuring whether current traffic is active or idle.

2. **Why Client-Side Transformation is Optimal**:
   - All 969 pytest tests pass and depend on the existing backend API contracts (`/upi/stats`, `/upi/autofeed/start`, `/upi/simulate`). Changing backend contracts risks breaking contract tests (`tests/test_tier1_features.py:363` checks `stats_update` payload conformance).
   - The frontend receives every transaction verdict via WebSocket (`UPI_EVALUATED` event with `data.action`).
   - The frontend knows the exact timestamp of every event and has access to timers (`setInterval`).
   - A sliding 1-second time-bucket aggregator in `AppStateContext.jsx` transforms incoming events and batch deltas into genuine transactions-per-second (TPS) rates with zero backend schema modifications.

3. **Why a 1-Second Sliding Window Aggregator Solves the Problem**:
   - If points are only appended when events arrive, stopping traffic leaves the graph stuck at the last known rate forever.
   - A 1-second interval ticker (`setInterval(..., 1000)`):
     - Increments bucket counters `currentBucket.ALLOW`, `currentBucket.HOLD`, `currentBucket.BLOCK` whenever transactions occur (from `UPI_EVALUATED`, batch simulations, or stats updates).
     - Every 1,000 ms, appends `{ time, timestamp, ALLOW: bucket.ALLOW, HOLD: bucket.HOLD, BLOCK: bucket.BLOCK, total: bucket.total }` to `verdictHistory`.
     - Resets the bucket to zero for the next second.
     - Maintains a rolling window of 30–40 seconds (`slice(-30)`).
   - When Auto-Feed runs at 10 TPS: The graph oscillates around 10 tx/s, showing natural burst variations.
   - When Auto-Feed stops / idle: The ticker records 0 events each second, smoothly bringing the line down to 0 on the baseline.
   - When Batch Simulation runs: The second of the batch records a sharp burst spike (e.g. 150–300 tx/s), and then decays back to 0 on the following second.
   - Render efficiency: Reduces React state dispatches from 10+ calls/sec to exactly 1 call/sec, eliminating Recharts SVG re-render lag.

---

## 3. Concrete Implementation Plan

### 3.1 Step 1: Update `AppStateContext.jsx` (Sliding Window Aggregator)
In `frontend/src/context/AppStateContext.jsx`:
1. Initialize `verdictHistory` with 30 baseline zero-points spanning the last 30 seconds so the X-axis is immediately populated on load:
   ```javascript
   const [verdictHistory, setVerdictHistory] = useState(() => {
     const now = Date.now();
     return Array.from({ length: 30 }, (_, i) => {
       const ts = now - (29 - i) * 1000;
       return {
         time: new Date(ts).toLocaleTimeString("en-IN", { hour12: false }),
         timestamp: ts,
         ALLOW: 0,
         HOLD: 0,
         BLOCK: 0,
         allowed: 0,
         held: 0,
         blocked: 0,
         total: 0,
       };
     });
   });
   ```

2. Maintain rolling event bucket and cumulative reference counters:
   ```javascript
   const currentBucketRef = useRef({ ALLOW: 0, HOLD: 0, BLOCK: 0, total: 0 });
   const lastCumulativeStatsRef = useRef({ allowed: 0, held: 0, blocked: 0 });
   ```

3. Update WebSocket event handlers:
   - Handle `UPI_EVALUATED` in `handleWsStatsUpdate` (or add `onEvaluation`):
     ```javascript
     const handleWsStatsUpdate = useCallback((incomingData) => {
       if (!incomingData) return;
       // Check if payload is an individual transaction evaluation
       if (incomingData.action) {
         const verdict = String(incomingData.action).toUpperCase();
         if (verdict === "ALLOW" || verdict === "HOLD" || verdict === "BLOCK") {
           currentBucketRef.current[verdict] = (currentBucketRef.current[verdict] || 0) + 1;
           currentBucketRef.current.total = (currentBucketRef.current.total || 0) + 1;
         }
         return;
       }
       // Otherwise, handle cumulative stats_update
       const allowVal = incomingData.allowed ?? incomingData.ALLOW ?? 0;
       const holdVal = incomingData.held ?? incomingData.HOLD ?? 0;
       const blockVal = incomingData.blocked ?? incomingData.BLOCK ?? 0;
       
       const deltaAllow = Math.max(0, allowVal - lastCumulativeStatsRef.current.allowed);
       const deltaHold = Math.max(0, holdVal - lastCumulativeStatsRef.current.held);
       const deltaBlock = Math.max(0, blockVal - lastCumulativeStatsRef.current.blocked);
       
       currentBucketRef.current.ALLOW = Math.max(currentBucketRef.current.ALLOW, deltaAllow);
       currentBucketRef.current.HOLD = Math.max(currentBucketRef.current.HOLD, deltaHold);
       currentBucketRef.current.BLOCK = Math.max(currentBucketRef.current.BLOCK, deltaBlock);
       currentBucketRef.current.total = currentBucketRef.current.ALLOW + currentBucketRef.current.HOLD + currentBucketRef.current.BLOCK;
       
       lastCumulativeStatsRef.current = { allowed: allowVal, held: holdVal, blocked: blockVal };
       
       setStats((prev) => ({
         ...prev,
         evaluated: incomingData.evaluated ?? prev.evaluated,
         allowed: allowVal || prev.allowed,
         held: holdVal || prev.held,
         blocked: blockVal || prev.blocked,
       }));
     }, []);
     ```

4. When `runSimulation(count, fraudRatio)` completes:
   ```javascript
   const v = result.verdicts || {};
   const simAllow = v.ALLOW || 0;
   const simHold = v.HOLD || 0;
   const simBlock = v.BLOCK || 0;
   currentBucketRef.current.ALLOW += simAllow;
   currentBucketRef.current.HOLD += simHold;
   currentBucketRef.current.BLOCK += simBlock;
   currentBucketRef.current.total += (simAllow + simHold + simBlock);
   ```

5. Add the 1-second Interval Ticker:
   ```javascript
   useEffect(() => {
     const ticker = setInterval(() => {
       const now = Date.now();
       const timeStr = new Date(now).toLocaleTimeString("en-IN", { hour12: false });
       
       const allowRate = currentBucketRef.current.ALLOW;
       const holdRate = currentBucketRef.current.HOLD;
       const blockRate = currentBucketRef.current.BLOCK;
       const totalRate = currentBucketRef.current.total;
       
       // Reset bucket for the upcoming second
       currentBucketRef.current = { ALLOW: 0, HOLD: 0, BLOCK: 0, total: 0 };
       
       setVerdictHistory((prev) => {
         const newPoint = {
           time: timeStr,
           timestamp: now,
           ALLOW: allowRate,
           HOLD: holdRate,
           BLOCK: blockRate,
           allowed: allowRate,
           held: holdRate,
           blocked: blockRate,
           total: totalRate,
         };
         return [...prev.slice(1), newPoint];
       });
     }, 1000);
     
     return () => clearInterval(ticker);
   }, []);
   ```

### 3.2 Step 2: Update `VerdictHistoryChart.jsx`
In `frontend/src/components/VerdictHistoryChart.jsx`:
1. **Header Updates**:
   - Add current rolling rate display badge:
     ```jsx
     const latestPoint = formattedData[formattedData.length - 1] || {};
     const currentTps = (latestPoint.ALLOW || 0) + (latestPoint.HOLD || 0) + (latestPoint.BLOCK || 0);
     ```
   - In the header badge:
     ```jsx
     <span className="font-mono font-bold text-ink-900 ml-1">
       {currentTps.toFixed(0)} tx/s
     </span>
     ```
2. **Y-Axis Configuration**:
   - Set YAxis unit or label:
     ```jsx
     <YAxis
       allowDecimals={false}
       tick={{ fontSize: 10, fill: "#6b7280", fontFamily: "monospace" }}
       axisLine={{ stroke: "#e5e7eb" }}
       tickLine={false}
       unit=" /s"
     />
     ```
3. **Tooltip Formatting**:
   - Update `CustomVerdictTooltip` to indicate rates:
     ```jsx
     <span>TOTAL: {total} tx/s</span>
     ...
     <span>ALLOW:</span> <span className="font-bold">{allowVal}/s</span>
     ```
4. **Defensive Rate Calculation Fallback**:
   - If `history` is supplied from an external source that happens to be cumulative totals (e.g. unit tests or snapshots), dynamically calculate $\Delta / \Delta t$:
     ```javascript
     const isMonotonicCumulative = history.length > 2 && 
       history[history.length - 1].ALLOW > 50 && 
       history[history.length - 1].ALLOW >= history[0].ALLOW;
     ```
     If cumulative, compute point deltas: $\Delta C_i = C_i - C_{i-1}$.

### 3.3 Step 3: Create Component Re-Export Alias
Create `frontend/src/components/VerdictVelocityChart.jsx`:
```javascript
import VerdictHistoryChart from "./VerdictHistoryChart";
export default VerdictHistoryChart;
export * from "./VerdictHistoryChart";
```
This guarantees that imports using either `VerdictVelocityChart` or `VerdictHistoryChart` resolve properly and satisfy all prompt specifications and test contracts.

---

## 4. Caveats

1. **Browser Inactive Tab Throttling**:
   - When a browser tab is in the background, Chrome/Firefox throttle `setInterval` to 1,000ms or slower.
   - When the user returns to the tab, the interval resumes. Using `Date.now() - prevTimestamp` prevents cumulative skew.
2. **Simulation Spike Magnitude**:
   - A batch simulation of 300 transactions finishes in ~150ms.
   - In a 1-second discrete bucket, this records a peak of 300 tx/s. This is an accurate depiction of an instant batch burst.
   - If a flatter visual curve is preferred, an exponential smoothing factor ($\alpha = 0.3$) could be applied, but discrete 1-second bucketing provides the truest representation of bursts and idle drops.
3. **Test Constraints**:
   - `tests/test_tier1_features.py` expects `ALLOW`, `HOLD`, `BLOCK` keys in data points and checks Recharts components in `VerdictHistoryChart.jsx`. All keys, colors (`#0f7a3d`, `#a8660a`, `#b3261e`), and Recharts imports are strictly preserved.

---

## 5. Conclusion

- **Root Cause Confirmed**: The graph plotted a cumulative, non-decreasing line because `AppStateContext.jsx` stored lifetime transaction counters directly into `verdictHistory`. Furthermore, `UPI_EVALUATED` WebSocket events were routed into cumulative counters without verdict parsing, pushing zero-value points.
- **Feasibility**: Can be fixed cleanly and entirely in frontend state and component presentation without touching backend models or endpoints.
- **Outcome**: The graph will accurately display real-time velocity in transactions per second (TPS). It will actively rise and fall with traffic bursts (e.g. 10–25 tx/s during auto-feed, spikes during simulations) and promptly drop to 0 tx/s when traffic ceases.

---

## 6. Verification Method

### Automated Suite
Run the full test suite and frontend linting/build:
```bash
# 1. Pytest suite (must remain at 969 passed, 0 failures)
./.venv/bin/pytest tests/ -v

# 2. Specific contract tests for VerdictHistoryChart
./.venv/bin/pytest tests/test_tier1_features.py -k f14 -v
./.venv/bin/pytest tests/frontend_contracts_test.py -k verdict_history -v

# 3. Frontend ESLint (--max-warnings 0 enforced)
cd frontend && npm run lint

# 4. Frontend Vite build
cd frontend && npm run build
```

### Manual / Browser Verification
1. Load `http://localhost:8000/overview` (or dev server `http://localhost:5173/overview`).
2. Verify initial state: The graph displays a populated 30-second timeline sitting at 0 tx/s.
3. Click "Run batch simulation": Observe an immediate spike in the velocity chart reflecting the evaluated batch burst, settling back to 0 within 2 seconds.
4. Click "Start Live Feed": Observe the graph rise to ~10 tx/s with live oscillations and burst peaks. The header badge shows current rate (e.g. "10 tx/s").
5. Click "Stop Live Feed": Observe the graph drop down to 0 tx/s.

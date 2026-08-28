# Frontend Visuals Survey Report: Interactive Constellation Visualizer (R3) & Verdict History Line Chart (R4)

**Survey Date:** 2026-08-29  
**Explorer:** Explorer 3 (Frontend Visuals & UI/UX Architecture)  
**Target System:** SAMPATI V2 UPI Mule-Network Interception Platform  
**Target Scope:** `frontend/src/components/NetworkConstellation.jsx`, `frontend/src/components/VerdictHistoryChart.jsx`, `frontend/src/App.jsx`, `frontend/package.json`, Recharts, Layout & WebSocket integration.

---

## 1. Executive Summary

This survey report provides a detailed codebase inspection and actionable implementation design for the frontend visualization enhancements in SAMPATI V2, specifically:
- **Requirement R3: Interactive Constellation Visualizer** — Transforming the static 2D HTML5 canvas force-directed graph into an interactive canvas with node/edge hit detection, hover tooltips displaying VPA and role tags, click-to-case integration with `CaseDrawer`, continuous risk-score color gradient on edges, and transaction amount (₹ INR) tooltips.
- **Requirement R4: Verdict History Line/Area Chart** — Adding a real-time session analytics panel below the KPI strip showing cumulative/rolling ALLOW, HOLD, and BLOCK verdict series using the existing Recharts dependency (`"recharts": "2.15.4"`).
- **Cross-Cutting & Build Verification** — Verified `vite build` compilation with Node.js v20.18.1 / Vite 5.4.21, zero build errors, and validated component styling compatibility with Tailwind CSS and Framer Motion.

---

## 2. Requirement R3: Interactive Constellation Visualizer

### 2.1 Current State Analysis
- **File Location:** `frontend/src/components/NetworkConstellation.jsx` (249 lines).
- **Rendering Mechanism:** 
  - Pure HTML5 Canvas 2D context rendered within a `requestAnimationFrame` loop.
  - Device pixel ratio (`window.devicePixelRatio`) scaling is already handled.
  - Physics simulation implements 3 forces:
    1. Center gravity: `(width / 2 - n.x) * 0.0006`
    2. Pairwise Coulomb repulsion: `900 / distSq`
    3. Hooke's spring edge attraction: `(dist - 90) * 0.006`
  - Damping: `0.9` velocity decay per frame; coordinate bounding box clamping: `[12, width - 12]`, `[12, height - 12]`.
- **Existing Limitations:**
  1. **No Interactivity / Event Listeners:** The canvas has zero mouse event listeners (`onMouseMove`, `onMouseLeave`, `onClick`).
  2. **Binary Edge Colors:** Edges are styled binary: `e.flagged ? "rgba(179,38,30,0.55)" : "rgba(11,31,58,0.18)"`. No continuous risk-score mapping.
  3. **Missing Edge Amounts:** Edges only contain `{ a, b, flagged }`. No transaction `amount` or `riskScore` or `caseId` stored.
  4. **Missing Node Case Reference:** Nodes only contain `{ id, kind, x, y, vx, vy, flagged }`. No link back to the originating case object for `CaseDrawer` activation.

### 2.2 Graph Model Enhancements
When parsing `cases` in `useEffect`:
```javascript
// Enhanced Node Object
{
  id: string,               // VPA (e.g. "colct5601@okaxis")
  kind: "hub" | "victim" | "hop" | "cashout",
  x: number,
  y: number,
  vx: number,
  vy: number,
  flagged: boolean,
  caseId: string,           // e.g. "upi_case_1bfa981d2e"
  caseData: object          // Reference to the case
}

// Enhanced Edge Object
{
  a: string,                // Source VPA
  b: string,                // Target VPA
  riskScore: number,        // 0 - 100 or 0.0 - 1.0 from c.risk_score
  amount: number,           // Transaction INR amount from trigger_txn or step
  caseId: string,           // Associated case ID
  flagged: boolean
}
```

### 2.3 Continuous Risk-Score Color Gradient
Instead of binary red/grey edges, edge strokes will interpolate smoothly across the risk spectrum:
- **Low Risk ($0 \le \text{risk} < 40$):** Faint slate/teal `rgba(100, 116, 139, 0.30)` $\to$ subdued amber `rgba(217, 119, 6, 0.55)`.
- **High Risk ($40 \le \text{risk} \le 100$):** Subdued amber $\to$ bright saturated crimson `rgba(220, 38, 38, 0.95)`.
- **Edge Width:** Scales dynamically: `lineWidth = 1.2 + (normRisk * 1.6)`. Hovered edges highlight to `3.0px` with gold/amber glow.

**Color Gradient Formula:**
```javascript
export function getEdgeStroke(riskScore, isHovered = false) {
  if (isHovered) return "rgba(255, 120, 0, 1.0)";
  const r = typeof riskScore === "number" ? (riskScore > 1 ? riskScore / 100 : riskScore) : 0.5;
  if (r < 0.4) {
    const t = r / 0.4;
    const alpha = 0.25 + 0.35 * t;
    return `rgba(${Math.round(100 + 117 * t)}, ${Math.round(116 + 3 * t)}, ${Math.round(139 - 133 * t)}, ${alpha})`;
  } else {
    const t = (r - 0.4) / 0.6;
    const alpha = 0.6 + 0.38 * t;
    return `rgba(${Math.round(217 + 3 * t)}, ${Math.round(119 - 81 * t)}, ${Math.round(6 + 32 * t)}, ${alpha})`;
  }
}
```

### 2.4 Mouse Event Handling & Hit Detection
- **Coordinate Conversion:**
  ```javascript
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  ```
- **Node Hit Testing:**
  Distance formula: `Math.hypot(n.x - mouseX, n.y - mouseY) <= (n.kind === 'hub' ? 14 : 10)`.
- **Edge Hit Testing (Point-to-Segment Projection):**
  ```javascript
  function pointToSegmentDistance(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(px - x1, py - y1);
    const u = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / lenSq));
    return Math.hypot(px - (x1 + u * dx), py - (y1 + u * dy));
  }
  ```
  Edge is hit if `pointToSegmentDistance(...) <= 7` pixels.
- **Cursor Feedback:** `canvas.style.cursor = hit ? "pointer" : "default"`.

### 2.5 Tooltip Rendering (HTML Overlay)
An HTML overlay layer (`pointer-events-none absolute z-30`) over the canvas provides crisp typography without canvas text-measuring friction:
- **Node Tooltip:**
  - VPA address in monospace
  - Node role badge:
    - `hub`: `Collector Hub (Mule)` (crimson badge)
    - `victim`: `Victim / Source` (green badge)
    - `hop`: `Layering Hop` (amber badge)
    - `cashout`: `Cash-Out Point` (dark navy badge)
  - Action hint: *"Click to view case details →"*
- **Edge Tooltip:**
  - Amount formatted via `formatINR(edge.amount)` in large bold font
  - Flow: `${shortVpa(edge.a)} → ${shortVpa(edge.b)}`
  - Risk Score badge: `Risk: ${edge.riskScore}`

### 2.6 Click-to-Case Integration
- Prop `onSelectCase` is passed from `App.jsx` to `NetworkConstellation`:
  `<NetworkConstellation cases={cases} onSelectCase={openCase} />`
- On canvas click:
  - If a node is clicked and has an associated case ID: `onSelectCase(node.caseData || findCase(node.caseId))`.
  - Opens `CaseDrawer` seamlessly with identical case details, SAR markdown, token economy, and feedback buttons.

---

## 3. Requirement R4: Verdict History Line/Area Chart

### 3.1 Dependencies & Placement
- **Dependency:** `recharts` is already installed (`"recharts": "2.15.4"` in `package.json`).
- **Placement:** In `frontend/src/App.jsx`, directly beneath `<KpiStrip stats={stats} />` and above `<ControlBar />`.

### 3.2 Component Architecture (`VerdictHistoryChart.jsx`)
- **Chart Type:** Recharts `AreaChart` with gradient fill areas (stacked or overlapping with subtle transparency), providing high visual quality.
- **Series:**
  1. `ALLOW` / `Allowed`: Stroke `#0f7a3d`, fill `rgba(15,122,61,0.18)`
  2. `HOLD` / `Held`: Stroke `#a8660a`, fill `rgba(168,102,10,0.18)`
  3. `BLOCK` / `Blocked`: Stroke `#b3261e`, fill `rgba(179,38,30,0.22)`
- **Axes & Grid:**
  - `XAxis dataKey="time"`: Formatted time string (e.g. `18:45:10`), font-mono text-[11px].
  - `YAxis`: Formatted integer counts with `allowDecimals={false}`.
  - `CartesianGrid`: `strokeDasharray="3 3"` with hairline color `#e1e6ee`.
- **Custom Tooltip:**
  - Displays timestamp, total transactions processed at that point, and individual counts for Allow / Hold / Block.
- **Controls/Header:**
  - Panel title: *"Verdict Velocity & History"*
  - Live pulse indicator: `● Live Session Stream`

### 3.3 State Management & History Ingestion in `App.jsx`
```javascript
const [verdictHistory, setVerdictHistory] = useState([
  {
    time: new Date().toLocaleTimeString("en-IN", { hour12: false }),
    timestamp: Date.now(),
    allowed: 0,
    held: 0,
    blocked: 0,
    evaluated: 0,
  }
]);

// Append function with sliding buffer (max 40 data points)
const appendVerdictHistory = useCallback((currentStats) => {
  const newPoint = {
    time: new Date().toLocaleTimeString("en-IN", { hour12: false }),
    timestamp: Date.now(),
    allowed: currentStats.allowed,
    held: currentStats.held,
    blocked: currentStats.blocked,
    evaluated: currentStats.evaluated,
  };
  setVerdictHistory(prev => {
    const updated = [...prev, newPoint];
    return updated.slice(-40); // Maintain last 40 time slices
  });
}, []);
```
- **Trigger Points:**
  1. Initial demo simulation completion.
  2. Manual simulation button click in `ControlBar`.
  3. WebSocket message arrival (`new_case` / `stats_update`).

---

## 4. Requirement R2: WebSocket Push & Frontend Integration

### 4.1 WebSocket Connection Strategy
- The frontend connects to `/ws/feed` (proxied by Vite to `ws://localhost:8000/ws/feed` in dev mode, or native origin in production).
- Reconnect loop with 3s backoff on disconnect.
- On message received:
  1. New case prepended to `cases` state.
  2. Live stats incremented without full page reload.
  3. `verdictHistory` appends a new data point.
  4. KPI strip counters update with smooth count-up animation (`useCountUp`).

---

## 5. Build & Environment Verification

| Check | Result | Details |
|---|---|---|
| Node.js / NPM availability | ✅ Verified | Portable Node v20.18.1 located at `C:\Users\ajha1\AppData\Local\Temp\node-portable\node-v20.18.1-win-x64` |
| `vite build` | ✅ Succeeded | Clean build in 12.45s (`dist/index.html`, `dist/assets/index-*.js`, `dist/assets/index-*.css`) |
| Recharts version | ✅ 2.15.4 | Compatible with React 18.3.1 |
| Framer Motion version | ✅ 11.11.17 | For modal animations and drawer transitions |
| Tailwind CSS | ✅ 3.4.19 | Color tokens (`verdict-allow`, `verdict-hold`, `verdict-block`, `ink-900`) fully available |

---

## 6. Implementation Action Plan for Implementers

1. **Step 1: Create `frontend/src/components/VerdictHistoryChart.jsx`**
   - Implement Recharts `AreaChart` with 3 series, gradient fills, formatted tooltips, and responsive layout.
2. **Step 2: Update `frontend/src/components/NetworkConstellation.jsx`**
   - Add mouse event listeners (`onMouseMove`, `onMouseLeave`, `onClick`).
   - Implement node and edge hit testing logic.
   - Implement continuous edge gradient calculation `getEdgeStroke`.
   - Add HTML tooltip overlay for node (VPA + role badge) and edge (INR amount + risk score).
   - Wire `onSelectCase` click callback.
3. **Step 3: Update `frontend/src/App.jsx`**
   - Add `verdictHistory` state and `appendVerdictHistory` handler.
   - Embed `<VerdictHistoryChart history={verdictHistory} />` below `<KpiStrip stats={stats} />`.
   - Pass `onSelectCase={openCase}` to `<NetworkConstellation />`.
   - Setup WebSocket subscriber to `/ws/feed` for real-time case updates and verdict history appending.
4. **Step 4: Verify Frontend Build**
   - Run `npm run build` using node v20.18.1.

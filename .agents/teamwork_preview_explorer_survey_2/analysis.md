# Frontend Architecture, Fraud Playback Timeline & Honeypot KPI Survey Report

**Explorer**: Explorer 2 (Frontend Architecture & Timeline / KPI)  
**Date**: 2026-08-31  
**Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2`  
**Targets Investigated**:
- `frontend/src/components/NetworkConstellation.jsx`
- `frontend/src/components/CaseDrawer.jsx`
- `frontend/src/components/KpiStrip.jsx`
- `frontend/src/pages/OverviewPage.jsx`
- `frontend/src/pages/InvestigationsPage.jsx`
- `frontend/src/context/AppStateContext.jsx`
- `frontend/src/services/api.js`
- `frontend/package.json` & build toolchain

---

## 1. Executive Summary

This investigation analyzed the frontend architecture of **SAMPATI V2** to design and blueprint the implementation of:
1. **R1. Fraud Playback Timeline**: Interactive range slider and Play/Pause/Reset playback controls beneath the `NetworkConstellation` canvas. This enables step-by-step chronological animation of mule-ring transactions (fan-in $\to$ layering hops $\to$ cash-out $\to$ trigger interception) directly on the canvas, with full per-case playback support in `CaseDrawer.jsx`.
2. **R3. Honeypot Hits (24h) KPI Counter**: Integration of a real-time "Honeypot Hits (24h)" metric tile into `KpiStrip.jsx` on the `OverviewPage.jsx`, wired to `AppStateContext.jsx` and the backend `/stats` & WebSocket streaming feeds.
3. **Build & Contract Verification**: Frontend build verification with Vite/Bun and test coverage with `tests/frontend_contracts_test.py` (13/13 passed, 0 regressions).

---

## 2. Deep Dive: Current Graph & Visualization System

### 2.1 `NetworkConstellation.jsx` Architecture
- **Rendering Engine**: HTML5 2D Canvas with HiDPR auto-scaling (`ctx.setTransform(dpr, 0, 0, dpr, 0, 0)`).
- **Physics Simulation Engine**: RequestAnimationFrame (RAF) tick updating node velocities based on:
  1. Center gravity: `(width / 2 - n.x) * 0.0006`
  2. Coulomb-like node-node repulsion: `force = 950 / distSq`
  3. Hooke's law spring attraction along edges: `distTarget = 95`, `k = 0.006`
  4. Friction damping: `vx *= 0.88, vy *= 0.88`
- **Visual Styles & Roles**:
  - **Collector Hub** (`#b3261e` crimson, pulsed radial glow `rgba(179,38,30,0.38)`)
  - **Victim** (`#0f7a3d` emerald)
  - **Layering Hop** (`#a8660a` amber)
  - **Cash-Out** (`#0b1f3a` dark indigo)
  - **Edges**: Dashed stroke with moving phase offset `ctx.lineDashOffset = -t * 26`, colored continuously by risk score via `getEdgeStroke(riskScore)`.
- **Hit Detection & Interaction**:
  - Node hit detection: Euclidean distance $\le 11$px (14px for hubs).
  - Edge hit detection: `pointToSegmentDistance(px, py, x1, y1, x2, y2) <= 6.5`px.
  - Interactive tooltip floating overlay and click-to-open case dispatch (`onSelectCase`).

### 2.2 Current Limitations vs Requirements
1. `NetworkConstellation` renders all nodes and edges simultaneously upon data load. There is currently no concept of time, step ordering, or playback state.
2. `CaseDrawer.jsx` currently displays text metadata, token economy stats, and SAR markdown, but lacks an embedded topology canvas.
3. Node and edge lists in `NetworkConstellation` do not extract or retain chronological timestamps for each transaction hop.

---

## 3. Concrete Design: R1. Fraud Playback Timeline

### 3.1 Chronological Transaction Extraction & Sorting
For any case or topology dataset, we extract an ordered array of transaction edges:
- **Sources**:
  1. `caseData.topology.transactions` / `caseData.transactions` (if explicit list exists).
  2. `caseData.topology.fan_in` (Victims $\to$ Hub).
  3. `caseData.topology.hops` (Hub $\to$ Layering Hops / intermediate hops).
  4. `caseData.topology.fan_out` (Hub / Hops $\to$ Cash-Out nodes).
  5. `caseData.trigger_txn` (Final triggering transaction).
- **Timestamp Synthesis & Normalization**:
  - If timestamps exist (`t.timestamp`), parse epoch ms: `new Date(t.timestamp).getTime()`.
  - If missing/synthetic, assign deterministic sequential offsets relative to `case.created_at` or trigger timestamp:
    - Step 1..$K_{fan\_in}$: $t_0 - 180s + (i \times 30s)$
    - Step $K+1..K+M_{hops}$: $t_0 - 90s + (j \times 30s)$
    - Step $K+M+1..$: $t_0 - 30s + (l \times 15s)$
    - Trigger Txn: $t_0$
  - Sort strictly by `timestamp ASC`.

### 3.2 Playback State Machine
```typescript
interface PlaybackState {
  currentStep: number;     // 0 (t=0, empty) to N (all edges visible)
  totalSteps: number;      // N (total chronological edges)
  isPlaying: boolean;      // True if auto-advancing
  playbackSpeed: number;   // 1x (1000ms/step), 2x (500ms), 0.5x (2000ms)
  activeEdge: Edge | null; // Most recently animated edge
}
```

### 3.3 Visibility & Incremental Reveal Logic
- **At $t=0$ (`currentStep === 0`)**:
  - `visibleEdges = []`
  - `visibleNodeIds = new Set()`
  - **Canvas is completely empty of nodes and edges** ("Reset returns to t=0 with no nodes visible").
  - An informational canvas overlay states: *"t=0: Initial state. Press Play (▶) or drag slider to reveal mule ring assembling in real time."*
- **At step $k$ (`1 <= currentStep <= N`)**:
  - `visibleEdges = sortedEdges.slice(0, k)`
  - `visibleNodeIds = new Set(visibleEdges.flatMap(e => [e.a, e.b]))`
  - Only `visibleEdges` are drawn by the canvas stroke loop.
  - Only `visibleNodeIds` are drawn by the node circle & glow loop.
  - Physics forces only execute on nodes present in `visibleNodeIds`.
  - Newly appearing nodes at step $k$ spawn near their source node with an entry ripple/shockwave effect.
  - Newly animated edge $E_{k-1}$ receives a luminous highlight stroke (`#fbbf24` gold) before settling into its continuous risk gradient.
- **At step $N$ (`currentStep === N`)**:
  - All topology edges and nodes are fully visible.
  - `isPlaying` automatically sets to `false`.

### 3.4 Playback Controls Strip (Beneath Canvas)
Placed directly beneath the canvas container:
1. **Play/Pause Button**:
   - When paused at $k < N$: Starts interval timer advancing `currentStep` by +1 every `1000 / playbackSpeed` ms.
   - When at $k === N$: Resets to step 1 and begins playback.
   - When playing: Pauses immediately, freezing nodes and edges in their current positions.
2. **Reset Button (`↺`)**:
   - Stops playback timer.
   - Sets `currentStep = 0`.
   - Clears all visible nodes and edges from the canvas.
3. **Timeline Range Slider (`<input type="range">`)**:
   - `min="0"`, `max={totalSteps}`, `value={currentStep}`, `step="1"`.
   - Allows instant random-access scrubbing to any chronological milestone.
4. **Playback Speed Selector**:
   - Buttons for `0.5x`, `1x`, `2x` speed multipliers.
5. **Step Telemetry Banner**:
   - Shows: `Step {currentStep}/{totalSteps}`
   - When $k > 0$: Displays active transaction details:
     `[Scenario Badge] [Amount in INR] [Payer VPA → Payee VPA] [Timestamp]`

### 3.5 Integration in `CaseDrawer.jsx`
In `CaseDrawer.jsx`, when `caseData` is active:
- Add a top visualization card above trigger transaction:
  ```jsx
  <div className="panel overflow-hidden">
    <div className="panel-header flex items-center justify-between">
      <div className="panel-title">
        <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
          Mule Ring Playback
        </div>
        <div className="font-serif font-bold text-ink-900">
          Chronological Topology Flow
        </div>
      </div>
      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
        Cinematic Playback
      </span>
    </div>
    <div className="h-64 p-1 bg-[#f8f9fc]">
      <NetworkConstellation caseData={caseData} />
    </div>
  </div>
  ```

---

## 4. Concrete Design: R3. Honeypot KPI Counter

### 4.1 `KpiStrip.jsx` Enhancement
In `frontend/src/components/KpiStrip.jsx`:
- Expand `TILES` array to include the Honeypot KPI tile:
  ```javascript
  const TILES = [
    { key: "evaluated", label: "Evaluated", icon: "⌁", tone: "text-ink-800 bg-ink-900/5" },
    { key: "allowed", label: "Allowed", icon: "✓", tone: "text-verdict-allow bg-verdict-allowBg" },
    { key: "held", label: "Held", icon: "⚑", tone: "text-verdict-hold bg-verdict-holdBg" },
    { key: "blocked", label: "Blocked", icon: "✕", tone: "text-verdict-block bg-verdict-blockBg" },
    { key: "honeypot_hits", label: "Honeypot Hits (24h)", icon: "🍯", tone: "text-amber-800 bg-amber-50 border-amber-200" },
    { key: "rings", label: "Mule rings", icon: "◈", tone: "text-purple-700 bg-purple-50" },
    { key: "dpip", label: "Sent to DPIP", icon: "⇄", tone: "text-ink-800 bg-ink-900/5" },
  ];
  ```
- Update Grid class in `KpiStrip.jsx`:
  `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3`
- Tile Value Accessor:
  `stats.honeypot_hits ?? stats.honeypot_hits_24h ?? stats.honeypots?.total_hits ?? 0`
- Pulse effect:
  `const pulse = (tile.key === "blocked" || tile.key === "honeypot_hits") && value > 0;`

### 4.2 State Management in `AppStateContext.jsx`
- Initial `stats` state:
  ```javascript
  const [stats, setStats] = useState({
    evaluated: 0,
    allowed: 0,
    held: 0,
    blocked: 0,
    honeypot_hits: 0,
    rings: 0,
    dpip: 0,
  });
  ```
- `refreshStats()`:
  Extracts `s.honeypot_hits_24h ?? s.honeypot_hits ?? s.honeypots?.total_hits ?? prev.honeypot_hits ?? 0`.
- WebSocket handlers:
  Update `honeypot_hits` upon `stats_update` and `new_case` events.

---

## 5. Build, Dependencies & Compatibility Verification

| Component / Tool | Version / Path | Status | Verification Detail |
|---|---|---|---|
| **Node/Bun Toolchain** | Bun 1.3.14 | PASS | `bun run build` transforms 1,382 modules and completes in ~10.5s |
| **Vite** | 5.4.21 | PASS | Generates production bundles with 0 syntax or Rollup errors |
| **React / DOM** | 18.3.1 | PASS | Strict mode compatible, hook exhaustive-deps compliant |
| **React Router DOM** | 6.28.0 | PASS | Client-side routing with URL synchronization |
| **Framer Motion** | 11.11.17 | PASS | Smooth spring transitions for drawer & KPI count-up |
| **Recharts** | 2.15.4 | PASS | Responsive container charts with time-series data |
| **Tailwind CSS** | 3.4.19 | PASS | Custom theme palettes (`saffron`, `ink`, `verdict`) compile cleanly |
| **Test Suite** | `pytest tests/frontend_contracts_test.py` | PASS | 13/13 unit and contract tests passed |

---

## 6. Implementation Blueprint & Proposed Code Changes

### 6.1 `NetworkConstellation.jsx` Proposed Changes
- Support both `caseData` prop (single case playback) and `cases` prop (multi-case constellation).
- Add timeline state: `currentStep`, `isPlaying`, `playbackSpeed`, `timelineEdges`.
- Build timeline controls container directly beneath the canvas with:
  - Play / Pause button with animated icons
  - Reset button returning to $t=0$
  - Range slider with custom track styling
  - Step counter & active transaction information chip
  - Speed selector pills (0.5x, 1x, 2x)
- Update canvas render loop to filter `nodes` and `edges` by `visibleNodeIds` and `visibleEdges`.

### 6.2 `CaseDrawer.jsx` Proposed Changes
- Import `NetworkConstellation` from `./NetworkConstellation`.
- Place `<NetworkConstellation caseData={caseData} />` inside a sleek panel directly in the case drawer.

### 6.3 `KpiStrip.jsx` Proposed Changes
- Add `honeypot_hits` tile with label `"Honeypot Hits (24h)"`, icon `"🍯"`, amber styling, count-up animation, and responsive 7-column grid layout.

### 6.4 `AppStateContext.jsx` Proposed Changes
- Initialize `honeypot_hits: 0` in `stats`.
- Ingest `honeypot_hits` / `honeypot_hits_24h` in `refreshStats` and WebSocket event dispatchers.

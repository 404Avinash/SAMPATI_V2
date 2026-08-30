# Handoff Report — Explorer 2 (Frontend Architecture & Timeline / KPI)

## 1. Observation

1. **Frontend File Paths and Structure**:
   - `frontend/src/components/NetworkConstellation.jsx` (552 lines): Implements HTML5 2D Canvas force-directed graph with center gravity ($0.0006$), node repulsion ($950/dist^2$), and spring attraction ($target=95, k=0.006$). Renders static snapshot of all nodes and edges with risk-gradient stroke coloring and hit detection (Euclidean distance $\le 11/14$px for nodes, point-to-segment $\le 6.5$px for edges). It currently has no time state, step state, or playback controls.
   - `frontend/src/components/CaseDrawer.jsx` (91 lines): Slide-out drawer displaying case ID, token economy statistics, trigger transaction, SAR narrative in Markdown, and feedback buttons. It does not currently contain a graph or topology visualization component.
   - `frontend/src/components/KpiStrip.jsx` (43 lines): Renders a 6-tile grid (`evaluated`, `allowed`, `held`, `blocked`, `rings`, `dpip`) using `useCountUp` and Framer Motion with `grid grid-cols-2 md:grid-cols-6 gap-3`. It does not yet include a Honeypot KPI counter.
   - `frontend/src/pages/OverviewPage.jsx` (98 lines): Renders `<KpiStrip stats={stats} />`, `<VerdictHistoryChart history={verdictHistory} />`, `<ControlBar />`, `<NetworkConstellation cases={cases} onSelectCase={openCase} />`, `<LiveFeed />`, and `<VerdictDonut />`.
   - `frontend/src/context/AppStateContext.jsx` (314 lines): Manages `stats`, `cases`, `verdictHistory`, WebSocket updates, simulation, and case review workflows.
   - `frontend/src/services/api.js` (186 lines): REST client covering `/upi/check`, `/upi/simulate`, `/upi/cases`, `/upi/stats`, `/stats/analytics`, and `/health/detailed`.

2. **Frontend Build & Dependency Verification**:
   - `frontend/package.json`: Contains `"react": "18.3.1"`, `"react-dom": "18.3.1"`, `"react-router-dom": "^6.28.0"`, `"framer-motion": "^11.11.17"`, `"recharts": "2.15.4"`, `"tailwindcss": "3.4.19"`, `"vite": "5.4.21"`.
   - Executed `bun run build` in `frontend/`: Successfully transformed 1,382 modules and emitted production bundles (`dist/assets/index-*.js` and `dist/assets/index-*.css`) in 10.57s with 0 errors.
   - Executed `.venv/bin/pytest tests/frontend_contracts_test.py -v`: All 13 unit and contract tests passed in 0.46s with 0 errors.

3. **Authoritative Requirements from ORIGINAL_REQUEST.md**:
   - **R1. Fraud Playback Timeline (Frontend)**:
     - Add Timeline Slider with Play/Pause/Reset controls beneath `NetworkConstellation` canvas.
     - Pressing Play animates edges onto canvas one-by-one in timestamp order.
     - Pause freezes animation.
     - Reset returns to $t=0$ with no nodes visible.
     - Must be usable per-case when case topology is loaded in `CaseDrawer`.
   - **R3. Honeypot Hits (24h) KPI Counter**:
     - Surface "Honeypot Hits (24h)" KPI counter on Overview dashboard page.

---

## 2. Logic Chain

1. **R1 Playback Architecture**:
   - From Observation 1, `NetworkConstellation.jsx` currently draws all edges and nodes simultaneously without step filtering.
   - To satisfy R1, `NetworkConstellation.jsx` must accept either `cases` (multi-case array) or `caseData` (single case object) and extract all chronological edges from `topology` (`fan_in`, `hops`, `fan_out`, `trigger_txn`, `transactions`).
   - Edges must be sorted chronologically by timestamp (`timestamp ASC`). If explicit timestamps are absent, synthetic chronological offsets ($t_0 - 180s \to t_0$) must be assigned.
   - A step-based state machine (`currentStep`: $0 \dots N$) must control visibility:
     - When `currentStep === 0` ($t=0$), `visibleEdges = []` and `visibleNodeIds = new Set()`, satisfying the requirement that "Reset returns to t=0 with no nodes visible".
     - When `currentStep === k`, `visibleEdges = sortedEdges.slice(0, k)` and `visibleNodeIds = Set(visibleEdges.flatMap(e => [e.a, e.b]))`.
     - When `isPlaying` is true, an interval timer increments `currentStep` from $0 \to N$, animating edges onto the canvas one-by-one.
     - Pause stops the timer, freezing the canvas elements in place.
   - To make this usable per-case in `CaseDrawer.jsx`, `<NetworkConstellation caseData={caseData} />` must be embedded in `CaseDrawer.jsx`.

2. **R3 Honeypot KPI Integration**:
   - From Observation 1, `KpiStrip.jsx` renders `TILES` across a CSS grid.
   - Adding a 7th tile `{ key: "honeypot_hits", label: "Honeypot Hits (24h)", icon: "🍯", tone: "text-amber-800 bg-amber-50 border-amber-200" }` and updating the grid to `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3` cleanly displays the counter.
   - Updating `AppStateContext.jsx` to initialize `honeypot_hits: 0` in `stats` and ingest `s.honeypot_hits_24h ?? s.honeypot_hits ?? s.honeypots?.total_hits ?? 0` ensures real-time WebSocket and polling updates reflect on the Overview page.

3. **Build & Compatibility**:
   - From Observation 2, `bun run build` and `pytest tests/frontend_contracts_test.py` both pass without errors. The existing dependencies (React 18, React Router 6, Framer Motion 11, Tailwind 3.4) fully support this implementation without adding any third-party packages.

---

## 3. Caveats

1. **Topology Timestamps**: For legacy or synthetically generated cases where individual hop transactions lack explicit ISO timestamps, the sorting algorithm will synthesize monotonically increasing timestamps based on flow scenario (`fan_in` $\to$ `hops` $\to$ `fan_out` $\to$ `trigger_txn`) relative to `created_at`.
2. **Global Overview Mode vs Case Drawer Mode**: In the Overview page's multi-case constellation, if no single case is selected, the timeline controls can either default to playing the most recent high-risk case or scrubbing all active rings collectively. When a single case is selected or when loaded inside `CaseDrawer`, it executes per-case playback.

---

## 4. Conclusion

The frontend codebase is well-structured, modular, and fully prepared for R1 and R3 implementation. No additional npm packages are required. The proposed modifications cleanly decouple timeline playback logic, canvas rendering, and KPI telemetry while adhering to all design standards and passing all contract tests.

---

## 5. Verification Method

To verify the implementation once coded:
1. **Build Verification**:
   ```bash
   cd /home/avi/Downloads/Sampati_v2/frontend && bun run build
   ```
   *Expected result*: Build completes cleanly with 0 errors and exits with status 0.

2. **Contract & Regression Test Suite**:
   ```bash
   cd /home/avi/Downloads/Sampati_v2 && .venv/bin/pytest tests/frontend_contracts_test.py -v
   ```
   *Expected result*: 13/13 tests pass.

3. **Full System Test Suite**:
   ```bash
   cd /home/avi/Downloads/Sampati_v2 && .venv/bin/pytest tests/ -v
   ```
   *Expected result*: Full 492+ test suite passes without regressions.

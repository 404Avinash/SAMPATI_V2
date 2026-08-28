# Handoff Report: Frontend Visuals Survey (R3 & R4)

## 1. Observation
- **Constellation Visualizer Location:** `frontend/src/components/NetworkConstellation.jsx` (249 lines).
- **Current Visualizer Mechanics:** HTML5 Canvas 2D running in a `requestAnimationFrame` loop with center gravity, node repulsion, and edge spring forces.
- **Visualizer Gaps:** Canvas currently lacks mousemove, mouseleave, and click event listeners. Node data model lacks `caseId` / `caseData` bindings. Edge model only contains `{ a, b, flagged }` without `amount`, `riskScore`, or continuous color gradients.
- **Dependencies & Libraries:** `frontend/package.json` contains `"recharts": "2.15.4"`, `"react": "18.3.1"`, `"framer-motion": "^11.11.17"`, `"tailwindcss": "3.4.19"`, `"vite": "5.4.21"`.
- **Layout:** `KpiStrip.jsx` is positioned at `frontend/src/App.jsx:138`. The new `VerdictHistoryChart.jsx` will be mounted directly below `KpiStrip`.
- **Case Drawer:** `frontend/src/components/CaseDrawer.jsx` is opened by `openCase` in `App.jsx:113` via `setSelectedCase(caseData)`.
- **Build Pipeline:** `vite build` executes and completes in ~12.45 seconds using portable Node v20.18.1 at `C:\Users\ajha1\AppData\Local\Temp\node-portable\node-v20.18.1-win-x64\node.exe`.

## 2. Logic Chain
1. To satisfy **R3 (Interactive Constellation Visualizer)**:
   - When building the graph model in `NetworkConstellation.jsx`, attach `caseId` and `caseData` to nodes, and attach `riskScore`, `amount` (INR), and `caseId` to edges.
   - Attach `onMouseMove`, `onMouseLeave`, and `onClick` handlers to the canvas element.
   - In `onMouseMove`, perform Euclidean distance hit testing on nodes (`dist <= 12px`) and point-to-line-segment distance projection on edges (`dist <= 6px`).
   - Render a high-contrast HTML overlay tooltip over the canvas for hovered nodes (displaying VPA, role badge, click-to-case prompt) and hovered edges (displaying ₹ INR transaction amount and risk score).
   - In `onClick`, if a node with `caseData`/`caseId` is clicked, invoke `onSelectCase(caseData)` passed from `App.jsx`, opening `CaseDrawer`.
   - In the canvas animation frame, calculate edge stroke color dynamically using continuous risk-score interpolation (`getEdgeStroke(riskScore)`: slate $\to$ amber $\to$ crimson).
2. To satisfy **R4 (Verdict History Line Chart)**:
   - Create `VerdictHistoryChart.jsx` using Recharts `AreaChart` with three series: `ALLOW` (`#0f7a3d`), `HOLD` (`#a8660a`), and `BLOCK` (`#b3261e`), along with time XAxis, count YAxis, CartesianGrid, Legend, and custom Tooltip.
   - Maintain `verdictHistory` state buffer (last ~40 time points) in `App.jsx`.
   - Ingest new points on simulation runs, federation updates, and real-time WebSocket `/ws/feed` events.
   - Place `<VerdictHistoryChart history={verdictHistory} />` directly below `<KpiStrip stats={stats} />` in `App.jsx`.

## 3. Caveats
- Multiple cases in a dense dataset may share identical hub or hop VPAs. The node click handler should prioritize the primary or most recent case associated with the node.
- WebSocket URL should handle both development Vite proxy (`/ws/feed`) and production paths (`ws://${window.location.host}/ws/feed`).

## 4. Conclusion
The frontend codebase is well-structured and ready for implementing Requirements R3 and R4. All necessary libraries (`recharts`, `framer-motion`, `tailwindcss`) are already in `package.json`, `vite build` builds with zero errors, and detailed designs have been documented in `survey_frontend_visuals.md`.

## 5. Verification Method
1. Build verification:
   `$env:PATH = "C:\Users\ajha1\AppData\Local\Temp\node-portable\node-v20.18.1-win-x64;" + $env:PATH; npm run build` in `frontend/`.
2. Inspect survey report:
   `c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_3\survey_frontend_visuals.md`.

# Worker M1 Task Assignment: UI Bugs & Geographic India Map

## Context
Authoritative Request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (Section `## 2026-09-04T12:04:16Z`)
Project Scope: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_14/PROJECT.md`
Working Directory: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1`
Skills: `/home/avi/Downloads/Sampati_v2/.agents/skills/safe-push/SKILL.md`

Detailed Survey Reports to Follow:
- Explorer 1 (R1 India Map & R2 Threat Intel Crash): `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_1/handoff.md`
- Explorer 2 (R3 Constellation Canvas Whitewash): `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md`
- Explorer 3 (R4 Verdict Velocity Rolling Rate): `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3/handoff.md`

## File Ownership Boundaries
You exclusively own and can modify or create:
1. `frontend/src/components/overview/GeoMuleMap.jsx` (New)
2. `frontend/src/components/common/ErrorBoundary.jsx` (New)
3. `frontend/src/components/VerdictVelocityChart.jsx` (New)
4. `frontend/src/pages/ThreatIntelPage.jsx`
5. `frontend/src/components/NetworkConstellation.jsx`
6. `frontend/src/context/AppStateContext.jsx`
7. `frontend/src/components/VerdictHistoryChart.jsx`
8. `frontend/src/pages/OverviewPage.jsx`

Do NOT touch files outside your ownership boundaries.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Detailed Tasks to Implement

### 1. Requirement R2: Fix Threat Intel Page Crash
- In `frontend/src/pages/ThreatIntelPage.jsx`:
  - Add `getCampaignLabel(campaign)` helper to safely extract string label from either a string or an object `{ campaign_id, name, campaign_name }`.
  - Fix lines 921-925 where `{signal.matched_campaign}` is rendered as a child (causes `Objects are not valid as a React child` crash).
  - Fix line 1019 where `{selectedSignal.matched_campaign}` is rendered.
  - Safe-guard identifier values with fallbacks (`phone`, `upi_id`, `url`, `tags`).
- In `frontend/src/components/common/ErrorBoundary.jsx`:
  - Create a React ErrorBoundary class component that catches any rendering error and displays a clean, graceful fallback alert without crashing the app.
  - Wrap `ThreatIntelPage` with this `ErrorBoundary`.

### 2. Requirement R1: Geographic India Map Visualization
- Create `frontend/src/components/overview/GeoMuleMap.jsx`:
  - Render a stylized vector map of India with cybersecurity / fintech aesthetic (darker or clean light grid, subtle radar coordinates).
  - Major tech/financial hubs calibrated: Mumbai, Bangalore/Bengaluru, Delhi NCR, Jamtara, Mewat, Kolkata, Hyderabad, Ahmedabad, Chennai.
  - Active mule corridors: Draw animated quadratic bezier arcs between hubs (e.g. Jamtara -> Mumbai, Jamtara -> Bengaluru, Mewat -> Delhi, Ahmedabad -> Mumbai, etc.) with animated stroke dash or traveling particles.
  - Pulsing radar hotspots for fraud epicenters (Jamtara, Mewat).
  - Telemetry summary cards: Active Corridors, Monitored Hubs, Intercepted Volume.
  - Interactive hover tooltips for hubs and corridors.
- In `frontend/src/pages/OverviewPage.jsx`:
  - Add a view toggle button in the Topology Visualizer panel header: `[ ☍ Constellation Graph | 🗺️ India Mule Corridors ]`.
  - Render `NetworkConstellation` when Constellation view is selected, and `GeoMuleMap` when India Mule Corridors view is selected.

### 3. Requirement R3: Whitewash Constellation Graph Background
- In `frontend/src/components/NetworkConstellation.jsx`:
  - Change root container from `bg-[#0f172a]` to `bg-white border border-hairline rounded-lg`.
  - In canvas render loop, explicitly fill background with white: `ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, width, height);` and draw subtle dot-grid (`rgba(226, 232, 240, 0.85)` at 28px).
  - Change active node / active edge stroke from invisible `#fbbf24` (1.6:1 contrast) to SAMPATI Saffron `#c8641e` (4.6:1 contrast).
  - Change default node border stroke from `#ffffff` to subtle outer shadow/stroke so white borders don't vanish on white canvas.
  - Change halo outer gradient stop from `rgba(0,0,0,0)` to `rgba(R, G, B, 0)` to avoid dark fringing artifacts on white.
  - Improve edge risk gradient contrast using Teal-600 (`#0d9488`), Amber-700 (`#b45309`), Red-600 (`#dc2626`).
  - Restyle HUD Legend, Zoom HUD, Hover Tooltip, and Timeline bottom bar to light theme (`bg-white/95`, `border-hairline`, `text-ink-900`, `bg-surface-muted/95`).

### 4. Requirement R4: Fix Verdict Velocity Graph to Show Rolling Rate
- In `frontend/src/context/AppStateContext.jsx`:
  - Implement a 1-second sliding window bucket aggregator (`currentBucketRef`).
  - Route individual evaluations (`UPI_EVALUATED` WebSocket events) to increment bucket counts for ALLOW, HOLD, BLOCK.
  - Handle simulation batch deltas and stats updates properly.
  - Every 1,000ms (`setInterval`), append `{ time, timestamp, ALLOW: bucket.ALLOW, HOLD: bucket.HOLD, BLOCK: bucket.BLOCK, total: bucket.total }` to `verdictHistory`, reset bucket to 0, and retain last 30-40 seconds.
- In `frontend/src/components/VerdictHistoryChart.jsx`:
  - Display current rolling rate in header badge (`{currentTps.toFixed(0)} tx/s`).
  - Set YAxis unit to `/s` or `tx/s`.
  - Update tooltip to show rate per second.
  - Add fallback rate computation if external input is cumulative.
- Create `frontend/src/components/VerdictVelocityChart.jsx`:
  - Re-export `VerdictHistoryChart` as default and named exports.

## Verification Requirements
You MUST run and verify:
1. `./.venv/bin/pytest tests/ -v` -> 969 tests must pass with 0 failures.
2. `cd frontend && npm run lint` -> 0 ESLint warnings (`--max-warnings 0` rule enforced).
3. `cd frontend && npm run build` -> Clean build with 0 errors.

Report your exact verification outputs and file changes in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`.

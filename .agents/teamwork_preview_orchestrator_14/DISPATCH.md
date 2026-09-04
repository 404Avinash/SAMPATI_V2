# Dispatch Record

## 2026-09-04T12:06:24Z
You are the Project Orchestrator for SAMPATI V2.

Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_14
Original Request: /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md (under timestamp 2026-09-04T12:04:16Z)
Project Root: /home/avi/Downloads/Sampati_v2

Your mission is to decompose and orchestrate the resolution of 3 critical UI bugs and 1 visual demo feature:

## Requirements:
1. R1. Geographic India Map Visualization:
   - Add a new visualizer (e.g., GeoMuleMap.jsx) to the Overview or Threat Intel dashboard that renders a stylized map of India.
   - Visualize active mule rings geographically, drawing animated connection lines (arcs or vectors) between major Indian tech/financial hubs (e.g., Mumbai, Bangalore, Delhi, Jamtara, NCR).
   - Can use react-simple-maps, deck.gl, or a lightweight SVG map of India.
   - High professional fintech/cybersecurity aesthetic with live fraud topology data or realistic simulated geographic coordinates.
2. R2. Fix Threat Intel Page Crash (White Screen):
   - The /threat-intel route is currently crashing and rendering a blank white screen due to a React runtime error.
   - Diagnose and fix the crash in ThreatIntelPage.jsx so the page renders reliably, with proper loading states or fallback data.
3. R3. Whitewash the Constellation Graph Background:
   - NetworkConstellation canvas currently has a dark/slate background that clashes with the clean white aesthetic.
   - Change canvas background to white (or transparent if resting on a white container) and update node, edge, and label colors so they are clearly visible against a white background (e.g. darker colors for text/edges, maintain semantic red/yellow/green for nodes).
4. R4. Fix Verdict Velocity Graph to Show Rolling Rate, Not Cumulative:
   - "Verdict Velocity & History" chart currently plots a cumulative, monotonically increasing line.
   - Update charting logic (in VerdictVelocityChart.jsx or data aggregation) to calculate and display the rolling rate (transactions per second/minute) instead of cumulative totals, reflecting actual traffic bursts.

## Acceptance Criteria:
- Automated:
  - `./.venv/bin/pytest tests/ -v` passes with 0 failures (969 tests).
  - `cd frontend && npm run lint` passes with 0 ESLint warnings (`--max-warnings 0`).
  - `cd frontend && npm run build` completes with 0 errors.
- Quality:
  - Geographic map of India renders on dashboard showing animated connections between cities.
  - /threat-intel page loads reliably without React error boundary or blank screen.
  - NetworkConstellation component has white/light background with clear legible contrast for nodes, links, and text.
  - Verdict Velocity chart computes and plots a rolling rate over time rather than cumulative sums.

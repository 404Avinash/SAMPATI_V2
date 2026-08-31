## 2026-08-31T15:34:18Z
You are Explorer 2 for SAMPATI V2 Sprint 3.
Your task: Survey frontend NetworkConstellation (R3) and Investigations / CaseDrawer / ForensicImageViewer (R4, R1 frontend part).

Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2
Workspace root: /home/avi/Downloads/Sampati_v2
Read:
- /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md (Sprint 3 section)
- /home/avi/Downloads/Sampati_v2/frontend/src/components/NetworkConstellation.jsx
- /home/avi/Downloads/Sampati_v2/frontend/src/components/CaseDrawer.jsx
- /home/avi/Downloads/Sampati_v2/frontend/src/components/ForensicImageViewer.jsx
- /home/avi/Downloads/Sampati_v2/frontend/src/pages/InvestigationsPage.jsx
- /home/avi/Downloads/Sampati_v2/frontend/src/services/api.js (or relevant api client)

Investigate:
1. `NetworkConstellation.jsx`:
   - How canvas force graph and timeline are currently implemented.
   - What is needed for:
     a) Continuous spring-force physics simulation (smooth drift/settle even when paused).
     b) Node pulsing glow animations on canvas (BLOCK = red, HOLD = amber, ALLOW = neutral).
     c) Edge risk gradient (teal/amber/crimson) and animated particle flow dots along high-risk edges.
     d) Auto-play on load when cases exist.
     e) Mouse scroll-to-zoom and click-drag-to-pan.
     f) Node click opening CaseDrawer.
2. `InvestigationsPage.jsx` & `CaseDrawer.jsx` & `ForensicImageViewer.jsx`:
   - Making case table rows clickable to open drawer.
   - Status badge filtering (OPEN / ESCALATED / DISMISSED) without reload.
   - Animated DMV arc/dial gauge in CaseDrawer (green <40, amber 40-70, red >70).
   - Sorted horizontal bar chart with Recharts for rule breakdown.
   - ForensicImageViewer: direct static fallback `/static/upi_cases/{case_id}_ring.png` on 404, smooth fade-in, and in-browser SVG ring topology fallback from `case.topology`.
   - SAR export button: real PDF binary download and error toast if not PDF.

Write your findings to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md`.
Use `send_message` to report back to parent when complete with path to handoff.md.

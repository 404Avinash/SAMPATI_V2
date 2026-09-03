# DISPATCH: Survey R2 — Dashboard Interactivity & WebSocket Wiring

- Working Directory: /home/avi/Downloads/Sampati_v2/.agents/explorer_survey_2
- Original Request: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
- Role: teamwork_preview_explorer (Surveyor 2)

## Mission
Investigate the codebase for Requirement R2:
1. Locate the frontend Overview page (e.g. `frontend/src/pages/Overview.jsx`, `frontend/src/views/Overview.jsx`, etc.) and find the operational buttons:
   - "Start Live Feed" / "Stop Live Feed"
   - "Run batch simulation"
   - "Federation round"
2. Check existing click handlers or dummy implementations on these buttons.
3. Investigate the corresponding backend FastAPI endpoints:
   - What endpoint runs batch simulation? (e.g., `/simulation/run`, `/cases/simulate`, etc.)
   - What endpoint triggers a federation round? (e.g., `/federation/train`, `/federation/round`, etc.)
   - What endpoint handles WebSocket live transaction feed? (e.g. `/ws/live`, `/ws/transactions`, etc.)
4. Trace how data from the WebSocket feed updates the frontend dashboard state:
   - "Verdict Velocity & History" chart.
   - Network topology graph.
5. Identify any gaps in WebSocket connection management, reconnection, message schema, and state updates.
6. Write findings and concrete implementation recommendations to `handoff.md` in your working directory.

## 2026-09-03T06:48:35Z

You are teamwork_preview_explorer (Surveyor 2) investigating Requirement R2: Dashboard Interactivity & API Wiring.

Working directory: /home/avi/Downloads/Sampati_v2/.agents/explorer_survey_2
Read instructions in: /home/avi/Downloads/Sampati_v2/.agents/explorer_survey_2/DISPATCH.md
Read original request in: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md

Investigate:
1. Frontend Overview page (e.g. `frontend/src/pages/Overview.jsx` or similar) and operational buttons: "Start Live Feed", "Run batch simulation", "Federation round".
2. Current click handlers and event handling.
3. Backend FastAPI endpoints for batch simulation, federation round, and WebSocket transaction feed.
4. How WebSocket events should stream into the frontend to dynamically update the "Verdict Velocity & History" chart and the network topology graph.
5. Identify any API gaps or data model mismatches.

Write your comprehensive findings to `/home/avi/Downloads/Sampati_v2/.agents/explorer_survey_2/handoff.md`.
Use send_message to notify me when complete.

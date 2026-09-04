# Challenger 2 Task Assignment

## Mission: Adversarial Simulation & Boundary Stress Testing
Adversarially challenge the implementation across all 4 requirements.
Worker Handoff Report: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`
Original Request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (Section `## 2026-09-04T12:04:16Z`)
Project Scope: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_14/PROJECT.md`

## Objectives
1. Perform boundary & corner case verification:
   - High-load burst simulation: what happens if 500 transactions arrive in 100ms? Does `AppStateContext.jsx` drop points, crash, or properly compute TPS?
   - Idle decay: does `AppStateContext.jsx` accurately tick down to 0 after 2 seconds of silence?
   - Malformed threat signal payloads: test `ThreatIntelPage.jsx` logic with null `matched_campaign`, empty object `{}`, nested unexpected types.
   - Constellation whitewash: inspect canvas code paths (t=0, paused, dragging, zooming, active edge) to verify all elements remain crisp and visible against `#ffffff`.
   - India Geo Map: test `GeoMuleMap.jsx` rendering with negative/invalid data and ensure responsive scaling.
2. Run automated validation:
   - `./.venv/bin/pytest tests/ -v`
   - `cd frontend && npm run lint`
   - `cd frontend && npm run build`

Deliver your verdict (APPROVE or REQUEST_CHANGES) with empirical evidence in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_2/handoff.md` and communicate back using send_message.

## 2026-09-04T12:26:16Z
You are Challenger 2. Read your task description in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_2/DISPATCH.md, /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md, and /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md.
Stress test edge cases, high burst rates, empty payloads, and responsive scaling.
Verify:
- ./.venv/bin/pytest tests/ -v (969 tests)
- cd frontend && npm run lint (0 warnings)
- cd frontend && npm run build (0 errors)
Write your verdict (APPROVE or REQUEST_CHANGES) with empirical evidence in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_2/handoff.md and notify orchestrator via send_message.

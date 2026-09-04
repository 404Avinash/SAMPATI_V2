# Reviewer 2 Task Assignment

## Mission: Adversarial & Defensive Code Review of UI Bugs & India Geo Map
Perform an independent, adversarial code review of Worker M1's changes.
Worker Handoff Report: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`
Original Request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (Section `## 2026-09-04T12:04:16Z`)
Project Scope: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_14/PROJECT.md`

## Objectives
1. Actively look for edge cases, subtle bugs, performance regressions, memory leaks (e.g. uncleared `setInterval`, requestAnimationFrame leaks, unhandled nulls/undefineds).
2. Examine `NetworkConstellation.jsx`: Is the white background completely applied? Are all text elements readable? Does any dark `#0f172a` remain?
3. Examine `ThreatIntelPage.jsx`: Does `getCampaignLabel()` handle every possible input (null, undefined, string, object without name/id)? Does `getEntityValues()` safely handle empty objects?
4. Examine `GeoMuleMap.jsx`: Are animations smooth? Does it handle empty `cases` or empty `threatSignals` without error?
5. Examine `AppStateContext.jsx` & `VerdictHistoryChart.jsx`: Does the rolling rate accurately drop to 0 when idle? Does it handle high frequency burst traffic?
6. Run verification commands:
   - `./.venv/bin/pytest tests/ -v` (must pass 969 tests)
   - `cd frontend && npm run lint` (0 warnings)
   - `cd frontend && npm run build` (0 errors)

Deliver your verdict (APPROVE or REQUEST_CHANGES) with clear evidence in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_reviewer_2/handoff.md` and communicate back using send_message.

## 2026-09-04T12:26:16Z
You are Reviewer 2. Read your task description in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_reviewer_2/DISPATCH.md, /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md, and /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md.
Perform adversarial review looking for subtle bugs, edge cases, or regressions.
Verify:
- ./.venv/bin/pytest tests/ -v (969 tests)
- cd frontend && npm run lint (0 warnings)
- cd frontend && npm run build (0 errors)
Write your verdict (APPROVE or REQUEST_CHANGES) with clear evidence in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_reviewer_2/handoff.md and notify orchestrator via send_message.

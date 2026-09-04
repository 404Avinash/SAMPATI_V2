# Challenger 1 Task Assignment

## Mission: Empirical Verification & Stress Testing of UI Bugfixes & Geo Map
Empirically verify the code changes implemented by Worker M1.
Worker Handoff Report: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md`
Original Request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (Section `## 2026-09-04T12:04:16Z`)
Project Scope: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_14/PROJECT.md`

## Objectives
1. Write/run scripts or harness tests to verify:
   - R1: `GeoMuleMap.jsx` exports valid JSX, handles edge cases (undefined props, zero cases, corrupted payloads) without crashing.
   - R2: `ThreatIntelPage.jsx` component renders without errors when fed mock payloads containing complex Pydantic `CampaignMatch` objects, missing fields, or empty arrays.
   - R3: `NetworkConstellation.jsx` canvas background rendering logic and style classes (verify no `#0f172a` container background, contrast ratio > 4.5:1 on white).
   - R4: `VerdictHistoryChart.jsx` and `AppStateContext.jsx` rate calculation: verify that when traffic bursts, TPS spikes, and when idle, TPS decays to 0.
2. Run backend regression and frontend validation:
   - `./.venv/bin/pytest tests/ -v`
   - `cd frontend && npm run lint`
   - `cd frontend && npm run build`

Deliver your verdict (APPROVE or REQUEST_CHANGES) with empirical evidence in `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_1/handoff.md` and communicate back using send_message.

## 2026-09-04T12:26:16Z
You are Challenger 1. Read your task description in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_1/DISPATCH.md, /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md, and /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1/handoff.md.
Empirically test all 4 features: GeoMuleMap, ThreatIntelPage crash fix, Constellation canvas white background, and Verdict Velocity rolling rate calculation.
Verify:
- ./.venv/bin/pytest tests/ -v (969 tests)
- cd frontend && npm run lint (0 warnings)
- cd frontend && npm run build (0 errors)
Write your verdict (APPROVE or REQUEST_CHANGES) with empirical evidence in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_challenger_1/handoff.md and notify orchestrator via send_message.


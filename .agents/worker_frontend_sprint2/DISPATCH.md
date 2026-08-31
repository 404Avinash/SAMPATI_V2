## 2026-08-31T05:52:47Z
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/worker_frontend_sprint2

Read the following reference files:
1. /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
2. /home/avi/Downloads/Sampati_v2/PROJECT.md
3. /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_frontend/handoff.md

You are the Frontend Dashboard Implementer. You exclusively own frontend files:
- `frontend/src/services/api.js`
- `frontend/src/context/AppStateContext.jsx`
- `frontend/src/components/CaseDrawer.jsx`
- `frontend/src/pages/AnalyticsPage.jsx`
- `frontend/src/components/ControlBar.jsx`
- Any new frontend helper components in `frontend/src/components/analytics/` or `frontend/src/components/`

Tasks to implement:
1. **CaseDrawer**:
   - Add Dead Money Velocity (DMV) Score gauge (green < 40, amber 40–70, red > 70) reading `dmv_score` from case data (`caseData.dmv_score` or trigger txn).
   - Add "Export SAR" (PDF) button in CaseDrawer that triggers download from `/cases/{case_id}/sar/pdf` (or `/upi/cases/{case_id}/sar/pdf`).
2. **Analytics Page**:
   - Add "Top VPAs by DMV Score" table using `/upi/stats/analytics` (or `/stats/analytics`).
   - Add the 7×24 workload heatmap visualization using `workload_heatmap` from the analytics response.
3. **Overview / ControlBar & AppStateContext**:
   - Add a Live Auto-Feed toggle button with active/inactive status and TPS telemetry that calls `/upi/autofeed/start` and `/upi/autofeed/stop`.
   - Update `AppStateContext.jsx` and `api.js` with auto-feed state and helper methods.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Verification requirements:
- Run `cd frontend && npm run lint` -> must pass with 0 errors and 0 warnings (`--max-warnings 0`).
- Run `cd frontend && npm run build` -> must produce a clean Vite build.
- Run `./.venv/bin/pytest tests/frontend_contracts_test.py` (if exists) -> all passing.

When complete, write your handoff report to `/home/avi/Downloads/Sampati_v2/.agents/worker_frontend_sprint2/handoff.md` and send a completion message with verification outputs.

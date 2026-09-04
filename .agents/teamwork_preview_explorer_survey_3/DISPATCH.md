# Explorer Survey 3 Task Assignment

## Mission: Survey R4 (Fix Verdict Velocity Graph to Show Rolling Rate, Not Cumulative)

### Context
Read `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (under timestamp 2026-09-04T12:04:16Z).
Project Root: `/home/avi/Downloads/Sampati_v2`
Working Directory: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3`

### Objectives
1. **R4 Investigation**:
   - Inspect `frontend/src/components/VerdictVelocityChart.jsx` (and wherever transaction history / velocity data is aggregated, fetched, or streamed via WebSocket, e.g. `OverviewPage.jsx`, hooks, or backend endpoints).
   - Diagnose why the "Verdict Velocity & History" chart plots a cumulative, monotonically increasing line instead of a rolling rate.
   - Trace how points are added to the chart dataset (timestamps, intervals, counters vs differential rate calculation).
   - Propose an algorithm and implementation to calculate and display the rolling rate (transactions per second or transactions per minute) over sliding windows, so the line reflects actual traffic bursts (rising during bursts, dropping when idle).
   - Check if any backend data format changes are needed, or if this can be computed cleanly in frontend state / data transformation.

### Output
Write your comprehensive investigation report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3/handoff.md` with:
- Exact file paths, line numbers, and data flow mechanisms.
- Concrete, actionable implementation recommendations for calculating and rendering rolling rates.
- Verification commands and test considerations.

## 2026-09-04T12:07:22Z
You are Explorer Survey 3. Read your task description in /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3/DISPATCH.md and /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md.
Investigate R4 (Fix Verdict Velocity Graph to Show Rolling Rate, Not Cumulative: inspect VerdictVelocityChart.jsx, OverviewPage.jsx, live feed/history data structures, cumulative accumulation vs rolling rate calculation).
Investigate thoroughly using view_file and grep_search.
Write your detailed report to /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_3/handoff.md.
Communicate back to orchestrator when finished using send_message.

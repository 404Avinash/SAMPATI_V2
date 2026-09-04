# Dispatch — Worker 15.M3: Ambient Traffic for Verdict Velocity Chart

Read:
- `/home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md`
- `/home/avi/Downloads/Sampati_v2/PROJECT.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_3/analysis.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_15_3/handoff.md`

Your working directory is: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m3`

File Write Ownership (Exclusive):
- `frontend/src/context/AppStateContext.jsx`
- `frontend/src/components/VerdictHistoryChart.jsx`
- `frontend/src/components/VerdictVelocityChart.jsx`

Task:
Implement Organic Ambient Background Traffic for the Verdict Velocity Chart:
1. In `frontend/src/context/AppStateContext.jsx`:
   - Eliminate the 30-zero flatline on initial state: pre-populate `verdictHistory` on mount with realistic ambient background points (2.0 to 5.0 TPS of legitimate `ALLOW` traffic).
   - In the 1-second interval ticker (`useEffect`), generate organic harmonic ambient baseline `ALLOW` traffic (2–5 TPS, e.g. using harmonic oscillation $A \cdot \sin(\omega t) + \text{jitter}$ or smooth interpolation) so the chart always breathes and flows across time even when no manual batch simulation or websocket feed is running.
   - Ensure real batch simulations or live feed WebSocket events stack smoothly ON TOP of the ambient baseline and gracefully settle back to the 2–5 TPS ambient floor after bursts finish.
   - Do NOT artificially inflate `stats.evaluated` or generate false-positive `HOLD` or `BLOCK` verdicts — only enrich the live rolling `verdictHistory` points with baseline legitimate ALLOW traffic.
2. In `frontend/src/components/VerdictHistoryChart.jsx`:
   - Anchor the Recharts YAxis domain floor: `domain={[0, (dataMax) => Math.max(8, Math.ceil(dataMax * 1.25))]}` to eliminate Y-axis scale jittering when values fluctuate between 2 and 5 TPS.
   - Ensure smooth animation transitions (e.g. `animationDuration={400}`, linear easing) and ensure live badge displays current TPS with a pulsing green indicator.
3. Verify:
   - `cd frontend && npm run lint` must pass with 0 warnings (`--max-warnings 0`).
   - `cd frontend && npm run build` must complete cleanly with 0 errors.
   - `./.venv/bin/pytest tests/ -v` must pass 969 tests.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your changes, run tests, and write your completion report in `handoff.md` in your working directory. Send a message to parent when done.

## 2026-09-04T13:22:54Z
You are Worker 15.M3 for SAMPATI V2.
Your working directory is /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_15_m3
Read DISPATCH.md in your working directory and follow all instructions.
Your exclusive file ownership: frontend/src/context/AppStateContext.jsx, frontend/src/components/VerdictHistoryChart.jsx, frontend/src/components/VerdictVelocityChart.jsx.
Implement organic harmonic ambient traffic (2-5 TPS background ALLOW traffic) in AppStateContext.jsx (both initial history and 1s interval ticker) and anchor Y-axis domain in VerdictHistoryChart.jsx. Ensure real bursts stack on top cleanly.
MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
Run verification: cd frontend && npm run lint && npm run build, and pytest tests/ -v.
Write your handoff report to handoff.md and send a completion message to parent.


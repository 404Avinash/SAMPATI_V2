## 2026-09-04T17:53:06Z

You are the SWE Light orchestrator for SAMPATI V2.
Your working directory is: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_swe_3
Project root: /home/avi/Downloads/Sampati_v2
Original request file: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
Dispatch file: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_swe_3/DISPATCH.md

Task:
Single self-contained fix: Update frontend/package-lock.json to resolve new map dependencies (`react-simple-maps`, `d3-geo`, `topojson-client`) so that `npm ci` passes strictly in the CI environment and frontend builds cleanly without Leaflet dependency issues.
Small focused team requested.

Requirements:
1. R1. Fix Frontend Dependencies: Update `frontend/package-lock.json` to correctly resolve the new map dependencies so that `npm ci` passes strictly in the CI environment.
2. R2. Verify Deployment: Ensure the frontend builds successfully and the correct static assets (without Leaflet) are bundled.

Acceptance Criteria:
- `cd frontend && npm ci` succeeds without throwing lockfile sync errors.
- `cd frontend && npm run build` succeeds.
- The old Leaflet dependencies are no longer causing the GitHub Action to fail.
- All repo standards pass: `.venv/bin/pytest tests/` passes with 0 failures, `.venv/bin/ruff check app tests` passes, `cd frontend && npm run lint` passes with 0 warnings.
- Safe-push commit & push if required / when validated per repository guidelines.

Execute the SWE Light protocol (implementer, reviewer, test verification) and report back when finished.

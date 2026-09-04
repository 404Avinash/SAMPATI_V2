# Implementer Briefing: Fix Frontend package-lock.json & Verify Build

## Overview
- **Task**: Update `frontend/package-lock.json` to resolve new map dependencies (`react-simple-maps`, `d3-geo`, `topojson-client`) so that `npm ci` passes strictly in CI environment and frontend builds cleanly without Leaflet dependency issues.
- **Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_implementer_r1`
- **Project Root**: `/home/avi/Downloads/Sampati_v2`

## Requirements & Acceptance Criteria
1. **R1**: Update `frontend/package-lock.json` to resolve dependencies so `npm ci` passes strictly.
2. **R2**: Verify frontend build succeeds and produces clean static bundle.
3. **Acceptance Criteria**:
   - `cd frontend && npm ci` succeeds without throwing lockfile sync errors.
   - `cd frontend && npm run build` succeeds.
   - Old Leaflet dependencies are not causing failures.
   - Pytest suite passes 0 failures: `./.venv/bin/pytest tests/`.
   - Ruff check passes: `./.venv/bin/ruff check app tests`.
   - Frontend lint passes 0 warnings: `cd frontend && npm run lint`.
   - Commit and safe-push if required/validated.

## Execution Plan
1. Check `frontend/package.json` dependencies and ensure `react-simple-maps`, `d3-geo`, `topojson-client` are properly listed and any old leaflet dependencies are removed or resolved.
2. Generate clean `frontend/package-lock.json` via npm install in frontend directory.
3. Test `npm ci` to guarantee strict lockfile conformance.
4. Clean up any accidental node_modules tracked file diffs if needed.
5. Run full verification suite:
   - `cd frontend && npm ci`
   - `cd frontend && npm run build`
   - `./.venv/bin/pytest tests/`
   - `./.venv/bin/ruff check app tests`
   - `cd frontend && npm run lint`
6. Commit & push per safe-push guidelines if validated.
7. Prepare final report and handoff documentation.

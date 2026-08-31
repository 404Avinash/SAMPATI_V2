## 2026-08-31T15:39:32Z
You are Worker 3 for SAMPATI V2 Sprint 3 Milestone 3 (Investigations Page & CaseDrawer: R4, R1 frontend part).

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m3
Workspace root: /home/avi/Downloads/Sampati_v2

You EXCLUSIVELY own and are permitted to modify:
- `frontend/src/components/investigations/ForensicImageViewer.jsx`
- `frontend/src/components/investigations/CaseFilterBar.jsx`
- `frontend/src/pages/InvestigationsPage.jsx`
- `frontend/src/components/CaseDrawer.jsx`
- `frontend/src/services/api.js`

Context & Input:
- Read /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md (Sprint 3 section)
- Read /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md for component blueprints (DMV arc gauge, Recharts rule breakdown, SVG ring topology, SAR PDF download).

Requirements to implement:
1. `InvestigationsPage.jsx` & `CaseFilterBar.jsx`:
   - Case table rows must be clickable: clicking any row opens the `CaseDrawer` for that case (using `openCase(c)`). Ensure `CaseDetailModal` is replaced/unified with `CaseDrawer` so no double-modal conflict occurs.
   - Status badge filtering in `CaseFilterBar.jsx`: interactive status pill badges (`ALL`, `OPEN`, `ESCALATED`, `DISMISSED`, `REVIEWED`, `RESOLVED`) that filter the table immediately without page reload.
2. `CaseDrawer.jsx`:
   - Animated DMV arc/dial gauge: replace linear progress bar with a semi-circular arc/dial gauge (Green <40, Amber 40-70, Red >70) with an animated needle that rotates smoothly to the DMV score.
   - Explainable Rule breakdown: render rule hits as a sorted horizontal bar chart (descending by points) using Recharts (`BarChart layout="vertical"`, `Bar isAnimationActive={true} animationDuration={800}`, `Cell` colored by point thresholds).
   - SAR Export: real PDF binary download (`api.downloadSarPdf(caseId)`). Validate that response is `application/pdf` binary. If not (or on error), display a prominent inline error toast message.
3. `ForensicImageViewer.jsx`:
   - Multi-tier image loading:
     1. Attempt `/upi/cases/${caseId}/graph.png`.
     2. Fallback to `/static/upi_cases/${caseId}_ring.png` on 404.
     3. If both fail or load error occurs, render an in-browser SVG vector ring topology fallback using `case.topology` or `case.ring_members_vpas` with smooth fade-in.
4. `api.js`:
   - Support `/static/upi_cases/${caseId}_ring.png` fallback path in `caseGraphUrl` or caller.
   - In `downloadSarPdf`, check `res.headers.get("content-type")?.includes("pdf")` before creating blob and downloading.

Lint & Build rules:
- Respect ESLint in React Hooks guidelines in AGENTS.md (`--max-warnings 0` enforced).
- Test build with `cd frontend && npm run lint && npm run build`.

Write your completion report to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m3/handoff.md`.
Use `send_message` to notify parent when complete.

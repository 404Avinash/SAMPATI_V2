# Dispatch Log

## 2026-08-31T15:33:25Z
You are the Project Orchestrator for SAMPATI V2 Sprint 3.

## Your Identity & Workspace
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_6
- Workspace root: /home/avi/Downloads/Sampati_v2
- User Request: Read /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md (Sprint 3 section starting at 2026-08-31T15:32:02Z)

## Sprint 3 Objectives
Execute and coordinate all requirements for Sprint 3: Deployment Fix + UI Polish + Demo-Ready Refinement:
1. R1: Fix Deployment — Forensic Image Persistence & Static Mount
   - In `app/main.py`, add `app.mount("/static", StaticFiles(directory="static"), name="static")` before SPA fallback mount.
   - In `app/services/upi_cases.py` (`UpiCaseService.__init__`), ensure `artifact_dir` path exists with `os.makedirs`.
   - In `frontend/src/components/ForensicImageViewer.jsx`, fallback to `/static/upi_cases/{case_id}_ring.png` if endpoint 404s.
   - Verify `requirements.txt` contains all needed packages.
2. R2: Demo Seed Data on Load
   - Background non-blocking simulation (~150 txns, fraud_ratio=0.25) on startup or first `/upi/stats` call if 0 evaluated txns.
3. R3: Cinematic NetworkConstellation (`frontend/src/components/NetworkConstellation.jsx`)
   - Continuous spring force physics simulation, pulsing glows for BLOCK (red) & HOLD (amber), risk gradient edges with particle animations, auto-play on load, zoom & pan support, node click opens CaseDrawer.
4. R4: Investigations Page & CaseDrawer
   - Clickable table rows opening drawer, status badge filtering, animated DMV arc/dial gauge, sorted horizontal bar chart for rule breakdown with Recharts, fallback SVG ring topology when PNG 404s, real PDF download for SAR export with toast on error.
5. R5: Analytics Page
   - All Recharts have `animationDuration={800}` & `isAnimationActive={true}`, 7x24 CSS grid heatmap with hover tooltips + skeleton loading state, Top VPAs table with inline progress bars and sortable headers, Active Campaigns metric card.
6. R6: Overview & Live Feed
   - Count-up KPI animations, Live Feed smooth slide-in/fade-out, Auto-Feed toggle with pulsing dot and live TPS counter, Honeypot alert red toast notification (5s).
7. R7: Test, Lint, Build & Safe-Push
   - Verify `.venv/bin/pytest tests/ -v` (648+ tests passing).
   - Verify `cd frontend && npm run lint` (0 warnings with `--max-warnings 0`) and `npm run build`.
   - Stage, commit with message: `feat(ui): polish sprint - cinematic constellation, live feed animations, forensic image fix, demo seed data`, and push to origin main via SSH.

Manage and dispatch specialists, track progress in `progress.md` and `plan.md`, and report back with your final victory claim when complete.

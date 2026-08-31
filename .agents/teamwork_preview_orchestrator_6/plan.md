# Master Plan — SAMPATI V2 Sprint 3: Deployment Fix + UI Polish + Demo-Ready Refinement

## High-Level Strategy
1. **Survey Phase**:
   - Spawn 3 parallel Explorers to inspect existing backend/frontend code, test files, static file mounts, constellation implementation, investigations/casedrawer, analytics, overview, and package dependencies.
2. **Milestone 1: Backend Deployment & Seed Data (R1, R2)**:
   - Worker implements static mount in `app/main.py`, artifact dir safety in `app/services/upi_cases.py`, requirements.txt check, and background seed data simulation (~150 txns, fraud_ratio=0.25) on startup / first `/upi/stats` call.
   - Reviewer, Challenger, Auditor verification.
3. **Milestone 2: Cinematic NetworkConstellation (R3)**:
   - Worker implements spring-force physics simulation (smooth drift/settle), pulsing glow for BLOCK (red) & HOLD (amber), risk gradient edges with traveling particle animation dots, zoom/pan via mouse/drag, auto-play on load, node click opens CaseDrawer.
   - Reviewer, Challenger, Auditor verification.
4. **Milestone 3: Investigations Page & CaseDrawer (R4)**:
   - Worker implements clickable table rows, status badge filtering without reload, animated DMV dial/arc gauge, sorted horizontal bar chart for rule breakdown (Recharts), smooth PNG fade-in + SVG ring fallback for 404s, real PDF download + error toast for SAR export.
   - Reviewer, Challenger, Auditor verification.
5. **Milestone 4: Analytics & Overview Dynamics (R5, R6)**:
   - Worker implements Recharts animation durations (800ms, active), 7x24 CSS grid heatmap with hover tooltips + skeleton loading state, Top VPAs with inline progress bars + sortable headers, Active Campaigns metric card.
   - Worker implements count-up KPI animations, LiveFeed slide-in/fade-out transitions, Auto-feed toggle pulsing dot + live TPS counter, honeypot red toast notification (5s).
   - Reviewer, Challenger, Auditor verification.
6. **Milestone 5: Verification, Lint, Build & Safe-Push (R7)**:
   - Full pytest backend run (648+ passing).
   - Frontend ESLint (`--max-warnings 0`) & Vite build validation.
   - Git stage, commit (`feat(ui): polish sprint - cinematic constellation, live feed animations, forensic image fix, demo seed data`), and push to `origin main` via SSH.

# Dispatch for teamwork_preview_explorer_survey_2

- Role: Frontend & Dashboard Explorer
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2
- Parent orchestrator: teamwork_preview_orchestrator_10
- Objective: Survey R2 (Threat Intelligence Dashboard frontend tab, real-time signal visualization, campaign similarity metrics, entity extraction flow) and R3 UI requirements (button wiring for Live Feed and simulation, reactive toasts).

## 2026-09-03T09:35:48Z
You are teamwork_preview_explorer_survey_2.
Your working directory is `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2`.
You MUST read the authoritative user request at `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (especially the latest section timestamp 2026-09-03T09:32:24Z) and your dispatch at `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/DISPATCH.md`.

Your mission:
Investigate the frontend architecture and UI requirements for Requirement 2 ("Threat Intelligence Dashboard") and R3 UI Interactivity.
Specifically:
1. Inspect `frontend/src/` navigation bar/tabs (e.g. `Navbar.jsx`, `App.jsx`, or router) to see how page tabs are defined and navigated.
2. Investigate how to create a dedicated "Threat Intelligence" tab/page in the top navigation bar.
3. Determine how to implement:
   - Real-time visualization of incoming pre-transaction signals (WebSocket or polling, signal stream component).
   - Suspected Campaign clustering metrics display (e.g., "Campaign similarity: 94%").
   - Explicit visualization of entity extraction flow (SMS -> Phone/UPI/URL -> Graph) using animated or visual workflow diagram/cards.
4. Investigate R3 UI wiring:
   - "Start Live Feed" button in `ControlBar.jsx` or `OverviewPage.jsx` and its connection to `/upi/autofeed/start` and `/upi/autofeed/stop`.
   - "Run batch simulation" button and its connection to `/upi/simulate`.
   - How WebSocket events currently update the charts (e.g., "Verdict Velocity & History" chart) and what changes are needed to ensure real-time dynamic updates.
   - Toast notification system: check if a toast library or custom toast component already exists in `frontend/src/` (e.g., in context/ or components/), or what is needed to implement reactive Toast Notifications for all button clicks.
5. Check ESLint setup and frontend build requirements (`npm run lint`, `npm run build`) and potential gotchas (React hooks ref cleanup, etc.).

Write your findings and recommendations into `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md`.
Use send_message to notify parent when complete with the path to your handoff file.


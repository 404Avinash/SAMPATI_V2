# BRIEFING — 2026-09-03T09:35:48Z

## Mission
Survey frontend architecture and UI requirements for Requirement 2 ("Threat Intelligence Dashboard") and R3 UI Interactivity (buttons, live feed, toasts, WebSocket updates).

## 🔒 My Identity
- Archetype: explorer
- Roles: frontend investigator, code surveyor, synthesizer
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2
- Original parent: e091e8ff-a378-4da9-bac2-dfc927cb605b
- Milestone: Sprint 3 Frontend Architecture Survey
- Milestone: R2 Terminology & UI Overhaul (The Pivot) Survey
- Milestone: R2 Threat Intelligence Dashboard & R3 UI Interactivity Survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze requested components thoroughly
- Produce structured 5-component handoff report
- Do NOT modify any source code files
- Grep of frontend source code must return 0 results for "Dead Money Velocity" and "Criminal Network" after implementation
- Remove overclaiming phrases ("100% confidence", "100% traceable")
- Identify Overview header layout for tagline "Everyone sees a piece. SAMPATI connects the dots."
- Audit backend and frontend test impacts
- Survey navigation tabs for "Threat Intelligence" page
- Determine real-time pre-transaction signal visualization & entity extraction flow
- Survey R3 UI wiring: Live feed start/stop, simulation button, WebSocket chart updates, and reactive toast notifications
- Verify ESLint and build constraints

## Current Parent
- Conversation ID: 1d0e3cfc-1bcd-4db9-88c0-55fb7981a628
- Updated: 2026-09-03T09:35:48Z

## Investigation State
- **Explored paths**:
  - `frontend/src/App.jsx`
  - `frontend/src/layouts/MainLayout.jsx`
  - `frontend/src/components/common/Navbar.jsx`
  - `frontend/src/pages/OverviewPage.jsx`
  - `frontend/src/pages/AnalyticsPage.jsx`
  - `frontend/src/pages/InvestigationsPage.jsx`
  - `frontend/src/components/ControlBar.jsx`
  - `frontend/src/components/VerdictHistoryChart.jsx`
  - `frontend/src/context/AppStateContext.jsx`
  - `frontend/src/hooks/useWebSocket.js`
  - `frontend/src/services/api.js`
  - `app/services/autofeed.py`
  - `app/services/upi_cases.py`
  - `frontend/package.json`
  - `frontend/.eslintrc.cjs`
  - `tests/frontend_contracts_test.py`
- **Key findings**:
  - Navigation: `Navbar.jsx` maps `NAV_ITEMS` using `NavLink`; adding `{ to: "/threat-intel", label: "Threat Intelligence", badgeKey: "threats" }` and `<Route path="/threat-intel" element={<ThreatIntelPage />} />` in `App.jsx` integrates cleanly.
  - Threat Intel Page architecture mapped: Live signal feed, suspected campaign similarity metrics (e.g. 94%), and 3-stage entity extraction flow (`SMS -> Phone/UPI/URL -> Central Fraud Graph`) with interactive playback and simulation button.
  - Button wiring: "Start Live Feed", "Run batch simulation", "Federation round" exist in `ControlBar.jsx` and `AppStateContext.jsx` but lack reactive toast feedback.
  - Chart WebSocket disconnect root cause identified: `autofeed.py` emits single transaction `eval_dict` without cumulative stats; `useWebSocket` and `AppStateContext` fail to increment counters, leading to static chart. Fix identified on both backend and frontend hook/state.
  - Toast notification system: zero-dependency `ToastContext.jsx` + `ToastContainer.jsx` using `framer-motion` `<AnimatePresence>` designed for instant feedback across all actions.
  - Quality gates: `npm run lint` and `npm run build` both pass with 0 warnings/errors.
- **Unexplored areas**: None.

## Key Decisions Made
- Authored complete 5-component hard handoff report in `handoff.md`.

## Artifact Index
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_2/handoff.md` — Complete 5-component handoff report for orchestrator



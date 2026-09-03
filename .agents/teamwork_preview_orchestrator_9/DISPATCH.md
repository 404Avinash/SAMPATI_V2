# DISPATCH LOG

## 2026-09-03T07:02:48Z
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_9
- Role: Project Orchestrator (teamwork_preview_orchestrator_9)
- Mission: Execute the final ML/UI polish and completely overhaul the dashboard's terminology to align with the new "Collaborative Fraud-Intelligence Mesh" narrative per ORIGINAL_REQUEST.md.
  1. R1: True Machine Learning Layer (Isolation Forest) in `app/engine/upi_scorer.py`, output in `/upi/check` response as `ml_anomaly_score`, factored into final verdict.
  2. R2: Terminology & UI Overhaul (The Pivot):
     - Replace "Dead Money Velocity" with "Dormant-to-Active Velocity".
     - Replace "Criminal Network" or "Criminal Hierarchy" with "Suspected Mule Cluster".
     - Remove any claims of "100% confidence" or "100% traceable" from UI.
     - Add tagline "Everyone sees a piece. SAMPATI connects the dots." prominently to Overview dashboard headers.
     - Ensure grep of frontend source code returns 0 results for "Dead Money Velocity" and "Criminal Network".
  3. R3: Dashboard Interactivity & API Wiring:
     - Ensure "Start Live Feed", "Run batch simulation", and "Federation round" buttons on Overview page trigger backend FastAPI endpoints.
     - Live Feed must initiate continuous WebSocket traffic dynamically updating charts and topology graph.
     - Implement reactive toast notification system across dashboard on operational button clicks.
- Quality Gates & Acceptance Criteria:
  - Existing pytest suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures (833+ tests).
  - Frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).
  - Frontend build succeeds (`cd frontend && npm run build`).
  - `/upi/check` response JSON explicitly includes `ml_anomaly_score`.
  - Zero grep hits in frontend for "Dead Money Velocity" and "Criminal Network".
  - Live feed WebSocket visibly updates "Verdict Velocity & History" chart in real-time.
  - Toast notifications display on actionable button clicks.
  - All automated safe-push checks in AGENTS.md pass.

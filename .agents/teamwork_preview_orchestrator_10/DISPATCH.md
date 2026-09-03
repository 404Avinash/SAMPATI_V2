# DISPATCH LOG

## 2026-09-03T09:32:24Z
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_10
- Role: Project Orchestrator (teamwork_preview_orchestrator_10)
- Mission: Execute the massive "Intelligence Mesh" pivot based on the updated PRD and complete interrupted polish per ORIGINAL_REQUEST.md.
  1. R1: Early Warning Intelligence Layer (Backend):
     - Build backend infrastructure (FastAPI routes + PostgreSQL models) to ingest "Pre-Transaction" threat signals.
     - Accept standard fraud signal JSON payloads (e.g. from external mobile app or mock PSPs) with identifiers (Phone, UPI ID, URL) and social engineering tags (e.g. "Bank impersonation", "Urgency").
     - Automatically link these signals to the central Fraud Graph.
  2. R2: Threat Intelligence Dashboard (Frontend):
     - Create dedicated "Threat Intelligence" tab in React frontend top navigation bar.
     - Visualize incoming pre-transaction signals in real-time.
     - Display suspected Campaign clustering metrics (e.g. "Campaign similarity: 94%").
     - Explicitly visualize entity extraction flow (SMS -> Phone/UPI/URL -> Graph).
  3. R3: Pitch Pivot & ML Polish (Interrupted Tasks):
     - ML Layer: Add Unsupervised Isolation Forest model (scikit-learn) to `app/engine/upi_scorer.py` and output `ml_anomaly_score` in `/upi/check`.
     - Terminology: Global overhaul replacing "Dead Money Velocity" with "Dormant-to-Active Velocity", "Criminal Network" with "Suspected Mule Cluster", strip all "100% confidence" claims, and add tagline "Everyone sees a piece. SAMPATI connects the dots."
     - UI Wiring: Ensure "Start Live Feed" and "Run batch simulation" buttons trigger real traffic. Implement reactive Toast Notifications for all button clicks.
- Quality Gates & Acceptance Criteria:
  - Existing pytest suite (`.venv/bin/pytest tests/ -v`) passes with 0 failures (833+ tests).
  - Frontend compiles cleanly with no ESLint errors (`cd frontend && npm run lint`).
  - Frontend build succeeds (`cd frontend && npm run build`).
  - New "Threat Intelligence" tab exists in UI and displays list of pre-transaction threat reports.
  - `/upi/check` response JSON explicitly includes `ml_anomaly_score`.
  - Zero grep hits in frontend for "Dead Money Velocity" and "Criminal Network".
  - Clicking "Start Live Feed" initiates real-time stream updating charts with toast feedback.
  - Follow repository guidelines and automated safe-push protocol in AGENTS.md.

# Orchestration Plan: SAMPATI V2 Final Polish & Intelligence Upgrade

## Mission Objectives
1. **R1: True Machine Learning Layer (Isolation Forest)**
   - Unsupervised Isolation Forest using scikit-learn in `app/engine/upi_scorer.py`.
   - Multivariate anomaly detection (amount, time-of-day, velocity, etc.).
   - Exposed as `ml_anomaly_score` in `/upi/check` response and factored into the final verdict.
2. **R2: Dashboard Interactivity & API Wiring**
   - Overview page buttons wired to FastAPI endpoints: "Start Live Feed", "Run batch simulation", "Federation round".
   - Continuous WebSocket traffic dynamically updating charts ("Verdict Velocity & History") and topology graph.
3. **R3: Reactive UI Toast Notifications**
   - Instant success/error feedback across the dashboard on operational button clicks.
   - Clean UI without console/linter errors.
4. **Acceptance & Quality Gates**
   - Pytest suite: 833+ tests pass with 0 failures (`.venv/bin/pytest tests/ -v`).
   - Frontend ESLint: 0 errors/warnings (`cd frontend && npm run lint`).
   - Frontend Build: Clean build (`cd frontend && npm run build`).

## Execution Phases
- **Phase 0: Survey & Codebase Exploration** (3 Explorers in parallel)
  - `explorer_1`: R1 ML Isolation Forest architecture, feature extraction, scoring integration, scikit-learn dependency, tests.
  - `explorer_2`: R2 Overview page button wiring, WebSocket streaming, chart and topology update mechanisms.
  - `explorer_3`: R3 Toast notification architecture, component tree, ESLint/build compliance.
- **Phase 1: Architecture & Scope Definition**
  - Synthesize findings into `PROJECT.md` with Feature Inventory, Milestones, and Interface Contracts.
- **Phase 2: Milestone Execution & Quality Gates**
  - M1: Backend ML Isolation Forest & API Scoring.
  - M2: Frontend Dashboard Wiring & WebSocket Stream Dynamic Updates.
  - M3: Reactive Toast Notifications across Operational Buttons.
  - M4: Integration, Unit Tests, and E2E Hardening.
- **Phase 3: Verification & Audit**
  - Pytest suite (833+ tests), frontend ESLint, frontend build.
  - Forensic Auditor integrity review.
- **Phase 4: Synthesis & Final Report to Parent**

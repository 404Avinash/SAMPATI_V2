# DISPATCH LOG

## 2026-09-03T10:10:00Z
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_11
- Role: Project Orchestrator (teamwork_preview_orchestrator_11)
- Mission: Resume and complete the "Intelligence Mesh" pivot based on PROJECT.md and ORIGINAL_REQUEST.md.
  * Status so far:
    - Step 0 (Scope Survey): Completed by Explorers 1, 2, and 3. Architectural specs consolidated in `/home/avi/Downloads/Sampati_v2/PROJECT.md`.
    - ML Scorer (R3 item 1): Pure-NumPy/Scikit-learn Isolation Forest implemented in `app/engine/isolation_forest.py` and integrated into `app/engine/upi_scorer.py`; 17 unit tests in `tests/test_isolation_forest.py` pass.
  * Pending Work:
    1. Milestone 1: Early Warning Intelligence Layer (Backend):
       - Implement Pydantic schemas in `app/models/threat_intel.py` (Phone, UPI ID, URL, social engineering tags).
       - Implement DB model in `app/models/upi_persistence.py` (`ThreatSignalModel`).
       - Implement Fraud Graph Service in `app/services/graph_service.py` (`FraudGraphService` via `networkx.DiGraph`) linking signals to VPAs and cases.
       - Implement Threat Intel Service in `app/services/threat_intel_service.py` (ingestion, campaign matching, graph updates, WebSocket broadcast).
       - Implement FastAPI routes in `app/api/intel.py` (`/intel/signals`, `/intel/graph`, `/intel/campaigns`, `/intel/simulate`).
       - Register router in `app/main.py` and update SPA `api_prefixes`.
       - Add backend test suite in `tests/test_threat_intel_r1.py`.
    2. Milestone 2: Threat Intelligence Dashboard & UI Polish (Frontend):
       - Add "Threat Intelligence" tab in `frontend/src/components/common/Navbar.jsx`.
       - Register route `/threat-intel` in `frontend/src/App.jsx`.
       - Create `frontend/src/pages/ThreatIntelPage.jsx` with real-time pre-transaction signal feed, campaign similarity card ("Campaign similarity: 94%"), and animated entity extraction flow (SMS -> Phone/UPI/URL -> Graph).
       - Add API methods in `frontend/src/services/api.js`.
    3. Milestone 3: Terminology Overhaul & UI Wiring:
       - Terminology find-and-replace: "Dead Money Velocity" -> "Dormant-to-Active Velocity", "Criminal Network" -> "Suspected Mule Cluster", cap confidence at 98% (no 100% claims), add mesh tagline "Everyone sees a piece. SAMPATI connects the dots."
       - Zero grep hits in frontend for "Dead Money Velocity" and "Criminal Network".
       - Wire "Start Live Feed" and "Run batch simulation" buttons to backend APIs.
       - Implement reactive Toast Notifications across operational buttons (`ToastContext.jsx` + `ToastContainer.jsx`).
    4. Milestone 4 & 5: Full Regression & Safe-Push:
       - Run full pytest suite (`.venv/bin/pytest tests/ -v`, 833+ tests) -> 0 failures.
       - Frontend lint (`cd frontend && npm run lint`) -> 0 errors/warnings (`--max-warnings 0`).
       - Frontend build (`cd frontend && npm run build`) -> clean build.
       - Automated safe-push per AGENTS.md.

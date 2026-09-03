# Project: SAMPATI V2 — ML Layer, Terminology Pivot & Dashboard Interactivity

## Architecture
SAMPATI V2 is a Collaborative Fraud-Intelligence Mesh for real-time UPI mule-network interception.
- **Backend**: FastAPI (Python 3.14) with an inline 4-layer risk evaluation pipeline (`app/engine/`):
  * Layer 1: Deterministic Rules (0-100 pts)
  * Layer 2: Adaptive EWMA Behavioral Anomaly (0-25 pts)
  * Layer 3: Federated Cross-PSP Graph Network Score (0-40 pts)
  * Layer 4: Unsupervised Isolation Forest Multivariate ML Anomaly Score (`ml_anomaly_score` in [0.0, 1.0])
- **Frontend**: React 18 / Vite / Tailwind CSS / Framer Motion:
  * Real-time WebSocket event ingestion (`/ws`, `/ws/feed`)
  * Overview Dashboard with live KPI counters, Verdict Velocity & History chart, and animated Network Constellation topology
  * Centralized reactive Toast Notification system (`ToastContext`)
  * Case Investigation Drawer with Dormant-to-Active Velocity (DMV) dial gauge and SAR PDF export

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Unsupervised Isolation Forest Engine | Pure-Python/NumPy iForest (Liu et al. 2008) in `app/engine/isolation_forest.py` with dynamic `sklearn` fallback | M1 | Survey / R1 |
| 2 | ML Score API Integration | Expose `ml_anomaly_score` in `UpiEvaluationResponse` and `/upi/check` response JSON | M1 | Survey / R1 |
| 3 | Scoring Pipeline & Verdict Factor | Layer 4 scoring in `UpiRiskScorer.evaluate`: $s \le 0.5 \implies 0$ pts, scaling to 25 pts, reason `"ML_MULTIVARIATE_ANOMALY"`, and `HOLD` floor at $s \ge 0.85$ | M1 | Survey / R1 |
| 4 | "Dead Money Velocity" -> "Dormant-to-Active Velocity" | Global replacement across frontend (`CaseDrawer.jsx`, `TopDmvAccountsTable.jsx`, `AnalyticsPage.jsx`) and backend (`dmv.py`, `gemini_service.py`, `encyclopedia_kb.py`) | M2 | Survey / R2 |
| 5 | "Criminal Network" -> "Suspected Mule Cluster" | Ensure 0 hits in frontend source and replace backend/encyclopedia occurrences | M2 | Survey / R2 |
| 6 | Overclaiming Language Removal | Remove "100% confidence" / "100% traceable", cap confidence at 98%, use signal-correlation phrasing | M2 | Survey / R2 |
| 7 | Collaborative Mesh Tagline | Add "Everyone sees a piece. SAMPATI connects the dots." prominently in Overview header banner, `Masthead.jsx`, and `Navbar.jsx` | M2 | Survey / R2 |
| 8 | Reactive Toast Notification System | Custom React + `framer-motion` `ToastContext` & `ToastContainer` with dark theme styling | M3 | Survey / R3 |
| 9 | Operational Button Wiring | Wire toasts and handlers to "Start Live Feed", "Run batch simulation", and "Federation round" | M3 | Survey / R3 |
| 10 | Dynamic Chart Velocity Streaming | Enrich `UPI_EVALUATED` WebSocket broadcasts with running stats and update `AppStateContext` to dynamically advance "Verdict Velocity & History" chart | M3 | Survey / R3 |
| 11 | Dynamic Topology Auto-Stepping | Update `NetworkConstellation.jsx` to auto-step when new cases arrive during live feed | M3 | Survey / R3 |
| 12 | E2E Regression & Quality Gates | 833+ pytest tests pass, ESLint 0 errors/warnings (`--max-warnings 0`), Vite build clean, 0 grep hits | Final | Quality Gates |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | True ML Layer (Isolation Forest) | Implement Isolation Forest engine, update `UpiEvaluationResponse`, integrate into `UpiRiskScorer.evaluate` and `/upi/check` | none | PLANNED |
| M2 | Terminology & UI Overhaul (The Pivot) | Replace DMV and Criminal Network terminology, strip overclaiming language, place tagline, update contract tests | none | PLANNED |
| M3 | Dashboard Interactivity & API Wiring | Toast system, Overview buttons wiring, live chart velocity updates, live topology auto-advance | M1, M2 | PLANNED |
| Final | Regression, Integration & E2E Validation | Full pytest suite (833+ tests), ESLint `--max-warnings 0`, Vite build, grep verification, Tier 5 adversarial check | M1, M2, M3 | PLANNED |

## Interface Contracts
### `app/engine/isolation_forest.py` ↔ `app/engine/upi_scorer.py`
- `UpiIsolationForest.score_txn(txn: UpiTransaction, state: UpiHotState, dmv_score: float) -> float`: returns normalized anomaly score in $[0.0, 1.0]$.
- `get_isolation_forest() -> UpiIsolationForest`: singleton getter.

### `app/models/upi_models.py` ↔ `/upi/check` REST API
- `UpiEvaluationResponse`: includes `ml_anomaly_score: float = Field(default=0.0, description="Unsupervised Isolation Forest multivariate anomaly score in [0.0, 1.0]")`.
- `resp.model_dump()` guarantees `ml_anomaly_score` is serialized in JSON response.

### `frontend/src/context/ToastContext.jsx` ↔ Components
- `useToast() -> { showToast(message, type, duration), toast: { success(msg), error(msg), info(msg), warning(msg) } }`.

## Code Layout
- `app/engine/isolation_forest.py`: Isolation Forest implementation.
- `app/engine/upi_scorer.py`: Layer 4 scoring integration.
- `app/models/upi_models.py`: Schema definitions.
- `app/services/autofeed.py`: Live feed streaming with aggregate stats.
- `frontend/src/context/ToastContext.jsx`: Toast state provider.
- `frontend/src/components/common/ToastContainer.jsx`: Toast notification rendering.
- `frontend/src/components/ControlBar.jsx`: Overview operational controls.
- `frontend/src/pages/OverviewPage.jsx`: Header tagline banner and layout.
- `frontend/src/components/CaseDrawer.jsx`: Terminology updates.
- `frontend/src/components/analytics/TopDmvAccountsTable.jsx`: Terminology updates.
- `frontend/src/pages/AnalyticsPage.jsx`: Terminology updates.
- `frontend/src/components/NetworkConstellation.jsx`: Live topology auto-advance.
- `tests/test_isolation_forest.py`: Unit and regression tests for ML model.
- `tests/frontend_contracts_test.py`: Contract tests updated for new terminology.

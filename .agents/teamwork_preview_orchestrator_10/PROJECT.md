# Project: SAMPATI V2 — Collaborative Fraud-Intelligence Mesh & Early Warning Pivot

## Architecture
SAMPATI V2 is an intelligence-mesh platform for real-time UPI mule-network interception and pre-transaction early warning signals.
- **Backend Architecture**:
  * Inline 4-Layer Risk Pipeline:
    - Layer 1: Deterministic Rules (`app/engine/upi_rules.py`, 0–100 pts)
    - Layer 2: Adaptive EWMA Behavioral Anomaly (`app/engine/adaptive_ewma.py`, 0–25 pts)
    - Layer 3: Federated Cross-PSP Graph Network Score (`app/federation/`, 0–40 pts)
    - Layer 4: Unsupervised Isolation Forest Anomaly (`app/engine/isolation_forest.py` & `app/engine/upi_scorer.py`, `ml_anomaly_score` in [0.0, 1.0], 0–25 pts, HOLD floor at 0.85)
  * Early Warning Pre-Transaction Threat Intelligence Layer:
    - Ingestion Routes: `/intel/signals`, `/intel/graph`, `/intel/campaigns`, `/intel/simulate` (aliases at `/threat-intel/`)
    - Schemas: `app/models/threat_intel.py` (Pydantic schemas + regex extractor for Phone, UPI ID, URL, social engineering tags)
    - Persistence: `ThreatSignalModel` in `app/models/upi_persistence.py` + thread-safe in-memory cache
    - Central Fraud Graph: `app/services/graph_service.py` (`FraudGraphService` via `networkx.DiGraph`) linking signals to VPAs, cases, and mule rings
    - Real-Time Push: WebSocket broadcast (`THREAT_SIGNAL_RECEIVED`) via `app/api/websocket.py`
    - SPA Fallback Guard: Registered in `api_prefixes` in `app/main.py`
- **Frontend Architecture**:
  * Top Navigation Bar: `Navbar.jsx` with dedicated "Threat Intelligence" tab (`/threat-intel`)
  * Threat Intelligence Page (`ThreatIntelPage.jsx`):
    - Real-time pre-transaction signal feed with live incoming events & sample trigger
    - Suspected Campaign clustering metrics card ("Campaign similarity: 94%")
    - 3-stage animated entity extraction flow (`SMS Phishing Payload -> Regex/NLP Extraction -> Central Fraud Graph Linking & Pre-Arming`)
  * Reactive UI Interactivity:
    - Zero-dependency custom Toast system (`ToastContext.jsx` + `ToastContainer.jsx`) powered by `framer-motion`
    - Wired to "Start Live Feed", "Run batch simulation", "Federation round", and "Export SAR"
    - Real-time Velocity Chart updates: `autofeed.py` broadcasting `stats` + `AppStateContext.jsx` incremental accumulation
    - Real-time Constellation auto-advance: `NetworkConstellation.jsx` advancing `currentStep` on new cases
  * Terminology Overhaul:
    - 0 hits for "Dead Money Velocity" (replaced with "Dormant-to-Active Velocity")
    - 0 hits for "Criminal Network" (replaced with "Suspected Mule Cluster")
    - Confidence claims capped at 98% (defensible signal correlation)
    - Tagline displayed: "Everyone sees a piece. SAMPATI connects the dots."

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Threat Signal Pydantic Schemas & Regex Extractor | Pydantic models for signal ingestion and regex extraction for Indian phones, UPI IDs, URLs, and social engineering tags in `app/models/threat_intel.py` | M1 | Survey R1 |
| 2 | Threat Signal DB Persistence | SQLAlchemy `ThreatSignalModel` in `app/models/upi_persistence.py` with foreign keys to cases and rings, plus in-memory fallback | M1 | Survey R1 |
| 3 | Central Fraud Graph Service | `FraudGraphService` in `app/services/graph_service.py` using `networkx.DiGraph` to link signals, VPAs, cases, and rings | M1 | Survey R1 |
| 4 | Threat Intelligence Service | `ThreatIntelService` in `app/services/threat_intel_service.py` managing signal ingestion, campaign matching, graph updates, and WebSocket broadcast | M1 | Survey R1 |
| 5 | Threat Intel FastAPI Routes | Endpoints `/intel/signals`, `/intel/graph`, `/intel/campaigns`, `/intel/simulate` with aliases at `/threat-intel` | M1 | Survey R1 |
| 6 | Router Registration & SPA Prefix Update | Mount `intel.router` and add `/intel`, `/threat-intel` to `api_prefixes` in `app/main.py` | M1 | Survey R1 |
| 7 | Dedicated Threat Intel Tab & Route | Add `/threat-intel` route in `App.jsx` and nav item in `Navbar.jsx` | M2 | Survey R2 |
| 8 | Threat Intelligence Dashboard Page | Implement `ThreatIntelPage.jsx` with signal feed, campaign similarity card (94%), and entity extraction flow | M2 | Survey R2 |
| 9 | Frontend Threat Intel API Integration | Add `getThreatSignals`, `getThreatCampaigns`, `ingestThreatSignal` in `frontend/src/services/api.js` | M2 | Survey R2 |
| 10 | Unsupervised Isolation Forest Scorer | Verified Pure-NumPy/Scikit-learn iForest in `app/engine/isolation_forest.py` and `app/engine/upi_scorer.py` | M3 | Survey R3 |
| 11 | `ml_anomaly_score` API Response Contract | Expose `ml_anomaly_score` in `UpiEvaluationResponse` and `/upi/check` response JSON | M3 | Survey R3 |
| 12 | Terminology Overhaul: Dormant-to-Active Velocity | Replace 6 instances in frontend and backend; update contract test in `tests/frontend_contracts_test.py` | M3 | Survey R3 |
| 13 | Terminology Overhaul: Suspected Mule Cluster | Verify 0 hits in frontend and replace docstrings in backend/encyclopedia | M3 | Survey R3 |
| 14 | Defensible Signal Phrasing | Strip 100% confidence/traceability claims, cap confidence at 98% | M3 | Survey R3 |
| 15 | Mesh Tagline Placement | Add "Everyone sees a piece. SAMPATI connects the dots." to `OverviewPage.jsx` and `Masthead.jsx` | M3 | Survey R3 |
| 16 | Reactive Toast Notification System | Custom React + `framer-motion` `ToastContext.jsx` and `ToastContainer.jsx` | M3 | Survey R3 |
| 17 | Button Wiring & Feedback Toasts | Wire toasts to "Start Live Feed", "Run batch simulation", "Federation round", "Export SAR" | M3 | Survey R3 |
| 18 | Dynamic Velocity Chart Streaming | Enrich `UPI_EVALUATED` with `stats` in `autofeed.py` and handle incremental updates in `AppStateContext.jsx` | M3 | Survey R3 |
| 19 | Dynamic Topology Graph Auto-Advance | Auto-advance `currentStep` in `NetworkConstellation.jsx` when live stream adds cases | M3 | Survey R3 |
| 20 | E2E Regression, Quality Gates & Safe-Push | 850+ pytest tests pass, ESLint 0 warnings (`--max-warnings 0`), clean Vite build, safe-push | Final | Quality Gates |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Early Warning Intelligence Layer (Backend) | Features 1–6: Schemas (`threat_intel.py`), DB model (`upi_persistence.py`), Fraud Graph (`graph_service.py`), Service (`threat_intel_service.py`), Routes (`intel.py`), Router mount (`main.py`), Tests (`test_threat_intel_r1.py`) | none | PLANNED |
| M2 | Threat Intelligence Dashboard & UI Polish (Frontend) | Features 7–9, 12–19: Nav tab (`Navbar.jsx`), Route (`App.jsx`), `ThreatIntelPage.jsx`, Toast system (`ToastContext.jsx`), Button wiring (`ControlBar.jsx`), Live stream fixes (`autofeed.py`, `AppStateContext.jsx`), Terminology overhaul & Tagline | M1 | PLANNED |
| Final | Regression, Integration, Quality Gates & Safe-Push | Features 10, 11, 20: Full pytest suite (850+ tests), ESLint 0 warnings, clean Vite build, grep verification, automated safe-push to origin main | M1, M2 | PLANNED |

## Interface Contracts
### `/intel/signals` ↔ Frontend / External PSPs
- `POST /intel/signals`:
  ```json
  {
    "source": "mobile_app",
    "phone": "+919876543210",
    "upi_id": "phish_trap@oksbi",
    "url": "https://sbi-kyc-alert.com/login",
    "tags": ["Bank impersonation", "Urgency"],
    "raw_content": "Dear customer your SBI account is blocked. Update KYC immediately at https://sbi-kyc-alert.com or send Rs 1 to phish_trap@oksbi. Call 9876543210.",
    "severity": "CRITICAL",
    "confidence": 0.95
  }
  ```
  Returns `201 Created` with `ThreatSignalResponse` containing `signal_id`, `extracted_entities`, `matched_campaign`, `linked_graph_nodes`.

### `/intel/graph` ↔ Frontend Graph Visualizer
- `GET /intel/graph`:
  Returns `{"nodes": [{"id": str, "type": "VPA"|"PHONE"|"URL"|"CASE"|"CAMPAIGN", "label": str, ...}], "edges": [{"source": str, "target": str, "type": str, ...}]}`.

### `app/models/upi_models.py` ↔ `/upi/check` REST API
- `UpiEvaluationResponse`: includes `ml_anomaly_score: float = Field(default=0.0, description="Unsupervised Isolation Forest multivariate anomaly score in [0.0, 1.0]")`.

### `frontend/src/context/ToastContext.jsx` ↔ Components
- `useToast() -> { toast: { success(msg), error(msg), info(msg), warning(msg) } }`.

## Code Layout
- `app/models/threat_intel.py`: Pydantic models for threat signals and entity extraction.
- `app/models/upi_persistence.py`: SQLAlchemy `ThreatSignalModel`.
- `app/services/graph_service.py`: `FraudGraphService` (`networkx.DiGraph`).
- `app/services/threat_intel_service.py`: `ThreatIntelService` logic.
- `app/api/intel.py`: FastAPI routes for threat intelligence.
- `app/main.py`: Include `intel_router` and update `api_prefixes`.
- `frontend/src/pages/ThreatIntelPage.jsx`: Threat Intelligence view.
- `frontend/src/components/common/Navbar.jsx`: Add "Threat Intelligence" tab.
- `frontend/src/App.jsx`: Register `/threat-intel` route.
- `frontend/src/services/api.js`: Add threat intel API methods.
- `frontend/src/context/ToastContext.jsx`: Toast provider.
- `frontend/src/components/common/ToastContainer.jsx`: Toast renderer.
- `frontend/src/components/ControlBar.jsx`: Wire buttons with toasts.
- `frontend/src/pages/OverviewPage.jsx`: Add mesh tagline banner.
- `frontend/src/components/CaseDrawer.jsx`: Replace "Dead Money Velocity" -> "Dormant-to-Active Velocity".
- `frontend/src/components/analytics/TopDmvAccountsTable.jsx`: Terminology update.
- `frontend/src/pages/AnalyticsPage.jsx`: Terminology update.
- `tests/test_threat_intel_r1.py`: Unit tests for Threat Intel backend.
- `tests/frontend_contracts_test.py`: Updated contract tests.

# Project: SAMPATI V2 — Production-Grade Fraud Intelligence Mesh

## Architecture
SAMPATI V2 is upgraded from a prototype fraud scorer into a production-grade fraud intelligence system:
1. **Supervised ML Layer (R1)**: [DONE]
   - Supervised classification engine (`PureNumpySupervisedClassifier` + optional `SklearnSupervisedClassifierAdapter`) in `app/engine/supervised_classifier.py` trained on PaySim / synthetic fraud benchmark dataset.
   - Dual ML outputs in `/upi/check`: `ml_anomaly_score` (Unsupervised Isolation Forest) AND `supervised_fraud_score` (Supervised classifier).
   - Demonstrates marked reduction in False Negatives compared to unsupervised baseline (100% relative FN reduction in benchmark).
   - Training pipeline in `app/engine/train_supervised.py` prints evaluation summary with Precision, Recall, F1 score.
2. **Simulated Institutional Signal Adapters (R2)**: [DONE]
   - Mock NPCI MuleHunter Adapter (`app/adapters/npci.py`): Central switch mule-probability score.
   - Mock DPIP Smart Registry Adapter (`app/adapters/dpip.py`): National fraud registry lookup by SHA-256 VPA hash, returning threat level.
   - Mock PSP Adapter (`app/adapters/psp.py`): Produces standard fraud signals in `StandardFraudSignal` format for PhonePe, Paytm, etc.
   - Deterministic VPA mapping: Transactions to honeypots/known-bad VPAs return non-zero `mock_npci_score` (>=0.85) and `mock_dpip_threat_level` (>=0.85).
   - Frontend visualization: Contributing signal sources displayed clearly with institution labels in `CaseDrawer.jsx`, `ThreatIntelPage.jsx`, and `LiveFeed.jsx`.
3. **Mobile App Push Notification System (R3)**: [DONE]
   - Push notification engine (`app/services/notification_service.py`) supporting FCM v1 API with a zero-credential hermetic `MockFcmProvider` for testing/demo.
   - Token registration endpoint `POST /notifications/register` with duplicate token deduplication.
   - Automatic dispatch on high-risk threats: BLOCK verdict in `/upi/check` and HIGH/CRITICAL in `POST /intel/signals` containing risk score, verdict, and top reason.
   - Benchmarked end-to-end ingestion-to-dispatch latency under 500ms on local machine (`tests/test_notifications_benchmark.py`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Supervised Classifier Architecture | Pure-NumPy classifier with scikit-learn adapter fallback in `app/engine/supervised_classifier.py` | M1 | Survey R1 |
| 2 | PaySim Data Pipeline & Ingestion | Data loader, cleaner, and synthetic benchmark generator in `app/engine/train_supervised.py` | M1 | Survey R1 |
| 3 | Training & Evaluation Summary | Printed Precision, Recall, F1 summary and False Negative Reduction comparison vs Isolation Forest | M1 | Survey R1 |
| 4 | Model Serialization & Artifacts | Serializes to `app/engine/artifacts/supervised_fraud_model.pkl` with inference loader | M1 | Survey R1 |
| 5 | Supervised Score Schema & Scorer | Add `supervised_fraud_score` to `UpiEvaluationResponse`, integrate into `UpiRiskScorer.evaluate` and `/upi/check` | M1 | Survey R1 |
| 6 | Supervised Unit & Contract Tests | Verify dual score outputs, model invariants, and False Negative reduction in `tests/test_supervised_model.py` | M1 | Survey R1 |
| 7 | StandardFraudSignal Model | `StandardFraudSignal` model in `app/models/threat_intel.py` for institutional and PSP feeds | M2 | Survey R2 |
| 8 | Mock NPCI MuleHunter Adapter | Central switch mule probability (0.96 for honeypots, low for clean) in `app/adapters/npci.py` | M2 | Survey R2 |
| 9 | Mock DPIP Smart Registry Adapter | National fraud registry query by VPA SHA-256 hash & update endpoint in `app/adapters/dpip.py` | M2 | Survey R2 |
| 10 | Mock PSP Adapter | Standardized fraud signal generator (PhonePe, Paytm) in `app/adapters/psp.py` | M2 | Survey R2 |
| 11 | Transaction Evaluation Integration | `/upi/check` returns `mock_npci_score`, `mock_dpip_threat_level`, and `contributing_signals` | M2 | Survey R2 |
| 12 | Adapters REST API Router | Endpoints at `/adapters/npci/mulehunter`, `/adapters/dpip/registry`, `/adapters/psp/simulate` | M2 | Survey R2 |
| 13 | Frontend Institutional Display | Institution cards in CaseDrawer, branded badges in ThreatIntelPage, pill tags in LiveFeed | M2 | Survey R2 |
| 14 | Institutional Adapters Tests | Unit, deterministic mapping, and API contract tests in `tests/test_institutional_adapters.py` | M2 | Survey R2 |
| 15 | Push Notification Core & Providers | `NotificationService` with `MockFcmProvider` & `HttpV1FcmProvider` in `app/services/notification_service.py` | M3 | Survey R3 |
| 16 | Device Token Registration API | `POST /notifications/register` endpoint with `DeviceRegistrationRequest`/`Response` in `app/api/notifications.py` | M3 | Survey R3 |
| 17 | High-Risk Threat Alert Triggers | Dispatches alert on BLOCK verdict and HIGH/CRITICAL in `POST /intel/signals` with score, verdict, reason | M3 | Survey R3 |
| 18 | Sub-500ms Benchmark Test | Measures end-to-end signal ingestion to FCM dispatch latency < 500ms in `tests/test_notifications_benchmark.py` | M3 | Survey R3 |
| 19 | Full Test Suite Regression Gate | 902+ existing tests pass with 0 failures (`./.venv/bin/pytest tests/ -v`) | Final | Quality Gate |
| 20 | Linter & Code Quality Gate | Ruff linter passes with 0 errors (`./.venv/bin/ruff check app tests`) | Final | Quality Gate |
| 21 | Frontend ESLint & Build Gate | ESLint `--max-warnings 0` passes and Vite builds cleanly (`cd frontend && npm run lint && npm run build`) | Final | Quality Gate |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Production-Grade Supervised ML Model | Features 1–6 (supervised classifier, PaySim data pipeline, Precision/Recall/F1 summary, FN reduction, dual scores in `/upi/check`) | none | DONE |
| M2 | Simulated Institutional Signal Adapters | Features 7–14 (Mock NPCI, Mock DPIP by hash, Mock PSP, deterministic bad VPA scores, frontend institutional display) | none | DONE |
| M3 | Mobile App Push Notification System | Features 15–18 (FCM integration, device registration endpoint, BLOCK & high-risk triggers, <500ms benchmark) | none | DONE |
| Final | Regression, Integration & Quality Gates | Features 19–21 (Full pytest suite, ruff check, frontend lint & build, adversarial verification) | M1, M2, M3 | DONE |

## Interface Contracts
### `app/engine/supervised_classifier.py` ↔ `app/engine/upi_scorer.py`
- `UpiSupervisedClassifier.score_txn(txn: UpiTransaction, state: UpiHotState, dmv_score: float) -> float`: returns supervised fraud probability in $[0.0, 1.0]$.
- `get_supervised_classifier() -> UpiSupervisedClassifier`: singleton getter.

### `app/models/upi_models.py` ↔ `/upi/check` REST API
- `UpiEvaluationResponse`:
  - `ml_anomaly_score: float`
  - `supervised_fraud_score: float`
  - `mock_npci_score: float`
  - `mock_dpip_threat_level: Union[float, int, str]`
  - `contributing_signals: List[Dict[str, Any]]`

### `app/adapters/` ↔ `app/services/upi_cases.py`
- `InstitutionalAdapterService.evaluate_for_transaction(txn: UpiTransaction) -> Dict[str, Any]`:
  - Returns dict with keys `"mock_npci_score"`, `"mock_dpip_threat_level"`, `"contributing_signals"`.

### `app/services/notification_service.py` ↔ `app/api/`
- `NotificationService.register_device(req: DeviceRegistrationRequest) -> DeviceRegistrationResponse`
- `NotificationService.dispatch_threat_alert(risk_score: int, verdict: str, top_reason: str, target_vpa: Optional[str], metadata: Optional[dict]) -> DispatchResult`

## Code Layout
- `app/engine/supervised_classifier.py`: Supervised ML model implementation (NumPy + sklearn fallback).
- `app/engine/train_supervised.py`: PaySim ingestion, benchmark dataset generator, model trainer, metrics summary.
- `app/engine/artifacts/supervised_fraud_model.pkl`: Serialized model weights/parameters.
- `app/adapters/npci.py`: Mock NPCI MuleHunter Adapter.
- `app/adapters/dpip.py`: Mock DPIP Smart Registry Adapter.
- `app/adapters/psp.py`: Mock PSP Adapter.
- `app/adapters/service.py`: Institutional Adapter service coordinating adapters.
- `app/services/notification_service.py`: FCM Push Notification Service and providers.
- `app/api/notifications.py`: `/notifications/register` endpoint.
- `app/api/adapters.py`: Endpoints for querying/updating institutional adapters.
- `frontend/src/components/CaseDrawer.jsx`: Institutional Contributing Signals display.
- `frontend/src/pages/ThreatIntelPage.jsx`: Institution badges and simulation presets.
- `frontend/src/components/LiveFeed.jsx`: Institutional pill tags in Signals column.
- `frontend/src/services/api.js`: Adapter API wrappers.
- `tests/test_supervised_model.py`: M1 unit and benchmark tests.
- `tests/test_institutional_adapters.py`: M2 unit and contract tests.
- `tests/test_notifications_benchmark.py`: M3 benchmark and notification tests.

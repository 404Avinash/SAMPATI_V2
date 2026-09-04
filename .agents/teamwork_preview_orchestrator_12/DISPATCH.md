# Dispatch Instructions — teamwork_preview_orchestrator_12

## Working Directory
- Agent metadata directory: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/`
- Workspace root: `/home/avi/Downloads/Sampati_v2`
- Original Request: `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md`

## Mission & Scope
Upgrade SAMPATI V2 from a prototype fraud scorer into a production-grade fraud intelligence system:
1. **R1. Production-Grade ML Model with Public Data**:
   - Train a supervised classifier on publicly available fraud datasets (e.g., PaySim or synthetic transaction fraud dataset).
   - Training pipeline must ingest and clean raw data, engineer features consistent with SAMPATI signals (amount, velocity, time-of-day, dormancy), train & evaluate with reported precision/recall/F1, and serialize for inference.
   - Demonstrably reduce false negatives compared to pure unsupervised baseline.
   - Update `/upi/check` response to include both `supervised_fraud_score` and `ml_anomaly_score`.
2. **R2. Simulated Institutional Signal Adapters (Mock NPCI, DPIP, PSP)**:
   - Mock NPCI MuleHunter Adapter: returns realistic mule-probability score for VPA/account.
   - Mock DPIP Smart Registry Adapter: queries/updates national fraud registry by VPA hash, returning threat level.
   - Mock PSP Adapter (e.g., PhonePe, Paytm): produces standardized fraud signals (`StandardFraudSignal`).
   - Deterministic and realistic outputs based on input VPA characteristics (e.g., honeypot VPAs return HIGH from mock NPCI).
   - Displayed clearly in dashboard as contributing signal sources with institution labels.
3. **R3. Mobile App Push Notification System (FCM Integration)**:
   - Integrate Firebase Cloud Messaging (FCM) to dispatch push notifications to registered devices when high-risk threats (BLOCK verdict or high-risk `/intel/signals`) are detected.
   - Device token registration endpoint: `POST /notifications/register`.
   - Threat alert payload includes risk score, verdict, top reason.
   - Benchmark test verifying end-to-end latency from signal ingestion to dispatch is under 500ms on local machine.

## Verification Requirements
- Pytest suite passes: `./.venv/bin/pytest tests/ -v` (0 failures)
- Ruff linter: `./.venv/bin/ruff check app tests` (0 errors)
- Frontend build: `cd frontend && npm run lint && npm run build` (clean, 0 warnings/errors)
- Specific capabilities:
  - `/upi/check` response has both `ml_anomaly_score` and `supervised_fraud_score`
  - Printed evaluation summary with Precision, Recall, F1 for the supervised model
  - Known-bad VPA returns non-zero `mock_npci_score` and `mock_dpip_threat_level`
  - High-risk payload to `POST /intel/signals` triggers FCM push within 500ms (benchmarked)

## 2026-09-03T21:50:50Z
Server restart recovery:
Milestone 1 (Supervised ML) is confirmed DONE and verified in the workspace (`supervised_classifier.py`, `train_supervised.py`, `supervised_fraud_model.pkl`, and 21 passing tests in `tests/test_supervised_model.py`).

Please immediately proceed to execute:
1. Milestone 2 (R2): Simulated Institutional Signal Adapters (Mock NPCI MuleHunter, Mock DPIP Smart Registry, Mock PSP adapters with StandardFraudSignal format, deterministic outputs, displayed on dashboard).
2. Milestone 3 (R3): Mobile App Push Notification System (FCM Integration, `POST /notifications/register` endpoint, sub-500ms latency benchmark test).
3. Final Milestone: Run the full test suite (`.venv/bin/pytest tests/ -v`), `ruff check app tests`, and `cd frontend && npm run build` before claiming completion.

Continue execution and update progress.md and BRIEFING.md as milestones complete.

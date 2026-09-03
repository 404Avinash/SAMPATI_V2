# DISPATCH: Survey R1 — ML Isolation Forest Layer

- Working Directory: /home/avi/Downloads/Sampati_v2/.agents/explorer_survey_1
- Original Request: /home/avi/Downloads/Sampati_v2/.agents/ORIGINAL_REQUEST.md
- Role: teamwork_preview_explorer (Surveyor 1)

## Mission
Investigate the codebase for Requirement R1:
1. Locate and examine `app/engine/upi_scorer.py` and `app/api/upi.py`.
2. Analyze current scoring logic, features used, and final verdict determination.
3. Check `scikit-learn` availability in the python environment (`.venv`) and dependencies.
4. Design the Unsupervised Isolation Forest architecture:
   - Feature vector: transaction amount, time-of-day (sin/cos or hour float), velocity, etc.
   - Model initialization / persistence / fitting strategy (e.g., pre-trained / fit on baseline data or synthetic baseline distributions).
   - Anomaly score normalization (e.g. 0.0 to 1.0 where higher is more anomalous).
   - Integration into `/upi/check` response schema (`ml_anomaly_score`) and weighting in final verdict calculation.
5. Identify existing tests that test UPI scorer and `/upi/check` endpoint.
6. Write findings and concrete implementation recommendations to `handoff.md` in your working directory.

## 2026-09-03T06:48:35Z
Investigate:
1. `app/engine/upi_scorer.py` and `app/api/upi.py`.
2. Current scoring logic, feature extraction, and verdict determination.
3. Check if `scikit-learn` is installed in `./.venv` and dependencies.
4. Design the Unsupervised Isolation Forest model: features (amount, time-of-day, velocity), training/initialization baseline distribution, scoring normalization, inclusion in `/upi/check` response as `ml_anomaly_score`, and factoring into final verdict.
5. Identify existing tests in `tests/` and recommend new unit tests.

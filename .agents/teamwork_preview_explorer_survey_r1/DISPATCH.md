# Dispatch: teamwork_preview_explorer_survey_r1

## Mission
Investigate R1: Production-Grade Supervised ML Model with Public Data for SAMPATI V2.

## Working Directory
/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r1/

## Mandatory Reading
- `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (read the latest request from 2026-09-03T20:13:42Z)
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/DISPATCH.md`

## Objectives
1. Investigate existing scoring in `app/engine/upi_scorer.py`, `app/engine/isolation_forest.py`, `app/models/upi_models.py`, `app/api/v1/upi.py` (or `/upi/check` endpoint).
2. Investigate feature engineering options using SAMPATI signals: amount, velocity, time-of-day, dormancy (DMV score), etc.
3. Investigate public fraud datasets (e.g. PaySim or synthetically generated transaction fraud dataset with labeled fraud column) available or cleanly generatable/ingestible in the repo.
4. Design the supervised classifier pipeline (e.g., Random Forest or Logistic Regression or Gradient Boosting using scikit-learn), including training script, evaluation summary printing Precision, Recall, and F1 score, model serialization (e.g., joblib/pickle or pure/lightweight inference model in `app/engine/`), and how it demonstrates reduced false negatives vs unsupervised baseline.
5. Identify required schema changes in `UpiEvaluationResponse` and `/upi/check` to include both `ml_anomaly_score` (Isolation Forest) and `supervised_fraud_score` (new supervised model).
6. Check existing pytest suite impact (902 tests) and test files for ML.
7. Write your findings to `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r1/handoff.md`.

## 2026-09-03T20:15:37Z
Investigate R1: Production-Grade Supervised ML Model with Public Data.
Explore the existing codebase:
- Examine app/engine/upi_scorer.py, app/engine/isolation_forest.py, app/models/upi_models.py, app/api/v1/upi.py.
- Check python packages installed in .venv (scikit-learn, joblib, numpy, etc.).
- Explore public datasets or clean data generation for fraud (e.g., PaySim or synthetic labeled fraud transactions).
- Investigate feature engineering based on SAMPATI signals (amount, velocity, time-of-day, dormancy).
- Determine model architecture, training pipeline script, evaluation summary format (printing Precision, Recall, F1), model serialization/loading, and how to verify false negative reduction vs unsupervised baseline.
- Determine the schema changes for /upi/check to return both supervised_fraud_score and ml_anomaly_score.
- Document all findings, file paths, concrete implementation steps, and verification strategies in handoff.md in your working directory.
Communicate completion back with send_message.

# Dispatch: teamwork_preview_worker_m1_r1

## Mission
Implement Milestone 1 (R1): Production-Grade Supervised ML Model with Public Data for SAMPATI V2.

## Working Directory
`/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_r1/`

## Mandatory Reading Before Starting Work
- `/home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md` (read latest request under 2026-09-03T20:13:42Z)
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md`
- `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r1/handoff.md`

## Exclusive Write Ownership
You own and may modify or create the following files:
- `app/engine/supervised_classifier.py` (new)
- `app/engine/train_supervised.py` (new)
- `app/engine/artifacts/supervised_fraud_model.pkl` (new)
- `data/paysim_benchmark.csv` (new/generated)
- `app/models/upi_models.py` (add `supervised_fraud_score` field)
- `app/engine/upi_scorer.py` (integrate supervised classifier into evaluation)
- `app/services/upi_cases.py` (record `supervised_fraud_score`)
- `tests/test_supervised_model.py` (new tests)

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Requirements & Implementation Guidelines
1. In `app/engine/supervised_classifier.py`:
   - Implement `PureNumpySupervisedClassifier` with feature scaling and calibrated classification (e.g. ensemble tree or regularized logistic model) operating completely self-contained in pure Python / NumPy.
   - Implement optional `SklearnSupervisedClassifierAdapter` if scikit-learn is available.
   - Implement `UpiSupervisedClassifier` with `score_txn(txn, state, dmv_score) -> float`, `extract_features()`, `save_model()`, `load_model()`.
   - Implement singleton getter `get_supervised_classifier()`.
2. In `app/engine/train_supervised.py`:
   - Ingest and clean public PaySim dataset (support `--data-path` or automatically generate high-fidelity synthetic benchmark sample `data/paysim_benchmark.csv`).
   - Extract features aligned with existing SAMPATI signals (amount, velocity, time-of-day, dormancy).
   - Train and evaluate the model on held-out test split.
   - Print printed evaluation summary with Precision, Recall, F1 score.
   - Compute and print False Negative Reduction vs unsupervised Isolation Forest baseline.
   - Serialize model to `app/engine/artifacts/supervised_fraud_model.pkl`.
3. In `app/models/upi_models.py`:
   - Add `supervised_fraud_score: float = Field(default=0.0, description="Supervised ML fraud probability score in [0.0, 1.0]")` to `UpiEvaluationResponse`.
4. In `app/engine/upi_scorer.py`:
   - Integrate `get_supervised_classifier()` into `UpiRiskScorer`.
   - Score transactions and populate `supervised_fraud_score`.
   - Append `"SUPERVISED_FRAUD_DETECTED"` to reasons when score >= 0.70.
5. In `app/services/upi_cases.py`:
   - Record `supervised_fraud_score` into case and transaction records.
6. In `tests/test_supervised_model.py`:
   - Unit tests for feature extraction, train/evaluate summary, model serialization, API schema check (`/upi/check` returns both `ml_anomaly_score` and `supervised_fraud_score`), and mathematical demonstration of False Negative reduction vs unsupervised baseline.

## Verification Commands
1. `./.venv/bin/python app/engine/train_supervised.py` (must print Precision, Recall, F1, FN reduction summary).
2. `./.venv/bin/pytest tests/test_supervised_model.py tests/test_isolation_forest.py -v`.
3. `./.venv/bin/pytest tests/ -q` (all 902+ tests must pass).
4. `./.venv/bin/ruff check app tests` (0 errors).
5. `cd frontend && npm run lint && npm run build && cd ..` (0 warnings, clean build).

Write your completion report to `handoff.md` in your working directory and notify the orchestrator with `send_message`.

## 2026-09-03T20:22:34Z
<USER_REQUEST>
You are teamwork_preview_worker_m1_r1.
Working directory: /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_r1/
Workspace root: /home/avi/Downloads/Sampati_v2
Read /home/avi/Downloads/Sampati_v2/ORIGINAL_REQUEST.md (specifically the latest request under 2026-09-03T20:13:42Z), /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_orchestrator_12/PROJECT.md, /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_r1/handoff.md, and your dispatch file at /home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_worker_m1_r1/DISPATCH.md.

Implement Milestone 1 (R1): Production-Grade Supervised ML Model with Public Data.
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Follow all instructions in DISPATCH.md. Implement the supervised classifier, the training and evaluation pipeline with printed Precision, Recall, and F1 score, model serialization, API schema updates for dual scores in /upi/check, and test suite. Run all verification commands. Write handoff.md and send_message when done.
</USER_REQUEST>

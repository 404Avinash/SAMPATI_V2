# Investigation Handoff: R1 — Production-Grade Supervised ML Model with Public Data

## 1. Observation

### 1.1 Python Virtual Environment & Dependency Constraints
Direct execution of `./.venv/bin/pip list` revealed that `numpy` (v2.5.2) is installed, but `scikit-learn` and `joblib` are **not installed** in the virtual environment (`Python 3.14.4`):
```
Package           Version
----------------- -----------
fastapi           0.141.1
numpy             2.5.2
pydantic          2.13.4
pytest            9.1.1
ruff              0.16.5
...
```
Attempting `./.venv/bin/pip install --dry-run scikit-learn joblib` failed with:
`NewConnectionError: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution`
Observation: The container environment has no external PyPI / internet access. Consequently, any ML solution must operate self-contained in pure Python / NumPy or provide a dual-backend architecture with a pure NumPy implementation as the default engine and an optional `scikit-learn` adapter.

### 1.2 Existing Unsupervised Layer Architecture
In `app/engine/isolation_forest.py` (lines 25–31, 133–174, 289–348), the existing unsupervised Layer 4 ML engine handles this exact dependency model:
- Defines `PureNumpyIsolationForest` implementing Liu et al. (2008) in pure NumPy.
- Conditionally imports `from sklearn.ensemble import IsolationForest as SklearnIsolationForest`.
- Extracts a 13-dimensional numerical feature vector via `UpiIsolationForest.extract_features()` (lines 363–436):
  1. `amount` (INR value)
  2. `log_amount` (`log1p(amount)`)
  3. `hour_fraction` (0.0 to 24.0)
  4. `hour_sin` (`sin(2*pi*hr/24)`)
  5. `hour_cos` (`cos(2*pi*hr/24)`)
  6. `is_night` (1.0 if hr < 5 or hr >= 23, else 0.0)
  7. `payer_account_age_days` (min(365, max(0, age)))
  8. `payee_vpa_age_days` (min(365, max(0, age)))
  9. `payee_is_new_for_payer` (1.0 if true, 0.0 otherwise)
  10. `payer_velocity_count_30m` (outbound transaction count from state in 30m window)
  11. `payer_velocity_amount_30m` (outbound amount sum from state in 30m window)
  12. `device_vpa_count` (distinct VPAs tied to device fingerprint)
  13. `dmv_score` (Dead Money Velocity / Dormancy score in [0.0, 100.0])

### 1.3 Risk Scoring & Verdict Integration
In `app/engine/upi_scorer.py`:
- `UpiRiskScorer.evaluate()` (lines 53–146) combines Layer 1 (Rules: 0–100), Layer 2 (Adaptive: 0–25), Layer 3 (Network: 0–40), and Layer 4 (Isolation Forest ML: 0–25).
- Anomaly score integration (lines 69–74):
  ```python
  ml_score = self.isolation_forest.score_txn(txn, self.state, dmv_score)
  if ml_score > 0.50:
      ml_pts = int(round((ml_score - 0.50) / 0.50 * ML_MAX_POINTS))
      ml_pts = min(ML_MAX_POINTS, max(0, ml_pts))
  else:
      ml_pts = 0
  ```
- Thresholds: `ALLOW_BELOW = 45`, `BLOCK_AT = 70`, `ML_HOLD_FLOOR = 0.85`, `ML_ANOMALY_THRESHOLD = 0.70`.
- Response model (lines 132–146) instantiates `UpiEvaluationResponse` including `ml_anomaly_score=round(ml_score, 4)`.

### 1.4 Models & API Gate Contracts
- `app/models/upi_models.py` (lines 59–78): `UpiEvaluationResponse` currently defines:
  ```python
  ml_anomaly_score: float = Field(
      default=0.0,
      description="Unsupervised Isolation Forest multivariate anomaly score in [0.0, 1.0]",
  )
  ```
  It currently lacks `supervised_fraud_score`.
- `app/api/upi.py` (lines 115–153): `@router.post("/check")` evaluates transactions via `UpiCaseService.evaluate(txn)` and returns `payload = resp.model_dump()`.
- `app/services/upi_cases.py` (lines 948–950 and 1042–1045): records `ml_anomaly_score` into `case_data` and `_txn_log`.

### 1.5 Baseline Test Suite Health
Running `./.venv/bin/pytest tests/test_isolation_forest.py` passed with 17 passed.
Running the full test suite (`./.venv/bin/pytest tests/ -q`) executes 902 tests (901 passing, 1 test in `tests/test_tier5_adversarial_challenge.py` was a transient microsecond benchmark sensitive to background CPU load; running alone passes 100% in 1.38s).
`./.venv/bin/ruff check app tests` passed cleanly with 0 errors.
`cd frontend && npm run lint` passed cleanly (0 warnings, `--max-warnings 0`).
`cd frontend && npm run build` built cleanly in 10.31s.

---

## 2. Logic Chain

### 2.1 Problem Analysis: Why Supervised Learning is Required Alongside Isolation Forest
1. **Unsupervised Isolation Forest Limitations**:
   - Isolation Forest isolates observations by random orthogonal feature partitioning. It measures sample isolation depth without access to ground truth labels.
   - Fraudulent transactions that mimic normal retail distributions across isolated individual dimensions (e.g., moderate amounts under Rs 25,000 during daytime hours) but exhibit specific adversarial combinations (e.g., sudden activation of a dormant account + brand new beneficiary + rapid pass-through velocity) are frequently assigned low anomaly scores ($< 0.50$).
   - This produces substantial **False Negatives (FN)** in unsupervised detection.
2. **Supervised Classifier Advantage**:
   - Supervised models (e.g., Logistic Regression with feature interactions, or Random Forest / Gradient Boosted Trees) optimize directly on ground-truth label boundaries.
   - By conditioning on labeled fraud data (PaySim or synthetic labeled mule transactions), the model weights high-risk signal conjunctions (e.g., high DMV score coupled with new payee novelty) heavily, capturing subtle fraud patterns that an unsupervised outlier detector overlooks.
   - Deploying both scores (`ml_anomaly_score` and `supervised_fraud_score`) provides dual-lens visibility: unsupervised detection catches novel zero-day distribution shifts, while supervised detection minimizes false negatives on known attack patterns.

### 2.2 Model Architecture & Zero-Dependency Execution
1. Given that `scikit-learn` is not installed and external downloads are unavailable, the model architecture must mirror the design of `app/engine/isolation_forest.py`:
   - Primary engine: `PureNumpySupervisedClassifier` implementing an ensemble of Decision Trees (Random Forest) or a regularized Logistic Regression classifier with standard scaling and calibrated sigmoid output in pure NumPy.
   - Fallback adapter: `SklearnSupervisedClassifierAdapter` wrapping `sklearn.ensemble.RandomForestClassifier` or `sklearn.linear_model.LogisticRegression` if ever installed in other environments.
2. Feature Dimension Consistency:
   - The supervised model uses the same 13 standardized features extracted by `UpiIsolationForest.extract_features()`. This guarantees zero extraction overhead and 100% feature consistency across both ML layers.
   - Additional derived feature (optional 14th/15th feature): `dormancy_novelty_risk` = `(dmv_score / 100.0) * (1.0 if payee_is_new_for_payer else 0.2)`.

### 2.3 Public Data Ingestion & Benchmark Generator Strategy
1. The requirement explicitly mentions PaySim (`step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest, isFraud`).
2. To ensure the repository is completely self-contained, reproducible, and verifiable offline:
   - Create `app/engine/train_supervised.py`:
     - Ingestion function: `load_and_clean_data(file_path: Optional[str] = None)`
     - If a CSV path is passed via CLI `--data-path` (e.g., a real PaySim CSV), it parses and cleans the dataset, mapping `step % 24` to `hour_fraction`, calculating balance depletion as dormancy/velocity signals, and creating labeled features.
     - If no file is provided or file does not exist, it automatically generates a high-fidelity synthetic benchmark dataset (`data/paysim_benchmark.csv` or in-memory) of 5,000+ transactions with realistic fraud characteristics (10–15% fraud ratio, smurfing bursts, dormant account takeovers, nocturnal cashouts).
3. The training pipeline cleans data, normalizes continuous features, performs a stratified train/test split (80/20), fits the classifier, evaluates metrics on the held-out test split, prints an evaluation summary, and serializes the model to `app/engine/artifacts/supervised_fraud_model.pkl`.

### 2.4 Mathematical Verification of False Negative Reduction
1. Let $D_{test}^{fraud} = \{ (x_i, y_i) \in D_{test} \mid y_i = 1 \}$ be the set of labeled fraudulent transactions in the test set.
2. Unsupervised baseline decision: flags fraud if $ml\_anomaly\_score \ge 0.70$.
   $$FN_{unsup} = \sum_{i \in D_{test}^{fraud}} \mathbb{I}(ml\_anomaly\_score(x_i) < 0.70)$$
3. Supervised model decision: flags fraud if $supervised\_fraud\_score \ge 0.50$.
   $$FN_{sup} = \sum_{i \in D_{test}^{fraud}} \mathbb{I}(supervised\_fraud\_score(x_i) < 0.50)$$
4. The False Negative Reduction rate is:
   $$\text{FN Reduction \%} = \frac{FN_{unsup} - FN_{sup}}{FN_{unsup}} \times 100\%$$
   Target benchmark: $FN_{unsup} \approx 30-50\%$, $FN_{sup} \le 8\%$, yielding $\ge 70\%$ relative reduction in missed fraud.

### 2.5 Scoring Integration & Invariants
1. `supervised_fraud_score` in $[0.0, 1.0]$.
2. Zero-regression invariant:
   - Clean, legitimate retail transactions MUST produce `supervised_fraud_score < 0.20` and contribute `0` risk points.
   - For high-confidence fraud ($supervised\_fraud\_score \ge 0.70$), append `"SUPERVISED_FRAUD_DETECTED"` to `reasons`.
   - When $supervised\_fraud\_score \ge 0.85$, escalate verdict floor to at least `HOLD` (`risk_score >= 45`).
3. Dual-reporting in `/upi/check`:
   - Both `ml_anomaly_score` and `supervised_fraud_score` are returned in the JSON payload.

---

## 3. Caveats

1. **Absence of `scikit-learn` in Sandbox**:
   - As observed in Section 1.1, `scikit-learn` is not installed and network isolation prevents pip installation.
   - Implementation must provide a pure NumPy implementation (`PureNumpySupervisedClassifier`) alongside an optional `SklearnSupervisedClassifierAdapter`. The system must never crash if `sklearn` cannot be imported.
2. **PaySim File Size vs Offline Storage**:
   - The full Kaggle PaySim dataset is 500+ MB uncompressed, which cannot be downloaded offline.
   - The ingestion pipeline must support both external PaySim CSV files (via `--data-path`) and an automated built-in synthetic PaySim benchmark generator that produces a statistically faithful sample in `data/paysim_benchmark.csv`.
3. **No Breaking Changes to Existing 902 Pytest Invariants**:
   - All existing tests in `tests/` expect exact scores or verdicts for established scenarios. The supervised model must strictly maintain zero regression on clean transactions.

---

## 4. Conclusion & Implementation Plan

### 4.1 Target File Changes
1. **New Module**: `app/engine/supervised_classifier.py`
   - Class `PureNumpySupervisedClassifier`: Binary classification tree ensemble or regularized logistic regression with feature scaling.
   - Class `SklearnSupervisedClassifierAdapter`: Wraps scikit-learn when present.
   - Class `UpiSupervisedClassifier`: Production wrapper with `score_txn()`, `extract_features()`, `fit_baseline()`, and model serialization (`save_model()`, `load_model()`).
   - Function `get_supervised_classifier()`: Thread-safe singleton getter.
2. **New Module**: `app/engine/train_supervised.py`
   - Standalone executable script (`./.venv/bin/python app/engine/train_supervised.py`).
   - Ingests / generates PaySim dataset (`data/paysim_benchmark.csv`).
   - Computes and prints Precision, Recall, F1 score, Confusion Matrix, and False Negative Reduction comparison table.
   - Serializes trained model to `app/engine/artifacts/supervised_fraud_model.pkl`.
3. **Model & Schema Updates**:
   - `app/models/upi_models.py`:
     - Add `supervised_fraud_score: float = Field(default=0.0, description="Supervised ML fraud probability score in [0.0, 1.0]")` to `UpiEvaluationResponse`.
4. **Scoring Engine Updates**:
   - `app/engine/upi_scorer.py`:
     - Initialize `self.supervised_classifier = get_supervised_classifier()` in `UpiRiskScorer.__init__`.
     - In `evaluate()`: compute `supervised_score = self.supervised_classifier.score_txn(txn, self.state, dmv_score)`.
     - Factor into verdict / reasons (`"SUPERVISED_FRAUD_DETECTED"` if $\ge 0.70$).
     - Populate `supervised_fraud_score=round(supervised_score, 4)` in `UpiEvaluationResponse`.
5. **Case Service & API Updates**:
   - `app/services/upi_cases.py`:
     - Record `supervised_fraud_score` into `txn_entry` and `case_data`.
   - `app/api/upi.py`:
     - `/upi/check` automatically serializes both fields.
6. **New Test Suite**: `tests/test_supervised_model.py`
   - Tests mathematical invariants, feature extraction, train/predict lifecycle, serialization/loading, API schema contract (`/upi/check` containing both `ml_anomaly_score` and `supervised_fraud_score`), and empirical proof of False Negative reduction vs Isolation Forest.

---

## 5. Verification Method

### 5.1 Verification Commands
1. **Model Training Pipeline Execution**:
   ```bash
   ./.venv/bin/python app/engine/train_supervised.py
   ```
   *Expected output*: Prints evaluation summary table with Precision $\ge 0.85$, Recall $\ge 0.85$, F1 $\ge 0.85$, and False Negative Reduction $\ge 50\%$. Serializes `app/engine/artifacts/supervised_fraud_model.pkl`.
2. **Unit & Integration Tests**:
   ```bash
   ./.venv/bin/pytest tests/test_supervised_model.py tests/test_isolation_forest.py -v
   ```
   *Expected output*: All unit tests pass, verifying dual scores in `/upi/check` and false negative reduction.
3. **Full Regression Suite**:
   ```bash
   ./.venv/bin/pytest tests/ -q
   ```
   *Expected output*: 902+ passed, 0 failures.
4. **Code Quality & Linter**:
   ```bash
   ./.venv/bin/ruff check app tests
   ```
   *Expected output*: All checks passed.
5. **Frontend Lint & Build**:
   ```bash
   cd frontend && npm run lint && npm run build
   ```
   *Expected output*: 0 ESLint warnings (`--max-warnings 0`), clean production build.

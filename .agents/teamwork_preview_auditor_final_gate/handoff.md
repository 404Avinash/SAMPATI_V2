# Forensic Integrity Audit & Final Gate Report: R1, R2, R3

**Work Product**: Deliverables R1 (Supervised ML Layer), R2 (Simulated Institutional Adapters), R3 (FCM Push Notifications & Latency Benchmark)
**Profile**: General Project
**Integrity Mode**: Benchmark (per `ORIGINAL_REQUEST.md`)
**Verdict**: CLEAN

---

## 1. Observation

### R1. Supervised Machine Learning Model (`app/engine/supervised_classifier.py`, `app/engine/train_supervised.py`)
- **Algorithmic Authenticity**: Inspected `app/engine/supervised_classifier.py`. The file implements a pure NumPy Decision Tree (`PureNumpyDecisionTree`) and Random Forest (`PureNumpySupervisedClassifier`). The code executes authentic mathematical calculations:
  - Gini Impurity calculation: `gini_parent = 2.0 * prob * (1.0 - prob)` (line 163).
  - Feature subsampling: `rng.choice(n_features, size=k, replace=False)` (line 168).
  - Information Gain evaluation across 10 quantiles: `gain = gini_parent - (n_left / n_samples) * gini_left - (n_right / n_samples) * gini_right` (line 197).
  - Class-weighted balanced bootstrap sampling: `sampling_weights = np.where(y_arr == 1, w_pos, w_neg)` (line 299).
  - Feature standardization: `PureNumpyStandardScaler` computes mean, variance, scale, and z-score (lines 42–74).
  - Probability calibration across clean retail, intermediate, and fraud tiers (lines 532–548).
- **Training Pipeline Execution**: Directly ran `./.venv/bin/python app/engine/train_supervised.py --n-samples 2000`. The output verified:
  ```
  [*] Training PureNumpySupervisedClassifier (30 trees, max_depth=6, class_weight=balanced)...
  [✓] Model training completed in 0.38 seconds.
  Precision: 1.0000 (Target >= 0.8500) PASS [✓]
  Recall:    1.0000 (Target >= 0.8500) PASS [✓]
  F1 Score:  1.0000 (Target >= 0.8500) PASS [✓]
  Accuracy:  1.0000 (Target >= 0.9000) PASS [✓]
  False Negative Reduction vs Isolation Forest Baseline:
    Isolation Forest (Baseline): 4 FN (6.67% FN rate, 93.33% recall)
    Supervised Classifier:       0 FN (0.00% FN rate, 100.00% recall)
    False Negative Reduction:    100.00% relative reduction (4 missed frauds prevented)
  [✓] Serialized supervised fraud model to: app/engine/artifacts/supervised_fraud_model.pkl (28.8 KB)
  ```
- **Artifact Verification**: Inspected `app/engine/artifacts/supervised_fraud_model.pkl` via Python pickle loader. The file contains a valid `PureNumpySupervisedClassifier` instance with 30 decision trees, `is_fitted: True`, 13 feature names, and normalized feature importances summing to 1.0.
- **Scoring Pipeline Integration**: In `app/engine/upi_scorer.py`, `UpiRiskScorer.evaluate` calls `self.supervised_classifier.score_txn(txn, self.state, dmv_score)` (line 84), factors it into verdicts (`action = "HOLD"` if `>= SUPERVISED_HOLD_FLOOR`, `reasons.append("SUPERVISED_FRAUD_DETECTED")` if `>= SUPERVISED_FRAUD_THRESHOLD`), and populates `supervised_fraud_score` alongside `ml_anomaly_score` in `UpiEvaluationResponse`.

### R2. Simulated Institutional Signal Adapters (`app/adapters/`, `app/api/adapters.py`)
- **NPCI MuleHunter Adapter (`app/adapters/npci.py`)**:
  - Implements deterministic honeypot scoring returning 0.96 mule probability (`CENTRAL_SWITCH_HONEYPOT_SINK`, `switch_velocity_percentile: 99.8`) for registered honeypots (line 76–89).
  - Uses SHA-256 deterministic hashing (`hashlib.sha256`) to assign realistic baseline velocities and low scores (<0.15) to clean retail VPAs.
- **DPIP Smart Registry Adapter (`app/adapters/dpip.py`)**:
  - Simulates the national fraud registry using SHA-256 hash lookups (`compute_hash`, lines 70–75).
  - Supports stateful dynamic updates (`update_registry`, lines 206–247) and queries by either plain VPA or 64-character SHA-256 hash (`query_hash`, line 93).
- **Mock PSP Adapter (`app/adapters/psp.py`)**:
  - Emulates PhonePe, Paytm, GooglePay, and BHIM producing standardized fraud signals (`StandardFraudSignal`) with typology tags (`velocity_anomaly`, `suspicious_beneficiary`).
  - Supports direct asynchronous ingestion into the central mesh (`publish_to_mesh`, lines 49–58).
- **Inline Evaluation Integration**:
  - In `app/services/upi_cases.py` (lines 1035–1039), `UpiCaseService.evaluate` calls `get_institutional_adapters().evaluate_for_transaction(txn)` to populate `mock_npci_score`, `mock_dpip_threat_level`, and `contributing_signals`.
  - In `tests/test_institutional_adapters.py`, verified honeypots return `mock_npci_score >= 0.85` and `mock_dpip_threat_level >= 0.85`, while clean accounts return low/zero scores.
- **Frontend Visualization**:
  - `frontend/src/components/CaseDrawer.jsx` (lines 555–582) renders institutional cards with `NPCI`, `DPIP`, and `PSP` badges and score breakdowns.
  - `frontend/src/pages/ThreatIntelPage.jsx` renders `renderInstitutionBadge` for contributing institutional feeds.
  - `frontend/src/components/LiveFeed.jsx` displays institutional pill tags for transactions with non-zero institutional scores.

### R3. Mobile Push Notifications & FCM Integration (`app/services/notification_service.py`, `app/api/notifications.py`)
- **Service Implementation**:
  - `NotificationService` maintains an in-memory, thread-safe token registry (`_tokens`) with deduplication (`status: "registered"` vs `"updated"`).
  - Dual-mode architecture: `MockFcmProvider` for hermetic testing and `HttpV1FcmProvider` for Google Cloud FCM HTTP v1 API (`https://fcm.googleapis.com/v1/projects/{project_id}/messages:send`).
- **REST Endpoints**:
  - `POST /notifications/register` registers tokens with platform and VPA metadata.
  - `GET /notifications/tokens`, `GET /notifications/history`, `GET /notifications/status` exposed and mounted at `/notifications` and `/upi/notifications`.
- **Threat Triggers**:
  - In `app/api/upi.py` (lines 127–146), any BLOCK verdict immediately triggers `notif_svc.dispatch_threat_alert` with risk score, verdict, top reason, and transaction metadata.
  - In `app/services/threat_intel_service.py` (lines 367–388), incoming signals via `POST /intel/signals` with HIGH or CRITICAL severity trigger `notif_svc.dispatch_threat_alert`.
- **Latency Benchmark (`tests/test_notifications_benchmark.py`)**:
  - Empirically executed benchmark across 60 real HTTP requests through the full FastAPI pipeline:
    - Average Latency: 6.06 ms
    - Median (p50): 5.81 ms
    - 95th Percentile: 9.08 ms
    - 99th Percentile: 17.67 ms
    - Maximum Latency: 17.67 ms
    - SLA Target: < 500.00 ms (PASS)

### Automated Test Suites, Linters & Builds
- **Full Pytest Suite**: `./.venv/bin/pytest tests/ -q` executed 969 tests.
  - Result: `969 passed, 6 warnings in 167.81s (0:02:47)`. 0 failures.
- **Ruff Python Linter**: `./.venv/bin/ruff check app tests` returned:
  - `All checks passed!`. 0 lint errors.
- **Frontend ESLint & Build**: `cd frontend && npm run lint && npm run build` returned:
  - ESLint: 0 errors, 0 warnings (`--max-warnings 0` passed).
  - Vite build: `✓ built in 13.55s`, clean bundle generated in `frontend/dist/`.

---

## 2. Logic Chain

1. **Absence of Hardcoding & Facades**:
   - Source code analysis of `supervised_classifier.py` reveals genuine recursive decision trees, Gini impurity mathematical formulas, feature standardizers, and random forest bagging. There are no static string-matching shortcuts or pre-determined return values.
   - `train_supervised.py` computes genuine empirical confusion matrices and serializes functional pickle models that are verified by inspecting the pickled tree structures.
   - `npci.py` and `dpip.py` use cryptographic SHA-256 hashing and dynamic registry dictionaries, rather than hardcoded test cases.
   - `notification_service.py` implements a real token registry and dispatch pipeline that executes real asynchronous task routines.

2. **Compliance with Benchmark Integrity Mode**:
   - `ORIGINAL_REQUEST.md` (line 386) specifies `Integrity mode: benchmark`.
   - The ML implementation operates in pure Python and NumPy with mathematical algorithms written from scratch, satisfying the strict requirements of benchmark mode. The optional scikit-learn adapter serves only as a fallback and is not required for inference.
   - Zero execution delegation to external closed-source services.

3. **Empirical Performance & Behavioral Verification**:
   - The latency benchmark in `tests/test_notifications_benchmark.py` was directly executed. It runs actual HTTP POST calls through the full FastAPI router and serialization stack, recording a p99 latency of 17.67 ms, far below the required 500 ms ceiling.
   - The full repository test suite (969 tests) executed to completion without a single regression or failure.

---

## 3. Caveats

- Live FCM delivery to physical devices requires valid Google Cloud service account credentials (`FCM_SERVICE_ACCOUNT_JSON` or `FCM_AUTH_TOKEN`). In their absence, the system utilizes `MockFcmProvider` / unauthenticated `HttpV1FcmProvider`, which is the intended design for local testing and CI/CD environments.
- No other caveats.

---

## 4. Conclusion

**Verdict: CLEAN**

All three deliverables (R1 Supervised ML, R2 Simulated Institutional Adapters, R3 FCM Push Notifications & Latency Benchmark) have been forensically audited and verified. The implementations contain genuine algorithms and data structures, zero test hardcoding, zero facade stubs, and authentic benchmark performance. All acceptance criteria and quality gates are completely satisfied.

---

## 5. Verification Method

To independently reproduce and verify this audit:

```bash
# 1. Verify Supervised ML Training Pipeline & Evaluation Summary
./.venv/bin/python app/engine/train_supervised.py --n-samples 2000

# 2. Run Milestone-Specific Test Suites
./.venv/bin/pytest tests/test_supervised_model.py -v
./.venv/bin/pytest tests/test_institutional_adapters.py -v
./.venv/bin/pytest tests/test_notifications_benchmark.py -v -s
./.venv/bin/pytest tests/test_challenger_m1_stress.py -v

# 3. Run Full Repository Test Suite (969 tests)
./.venv/bin/pytest tests/ -q

# 4. Run Python Linter
./.venv/bin/ruff check app tests

# 5. Run Frontend Lint and Vite Build
cd frontend && npm run lint && npm run build && cd ..
```

**Invalidation Conditions**:
- Any failure in the 969 pytest tests.
- Any Ruff linting error.
- Any ESLint warning/error or Vite build failure.
- End-to-end FCM latency exceeding 500 ms.
- Failure of `/upi/check` to output dual scores (`ml_anomaly_score` and `supervised_fraud_score`) or institutional scores (`mock_npci_score` and `mock_dpip_threat_level`).

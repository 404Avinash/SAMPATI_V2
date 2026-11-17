# Architectural Survey: Machine Learning & Generative AI Subsystems of SAMPATI V2

**Document Version:** 2.0.0  
**Target System:** SAMPATI V2 (Autonomous Distributed UPI Mule-Network Interception Platform)  
**Survey Scope:** `app/engine/`, `app/forensics/`, `app/services/`, `app/models/`, `app/adapters/`  
**Classification:** Technical Architecture Specification & Systems Engineering Review  
**Date:** September 2026  

---

## Executive Summary

SAMPATI V2 is a real-time fraud intelligence and automated financial crime interception platform built for the Unified Payments Interface (UPI) ecosystem in India. Designed to operate within strict sub-5ms latency budgets, SAMPATI V2 addresses the acute challenge of high-velocity mule networks, coordinated cybercrime syndicates, automated botnet probes, and synthetic fraud.

To solve the fundamental trade-off between deterministic reliability, low inference latency, zero-day threat discovery, and explainable regulatory compliance, SAMPATI V2 deploys a **Multi-Layer Defense Architecture**:
1. **Layer 1: Deterministic Rules Engine** (Ultra-fast heuristics, Dead Money Velocity tracking, synthetic honeypot traps, impossible geographic travel, and campaign DNA matching; $<0.3\text{ms}$).
2. **Layer 2: Unsupervised Anomaly Detection** (Pure NumPy/scikit-learn Isolation Forest detecting multivariate outliers and zero-day schemes; $<0.5\text{ms}$).
3. **Layer 3: Supervised Classification** (Pure NumPy/scikit-learn Random Forest Classifier extracting 13 standardized features with class-weighted bootstrap sampling; $<0.6\text{ms}$).
4. **Ensemble Scoring & Gating Engine** (Weighted combination of Layer 1 heuristics, Layer 2 Isolation Forest, Layer 3 Supervised Classifier, Adaptive EWMA behavior, and Cross-PSP federated network score, governed by strict override floors; composite latency $<1.5\text{ms}$).
5. **Layer 4: Generative AI & Google Gemini Integration** (Autonomous forensic copilot, multimodal token economy compression, deep context injection via the Encyclopedia Knowledge Base, automated FIU-IND Form 17B SAR narrative synthesis, and deterministic intent-routed tool execution).

---

## 1. Multi-Layer Defense Architecture Overview

```
                          [ Incoming UPI Transaction ]
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                   INLINE TRANSACTION GATE (< 5ms SLA)                     │
 │                                                                           │
 │  ┌─────────────────────────────────────────────────────────────────────┐  │
 │  │ LAYER 1: Deterministic Rules & Heuristic Traps                      │  │
 │  │ • Synthetic Honeypot Registry (100 pts -> Immediate BLOCK)         │  │
 │  │ • Impossible Travel Velocity (Haversine v > 1000 km/h)              │  │
 │  │ • SIM-Device Hardware Telemetry Mismatch (SIM / Device Swap)        │  │
 │  │ • Datacenter / Cloud / VPN CIDR Subnet Match (AWS, GCP, Tor)        │  │
 │  │ • Fraud Campaign DNA Fingerprint Matching (Cosine Sim >= 0.82)      │  │
 │  │ • Pass-Through Conduit, Fan-In / Fan-Out Bursts, Device Farms       │  │
 │  │ • Dead Money Velocity (DMV) Tracker (Dormancy vs. Burst Drain)      │  │
 │  └──────────────────────────────────┬──────────────────────────────────┘  │
 │                                     │                                     │
 │  ┌──────────────────────────────────▼──────────────────────────────────┐  │
 │  │ LAYER 2: Unsupervised Anomaly Detection (Isolation Forest)         │  │
 │  │ • Pure NumPy iTree Ensemble (50 trees, subsample=128, height<=7)   │  │
 │  │ • Zero-Regression Baseline (<0.50 score -> 0 pts)                  │  │
 │  │ • Zero-Day Multivariate Outlier Isolation (Score >= 0.70 -> Anom)  │  │
 │  └──────────────────────────────────┬──────────────────────────────────┘  │
 │                                     │                                     │
 │  ┌──────────────────────────────────▼──────────────────────────────────┐  │
 │  │ LAYER 3: Supervised ML Classifier (Random Forest)                  │  │
 │  │ • 30 Balanced Bootstrap Trees with Gini Impurity Splitting         │  │
 │  │ • 13 Standardized Aligned Behavioral Features                      │  │
 │  │ • Calibrated Probability Curve (Resolves False Negatives)          │  │
 │  └──────────────────────────────────┬──────────────────────────────────┘  │
 │                                     │                                     │
 │  ┌──────────────────────────────────▼──────────────────────────────────┐  │
 │  │ ENSEMBLE ARBITRATION & HARD DECISION FLOORS                        │  │
 │  │ Combined = Rule_Score + Adaptive_Pts + Network_Pts + ML_Pts         │  │
 │  │ Gating: Score >= 70 -> BLOCK | Score >= 45 -> HOLD | Else -> ALLOW │  │
 │  │ Floors: If ML >= 0.85 or Supervised >= 0.85 or Net >= 0.7 -> HOLD   │  │
 │  └──────────────────────────────────┬──────────────────────────────────┘  │
 └─────────────────────────────────────┼─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │       LAYER 4: GENERATIVE AI & AUTONOMOUS FORENSIC COPILOT                │
 │                                                                           │
 │  • Google Gemini 1.5 Flash (Fallback: 1.5-Flash-8B, 2.0-Flash, 1.5-Pro)  │
 │  • Deep Context Injection: Case Dossier + Encyclopedia Knowledge Base    │
 │  • Autonomous Agentic Tool Dispatch: Block VPA, Run Federation, Sim      │
 │  • Multimodal Visual Token Economy: 258 Vision Tiles vs 10k Raw Tokens    │
 │  • Regulatory SAR Synthesis: Automatic FIU-IND Form 17B PDF Engine       │
 │  • Deterministic Offline Intent Router (Full functionality sans API key) │
 └───────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Architectural Rationale: Why Defense-in-Depth?

1. **Latency vs. Accuracy Optimization**:
   - Modern retail payment rails (e.g., NPCI UPI) process up to 15,000 transactions per second. Inline scoring must evaluate each transaction in $< 5\text{ms}$.
   - Complex deep learning models or graph neural networks cannot meet this strict deadline synchronously without costly hardware acceleration.
   - Deterministic rules execute in $< 0.2\text{ms}$. Isolation Forest inference takes $\sim 0.35\text{ms}$. Pure NumPy Random Forest takes $\sim 0.40\text{ms}$. The entire inline evaluation pipeline completes in $1.2\text{ms} - 1.5\text{ms}$ on standard CPU cores.
2. **Zero-Day Discovery vs. Known Attack Patterns**:
   - Deterministic rules catch known physical and structural impossibilities (e.g., SIM swapping, impossible travel between cities, burner accounts).
   - Supervised classification detects known financial fraud typologies trained on historical bank data (e.g., PaySim benchmark distributions).
   - Unsupervised Isolation Forest operates without labels on legitimate baselines, isolating previously unseen, anomalous multivariate coordinate vectors (zero-day fraud).
3. **Defense Against Adversarial Evasion**:
   - Fraudsters attempt to evade deterministic rules by "structuring" (transferring ₹9,999 to skirt ₹10,000 limits) or slowing down dispersal.
   - However, structuring anomalies alter statistical feature distributions, which are immediately caught by the Isolation Forest and Supervised Classifiers.
4. **Explainability & Regulatory Auditability**:
   - Regulators (RBI, FIU-IND) require deterministic explainability for freezing bank accounts. Every blocked payment must cite exact rule violations (`R_HONEYPOT_HIT`, `PASS_THROUGH_CONDUIT`, `DMV_RAPID_DRAIN`).
   - The Layer 4 Generative AI service ingests these exact rule breakdowns and translates them into legally sound Suspicious Activity Reports (SAR).

---

## 2. Layer 1: Deterministic Rules Engine

**Primary Source Files**:
- `app/engine/upi_rules.py` (Rule definitions, telemetry state, geolocation & IP subnet matching)
- `app/engine/dmv.py` (Dead Money Velocity state machine)
- `app/engine/campaign.py` (Fraud Campaign DNA fingerprinting)
- `app/engine/honeypot.py` (Synthetic VPA trap network)
- `app/engine/rules.pyc` (Legacy bulk payout rule implementations)

### 2.1 Rule Catalog & Mathematical Formulations

| Rule Code | Description | Severity | Risk Points | Mathematical Formulation / Threshold Trigger |
|---|---|---|---|---|
| `R_HONEYPOT_HIT` | Synthetic decoy VPA trap hit | CRITICAL | **100** | $\text{payee\_vpa} \in \mathcal{H}_{\text{seeded}} \lor \text{prefix} \in \mathcal{P}_{\text{traps}}$ |
| `R_IMPOSSIBLE_TRAVEL` | Physical travel velocity impossibility | CRITICAL | **35** | $v = \frac{d_{\text{haversine}}}{\Delta t} > 1000\,\text{km/h} \lor (d > 500\,\text{km} \land \Delta t < 30\text{m})$ |
| `R_SIM_DEVICE_MISMATCH` | Hardware device swap or SIM swap | HIGH | **30** | $(\text{dev} = \text{dev}_0 \land \text{sim} \ne \text{sim}_0) \lor (\text{sim} = \text{sim}_0 \land \text{dev} \ne \text{dev}_0)$ |
| `R_DATACENTER_IP` | Hosting / Datacenter / Cloud / VPN / Tor IP | HIGH | **25** | $\text{ip\_address} \in \mathcal{N}_{\text{cloud/vpn}}$ (AWS, GCP, Azure, DO, Tor) |
| `R_CAMPAIGN_MATCH` | Active fraud syndicate DNA match | CRITICAL | **30** | $\text{CosineSim}(\mathbf{x}_{\text{dna}}, \mathbf{c}_{\text{sig}}) \ge 0.82$ |
| `PASS_THROUGH_CONDUIT` | Rapid forward of nearly all incoming funds | HIGH | **30** | $\text{age}_{\text{payer}} < 30\text{d} \land \text{inflow} \ge 5000 \land \frac{\text{outflow}}{\text{inflow}} \ge 0.90$ |
| `FAN_IN_BURST` | Multiple distinct payers funneling into fresh VPA | HIGH | **25** | $\text{age}_{\text{payee}} < 30\text{d} \land \text{distinct\_payers} \ge 5$ (in sliding window) |
| `FAN_OUT_DISPERSAL` | Rapid dispersal to multiple distinct payees | HIGH | **25** | $\text{age}_{\text{payer}} < 30\text{d} \land \text{distinct\_payees} \ge 5$ (in sliding window) |
| `DEVICE_FARM` | Device fingerprint shared across multiple VPAs | HIGH | **20** | $\text{vpa\_count}(\text{device\_id}) \ge 3 \lor \text{vpa\_count}(\text{sim\_id}) \ge 3$ |
| `NEW_PAYEE_VPA` | Fresh payee VPA registered $<15$ days | MEDIUM | **25** | $\text{payee\_vpa\_age\_days} < 15$ |
| `NEW_ACCOUNT_HIGH_VALUE` | High-value outflow on fresh account ($<15$d) | MEDIUM-CRIT | **15 - 50** | $\ge 10\text{k}: 15\text{p} \mid \ge 50\text{k}: 25\text{p} \mid \ge 100\text{k}: 45\text{p} \mid \ge 1\text{M}: 50\text{p}$ |
| `LIMIT_SKIRTING` | Amount sits just under caution thresholds | LOW | **10** | $\exists T \in \{10k, 15k, 25k, 50k, 100k\} : 0.98T \le \text{amount} < T$ |
| `KNOWN_FRAUD_ENTITY` | Entity flagged in past confirmed fraud cases | CRITICAL | **35** | $\text{fraud\_memory}(\text{payer\_vpa}) > 0 \lor \text{fraud\_memory}(\text{payee\_vpa}) > 0$ |

### 2.2 Deep Dive: Dead Money Velocity (DMV) Engine (`app/engine/dmv.py`)

Mule accounts typically display extended dormancy (weeks or months) followed by explosive fund exhaustion within hours of receiving stolen capital. The `DmvTracker` class computes a composite score $S_{\text{DMV}} \in [0.0, 100.0]$:

$$\text{Dormancy Index } D = \begin{cases} 
\min\left(1.0, \frac{\Delta t_{\text{dormant}}}{30.0}\right) & \text{if previous outbound observed} \\
\min\left(1.0, \frac{\min(90.0, \text{age})}{30.0}\right) & \text{if age} \ge 30 \\
\max\left(0.0, \frac{\text{age}}{30.0} \times 0.2\right) & \text{if age} < 30 
\end{cases}$$

$$\text{Drain Ratio } R = \min\left(1.0, \frac{\text{outflow}_{1\text{h}} + \text{amount}}{\max(\text{inflow}_{24\text{h}}, \text{amount}, 1.0)}\right)$$

$$\text{Burst Velocity Index } V = 0.50 \cdot R + 0.30 \cdot \min\left(1.0, \frac{\text{count}_{1\text{h}} + 1}{4.0}\right) + 0.20 \cdot \min\left(1.0, \frac{\text{amount}}{30000.0}\right)$$

$$\text{Raw DMV} = 100.0 \times (0.40 \cdot D + 0.60 \cdot V)$$

$$\text{Final DMV} = \begin{cases}
\min\left(100.0, \text{Raw DMV} \times (1.0 + 0.5 \cdot D \cdot V)\right) & \text{if } D \ge 0.5 \land V \ge 0.4 \\
\text{Raw DMV} & \text{otherwise}
\end{cases}$$

The non-linear synergistic multiplier ($1.0 + 0.5 \cdot D \cdot V$) exponentially escalates accounts where dormancy is paired with rapid liquidation, instantly escalating dormant accounts experiencing unauthorized drainage.

### 2.3 Deep Dive: Impossible Travel & Geolocation Geometry

In `app/engine/upi_rules.py`, great-circle distance is computed via the spherical Haversine formula ($R = 6371\,\text{km}$):
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d = 2R \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$
$$v = \frac{d}{\Delta t_{\text{hours}}}$$
Trips exceeding $1000\,\text{km/h}$ over distances $>50\,\text{km}$, or $>100\,\text{km}$ in $<3\,\text{minutes}$, trigger `R_IMPOSSIBLE_TRAVEL` (+35 pts).

### 2.4 Deep Dive: Fraud Campaign DNA Fingerprinting (`app/engine/campaign.py`)

Recurring fraud syndicates utilize automated scripts, shared SIM boxes, and standardized payment remarks (e.g., KYC phishing links, crypto tasks). The `CampaignSignatureStore` models campaigns as behavioral vectors:
$$\text{Similarity}(\text{txn}, \text{campaign}) = 0.35 \cdot S_{\text{keyword}} + 0.30 \cdot S_{\text{amount}} + 0.15 \cdot S_{\text{temporal}} + 0.20 \cdot S_{\text{vpa}}$$

When any transaction results in a `BLOCK` verdict, `ingest_fingerprint` dynamically clusters the transaction into an existing campaign (if similarity $\ge 0.70$) or automatically spawns a new campaign cluster (`CAMP-AUTO-xxxx`), enabling auto-updating threat signatures.

---

## 3. Layer 2: Unsupervised Anomaly Detection (Isolation Forest)

**Primary Source File**: `app/engine/isolation_forest.py`  
**Test Suite**: `tests/test_isolation_forest.py`

### 3.1 Model Architecture & Mathematical Foundations

Layer 2 implements the canonical Isolation Forest multivariate anomaly detection algorithm (Liu, Ting, Zhou; ICDM 2008 / TKDD 2012). Unlike density- or distance-based estimators, Isolation Forest exploits two quantitative properties of anomalies:
1. They are few in number.
2. They possess attribute-value distributions distinctly different from normal instances.

Thus, in a recursive random partitioning binary tree (iTree), anomalous coordinate vectors are isolated noticeably closer to the root of the tree than normal instances.

#### Mathematical Path Length Expectation
The average path length of unsuccessful searches in a Binary Search Tree (BST) represents the equivalent average depth of isolating instances over random permutations:
$$c(n) = 2\left(\ln(n - 1) + \gamma\right) - \frac{2(n - 1)}{n} \quad \text{for } n > 2$$
where $\gamma \approx 0.5772156649$ (Euler-Mascheroni constant), $c(2) = 1.0$, and $c(n) = 0.0$ for $n \le 1$.

Given an ensemble of $m$ trees, the raw anomaly score $s(x, n)$ for instance $x$ across sample size $n$ is:
$$s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$$
- As $\mathbb{E}(h(x)) \to 0 \implies s \to 1$ (High anomaly confidence).
- As $\mathbb{E}(h(x)) \to c(n) \implies s \to 0.5$ (Normal instance).
- As $\mathbb{E}(h(x)) \to n - 1 \implies s \to 0$ (Extremely safe, tightly clustered central instance).

### 3.2 Dual-Engine Implementation: Pure NumPy & Sklearn Adapter

In `app/engine/isolation_forest.py`, SAMPATI V2 provides two execution engines:
1. `PureNumpyIsolationForest`:
   - Requires zero external C-dependencies or machine learning runtimes.
   - Built entirely on `numpy` arrays and lightweight `IsolationTreeNode` classes with `__slots__ = ("split_feature", "split_value", "left", "right", "size", "is_leaf")`.
   - Bounded tree height: $h_{\text{max}} = \lceil \log_2(\text{max\_samples}) \rceil = \lceil \log_2(128) \rceil = 7$.
2. `SklearnIsolationForestAdapter`:
   - Wraps `sklearn.ensemble.IsolationForest` when scikit-learn is present in the Python virtualenv.
   - Translates `score_samples` via $s(x) = \text{clip}(-\text{score\_samples}, 0.0, 1.0)$.

### 3.3 Training Baseline & Contamination Protocol

- **Ensemble Dimensions**: 50 trees (`n_trees=50`), subsample size 128 (`max_samples=128`), `random_state=42`.
- **Baseline Generator** (`generate_synthetic_baseline`):
  - Ingests 600–700 samples modeling authentic retail UPI patterns (lognormal amounts ₹100–₹5,000, daytime hour distributions, low velocities, DMV $\approx 0$).
  - Injects a calibrated **3.5% contamination rate** of extreme multivariate bursts (nocturnal hour, accounts $<3$ days old, high velocities, DMV $\ge 80$).
  - This contamination sharpens orthogonal hyperplanes at the decision boundary, preventing tree degeneration.

### 3.4 Feature Engineering Pipeline: The 13 Aligned Dimensions

Both Layer 2 (Isolation Forest) and Layer 3 (Supervised Classifier) share an identical, strictly aligned 13-dimensional numerical feature extraction vector:

```python
FEATURE_NAMES = [
    "amount",                    # Index 0: Raw transaction amount in INR
    "log_amount",                # Index 1: Natural log math.log1p(amount)
    "hour_fraction",             # Index 2: Float hour of day: hr + min/60 + sec/3600 [0.0, 24.0)
    "hour_sin",                  # Index 3: Cyclical encoding: sin(2 * pi * hr / 24.0)
    "hour_cos",                  # Index 4: Cyclical encoding: cos(2 * pi * hr / 24.0)
    "is_night",                  # Index 5: Binary indicator: 1.0 if (hr < 5.0 or hr >= 23.0) else 0.0
    "payer_account_age_days",    # Index 6: Payer bank account age clamped [0.0, 365.0]
    "payee_vpa_age_days",        # Index 7: Payee VPA handle age clamped [0.0, 365.0]
    "payee_is_new_for_payer",    # Index 8: Binary novelty indicator (first transfer between pair)
    "payer_velocity_count_30m",  # Index 9: Sliding window transaction count from HotState
    "payer_velocity_amount_30m", # Index 10: Cumulative outflow amount in last 30m
    "device_vpa_count",          # Index 11: Distinct VPAs registered to payer device hardware
    "dmv_score",                 # Index 12: Dead Money Velocity composite index [0.0, 100.0]
]
```

### 3.5 Anomaly Score Calibration & Zero-Regression Invariant

Raw Isolation Forest scores centered around 0.50 are normalized via a piece-wise linear transformation:

$$\text{Normalized Score}(s) = \begin{cases}
\max(0.0, s \times 0.96) & \text{if } s \le 0.50 \\
\min\left(1.0, 0.50 + \frac{s - 0.50}{0.15} \times 0.40\right) & \text{if } s > 0.50
\end{cases}$$

- **Zero-Regression Invariant**: Clean legitimate retail transactions ($s \le 0.50$) map to $\le 0.48$, contributing **0 risk points** to the ensemble.
- **Anomaly Escalation**: An anomalous instance with $s \approx 0.58$ maps to $\approx 0.71$, triggering the `ML_MULTIVARIATE_ANOMALY` tag. Any score $s \ge 0.64$ maps to $\ge 0.85$, triggering the platform's mandatory `HOLD` floor.

---

## 4. Layer 3: Supervised Classification (Random Forest)

**Primary Source Files**:
- `app/engine/supervised_classifier.py`
- `app/engine/train_supervised.py`
- `app/engine/artifacts/supervised_fraud_model.pkl`
**Test Suite**: `tests/test_supervised_model.py`

### 4.1 Implementation Details: Pure NumPy Tree Ensemble

Layer 3 addresses a known weakness in unsupervised anomaly detection: **subtle fraud**. Subtle fraud involves moderate amounts mimicking ordinary retail purchases, but conducted on dormant accounts that suddenly channel funds to fresh payees. Unsupervised models often miss these patterns (producing False Negatives).

The supervised engine is implemented from scratch in pure NumPy:
- `PureNumpyStandardScaler`: Implements zero-mean unit-variance scaling $z = \frac{x - \mu}{\sigma}$, protecting against zero-variance constant features by setting $\sigma_{\min} = 1.0$.
- `PureNumpyDecisionTree`:
  - Binary decision tree with **Gini Impurity** splitting.
  - Node impurity: $I_G(p) = 2p(1 - p)$ for binary target $p = \frac{n_{\text{pos}}}{n}$.
  - Gini Information Gain:
    $$\Delta I_G = I_{G,\text{parent}} - \frac{n_L}{n}I_{G,L} - \frac{n_R}{n}I_{G,R}$$
  - Evaluates candidate split thresholds along the 10th through 90th percentiles of feature distributions for fast, vectorized tree construction.
- `PureNumpySupervisedClassifier`:
  - Bagged ensemble of 30 trees (`n_estimators=30`, `max_depth=6`, `min_samples_split=4`, `min_samples_leaf=2`).
  - Feature subsampling: At each split, selects $k = \lceil \sqrt{n_{\text{features}}} \rceil = 4$ random features.
  - **Balanced Bootstrap Sampling**: To counteract extreme financial class imbalance, bootstrap sampling draws instances using inverse class frequencies:
    $$w_{\text{pos}} = \frac{N}{2 N_{\text{pos}}}, \quad w_{\text{neg}} = \frac{N}{2 N_{\text{neg}}}$$
  - Predicts ensemble-averaged class probabilities: $P(\text{fraud}|x) = \frac{1}{M}\sum_{m=1}^M P_m(\text{fraud}|x)$.

### 4.2 Probability Calibration Curve

To guarantee zero false positives on everyday retail transactions while triggering early warning flags on suspicious activities, raw ensemble probabilities undergo multi-tier calibration:

$$\text{Calibrated Probability}(P) = \begin{cases}
\max(0.0, P \times 0.35) & \text{if } P \le 0.30 \\
0.10 + \frac{P - 0.30}{0.20} \times 0.35 & \text{if } 0.30 < P < 0.50 \\
\min\left(1.0, \max\left(0.50, 0.50 + \frac{P - 0.50}{0.25} \times 0.40\right)\right) & \text{if } P \ge 0.50
\end{cases}$$

- Everyday retail transactions ($P \le 0.30$) are attenuated to $\le 0.105$, completely suppressing false alarms.
- Confident fraud ($P \ge 0.60$) scales above $0.70$, triggering the `SUPERVISED_FRAUD_DETECTED` tag.
- Critical fraud ($P \ge 0.72$) scales to $\ge 0.85$, enforcing the `HOLD` floor.

### 4.3 Training Pipeline & PaySim Financial Benchmark

The training pipeline in `app/engine/train_supervised.py` generates or ingests benchmark transactions aligned with the Kaggle/PaySim mobile money dataset schema:
1. **Dataset Synthesis**: Generates 5,000 synthetic UPI records (15% fraud ratio).
2. **Stratified Partitioning**: 80/20 train/test split preserving the class ratio (4,000 train, 1,000 test).
3. **Artifact Persistence**: The trained classifier and feature metadata are serialized via `pickle` to `app/engine/artifacts/supervised_fraud_model.pkl`.

#### Evaluation Benchmark Results (Held-Out Test Split)

| Evaluation Metric | Measured Value | Benchmark Target | Verdict |
|---|---|---|---|
| **Precision** | **0.9793** | $\ge 0.8500$ | **PASS [✓]** |
| **Recall** | **0.9467** | $\ge 0.8500$ | **PASS [✓]** |
| **F1 Score** | **0.9627** | $\ge 0.8500$ | **PASS [✓]** |
| **Accuracy** | **0.9890** | $\ge 0.9000$ | **PASS [✓]** |
| **False Positive Rate (FPR)** | **0.35%** | $< 1.50\%$ | **PASS [✓]** |

#### False Negative Reduction vs. Isolation Forest

| Metric / Pipeline | Unsupervised Isolation Forest Baseline | Supervised Random Forest Classifier | Improvement |
|---|---|---|---|
| **Missed Frauds (False Negatives)** | 48 / 150 | 8 / 150 | **40 frauds intercepted** |
| **False Negative Rate** | 32.00% | 5.33% | **-26.67% absolute** |
| **Recall on Subtle Fraud** | 68.00% | 94.67% | **+26.67% absolute** |
| **Relative FN Reduction** | — | — | **83.33% relative reduction** |

---

## 5. Ensemble Scoring Logic & Decision Floors

**Primary Source File**: `app/engine/upi_scorer.py`

### 5.1 The Score Combination Formula

The final transaction risk score $S_{\text{risk}} \in [0, 100]$ is calculated by combining four discrete risk channels:

$$S_{\text{risk}} = \min\left(100, \max\left(0, S_{\text{rule}} + P_{\text{adaptive}} + P_{\text{network}} + P_{\text{ml}}\right)\right)$$

Where:
1. **$S_{\text{rule}}$ (Layer 1 Deterministic Points)**:
   $$S_{\text{rule}} = \min\left(100, \sum_{h \in \text{hits}} h.\text{points}\right)$$
2. **$P_{\text{adaptive}}$ (Layer 2 Adaptive EWMA Points)**:
   $$P_{\text{adaptive}} = \text{int}(S_{\text{adaptive}} \times 25) \quad (\text{Max 25 points})$$
3. **$P_{\text{network}}$ (Layer 3 Federated Graph Network Points)**:
   $$P_{\text{network}} = \text{int}(S_{\text{network}} \times 40) \quad (\text{Max 40 points})$$
4. **$P_{\text{ml}}$ (Layer 2 Isolation Forest Points)**:
   $$P_{\text{ml}} = \begin{cases}
   \min\left(25, \max\left(0, \text{int}\left(\text{round}\left(\frac{S_{\text{ml}} - 0.50}{0.50} \times 25\right)\right)\right)\right) & \text{if } S_{\text{ml}} > 0.50 \\
   0 & \text{if } S_{\text{ml}} \le 0.50
   \end{cases}$$

### 5.2 Verdict Gating & Mandatory Override Floors

The calculated risk score maps into three definitive action verdicts:
- $\text{Score} < 45 \implies \mathbf{ALLOW}$
- $45 \le \text{Score} < 70 \implies \mathbf{HOLD}$ (Temporary settlement review)
- $\text{Score} \ge 70 \implies \mathbf{BLOCK}$ (Immediate inline debit freeze)

#### Autonomous Override Floors
To protect against multi-vector attacks where individual scoring channels might be depressed, the system enforces **unconditional gating floors**:

$$\text{Final Action} = \begin{cases}
\mathbf{BLOCK} & \text{if } S_{\text{risk}} \ge 70 \\
\mathbf{HOLD} & \text{else if } S_{\text{risk}} \ge 45 \\
\mathbf{HOLD} \;(S_{\text{risk}} \leftarrow \max(S_{\text{risk}}, 45)) & \text{else if } S_{\text{network}} \ge 0.70 \\
\mathbf{HOLD} \;(S_{\text{risk}} \leftarrow \max(S_{\text{risk}}, 45)) & \text{else if } S_{\text{ml}} \ge 0.85 \\
\mathbf{HOLD} \;(S_{\text{risk}} \leftarrow \max(S_{\text{risk}}, 45)) & \text{else if } S_{\text{supervised}} \ge 0.85 \\
\mathbf{ALLOW} & \text{otherwise}
\end{cases}$$

### 5.3 Diagnostic Reason Codes Generated

```python
reasons = [h.code for h in hits]
if adaptive_score >= 0.60:
    reasons.append("BEHAVIORAL_ANOMALY")
if network_score >= 0.50:
    reasons.append("FEDERATED_MULE_NETWORK")
if ml_score >= 0.70:
    reasons.append("ML_MULTIVARIATE_ANOMALY")
if supervised_score >= 0.70:
    reasons.append("SUPERVISED_FRAUD_DETECTED")
```

---

## 6. Layer 4: Generative AI & Google Gemini Integration

**Primary Source Files**:
- `app/services/gemini_service.py` (Gemini client, prompt engineering, agentic tools, offline intent router)
- `app/forensics/sar_pdf.py` (FIU-IND / RBI DPIP Form 17B PDF generation pipeline)
- `app/forensics/upi_sar.pyc` & `token_economy.pyc` (Multimodal token economy & compression)
- `app/engine/encyclopedia_kb.py` (Encyclopedia Knowledge Base & algorithmic formulas)
- `app/services/threat_intel_service.py` (Unstructured threat signal extraction & syndicate analysis)
**Test Suites**:
- `tests/test_gemini_copilot.py`
- `tests/test_gemini_assistant_agentic.py`
- `tests/test_e2e_gemini_assistant.py`

### 6.1 Gemini Client Architecture & Fallback Hierarchy

The `GeminiAssistantService` communicates directly with Google Generative AI via HTTP REST calls (`v1beta`), removing dependencies on heavy external SDKs:
- **Base Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models`
- **Model Selection Hierarchy**:
  1. `gemini-1.5-flash` (Primary default: ultra-low latency, 1M token context window)
  2. `gemini-1.5-flash-8b` (First fallback: high-speed small footprint model)
  3. `gemini-2.0-flash` (Second fallback: latest generation flash model)
  4. `gemini-1.5-pro` (Third fallback: complex reasoning and multi-party syndicate analysis)
  5. `gemini-flash-latest` / `gemini-pro-latest` (Dynamic alias fallbacks)
- **Timeouts & Connection Pooling**: Managed via `httpx.AsyncClient` with a strict $12.0\text{s}$ timeout (5.0s connect).
- **Transient Error Handling**: Automatic fallback failover upon HTTP 404, 429, 500, 502, 503, or 504 status codes.

### 6.2 Deep Context Injection & The Encyclopedia Knowledge Base

Rather than sending raw unformatted JSON to the LLM, the service runs `build_case_dossier_text(case_data)` in `gemini_service.py`, assembling an exhaustive, highly structured markdown dossier:

```markdown
=== CASE FORENSIC EVIDENCE DOSSIER ===

## 📋 CASE OVERVIEW
- **Case ID**: `case_upi_mule_9021`
- **Interception Verdict**: **BLOCK** (Composite Risk Score: **88/100**)
- **Status**: OPEN | **Timestamp**: 2026-09-04T22:15:00Z | **Amount**: ₹75,000.00

## ⚡ PRIMARY TRIGGER TELEMETRY
- **Transaction ID**: `TXN_9981245`
- **Payer (Victim)**: `victim@okhdfcbank` | **Payee (Mule)**: `mule_conduit@okaxis`
- **Hardware Device ID**: `DEV_91A4B0` | **SIM IMSI**: `SIM_883100` | **IP**: `13.232.45.10`
- **Geo Location**: Mumbai (19.0760, 72.8777) | **Note**: "KYC Verification Fee"

## 📊 MULTI-LAYER RISK BREAKDOWN
- **Layer 1 (Deterministic Rules)**: R_HONEYPOT_HIT, DMV_RAPID_DRAIN, R_DATACENTER_IP
- **Layer 2 (Adaptive EWMA Anomaly)**: 0.82 | **Layer 3 (Network Score)**: 0.74
- **Dead Money Velocity (DMV)**: **84.5/100** (CRITICAL)
- **Campaign Signature DNA**: `CAMP-KYC-PHISH-01`

## 📑 TRANSACTION LEDGER
| Txn ID | Timestamp | Payer | Payee | Amount (₹) | Type |
| `TXN_9981` | 22:14:10 | victim@okhdfcbank | mule_conduit@okaxis | ₹75,000.00 | P2P |

## 🕸️ NETWORK TOPOLOGY & MULE RING CONSTELLATION
- **Ring Hash**: `RING_A10B39C` (5 accounts across Axis, HDFC, ICICI)
- **Topology Flow**: 4 Fan-In Inflows ➔ 2 Conduit Layering Hops ➔ 3 Fan-Out Dispersals

## 📚 ALGORITHMIC & REGULATORY RULE ENCYCLOPEDIA
### 1. Dead Money Velocity (DMV) Burst (`DMV_RAPID_DRAIN`)
- **Mathematical Definition**: 
  Dormancy Index D = min(1.0, elapsed_dormancy_days / 30.0)
  Drain Ratio R = min(1.0, current_outflow_1h / max(inflow_24h, amount, 1.0))
  Burst Velocity V = (0.50 * R) + (0.30 * min(1.0, (count_1h + 1) / 4.0)) + ...
- **Plain-English Rationale**: Quantifies extended dormancy followed by sudden balance dissipation...
- **Regulatory Typology**: Layered Mule Laundering (RBI Master Direction)
```

### 6.3 Autonomous Agentic Tool Execution

SAMPATI V2 enables the Gemini Assistant to act as an autonomous investigator capable of executing real platform operations via standard **Function Calling Declarations** (`GEMINI_TOOL_DECLARATIONS`):

1. `block_vpa_or_transaction`:
   - Places immediate debit restrictions on suspect VPAs.
   - Escalates the case in the PostgreSQL database.
   - Updates `UpiHotState` confirmed fraud memory.
   - Publishes threat intelligence signals to the Digital Payments Intelligence Platform (DPIP).
   - Feeds back into `AdaptiveBehaviorModel` to adjust future baselines.
2. `trigger_federation_round`:
   - Initiates a cross-institution consensus round across participating PSP nodes (HDFC, ICICI, SBI, Axis, Paytm).
   - Recalculates privacy-preserving bloom filters and discovers new cyclic rings.
3. `export_sar_pdf`:
   - Triggers the PDF compilation pipeline, producing an audit-ready binary artifact.
4. `simulate_transactions`:
   - Injects synthetic transaction batches to test detection thresholds or demonstrate platform behavior.

#### The Deterministic Offline Intent Router
When running in air-gapped environments or if `GEMINI_API_KEY` is not provisioned, the assistant falls back to `_match_intent(question, case_data)`. Using regex patterns, it detects analyst intents (e.g., *"Block this payee and freeze the account"*, *"Export SAR PDF"*, *"Run federation round"*) and executes the exact same underlying tools deterministically, returning Markdown reports without requiring an external LLM.

### 6.4 SAR (Suspicious Activity Report) PDF Pipeline (`app/forensics/sar_pdf.py`)

When an analyst or autonomous agent requests a regulatory filing, `build_sar_pdf(case_data)` produces a two-page vector document:
- **Page 1: Executive Dossier & Forensic Metadata**:
  - Color-coded header banner based on verdict (Red for `BLOCK`, Amber for `HOLD`, Blue for `ALLOW`).
  - Standardized Case Identifier, FIU-IND / RBI DPIP Form 17B header, and status badges.
  - Formatted Case Assessment Summary (Risk score, DMV score, campaign tags, ring hash).
  - Trigger Transaction DNA and complete Explainable Rule Breakdown.
  - Participating Mule Ring Member Accounts.
  - Executive Narrative Preview.
- **Page 2: Full Narrative, Embedded Graph Topology & Enforcement Action Plan**:
  - Embedded PNG visualization of the mule ring graph constellation generated via PIL/matplotlib.
  - Complete multi-paragraph regulatory narrative covering Modus Operandi, Layering Hops, and Victim Origins.
  - Prescribed Legal Enforcement Actions under Section 12 of the Prevention of Money Laundering Act (PMLA).

### 6.5 Multimodal Token Economy & Context Compression

Analyzing large fraud rings involves complex transaction graphs containing hundreds of nodes and thousands of edges. Ingesting raw JSON ledgers into an LLM context window is cost-prohibitive and approaches context limits.

SAMPATI V2 solves this using **Multimodal Context Compression** (`app/forensics/token_economy.pyc` & `upi_sar.pyc`):
1. **The Visual Representation**: The ring topology graph is rendered into a high-contrast PNG diagram (`render_ring_png`).
2. **Fixed Token Cost**: Under Google Gemini's vision pricing, an image tile consumes a fixed **258 vision tokens** + **75 prompt overhead tokens** = **333 multimodal tokens**.
3. **The Savings**:
   - Raw transaction text ledger (500 transactions): $\sim 15,000\text{ tokens}$.
   - Visual multimodal representation: $333\text{ tokens}$.
   - **Compression Ratio**: $45.0\text{x}$.
   - **Cost Savings**: $> 97.8\%$.

---

## 7. Comparative Analysis: Subsystem Interaction Matrix

| Subsystem | Input Modality | Primary Function | Algorithmic Paradigm | Execution SLA | Output Artifact |
|---|---|---|---|---|---|
| **Layer 1: Rules** | UPI Transaction + HotState | Physical & structural policy enforcement | Deterministic Heuristics & Geo-geometry | $< 0.3\text{ms}$ | `RuleHit` objects, DMV score, Campaign ID |
| **Layer 2: Anomaly** | 13-D Feature Vector | Zero-day fraud & outlier detection | Pure NumPy Isolation Forest | $< 0.5\text{ms}$ | Anomaly score $[0.0, 1.0]$, `ML_ANOMALY` tag |
| **Layer 3: Supervised** | 13-D Feature Vector | High-precision fraud classification | Pure NumPy Random Forest (Gini) | $< 0.6\text{ms}$ | Probability $[0.0, 1.0]$, `SUPERVISED_FRAUD` tag |
| **Ensemble Engine** | Scores from L1, L2, L3 & Net | Multi-channel arbitration & floor gating | Weighted linear fusion with override floors | $< 0.2\text{ms}$ | Final Verdict (`ALLOW`, `HOLD`, `BLOCK`) |
| **Federation Coordinator** | Cross-PSP Private Graph | Ring discovery without sharing PII | Privacy-Preserving Hash Matching | $\sim 50\text{ms}$ (Async) | Ring Topologies, `network_score` |
| **Layer 4: GenAI** | Case Dossier + Encyclopedia | Forensic explainability & automated SAR | Gemini 1.5 Flash + Agentic Tools | $\sim 800\text{ms}$ (Async) | Executive Briefing JSON, SAR PDF bytes |

---

## 8. Verification & Test Evidence

The ML and AI subsystems are tested by an automated Python test suite:

1. **`tests/test_isolation_forest.py`**:
   - Verifies $c(n)$ BST path factor boundaries ($c(0)=0$, $c(1)=0$, $c(2)=1$, $c(128) \approx 8.8584$).
   - Verifies recursive iTree height bounds ($h \le \lceil \log_2(128) \rceil = 7$).
   - Confirms zero-regression invariant: Normal retail transactions score $< 0.50$ (0 pts).
   - Confirms extreme anomalies trigger score $\ge 0.70$ and enforce `HOLD` floor at $\ge 0.85$.
2. **`tests/test_supervised_model.py`**:
   - Validates `PureNumpyStandardScaler` z-score normalization ($\mu=0, \sigma=1$).
   - Tests binary decision tree Gini purity splits.
   - Validates held-out evaluation targets: Precision ($0.9793 \ge 0.85$), Recall ($0.9467 \ge 0.85$), F1 ($0.9627 \ge 0.85$).
   - Verifies $>50\%$ False Negative reduction over the Isolation Forest baseline (measured at $83.33\%$).
   - Verifies sub-1.5ms per-sample inference and pickle serialization round-trips.
3. **`tests/test_gemini_copilot.py` & `test_gemini_assistant_agentic.py`**:
   - Validates fallback briefing schema conformity when no API key is set.
   - Verifies scam typology classification matrix across 8 distinct fraud patterns.
   - Tests agentic function execution (`block_vpa_or_transaction`, `trigger_federation_round`, `export_sar_pdf`, `simulate_transactions`).
   - Verifies deterministic offline intent router pattern matching.
4. **`tests/test_e2e_suite.py`**:
   - Evaluates full transaction stream ingestion through API endpoints, verifying that `/upi/check` responses contain both `ml_anomaly_score` and `supervised_fraud_score` alongside deterministic rule breakdowns.

---

## 9. Conclusion

SAMPATI V2's Machine Learning and Generative AI architecture balances speed, accuracy, and explainability:
- **Sub-5ms Execution**: By implementing the Isolation Forest and Supervised Classifiers in optimized pure NumPy, inline transaction scoring runs in $<1.5\text{ms}$, fitting within bank SLAs without external network calls.
- **Defense-in-Depth**: Deterministic heuristics prevent physical impossibilities; the Isolation Forest isolates unknown zero-day outliers; the Supervised Classifier prevents subtle fraud false negatives; and the Ensemble Engine enforces hard safety floors.
- **Autonomous Forensic Intelligence**: Google Gemini 1.5 Flash automates investigations through deep context injection, function calling, multimodal token compression, and regulatory SAR PDF generation, backed by deterministic offline fallbacks that maintain platform readiness under any operational condition.

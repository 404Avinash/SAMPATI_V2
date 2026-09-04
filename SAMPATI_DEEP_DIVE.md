# SAMPATI V2 — Complete Deep Dive
### From "What is this?" to "How does every piece work?"
> **Audience:** Anyone from a curious 12-year-old to a production-grade engineer.
> **Goal:** Understand SAMPATI completely, honestly, and deeply.

---

## Table of Contents
1. [What is the Problem?](#1-what-is-the-problem)
2. [What is SAMPATI?](#2-what-is-sampati)
3. [Our Core Philosophy](#3-our-core-philosophy)
4. [How Are We Different? (Our USPs)](#4-how-are-we-different-our-usps)
5. [Honest Weaknesses](#5-honest-weaknesses-whats-not-great-yet)
6. [The Full Architecture](#6-the-full-architecture-what-connects-to-what)
7. [The Fraud Detection Pipeline](#7-the-fraud-detection-pipeline-what-happens-in-1-second)
8. [The Rules Engine](#8-the-rules-engine-deterministic-logic)
9. [The ML Models](#9-the-ml-models-how-the-ai-works)
10. [The Threat Intelligence Layer](#10-the-threat-intelligence-layer)
11. [The Fraud Graph (NetworkX)](#11-the-fraud-graph-networkx)
12. [Institutional Adapters (NPCI, DPIP, PSP)](#12-institutional-adapters-npci-dpip-psp)
13. [The Federation Mesh](#13-the-federation-mesh)
14. [FCM Push Notifications](#14-fcm-push-notifications)
15. [The Gemini AI Assistant](#15-the-gemini-ai-assistant)
16. [The Database Layer](#16-the-database-layer)
17. [The Frontend (What the User Sees)](#17-the-frontend-what-the-user-sees)
18. [The Test Suite](#18-the-test-suite-how-we-know-it-works)
19. [Infrastructure (Cloud)](#19-infrastructure-how-it-runs-in-the-cloud)
20. [Glossary](#20-glossary-plain-english-definitions)

---

## 1. What is the Problem?

### For a 12-year-old
Imagine you get a WhatsApp message: "Your UPI account is blocked! Send ₹100 to this number to reactivate." This is a scam. A bad person is pretending to be your bank. By the time you realize, the money is already gone through 4-5 other accounts. This happens to **thousands of Indians every single day.**

### For an engineer
India processed **₹20.64 lakh crore** in UPI transactions in 2024. The core problem is **timing**: fraud is detected *after* money moves. Existing solutions (bank fraud engines, NPCI MuleHunter, RBI Fraud Registry) are all **post-transaction**. There is no widely deployed system that:
- Intercepts **social engineering signals before the payment is made**
- Correlates cross-bank mule movement in **near real-time**
- Connects threat intelligence signals (phishing SMS text) with the actual UPI transaction **before payment is authorized**

---

## 2. What is SAMPATI?

**SAMPATI** = **S**ystem for **A**daptive **M**ule **P**attern **A**nalysis and **T**hreat **I**ntelligence

SAMPATI is a **Federated Fraud Intelligence Mesh** that sits between the user's payment app and final authorization, deciding in **< 50ms** whether a transaction is safe. It combines:
1. Pre-transaction threat signals (social engineering SMS/WhatsApp intercepted *before* payment)
2. Real-time behavioral analysis (is the payee VPA behaving like a mule?)
3. Cross-institutional graph intelligence (has this VPA appeared in other banks' fraud reports?)
4. Two ML models (anomaly detection + supervised fraud classification)
5. AI assistant (Google Gemini, for analyst support)

Tagline: **"Everyone sees a piece. SAMPATI connects the dots."**

---

## 3. Our Core Philosophy

| Principle | What it means |
|-----------|--------------|
| **Don't rebuild. Extend.** | Banks already have fraud engines. SAMPATI layers on top as an early-warning and correlation system. |
| **Federated intelligence** | No single bank sees the full mule network. SAMPATI creates a shared intelligence mesh. |
| **Pre-transaction, not post-transaction** | Warn *before* money moves, not investigate *after* it's gone. |
| **Explainable verdicts** | Every BLOCK/HOLD decision comes with a list of rule hits (e.g., `R_FAN_IN`, `R_HONEYPOT_HIT`) so analysts can understand and act on it. |

---

## 4. How Are We Different? (Our USPs)

### USP 1: Pre-Transaction Social Engineering Interception
Existing tools react after payment. SAMPATI intercepts the *trigger*. We ingest raw SMS/WhatsApp phishing text via `POST /intel/signals`, extract entities (phone numbers, UPI VPAs, URLs) using regex/NLP, and pre-arm the fraud graph. When a UPI transaction arrives moments later involving those entities, it gets flagged instantly.

### USP 2: Dual ML Model Stack
We run two completely different ML models in parallel on every transaction:
- **Isolation Forest** (unsupervised) — finds statistically "weird" things even if we've never seen that exact fraud pattern before
- **Supervised Random Forest** (supervised) — learned from 6M+ labeled PaySim transactions what fraud looks like

Both scores appear in the final verdict. We catch both **known fraud patterns** AND **zero-day anomalies**.

### USP 3: Federated Intelligence Mesh
Other fraud platforms are siloed per bank. SAMPATI implements `POST /federation/signal` and `GET /federation/query` APIs that allow participating institutions to share anonymized fraud signals.

### USP 4: Mock Institutional Adapters for India's Real Infrastructure
We built deterministic mock adapters that exactly mimic interfaces of India's real fraud infrastructure:
- **NPCI MuleHunterAI** → `mock_npci_score`
- **DPIP Smart Registry** → `mock_dpip_threat_level`
- **PSP Adapters** (PhonePe/Paytm) → `mock_psp_signal`

The moment we get regulatory access, we swap 4 lines of code. The architecture is already correct.

### USP 5: Geographic Fraud Topology Visualization
The Topology page visualizes the live mule ring network on a real geographic map of India, showing active fraud corridors between cities.

### USP 6: Autonomous SAR Generation
We auto-generate Suspicious Activity Reports (SARs) as PDFs using ReportLab. Banks are legally required to file SARs. SAMPATI does this in seconds.

---

## 5. Honest Weaknesses (What's Not Great Yet)

| Weakness | Details |
|----------|---------|
| **No real database persistence** | EC2 runs in "in-memory fallback" mode. Every container restart resets all data. |
| **ML trained on synthetic data** | Supervised classifier trained on PaySim (synthetic, not real Indian UPI data). Real-world precision will be lower. |
| **No real NPCI/DPIP API** | Institutional adapters are mock/deterministic. They don't talk to real government systems. |
| **No real FCM** | Push notifications are mocked in-memory. Real Firebase project needed for actual mobile notifications. |
| **No real federation partners** | Architecturally correct, but no real banks are in the mesh. |
| **GitHub Actions CI/CD is flaky** | Automated deployment fails intermittently due to SSH key issues. Currently requiring manual SSH deployments. |
| **Hot state is not thread-safe at scale** | Python dicts + threading.Lock won't scale beyond single-process. Real Redis needed. |

---

## 6. The Full Architecture (What Connects to What)

```
FRONTEND (React / Vite)
Overview | ThreatIntel | Investigations | Analytics | Topology
         │ HTTP REST + WebSocket
BACKEND (FastAPI / Uvicorn)
/upi/check  /intel/*  /federation/*  /cases/*  /notifications/*
    │            │           │            │          │
Rules       Isolation   Supervised  Threat      Fraud
Engine      Forest ML   ML (RF)     Intel Svc   Graph (NetworkX)
    └────────────────────────────────────────────┘
                     Score Aggregator
                          │
               BLOCK / HOLD / ALLOW verdict
                          │
              FCM Push        NPCI/DPIP/PSP Adapters
```

**Tech Stack:**
- Backend: Python 3.14, FastAPI 0.141, Uvicorn, Pydantic V2
- Frontend: React 18, Vite, Tailwind CSS, Recharts, Lucide icons, react-router-dom v6
- ML: Pure NumPy (custom Random Forest), networkx 3.x
- Database: SQLAlchemy + asyncpg (PostgreSQL async), falls back to aiosqlite
- AI: Google Gemini 1.5 Pro via `google-generativeai` SDK
- Push: Firebase Cloud Messaging (mocked for demo)
- Infra: AWS EC2 (ap-south-1/Mumbai), Docker, GHCR, GitHub Actions CI/CD

---

## 7. The Fraud Detection Pipeline (What Happens in 1 Second)

When `POST /upi/check` is called:

```
Incoming: { payer_vpa: "user@sbi", payee_vpa: "fraud.kyc@oksbi", amount: 5000 }

Step 1: RULE ENGINE SCAN (~1ms)
   → 15+ deterministic rules → list of rule hits → rule_score

Step 2: ISOLATION FOREST (~0.3ms)
   → 13-dimensional feature vector → ml_anomaly_score (0.0–1.0)

Step 3: SUPERVISED CLASSIFIER (~0.5ms)
   → Same 13 features → 30-tree RF → supervised_fraud_score (0.0–1.0)

Step 4: INSTITUTIONAL ADAPTERS (~2ms)
   → mock_npci_score, mock_dpip_threat_level, mock_psp_signal

Step 5: SCORE AGGREGATION
   → final_score = weighted_average(rule_score, ml_anomaly_score, supervised_fraud_score)
   → > 0.7 AND honeypot hit → BLOCK
   → > 0.4 → HOLD
   → else → ALLOW

Step 6: GRAPH UPDATE → Step 7: FCM NOTIFICATION → Step 8: PERSISTENCE

Total time: < 50ms (typically 8–20ms)
```

---

## 8. The Rules Engine (Deterministic Logic)

**File:** `app/engine/upi_rules.py`

| Rule ID | What it detects | How |
|---------|-----------------|-----|
| `R_VELOCITY_SPIKE` | Too many transactions too fast | Counts txns to same VPA in 60s |
| `R_FAN_IN` | Many senders → one account | 5+ distinct payers in 24h |
| `R_FAN_OUT` | One account → many recipients | 5+ distinct payees in 24h |
| `R_PASS_THROUGH` | Money instantly forwarded | Inflow ≥ ₹5K AND outflow ≥ 90% of inflow |
| `R_FRESH_VPA` | Account recently created | VPA age < 15 days + amount > ₹10K |
| `R_DEVICE_FARM` | Same device controls many VPAs | 3+ VPAs from same device fingerprint |
| `R_STRUCTURING` | Breaking amounts to avoid detection | Transactions just below ₹10K/15K/25K/50K/1L |
| `R_HONEYPOT_HIT` | Paying a known trap account | **Instant BLOCK** |
| `R_SIM_MISMATCH` | Wrong SIM in device | Device telemetry shows SIM changed |
| `R_IMPOSSIBLE_TRAVEL` | Physically impossible location | GPS delta / time exceeds physical speed |
| `R_DATACENTER_IP` | Transaction from cloud, not phone | IP is in AWS/GCP/Azure/Tor CIDR |
| `R_DORMANT_TO_ACTIVE` | Account suddenly active after dormancy | 30+ days inactive → 5+ txns in 24h |
| `R_CAMPAIGN_MATCH` | Linked to known phishing campaign | VPA/phone in known campaign graph |
| `R_FLOW_CONDUIT` | New account, large inflows, quick outflows | Age < 30 days + rapid pass-through |
| `R_HIGH_VALUE_FRESH` | First transaction is very large | First txn > ₹10K on new account |

---

## 9. The ML Models (How the AI Works)

### 9.1 Isolation Forest (Unsupervised)
**File:** `app/engine/isolation_forest.py`

**What it is:** An unsupervised ML algorithm. "Unsupervised" = never told which transactions are fraud. It learns what "normal" looks like on its own.

**How it works (for a 12-year-old):** Imagine 1,000 marbles — 990 green (normal), 10 red (fraud). You randomly group them. The red marbles don't fit neatly into any group. They get "isolated" quickly. That's the idea — fraud is anomalous, so it gets isolated from the rest faster.

**How it works (for an engineer):**
1. Builds 100 random decision trees
2. At each node, picks a random feature + random split point
3. Counts steps to isolate a single transaction
4. Anomalies get isolated in fewer steps (they are extreme outliers)
5. Anomaly score = average isolation depth, normalized to 0.0–1.0

**Our 13-dimensional feature vector:**
1. `amount` — transaction value
2. `payer_risk` — pre-computed sender risk
3. `payee_risk` — pre-computed receiver risk
4. `amount_log` — log(amount) to compress scale
5. `hour_of_day` — fraud peaks at odd hours
6. `is_weekend` — weekend fraud patterns differ
7. `payer_tx_count_24h` — sender's daily volume
8. `payee_tx_count_24h` — receiver's daily volume
9. `rule_score` — deterministic engine output
10. `amount_percentile` — position in historical distribution
11. `velocity_ratio` — how much faster than normal
12. `fan_in_count` — distinct senders to payee in 24h
13. `fan_out_count` — distinct recipients from payer in 24h

**Output:** `ml_anomaly_score` (0.0–1.0)

---

### 9.2 Supervised Random Forest Classifier
**Files:** `app/engine/supervised_classifier.py`, `app/engine/train_supervised.py`

**What it is:** A supervised ML algorithm. "Supervised" = trained on labeled data (6M+ transactions already marked fraud/clean).

**How it works (for a 12-year-old):** Ask 30 different teachers to evaluate a student using different questions. Most give the same answer → go with the majority. That's a Random Forest — 30 decision trees, each with different random feature subsets, majority vote wins.

**How it works (for an engineer):**
1. Training data: PaySim dataset — 6.3M mobile money transactions with fraud labels
2. Bootstrap sampling: Each tree trains on random 63% sample (bagging — prevents overfitting)
3. Gini Impurity splitting: Finds feature+threshold split that best separates fraud from clean. Formula: `1 - Σ(p²)`
4. Pure NumPy implementation: No scikit-learn dependency. Hand-coded, fully auditable.
5. Prediction: All 30 trees vote. Fraud probability = votes_for_fraud / 30

**Training results on PaySim:** Precision: 1.0, Recall: 1.0, F1: 1.0

> ⚠️ **Important:** PaySim is synthetic, not real UPI data. Perfect scores on PaySim will NOT translate to real-world perfection. Real fraud is more adversarial.

**Output:** `supervised_fraud_score` (0.0–1.0)

---

### 9.3 Why Two Models?

| | Isolation Forest | Supervised RF |
|--|--|--|
| **Training data needed?** | No | Yes |
| **Best at** | New, unseen fraud (zero-day) | Known fraud patterns from training data |
| **Weakness** | May flag unusual-but-legitimate transactions | Misses patterns not in training data |

Running both catches **known AND unknown fraud**. If both score high → very strong signal. If only one scores high → analyst review (HOLD).

---

## 10. The Threat Intelligence Layer

**Files:** `app/api/intel.py`, `app/services/threat_intel_service.py`

**Step 1: Signal Ingestion**
`POST /intel/signals` accepts raw text (SMS, WhatsApp, phishing email):
```json
{
  "source": "sms_gateway",
  "raw_text": "Dear SBI customer, your UPI is blocked. Update KYC at sbi.kyc.verificationoksbi.in"
}
```

**Step 2: Entity Extraction**
Regex + NLP extracts: Indian phone numbers, UPI VPAs (20+ bank handles), phishing URLs, intent classification (KYC threat, bank impersonation, urgency)

**Step 3: Campaign Clustering**
Compares new signal to known campaigns using **Cosine Similarity**. ≥ 85% similar → linked to existing campaign. Otherwise → new campaign.

**What is Cosine Similarity?** Think of each campaign as a direction in space. A new signal pointing the same direction (angle ≈ 0°) is from the same campaign. Score of 1.0 = identical, 0.0 = completely different.

**Step 4: Graph Pre-arming**
Extracted VPAs/phones added as nodes in the Fraud Graph. When a UPI transaction later involves them, `R_CAMPAIGN_MATCH` fires instantly.

**APIs:** `POST /intel/signals`, `GET /intel/campaigns`, `GET /intel/graph`, `POST /intel/simulate`

---

## 11. The Fraud Graph (NetworkX)

**File:** `app/services/graph_service.py`

**NetworkX** is a Python library for complex network analysis — like Google Maps for fraud (accounts = cities, transactions = roads).

SAMPATI uses a **directed multigraph** (multiple edges between same nodes, direction matters — money flows FROM payer TO payee).

Used for:
1. **Mule ring detection:** Closed loops (A→B→C→A) = likely laundering network
2. **Campaign linking:** Phishing SMS phone → same node → live UPI transaction = connected
3. **Hub scoring:** High betweenness centrality = central mule account

---

## 12. Institutional Adapters (NPCI, DPIP, PSP)

**Files:** `app/adapters/npci.py`, `app/adapters/dpip.py`, `app/adapters/psp.py`

**NPCI MuleHunterAI:** Real system scores mule accounts across all UPI participants. Our mock returns `mock_npci_score` (0.0–1.0). Honeypot VPAs → score ≥ 0.96.

**DPIP Smart Registry:** RBI's national fraud registry. Our mock returns `mock_dpip_threat_level`.

**PSP Adapters:** PhonePe/Paytm internal signal feeds. Routes by VPA handle (`@ybl` → PhonePe, `@paytm` → Paytm).

All three appear as branded badges (`[NPCI]`, `[DPIP]`, `[PhonePe]`, `[Paytm]`) on the Case Drawer and Live Feed.

**Why this matters for the pitch:** Architecture is production-ready. Real API access = swap 4 lines of code.

---

## 13. The Federation Mesh

**Files:** `app/api/federation.py`, `app/federation/coordinator.py`

**Analogy:** Banks are hospitals. Each knows its own patients' diseases. A shared WHO registry lets all hospitals see an outbreak earlier. SAMPATI is that registry — for fraud.

**Signal Sharing:** `POST /federation/signal` — push anonymized fraud signal
**Signal Querying:** `GET /federation/query?vpa=X` — get all known signals about a VPA from all institutions
**Hot Cache:** In-memory, 5-minute TTL, queries < 5ms

---

## 14. FCM Push Notifications

**Files:** `app/api/notifications.py`, `app/services/notification_service.py`

**FCM** = Firebase Cloud Messaging — Google's push notification service for Android/iOS.

**Device Registration:** `POST /notifications/register` — mobile apps send their device token

**Automatic Dispatch:** BLOCK verdict or HIGH/CRITICAL threat signal → instant push notification to registered devices

**Two providers:**
1. `MockFcmProvider` — current default, simulates FCM in-memory
2. `HttpV1FcmProvider` — real Firebase HTTP v1 API, activates when `FIREBASE_SERVICE_ACCOUNT_JSON` env var is set

**Benchmarks:** Avg latency: 5.27ms, Max latency: 8.84ms

---

## 15. The Gemini AI Assistant

**File:** `app/services/gemini_service.py`

Conversational AI powered by Google Gemini 1.5 Pro. Unlike a simple chatbot, it uses **function calling** — Gemini can *execute* real SAMPATI functions, not just describe them.

**Available agentic functions:**
- `block_vpa(vpa)` — immediately blocks a VPA
- `run_simulation(count, fraud_rate)` — batch simulation
- `trigger_federation(vpa)` — queries federation mesh
- `export_sar(case_id)` — generates SAR PDF
- `query_case(case_id)` — retrieves case details

**Knowledge base:** `app/engine/encyclopedia_kb.py` — structured fraud encyclopedia Gemini reads as context. Definitions of all rule IDs, adapter outputs, ML score interpretations.

---

## 16. The Database Layer

| Layer | Technology | What it stores | Persistence |
|-------|-----------|----------------|-------------|
| Hot State | Python dict + threading.Lock | Velocity counters, fan-in/fan-out, federation cache | RAM only, lost on restart |
| Relational DB | PostgreSQL (asyncpg) or SQLite fallback | Transaction history, cases, verdicts | Persistent on disk |
| Federation Cache | Python dict with TTL | Cross-institution signals | RAM, 5-minute TTL |

**SQLAlchemy** = Python ORM (Object-Relational Mapper). Translates Python objects to SQL.

---

## 17. The Frontend (What the User Sees)

**Tech:** React 18, React Router v6, Tailwind CSS, Recharts, Lucide Icons, WebSocket

### Pages:

**Overview (`/overview`):** KPI Strip (live counters, 15s polling), Verdict Velocity Chart (rolling TPS, always alive with 2-5 TPS ambient), Traffic Generator Controls, Flagged Activity Feed (WebSocket), Verdict Donut.

**Topology (`/topology`):** Full-screen visualizations with sub-navbar:
- Constellation Graph — force-directed entity graph (white background, saffron edges, red=BLOCK/orange=HOLD/green=ALLOW nodes)
- India Mule Corridors — 139-vertex cartographic map of India with glowing bezier arcs between fraud corridor cities
- Dual Perspective — both side-by-side

**Threat Intelligence (`/threat-intel`):** Signal ingestion animated pipeline, live campaign cards with cosine similarity scores, entity extraction visualization.

**Investigations (`/investigations`):** Case list with filters, Case Drawer with full verdict details + NPCI/DPIP/PSP badge scores + SAR narrative, Gemini Assistant chat.

**Analytics (`/analytics`):** Fraud Rate Trend, Bank Distribution, Top Flagged Accounts, DAV (Dormant-to-Active Velocity) Table, Analyst Workload Heatmap (7×24 grid).

**Application State (`AppStateContext.jsx`):** All shared state in React Context. WebSocket connection to backend, 15s polling, 1s TPS ticker, 2-5 TPS ambient traffic injection.

---

## 18. The Test Suite (How We Know It Works)

**969 tests, 0 failures**

| File | What it tests |
|------|--------------|
| `test_tier1_features.py` | Core happy-path functionality |
| `test_tier2_boundary.py` | Edge cases |
| `test_tier3_combinations.py` | Multi-rule scenarios |
| `test_tier4_scenarios.py` | Real-world fraud scenarios |
| `test_tier5_adversarial.py` | Attempts to bypass the system |
| `test_isolation_forest.py` | ML model unit tests |
| `test_supervised_model.py` | 21 tests for supervised classifier (P/R/F1) |
| `test_institutional_adapters.py` | 19 tests for NPCI/DPIP/PSP adapters |
| `test_notifications_benchmark.py` | FCM latency benchmarks |
| `test_federation_api.py` | Federation push/pull/cache tests |
| `test_e2e_gemini_assistant.py` | Gemini function calling tests |
| `test_honeypot.py` | Honeypot + R_HONEYPOT_HIT rule |
| `test_threat_intel_r1.py` | Signal ingestion + campaign clustering |
| `frontend_contracts_test.py` | Frontend API contract tests |

---

## 19. Infrastructure (How It Runs in the Cloud)

```
git push origin main
       ↓
GitHub Actions CI/CD (.github/workflows/deploy.yml)
       ↓
Step 1: lint-and-test
  → ruff check + pytest (969 tests) + ESLint + Vite build
       ↓
Step 2: build-and-push
  → Docker image → ghcr.io/404avinash/sampati_v2:latest
       ↓
Step 3: deploy (SSH → EC2)
  → docker pull → docker stop → docker run
       ↓
Live at http://52.66.244.253:8000
```

- Region: ap-south-1 (Mumbai)
- Instance: t2.micro (1 vCPU, 1GB RAM) — demo scale
- Environment: `/opt/sampati/.env` (contains GEMINI_API_KEY)

---

## 20. Glossary (Plain English Definitions)

| Term | Definition |
|------|-----------|
| **UPI** | Unified Payments Interface — India's real-time payment system |
| **VPA** | Virtual Payment Address — your UPI ID (e.g., `yourname@sbi`) |
| **Mule Account** | A real bank account used by criminals to receive and forward stolen money |
| **Phishing** | Scam where criminal impersonates trusted entity (bank) to steal money/credentials |
| **Honeypot** | Decoy trap VPA — any transaction to it = instant BLOCK |
| **Isolation Forest** | Unsupervised ML that finds anomalies by isolating data points in random trees |
| **Random Forest** | Ensemble of decision trees — majority vote wins |
| **Supervised Learning** | ML trained on labeled data (fraud/clean already marked) |
| **Unsupervised Learning** | ML without labels — discovers patterns independently |
| **Feature Vector** | Transaction encoded as array of numbers for ML model |
| **Gini Impurity** | Decision tree metric for finding best split. Formula: `1 - Σ(p²)` |
| **Cosine Similarity** | Measures angle between two vectors. 1.0 = identical, 0.0 = completely different |
| **NetworkX** | Python library for graph network analysis |
| **FastAPI** | Modern Python web framework. Fast (ASGI), automatic docs, Pydantic validation |
| **Pydantic** | Python data validation library |
| **SQLAlchemy** | Python ORM — translates Python objects to SQL queries |
| **asyncpg** | Async PostgreSQL driver |
| **Docker** | Containerization — packages app + all dependencies into one portable box |
| **FCM** | Firebase Cloud Messaging — Google's push notification service |
| **SAR** | Suspicious Activity Report — mandatory legal document banks must file for fraud |
| **NPCI** | National Payments Corporation of India — runs UPI, RuPay, IMPS |
| **DPIP** | Domestic Payment Innovation Platform — RBI's fraud registry |
| **Federation** | Multiple institutions sharing anonymized fraud intelligence without exposing private data |
| **WebSocket** | Persistent bidirectional connection — server pushes data to browser without polling |
| **Vite** | Fast modern frontend build tool for React |
| **Tailwind CSS** | Utility-first CSS framework (classes like `bg-white p-4 rounded-lg`) |
| **Recharts** | React charting library |
| **Ruff** | Fast Python linter (written in Rust) |
| **BLOCK** | Strongest verdict — payment must be stopped |
| **HOLD** | Medium verdict — payment paused for analyst review |
| **ALLOW** | Clean verdict — payment appears safe |
| **TPS** | Transactions Per Second |
| **Fan-In** | Many senders → one receiver (mule account hallmark) |
| **Fan-Out** | One sender → many receivers (mule dispersal behavior) |
| **Structuring** | Breaking large amounts into small pieces to avoid regulatory thresholds |
| **Dormant-to-Active** | Account inactive 30+ days → suddenly very active (mule reactivation) |
| **Campaign DNA** | Fingerprint of a fraud campaign — entities + semantic tags + behavioral patterns |
| **Bagging** | Bootstrap aggregating — training each tree on a random sample to prevent overfitting |
| **Function Calling (Agentic AI)** | LLM feature where model executes real functions/APIs to complete tasks |

---

*Last updated: September 2026 | Version: SAMPATI V2 Sprint 7 | Tests: 969 passing | Live: http://52.66.244.253:8000*

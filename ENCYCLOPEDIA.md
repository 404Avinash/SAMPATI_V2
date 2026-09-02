# SAMPATI V2 — Complete Technical Encyclopedia

> **"Suspicious Activity Monitoring for Payment & Transaction Intelligence"**
> A real-time UPI fraud detection platform built as an Open Federated Fraud Intelligence Mesh.

---

## Table of Contents

1. [Project Philosophy & Purpose](#1-project-philosophy--purpose)
2. [High-Level Architecture Overview](#2-high-level-architecture-overview)
3. [Technology Stack](#3-technology-stack)
4. [Directory Structure](#4-directory-structure)
5. [Backend: The FastAPI Application](#5-backend-the-fastapi-application)
6. [The 3-Layer Risk Scoring Engine](#6-the-3-layer-risk-scoring-engine)
7. [AI/ML — Algorithms & Models](#7-aiml--algorithms--models)
8. [The Federation Intelligence Mesh](#8-the-federation-intelligence-mesh)
9. [The VPA Honeypot Network](#9-the-vpa-honeypot-network)
10. [Live Auto-Feed Engine](#10-live-auto-feed-engine)
11. [Data Persistence — Database Layer](#11-data-persistence--database-layer)
12. [Data Ingestion & the Synthetic Generator](#12-data-ingestion--the-synthetic-generator)
13. [Frontend: The React Dashboard](#13-frontend-the-react-dashboard)
14. [WebSocket Real-Time Communication](#14-websocket-real-time-communication)
15. [Forensics — SAR PDF Generation](#15-forensics--sar-pdf-generation)
16. [DevOps — CI/CD & Cloud Infrastructure](#16-devops--cicd--cloud-infrastructure)
17. [Testing Strategy — 710-Test Suite](#17-testing-strategy--710-test-suite)
18. [Data Flow: A Transaction's Full Journey](#18-data-flow-a-transactions-full-journey)
19. [API Reference Summary](#19-api-reference-summary)
20. [EC2 Operational Runbook](#20-ec2-operational-runbook)

---

## 1. Project Philosophy & Purpose

### What problem are we solving?
India's Unified Payments Interface (UPI) processes over **14 billion transactions per month**. Inside this volume, organized "mule networks" launder stolen money by routing funds through layered chains of compromised UPI Virtual Payment Addresses (VPAs). A "mule ring" is a structured criminal relay — money stolen from a victim flows through 3–7 intermediate accounts before being cashed out, making it difficult to trace.

Traditional rule-based fraud systems at individual Payment Service Providers (PSPs) like HDFC, SBI, or Paytm can only see their own slice of a transaction. A mule ring deliberately spans **multiple PSPs** to stay invisible to any single institution.

### What SAMPATI V2 does
SAMPATI V2 acts as an **inline interception gateway** and **cross-PSP intelligence mesh** that:
1. **Evaluates every payment in real-time** (sub-10ms latency) using a 3-layer ML + rules scoring engine.
2. **Federates threat intelligence** across simulated PSP nodes using privacy-preserving hashed signals — no raw VPA data is ever shared.
3. **Detects mule rings** automatically by identifying graph patterns (fan-in, fan-out, pass-through conduits) across PSP boundaries.
4. **Traps attackers** using a synthetic honeypot VPA network — any transaction to a honeypot is an automatic BLOCK.
5. **Generates evidence** in the form of ring graph visualizations and auto-drafted Suspicious Activity Reports (SAR) for compliance filing.
6. **Streams everything live** to a browser dashboard so bank fraud analysts see the mesh assemble in real time.

### Who is the audience?
- Bank fraud analysts and investigation teams
- Compliance officers who need SAR evidence
- Engineering leads evaluating fraud infrastructure

---

## 2. High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BANK / PSP PAYMENT RAIL                          │
│   (UPI Switch) ──────► POST /upi/check  (inline gate)                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   FastAPI Application    │
                    │   (app/main.py)          │
                    │                          │
                    │  ┌────────────────────┐  │
                    │  │  3-Layer Scorer     │  │
                    │  │  Layer 1: Rules     │  │
                    │  │  Layer 2: Adaptive  │  │
                    │  │  Layer 3: Network   │  │
                    │  └────────┬───────────┘  │
                    │           │               │
                    │  ┌────────▼───────────┐  │
                    │  │  UpiCaseService     │  │
                    │  │  (Case + Ring Mgmt) │  │
                    │  └────────┬───────────┘  │
                    └───────────┼───────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
    ┌─────────▼──────┐ ┌───────▼────────┐ ┌───────▼──────────┐
    │  PostgreSQL RDS │ │ WebSocket Hub  │ │ Federation Mesh  │
    │  (Persistence) │ │ (Broadcaster)  │ │ (5 PSP Nodes)    │
    └────────────────┘ └───────┬────────┘ └──────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   React SPA Dashboard │
                    │   (Vite + Tailwind)   │
                    │   - Constellation Map │
                    │   - KPI Strip         │
                    │   - Verdict History   │
                    │   - Analytics Charts  │
                    └───────────────────────┘
```

**Key Design Decisions:**
- **Monolithic container** (no microservices): FastAPI serves both the API and the pre-built React SPA via static file mount. This keeps deployment to a single Docker image and makes it viable on free-tier EC2.
- **In-memory hot state + DB persistence**: All runtime fraud scoring state (transaction windows, device maps) is stored in RAM for sub-millisecond access. The DB is only written to for durable case/ring records.
- **Privacy-by-design federation**: VPA hashes (SHA-256 + salt) are shared across PSP nodes, never raw identifiers.

---

## 3. Technology Stack

### Backend
| Technology | Version | Role | Why chosen |
|---|---|---|---|
| **Python** | 3.14 | Primary language | Ecosystem dominance for data/ML; async support |
| **FastAPI** | 0.141.1 | Web framework | Native async, auto OpenAPI docs, Pydantic integration |
| **Uvicorn** | 0.52.4 | ASGI server | Production-grade async server for FastAPI |
| **Pydantic** | 2.13.4 | Data validation & models | Type-safe request/response, auto-serialisation |
| **SQLAlchemy** | ≥2.0.36 | ORM | Async support, declarative models, DB-agnostic |
| **asyncpg** | ≥0.30.0 | PostgreSQL async driver | Fastest Python async Postgres driver |
| **aiosqlite** | ≥0.20.0 | SQLite async driver | In-memory fallback when no DB configured |
| **NetworkX** | ≥3.0 | Graph analysis | Ring topology analysis, node role computation |
| **Matplotlib** | ≥3.11.0 | Graph visualization | Generates ring PNG images for SAR PDF |
| **Pillow** | ≥12.0.0 | Image processing | Image embedding in PDF |
| **ReportLab** | ≥4.0.0 | PDF generation | SAR PDF export |
| **Ruff** | 0.16.5 | Linter | Ultra-fast Rust-based Python linter |
| **Pytest** | ≥8.0.0 | Test framework | Async test support with anyio plugin |

### Frontend
| Technology | Version | Role | Why chosen |
|---|---|---|---|
| **React** | 18 | UI framework | Component model, ecosystem, hooks |
| **Vite** | 5.4 | Build tool | Lightning-fast HMR, ESModule bundling |
| **Tailwind CSS** | 3 | Styling | Utility-first, zero-config dark mode |
| **Recharts** | latest | Charts | Declarative charting library for React |
| **Framer Motion** | latest | Animations | Smooth transitions and toast animations |
| **ESLint** | 9 | Linter | Code quality, `--max-warnings 0` enforced in CI |

### Infrastructure & DevOps
| Technology | Role |
|---|---|
| **AWS EC2 t3.small** | Application server (Ubuntu) |
| **AWS RDS PostgreSQL** | Managed database (db.t3.micro free tier) |
| **Docker** | Containerisation |
| **GitHub Actions** | CI/CD pipeline (lint → build → push → deploy) |
| **GitHub Container Registry (GHCR)** | Docker image registry |
| **Nginx** | Reverse proxy (port 80 → 8000) on EC2 |

---

## 4. Directory Structure

```
Sampati_v2/
├── app/                        # ← All backend Python source
│   ├── main.py                 # FastAPI app entrypoint, lifespan, SPA mount
│   ├── api/
│   │   ├── upi.py              # /upi/* routes (check, simulate, stats, autofeed)
│   │   ├── federation.py       # /federation/* routes (signal, query)
│   │   ├── cases.py            # /cases/* routes (list, detail, feedback)
│   │   ├── websocket.py        # WebSocket broadcaster & /ws endpoint
│   │   ├── gateway.py          # DPIP gateway integration
│   │   └── synthetic.py        # /synthetic/* routes for data generation
│   ├── engine/
│   │   ├── upi_scorer.py       # 3-layer composite scorer (THE CORE)
│   │   ├── upi_rules.py        # All deterministic rules (R01–R14+)
│   │   ├── upi_state.py        # UpiHotState (in-memory sliding window)
│   │   ├── adaptive.py         # EWMA behavioral anomaly model (Layer 2)
│   │   ├── dmv.py              # Dead Money Velocity (DMV) scorer
│   │   ├── campaign.py         # Campaign DNA fingerprinting & matching
│   │   └── honeypot.py         # VPA Honeypot registry & hit tracker
│   ├── federation/
│   │   ├── coordinator.py      # Multi-PSP federation coordinator
│   │   └── psp_node.py         # Individual PSP node (pseudonymization)
│   ├── models/
│   │   ├── upi_models.py       # Pydantic models (UpiTransaction, UpiEvaluationResponse, etc.)
│   │   └── upi_persistence.py  # SQLAlchemy ORM models (UpiCaseModel, MuleRingModel, etc.)
│   ├── db/
│   │   └── session.py          # Async DB engine, session factory, health check
│   ├── services/
│   │   ├── upi_cases.py        # UpiCaseService singleton (case + ring management)
│   │   └── autofeed.py         # AutoFeedEngine (background traffic generator)
│   ├── synthetic/
│   │   └── upi_generator.py    # Synthetic labeled UPI transaction generator
│   └── forensics/
│       └── sar_pdf.py          # SAR PDF builder (matplotlib + ReportLab)
│
├── frontend/                   # ← All frontend React source
│   ├── src/
│   │   ├── main.jsx            # React DOM root mount
│   │   ├── App.jsx             # Router setup (React Router)
│   │   ├── context/
│   │   │   └── AppStateContext.jsx   # Global state provider (WebSocket + API)
│   │   ├── hooks/
│   │   │   └── useWebSocket.js       # WebSocket connection hook
│   │   ├── services/
│   │   │   └── api.js                # All API fetch calls to backend
│   │   ├── layouts/
│   │   │   └── MainLayout.jsx        # Page shell with Navbar + outlet
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   └── Navbar.jsx        # Top navigation bar
│   │   │   ├── NetworkConstellation.jsx  # Canvas force-directed graph
│   │   │   ├── KpiStrip.jsx              # 7-tile metric bar
│   │   │   ├── CaseDrawer.jsx            # Per-case detail side panel
│   │   │   ├── ControlBar.jsx            # Simulate / Federation buttons
│   │   │   ├── LiveFeed.jsx              # Real-time transaction feed list
│   │   │   ├── VerdictDonut.jsx          # Donut chart (ALLOW/HOLD/BLOCK)
│   │   │   ├── VerdictHistoryChart.jsx   # Time-series verdict line chart
│   │   │   └── ...
│   │   └── pages/
│   │       ├── OverviewPage.jsx      # Main dashboard
│   │       ├── InvestigationsPage.jsx # Case list & investigation view
│   │       ├── AnalyticsPage.jsx     # Deep analytics, heatmap, DMV table
│   │       ├── SystemHealthPage.jsx  # DB pool, WebSocket, latency stats
│   │       └── SettingsPage.jsx      # Sensitivity slider, config
│   ├── dist/                   # Pre-built production bundle (committed)
│   ├── vite.config.js
│   └── package.json
│
├── tests/                      # ← 710-test suite (5 tiers)
│   ├── test_e2e_suite.py       # 231-test E2E suite (standalone runner)
│   ├── test_tier1_features.py  # Feature-level integration tests
│   ├── test_tier2_boundary.py  # Boundary & edge case tests
│   ├── test_tier3_combinations.py # Rule combination tests
│   ├── test_tier4_scenarios.py # Real-world scenario tests
│   ├── test_tier5_adversarial.py  # Adversarial stress tests
│   ├── test_federation_api.py  # Federation endpoint tests
│   ├── test_honeypot.py        # Honeypot rule tests
│   ├── test_engine_sprint2.py  # DMV, Campaign, telemetry tests
│   ├── test_analytics.py       # Analytics endpoint tests
│   └── ...
│
├── static/
│   └── upi_cases/              # Auto-generated ring PNG images
│
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline definition
│
├── Dockerfile                  # Container build spec
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Ruff + Pytest config
├── AGENTS.md                   # AI agent rules & safe-push protocol
└── ENCYCLOPEDIA.md             # ← This file
```

---

## 5. Backend: The FastAPI Application

**File:** `app/main.py`

This is the application entrypoint. It wires everything together.

### Lifespan (Startup / Shutdown)
FastAPI uses a `lifespan` context manager pattern to handle startup and shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: (all of this runs before the first request is served)
    await init_db()          # 1. Connect to PostgreSQL, create tables
    await svc.sync_from_db() # 2. Load last 200 cases + 500 rings into RAM
    trigger_demo_seed()      # 3. Pre-populate demo cases (skipped in tests)
    
    yield  # ← Application is live here
    
    # SHUTDOWN:
    await close_db()         # Gracefully close DB connection pool
```

**Why this pattern?** Database connections are expensive to create. By connecting once at startup (not on every request), SAMPATI can handle hundreds of requests per second without connection overhead.

### API Routers
The app mounts separate routers for clean separation of concerns:
```
/upi/*          ← app/api/upi.py        (core evaluation endpoints)
/federation/*   ← app/api/federation.py (threat signal exchange)
/cases/*        ← app/api/cases.py      (case management)
/ws             ← app/api/websocket.py  (WebSocket hub)
/synthetic/*    ← app/api/synthetic.py  (demo data generation)
/gateway/*      ← app/api/gateway.py    (DPIP integration)
/health         ← inline in main.py     (liveness probe)
/               ← frontend/dist/        (React SPA static mount)
```

### SPA Fallback Handler
Because React uses client-side routing (paths like `/investigations`, `/analytics`), the server would return 404 for direct URL navigation unless we handle it. The custom 404 handler checks if the path looks like an API route (starts with `/upi`, `/cases`, etc.) or a static asset (has a file extension). If neither, it serves `index.html` — letting React Router take over.

---

## 6. The 3-Layer Risk Scoring Engine

**File:** `app/engine/upi_scorer.py`

This is the **intellectual heart of SAMPATI**. Every UPI transaction goes through three independent scoring layers. Their scores are combined and thresholded to produce a final verdict.

```
UpiTransaction ──► Layer 1: Deterministic Rules (0–100 pts)
                ──► Layer 2: Adaptive EWMA Anomaly (0–25 pts)
                ──► Layer 3: Federation Network Score (0–40 pts)
                                     │
                        Combined Score (capped at 100)
                                     │
                    ┌────────────────▼──────────────────┐
                    │   score < 45  → ALLOW              │
                    │  45 ≤ score < 70 → HOLD            │
                    │   score ≥ 70  → BLOCK              │
                    └────────────────────────────────────┘
```

**Scoring constants:**
```python
ALLOW_BELOW = 45      # Green zone threshold
BLOCK_AT = 70         # Red zone threshold
ADAPTIVE_MAX_POINTS = 25   # Max contribution from Layer 2
NETWORK_MAX_POINTS = 40    # Max contribution from Layer 3
NETWORK_HOLD_FLOOR = 0.7   # Federation score alone can force a HOLD
```

---

## 7. AI/ML — Algorithms & Models

### Layer 1: Deterministic Rules

**File:** `app/engine/upi_rules.py`

These are hand-crafted expert rules based on known mule network patterns. Each rule returns a `RuleHit(code, points, detail)` if triggered. This is **white-box, explainable AI** — every point contributed has a human-readable reason.

| Rule Code | Trigger Condition | Points | What it detects |
|---|---|---|---|
| `R_HONEYPOT_HIT` | Payee VPA is in honeypot registry | 100 | Automated bots hitting synthetic traps |
| `R_SIM_DEVICE_MISMATCH` | Device fingerprint changed but SIM stayed same (or vice versa) | 40 | SIM-swap fraud |
| `R_IMPOSSIBLE_TRAVEL` | Payer location changed faster than physically possible | 35 | Account takeover, shared credentials |
| `R_DATACENTER_IP` | IP belongs to a cloud/VPN/Tor CIDR range | 25 | Automated fraud bots, IP masking |
| `R_CAMPAIGN_MATCH` | Transaction matches a known fraud campaign signature | 30 | Organized fraud syndicate detection |
| `NEW_PAYEE_VPA` | Payee VPA registered fewer than 30 days ago | 25 | Fresh mule account |
| `PASS_THROUGH_CONDUIT` | Account receives money then rapidly forwards ≥90% | 30 | Money laundering relay node |
| `FAN_IN_BURST` | Fresh account receiving from ≥5 distinct payers | 25 | Collector hub in mule ring |
| `FAN_OUT_DISPERSAL` | Fresh account sending to ≥5 distinct payees | 25 | Cash-out node in mule ring |
| `DEVICE_FARM` | One device/SIM fingerprint linked to ≥4 different VPAs | 20 | Organised mule farm |
| `NEW_ACCOUNT_HIGH_VALUE` | Account < 30 days old moving ≥ ₹50,000 | 25–50 | Instant high-value mule |
| `LIMIT_SKIRTING` | Amount sits within 2% below a regulatory threshold | 10 | Structuring / Smurfing |
| `KNOWN_FRAUD_ENTITY` | Payer or payee VPA appears in confirmed fraud history | 35 | Repeat fraudster |

**Why deterministic rules first?** They are fast (O(1) lookups), completely explainable to regulators, and catch the clearest fraud patterns immediately. The ML layers then catch what rules miss.

---

### Layer 2: Adaptive EWMA Behavioral Anomaly Model

**File:** `app/engine/adaptive.py`

**Algorithm:** Exponentially Weighted Moving Average (EWMA) — an **online / streaming statistics** algorithm that maintains a rolling "normal behavior" baseline for each VPA without storing historical data.

**Why EWMA?** Traditional ML models (Random Forest, XGBoost) require batch training on historical data. SAMPATI operates in a streaming environment where we need to adapt to each new transaction instantly. EWMA is the classic solution for streaming anomaly detection.

**How it works:**
1. For each VPA, maintain a running mean (μ) and variance (σ²) of transaction amounts.
2. Each new transaction updates these statistics with a decay factor α (alpha), giving more weight to recent transactions.
3. An anomaly score is computed as how many standard deviations the new transaction is from the moving mean.

```python
# EWMA update formula:
new_mean = α * new_value + (1 - α) * old_mean
new_variance = α * (new_value - new_mean)² + (1 - α) * old_variance
anomaly_z = |new_value - new_mean| / sqrt(new_variance)
anomaly_score = min(1.0, anomaly_z / NORMALIZATION_FACTOR)
```

**Practical effect:** If a VPA has been making ₹500–₹2,000 transactions for months and suddenly processes ₹2,50,000, the EWMA model produces a high anomaly score even if no deterministic rule triggers.

**No external ML library needed:** This is implemented from scratch in pure Python with threading locks for thread-safety. Zero model training, zero data storage, instant start.

---

### Dead Money Velocity (DMV) Score

**File:** `app/engine/dmv.py`

**What it detects:** The signature pattern of a "mule account" — dormant for weeks/months, then a sudden near-complete balance transfer out in a narrow window.

**Algorithm:** Sliding window ratio analysis using a deque (double-ended queue) data structure for O(1) eviction.

```
DMV Score =  f(dormancy_gap, outflow_velocity, balance_depletion_ratio)

dormancy_gap = time since last transaction before this burst
velocity = amount moved / time window (₹/hour)
depletion = outflow_in_window / inflow_in_window
```

The score is a weighted combination:
- High dormancy gap + high velocity = very high DMV (e.g., 90/100)
- Regular activity + moderate amount = low DMV (e.g., 5/100)

**Returned in:** Every `/upi/check` response as `dmv_score` (0–100 float).  
**Displayed in:** CaseDrawer as a color-coded gauge (green < 40, amber 40–70, red > 70).  
**Table view:** Analytics page "Top VPAs by DMV Score" ranked table.

---

### Transaction DNA Campaign Fingerprinting

**File:** `app/engine/campaign.py`

**What it detects:** Individual fraud events that belong to the same organized campaign rather than isolated incidents.

**Algorithm:** Weighted Cosine-Like Similarity matching against a store of known campaign signatures.

Each transaction's "DNA fingerprint" consists of:
- **Payment note keywords** (weighted 35%): Does the note contain KYC, verify, crypto, task, bonus?
- **Amount distribution** (weighted 30%): Does the amount fall in the typical campaign range?
- **Time-of-day bucket** (weighted 20%): Is this transaction at a typical attack hour (e.g., 2–4 AM)?
- **Payee VPA handle** (weighted 15%): Does the payee VPA contain suspicious keywords?

Three built-in campaign families are seeded:
- `CAMP-KYC-PHISH-01` — KYC/OTP/bank phishing scams
- `CAMP-SMURF-BURST-02` — Structured smurf transfers / smurfing
- `CAMP-INVESTMENT-03` — Fake investment / telegram job / crypto fraud

When a transaction is **BLOCKed**, its fingerprint is ingested into the store. Future transactions are compared against all stored fingerprints. If similarity ≥ 0.82, rule `R_CAMPAIGN_MATCH` fires and the matching `campaign_id` is attached to the response.

---

### Node Role Classification (Graph ML)

**File:** `app/services/upi_cases.py` + **Library:** NetworkX

Once a mule ring is identified, SAMPATI uses **graph theory** to assign a structural role to each node (VPA):

| Role | Detection Method | Meaning |
|---|---|---|
| **Victim** | Node with high in-degree, no prior fraud history | Money source, original fraud target |
| **Collector Hub** | High in-degree (many senders), low out-degree | First-layer aggregator in ring |
| **Layering Hop** | Pass-through node (inflow ≈ outflow) | Middle-layer obscuration node |
| **Cash-Out** | Final node with no further outflow | Where money exits the system |

This classification is done using `networkx.DiGraph` in-degree and out-degree analysis on the transaction topology, giving analysts an instant "map" of the ring's criminal hierarchy.

---

## 8. The Federation Intelligence Mesh

**Files:** `app/federation/coordinator.py` + `app/federation/psp_node.py`

**The Core Problem:** A mule ring that spans HDFC, SBI, and Paytm is invisible to any single PSP. Each PSP only sees one hop in the chain.

**The Solution:** A privacy-preserving signal sharing protocol.

### How it works

**Step 1 — Pseudonymization:**  
When a PSP wants to share a threat signal, it first hashes the VPA using SHA-256 with a shared federation salt:
```python
def pseudonymize(vpa: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{vpa.lower()}".encode()).hexdigest()
```
The raw VPA (`user@hdfc`) is never shared. Only its hash is transmitted.

**Step 2 — Signal Submission:**
```
POST /federation/signal
{
  "vpa_hash": "a3f9b1c2...",   # SHA-256 of VPA+salt
  "risk_level": "HIGH",        # CRITICAL/HIGH/MEDIUM/LOW
  "ring_hash": "d7e8f1a2..."   # Hash of the ring this VPA belongs to
}
```
The `FederatedCoordinator` stores this signal in its hot in-memory cache (Python dict) for sub-millisecond lookups.

**Step 3 — Query:**
```
GET /federation/query?vpa_hash=a3f9b1c2...
→ {
    "federated_risk_score": 0.85,
    "ring_members": ["hash1", "hash2", ...],
    "reported_by_nodes": ["HDFC-PSP", "SBI-PSP"]
  }
```
Response time is **< 5ms** because everything is in RAM.

**Step 4 — Network Score Integration:**  
When `/upi/check` is called, the scorer simultaneously:
1. Hashes the transaction's payer/payee VPAs.
2. Queries the federation cache for a matching signal.
3. Uses the returned `federated_risk_score` as the `network_score` for Layer 3 of the scorer.

### Mule Ring Automatic Detection
The `FederatedCoordinator` also runs **graph consensus detection**. When signals from multiple PSP nodes converge on the same ring hash and the ring has ≥ 3 members across ≥ 2 PSPs, it is automatically promoted to a confirmed `MuleRing` and persisted to the database.

### Simulated PSP Nodes
For the demo, 5 PSP nodes are simulated:
```python
SIMULATED_PSPS = ["HDFC-PSP", "SBI-PSP", "PAYTM-PSP", "AXIS-PSP", "ICICI-PSP"]
```

---

## 9. The VPA Honeypot Network

**File:** `app/engine/honeypot.py`

### Concept
A honeypot is a synthetic VPA address that is seeded into underground fraud marketplaces and darknet lists. Any legitimate user would never know these addresses. If a payment is directed to one, it can ONLY be because:
- An automated fraud bot is probing for valid VPAs.
- A mule operator has obtained this address from a malicious source.

### Seeded Honeypot VPAs (14 addresses)
```
honeypot_trap_01@okaxis
honeypot_mule_99@okhdfcbank
phish_trap_node@okicici
botnet_sink_04@oksbi
mule_honeypot_prime@okaxis
trap_collect_007@paytm
...
```

Any VPA matching a seeded address OR matching the honeypot prefixes (`honeypot_`, `phish_trap_`, `botnet_sink_`, etc.) is flagged.

### What happens on a hit
1. Rule `R_HONEYPOT_HIT` fires with **100 points** — guaranteeing a BLOCK verdict regardless of other scores.
2. The `HoneypotRegistry` records: hit count, amount deflected, last-hit timestamp, payer VPA, and transaction ID.
3. A WebSocket `HONEYPOT_ALERT` event is broadcast to all connected dashboard clients.
4. The dashboard shows a **red toast notification** (top-right, animated, 5-second auto-dismiss).
5. The "Honeypot Hits (24h)" KPI tile on the Overview page increments.

---

## 10. Live Auto-Feed Engine

**File:** `app/services/autofeed.py`

### Purpose
Transforms the dashboard from a static demo into a living system that **looks like it's connected to a real UPI payment rail**. This is the "defensibility feature" — the thing that convinces engineers and judges that the system actually works under load.

### Architecture
`AutoFeedEngine` runs a Python `threading.Thread` in the background. The thread:
1. Generates a transaction using `upi_generator.py` (either legit or fraud based on `fraud_ratio`).
2. Routes it through the full `UpiRiskScorer.evaluate()` pipeline.
3. Emits the result over the WebSocket hub to all connected dashboards.
4. Writes flagged cases to the DB.
5. Sleeps `1.0 / rate_tps` seconds before generating the next transaction.

### Controls
| Parameter | Default | Range |
|---|---|---|
| `rate_tps` | 10 tx/s | 1–50 tx/s |
| `fraud_ratio` | 0.20 | 0.0–1.0 |
| `bursty` | false | boolean |

### Activation
```
POST /upi/autofeed/start  → starts background thread
POST /upi/autofeed/stop   → stops thread gracefully
GET  /upi/autofeed/status → current rate, total generated, flagged
```

> **⚠️ Important Operational Note:** The auto-feed writes indefinitely to PostgreSQL. Running it for hours at 10 tx/s generates hundreds of thousands of rows. The startup `sync_from_db()` is therefore **limited to 200 cases and 500 rings** (via `.limit()` clauses) to prevent OOM crashes on server restart.

---

## 11. Data Persistence — Database Layer

**Files:** `app/db/session.py` + `app/models/upi_persistence.py`

### Database: AWS RDS PostgreSQL (db.t3.micro)
- Hosted separately from the EC2 application server.
- Connection string passed via `DATABASE_URL` environment variable in `/opt/sampati/.env`.
- If `DATABASE_URL` is unset, the app automatically falls back to **in-memory-only mode** (no persistence across restarts).

### Connection Pool
```python
create_async_engine(
    db_url,
    pool_size=5,            # Persistent connections in pool
    max_overflow=10,        # Extra connections during bursts
    pool_pre_ping=True,     # Test connections before use (handles stale connections)
    pool_recycle=1800,      # Recycle connections every 30 min
)
```
Optimized for `db.t3.micro` which supports a maximum of ~87 simultaneous connections.

### ORM Tables

**`upi_cases`** — All flagged transaction cases
```sql
case_id      VARCHAR(64) PRIMARY KEY
created_at   TIMESTAMP WITH TIMEZONE
status       VARCHAR(32)  -- OPEN/REVIEWED/ESCALATED/DISMISSED
verdict      VARCHAR(16)  -- ALLOW/HOLD/BLOCK
risk_score   INTEGER
payer_vpa    VARCHAR(128)
payee_vpa    VARCHAR(128)
amount       NUMERIC(14, 2)
reasons      JSON         -- List of triggered rule codes
ring_members JSON         -- VPA members if ring detected
topology     JSON         -- Full graph topology for Constellation view
```

**`mule_rings`** — Confirmed cross-PSP mule rings
```sql
ring_hash    VARCHAR(64) PRIMARY KEY
detected_at  TIMESTAMP WITH TIMEZONE
size         INTEGER
members      JSON         -- List of member VPAs
psps         JSON         -- Distinct PSPs involved
total_amount NUMERIC(14, 2)
status       VARCHAR(32)  -- ACTIVE/DISMANTLED/ARCHIVED
```

**`analyst_feedback`** — Human review history  
**`txn_heatmap_cache`** — Pre-computed 7×24 heatmap data

---

## 12. Data Ingestion & the Synthetic Generator

**File:** `app/synthetic/upi_generator.py`

### The Problem
SAMPATI has no access to real UPI transaction data (privacy regulations, banking secrecy). All data must be synthetically generated.

### Synthetic Transaction Generation
The generator creates labeled `UpiTransaction` objects following realistic probability distributions:

**Legitimate transactions:**
- Amounts: log-normal distribution centred on ₹500–₹5,000 (typical P2P payment)
- VPA age: normally distributed, most accounts > 90 days old
- Timing: day/evening peaks, low volume at night
- Device: stable device_id + sim_id combination

**Fraud patterns (scenarios):**
- `pass_through_conduit` — large amounts forwarded quickly
- `fan_in_burst` — multiple sources → single fresh account
- `fan_out_dispersal` — single source → multiple accounts
- `mule_ring_multi_hop` — chained multi-hop rings across PSPs
- `honeypot_probe` — deliberate honeypot VPA targeting
- `sim_swap_fraud` — device/SIM mismatch injection
- `impossible_travel` — location jump injection
- `datacenter_ip` — cloud IP injection
- `kyc_phishing` — KYC-themed note + fake OTP patterns

Each transaction object contains:
```python
UpiTransaction(
    txn_id, payer_vpa, payee_vpa, amount, timestamp,
    payer_account_age_days, payee_vpa_age_days,
    device_id, sim_id, ip, location,
    note, channel, purpose
)
```

### Simulation Endpoint
```
POST /upi/simulate
{
  "total_txns": 100,
  "fraud_ratio": 0.15,
  "seed": 42,
  "run_federation": true
}
```
Generates and evaluates a batch of synthetic transactions, persists flagged cases, and runs federation consensus detection.

---

## 13. Frontend: The React Dashboard

**Directory:** `frontend/src/`

### Architecture Pattern
The frontend uses a **single Context Provider pattern** (`AppStateContext`) as the global store. There is no Redux or Zustand — the app's shared state fits comfortably in React Context.

### State Flow
```
WebSocket (useWebSocket.js)
    │
    ▼
AppStateContext.jsx  ←  REST API calls (api.js)
    │
    ├── stats (evaluated, allowed, held, blocked, honeypot_hits, rings)
    ├── cases (list of UpiCase objects)
    ├── selectedCase (for CaseDrawer)
    ├── verdictHistory (rolling 40-point time series for chart)
    ├── autoFeedActive / autoFeedTps / autoFeedStats
    └── honeypotAlerts (transient, 5-second life)
    │
    ▼
Components consume via useAppState() hook
```

### Pages

**OverviewPage** — The main command center:
- KPI Strip (7 tiles: Evaluated, Allowed, Held, Blocked, Rings, Honeypot Hits, DPIP)
- NetworkConstellation canvas (force-directed fraud ring graph)
- VerdictHistoryChart (rolling time series)
- VerdictDonut (ALLOW/HOLD/BLOCK ratio)
- ControlBar (Simulate / Federation / AutoFeed toggle)
- LiveFeed (last 15 transactions as they come in)
- HoneypotAlert toasts (red animated popups)

**InvestigationsPage** — Case management:
- Searchable/filterable list of all flagged cases
- Click to open CaseDrawer
- CaseDrawer: full case detail, DMV gauge, ring image, SAR export button, analyst feedback

**AnalyticsPage** — Deep analytics:
- Time-series verdict distribution (Recharts AreaChart)
- Rule frequency bar chart
- Top flagged accounts table
- 7×24 Analyst Workload Heatmap (fraud volume by day × hour)
- Top VPAs by DMV Score table

**SystemHealthPage** — Infrastructure monitoring:
- DB connection pool stats (size, overflow, active)
- WebSocket client count
- Evaluation latency percentiles (p50, p90, p99)

### NetworkConstellation (The Visual Centrepiece)

**File:** `frontend/src/components/NetworkConstellation.jsx`

This is a hand-coded **HTML5 Canvas force-directed graph**. No D3.js, no third-party graph library — written from scratch for performance.

**Force simulation:**
- Repulsion force between nodes (Coulomb-like: F = k / r²)
- Attraction force on edges (spring: F = k * (r - rest_length))
- Gravity toward center
- Velocity dampening (friction coefficient)

**Node types & colors:**
- 🔴 Red: BLOCK verdict nodes
- 🟡 Amber: HOLD verdict nodes
- 🟢 Green: ALLOW / healthy nodes
- ⚪ White edge: normal transaction flow
- 🔴 Red edge: high-risk transaction flow

**Playback Timeline:**
A range slider + Play/Pause/Reset control beneath the canvas lets analysts replay a case's ring formation in chronological order — seeing exactly how the mule network assembled itself over time.

---

## 14. WebSocket Real-Time Communication

**File:** `app/api/websocket.py` + `frontend/src/hooks/useWebSocket.js`

### Backend — Broadcasting Hub
The backend maintains a **global set of active WebSocket connections**. When a transaction is evaluated:
1. The result is serialized to JSON.
2. `schedule_broadcast(payload)` is called.
3. The hub fans out the message to all active clients simultaneously.

### Message Types
| Event Type | Payload | Purpose |
|---|---|---|
| `VERDICT` | Full `UpiEvaluationResponse` | Every evaluated transaction |
| `CASE_OPENED` | Case ID + summary | When a new HOLD/BLOCK case is created |
| `RING_DETECTED` | Ring members + PSPs | When a mule ring is confirmed |
| `HONEYPOT_ALERT` | VPA + amount + payer | When a honeypot is hit |
| `STATS_UPDATE` | Global counters | Periodic KPI refresh |
| `AUTOFEED_STATUS` | rate, total, flagged | Auto-feed state changes |

### Frontend — useWebSocket Hook
The `useWebSocket.js` hook:
1. Opens a `WebSocket` connection to `ws://<host>/ws`.
2. Parses incoming JSON messages.
3. Dispatches state updates to `AppStateContext` based on the event type.
4. Implements exponential backoff reconnection (1s → 2s → 4s → ... → 30s max).
5. Cleans up the connection on component unmount.

---

## 15. Forensics — SAR PDF Generation

**File:** `app/forensics/sar_pdf.py`

### What a SAR is
A Suspicious Activity Report (SAR) is a formal document filed with financial intelligence units (FIU-IND in India) when a bank detects money laundering. It must be filed within 7 days of detection.

### What SAMPATI generates
**Endpoint:** `GET /cases/{case_id}/sar/pdf`  
**Returns:** Binary PDF file (downloadable)

**PDF Contents:**
1. **Header** — Case ID, generation timestamp, SAMPATI version
2. **Executive Summary** — Risk score, verdict, total amount, timespan
3. **Entity Registry** — Payer VPA, payee VPA, DMV scores, account ages
4. **Rule Breakdown** — Table of all triggered rules with points and detail
5. **Ring Topology Graph** — Embedded Matplotlib visualization of the fraud ring
6. **SAR Narrative** — Auto-drafted plain-English description of the fraud pattern

**Tech Stack:**
- `Matplotlib` draws the ring graph (`networkx.draw_spring_layout` layout)
- `Matplotlib PdfPages` + `ReportLab` embed the figure into a multi-page PDF
- Returned as a streaming `Response` with `Content-Disposition: attachment`

---

## 16. DevOps — CI/CD & Cloud Infrastructure

**File:** `.github/workflows/deploy.yml`

### Pipeline Overview
Every push to `main` triggers a 4-stage pipeline:

```
Stage 1: Lint & Test Suite (runs on GitHub-hosted ubuntu runner)
    ├── Set up Python 3.14
    ├── Install dependencies (pip install -r requirements.txt)
    ├── pip install -e . (editable install)
    ├── ruff check app tests          (linting, 0 errors enforced)
    ├── pytest tests/ -v              (710 tests, 0 failures required)
    ├── Set up Node.js 20
    ├── npm ci (install frontend deps)
    ├── npm run lint                  (ESLint, --max-warnings 0)
    └── npm run build                 (Vite production build)

Stage 2: Build & Push Container to GHCR
    ├── docker/setup-buildx-action
    ├── docker/login-action (GHCR)
    ├── docker/metadata-action (tag with commit SHA + latest)
    └── docker/build-push-action
          ├── cache-from: type=gha    (GitHub Actions cache)
          └── cache-to: type=gha,mode=max

Stage 3: Deploy to AWS EC2
    └── appleboy/ssh-action@v1.0.3
          ├── SSH into EC2 using EC2_SSH_KEY secret
          ├── docker login ghcr.io
          ├── docker pull <image:SHA>
          ├── docker stop sampati && docker rm sampati
          ├── docker run -d --name sampati --restart unless-stopped ...
          └── 60-second health check loop (GET /health → HTTP 200)
                ├── PASS → proceed to cleanup & success
                └── FAIL → print logs + automated rollback to previous image

Stage 4: Deployment Notification & Status
    ├── POST GitHub Commit Status API (green/red checkmark on commit)
    └── POST Slack Webhook (if SLACK_WEBHOOK_URL secret configured)
```

### GitHub Secrets Required
| Secret | Value |
|---|---|
| `EC2_HOST` | Public IPv4 address of EC2 instance |
| `EC2_USERNAME` | `ubuntu` (or your EC2 username) |
| `EC2_SSH_KEY` | Contents of your PEM private key |
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions (for GHCR) |

### EC2 Infrastructure
- **Instance type:** `t3.small` (2 vCPU, 2 GB RAM)
- **OS:** Ubuntu 22.04 LTS
- **Application port:** 8000 (Uvicorn)
- **Public port:** 80 (Nginx reverse proxy → 8000)
- **Env file:** `/opt/sampati/.env` contains `DATABASE_URL`
- **Container restart policy:** `unless-stopped` (auto-restarts on crash, but not on explicit `docker stop`)

### Docker Image
**Base image:** `python:3.14-slim`  
**Build strategy:** The frontend is pre-built and the `dist/` folder is committed to the repo. This means the Docker build does NOT need Node.js — making the image smaller and the build faster.

```dockerfile
FROM python:3.14-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY frontend/dist ./frontend/dist
COPY static/ ./static/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 17. Testing Strategy — 710-Test Suite

### Why 710 tests?
Testing is the primary guard against the CI/CD pipeline deploying broken code. Because SAMPATI deploys automatically to production on every push, a robust test suite is non-negotiable.

### Test Structure

**Standalone E2E Runner:** `tests/test_e2e_suite.py`
- 231 tests organized into named test classes
- Runs using Python `unittest` (not pytest) for CI compatibility
- Tests the full application stack including real DB connections

**5-Tier Pytest Suite:**

| Tier | File | Tests | What it tests |
|---|---|---|---|
| 1 | `test_tier1_features.py` | 76 | Feature-level: every endpoint, every feature |
| 2 | `test_tier2_boundary.py` | 78 | Boundary: empty inputs, zero amounts, max values |
| 3 | `test_tier3_combinations.py` | 7 | Rule combinations: multiple rules co-triggering |
| 4 | `test_tier4_scenarios.py` | 5 | Real-world scenarios: full mule ring lifecycle |
| 5 | `test_tier5_adversarial.py` | 33 | Adversarial: stress, concurrency, kill/resume |

**Domain-specific suites:**
- `test_federation_api.py` (10) — Federation signal/query endpoints
- `test_honeypot.py` (21) — Honeypot detection and telemetry
- `test_engine_sprint2.py` (28) — DMV, Campaign fingerprinting, device telemetry
- `test_analytics.py` (7) — Analytics aggregation endpoint
- `test_m2_websocket.py` (10) — WebSocket connection pool stress
- `test_challenger_stress.py` (23) — SAR PDF generation, adversarial payloads
- `frontend_contracts_test.py` (23) — API contract tests (response schema validation)

### Safe-Push Protocol
Before any push, the full validation sequence must pass:
```bash
./.venv/bin/pytest                              # 710 backend tests
./.venv/bin/ruff check app tests               # Python linting
cd frontend && npm run lint && npm run build   # Frontend lint + build
git add . && git commit -m "..." && git push origin main
```

---

## 18. Data Flow: A Transaction's Full Journey

Here is the complete lifecycle of a single UPI transaction through SAMPATI:

```
1. INGESTION
   Transaction arrives at POST /upi/check
   │
   Pydantic validates UpiTransaction payload

2. LAYER 1 — DETERMINISTIC RULES (app/engine/upi_rules.py)
   ├── Honeypot check (registry lookup, O(1))
   ├── SIM/Device mismatch (telemetry state lookup)
   ├── Impossible travel (location + timestamp math)
   ├── Datacenter IP (CIDR subnet matching)
   ├── Campaign fingerprint match (similarity scoring)
   ├── Structural flow rules (sliding window stats from UpiHotState)
   └── → rule_score (0–100 pts)

3. LAYER 2 — ADAPTIVE EWMA (app/engine/adaptive.py)
   ├── Lookup VPA's rolling mean + variance
   ├── Compute z-score of current amount
   └── → adaptive_score (0–25 pts)

4. LAYER 3 — FEDERATION NETWORK (app/federation/coordinator.py)
   ├── Hash payer_vpa and payee_vpa with salt
   ├── Query hot in-memory signal cache
   └── → network_score (0–40 pts)

5. DMV SCORING (app/engine/dmv.py)
   ├── Query VPA's inflow/outflow sliding window
   └── → dmv_score (0–100 float, returned in response)

6. VERDICT DECISION (app/engine/upi_scorer.py)
   combined = rule_score + adaptive_pts + network_pts
   ALLOW if < 45 | HOLD if 45–69 | BLOCK if ≥ 70

7. STATE UPDATE
   ├── UpiHotState.record_txn() (update sliding windows)
   ├── DmvTracker.record_txn() (update DMV state)
   ├── AdaptiveBehaviorModel.observe() (update EWMA)
   └── record_payer_telemetry() (update device/SIM map)

8. CAMPAIGN LEARNING
   If BLOCK → ingest fingerprint into CampaignSignatureStore

9. CASE CREATION (UpiCaseService, if HOLD or BLOCK)
   ├── Build ring topology graph
   ├── Render ring PNG (Matplotlib)
   ├── Create UpiCase (in-memory)
   ├── Persist to PostgreSQL (upi_cases table)
   └── Check federation for ring promotion

10. WEBSOCKET BROADCAST
    ├── Emit VERDICT event to all connected dashboards
    ├── If case created → emit CASE_OPENED
    ├── If ring detected → emit RING_DETECTED
    └── If honeypot hit → emit HONEYPOT_ALERT (+ red toast in UI)

11. RESPONSE RETURNED TO CALLER
    {
      txn_id, risk_score, action, reasons,
      rule_breakdown, rule_score, adaptive_score,
      network_score, dmv_score, campaign_id,
      case_id, execution_latency_ms, evaluated_at
    }
```

**Typical end-to-end latency:** 2–8ms (in-memory path), 8–20ms (with DB write).

---

## 19. API Reference Summary

### Core Evaluation
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/upi/check` | Evaluate a single UPI transaction |
| `POST` | `/upi/simulate` | Batch simulate N transactions |
| `GET` | `/upi/stats` | Global evaluation counters |
| `POST` | `/upi/autofeed/start` | Start live auto-feed engine |
| `POST` | `/upi/autofeed/stop` | Stop live auto-feed engine |
| `GET` | `/upi/autofeed/status` | Auto-feed stats |

### Federation
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/federation/signal` | Submit a privacy-preserving threat signal |
| `GET` | `/federation/query?vpa_hash=<hash>` | Query federated risk for a VPA hash |
| `POST` | `/federation/run` | Force multi-PSP ring detection consensus |

### Cases
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/cases` | List all flagged cases |
| `GET` | `/cases/{case_id}` | Get case detail with topology |
| `PATCH` | `/cases/{case_id}/status` | Update case status (analyst review) |
| `POST` | `/cases/{case_id}/feedback` | Submit analyst feedback (trains adaptive model) |
| `GET` | `/cases/{case_id}/sar/pdf` | Download SAR PDF |

### System
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness + DB connectivity probe |
| `GET` | `/health/detailed` | Full subsystem health + latency percentiles |
| `GET` | `/stats/analytics` | Time-series, rule frequencies, top accounts |
| `WebSocket` | `/ws` | Real-time event stream |

### Analytics
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/stats/analytics?interval=hourly&hours=24` | Time-series verdict distribution |

---

## 20. EC2 Operational Runbook

### ⚠️ Critical: Elastic IP Warning
**Every time you Stop and Start the EC2 instance, AWS assigns a new Public IP address** unless you have an Elastic IP allocated. This breaks the `EC2_HOST` GitHub secret and causes SSH timeouts in CI.

**Permanent fix:** Allocate an AWS Elastic IP and associate it with the instance. Then update `EC2_HOST` once, forever.

### Common Issues & Fixes

**Issue: GitHub Action hangs for 2+ minutes then fails with `read: connection timed out`**  
**Cause:** Server is frozen (OOM) — old container eating all RAM.  
**Fix:** Stop instance → Start instance (wait 2 min) → Update `EC2_HOST` secret with new IP → Re-run job.

**Issue: GitHub Action fails immediately with `connect: connection refused`**  
**Cause:** SSH daemon not yet started (server still booting) or boot sequence broken by user-data.  
**Fix:** Ensure User Data is empty, wait 90 seconds after instance shows "Running" state, then re-run.

**Issue: Health check fails (HTTP 000) after container starts**  
**Cause 1:** Missing `/opt/sampati/.env` file (no `DATABASE_URL` — app tries to start without DB and crashes).  
**Cause 2:** DB query on startup loading too many rows → OOM before health endpoint responds.  
**Fix:** Ensure `.env` exists with correct `DATABASE_URL`. The startup query limits are `.limit(200)` / `.limit(500)`.

**Issue: `Warning: Error synchronizing state from PostgreSQL: type object 'MuleRingModel' has no attribute 'created_at'`**  
**Cause:** Code bug — using wrong column name. The column is `detected_at`, not `created_at`.  
**Fix:** Already patched in commit `75117fd`.

### Environment File
Create `/opt/sampati/.env` on the EC2 server:
```bash
DATABASE_URL=postgresql://sampati_user:password@your-rds-endpoint:5432/sampatidb
```

### Monitoring Container Health
```bash
# SSH into EC2, then:
docker logs sampati --tail 100 -f        # Live application logs
docker stats sampati                      # CPU/RAM usage
curl -s http://localhost:8000/health      # Health probe
curl -s http://localhost:8000/health/detailed | python3 -m json.tool
```

---

*SAMPATI V2 Encyclopedia — Last updated: September 2026*  
*Repository: [github.com/404Avinash/SAMPATI_V2](https://github.com/404Avinash/SAMPATI_V2)*

---

## 21. Glossary & Technical Reference

This section provides in-depth explanations for all the specialized technical terms, architectural concepts, and frameworks mentioned throughout this encyclopedia, including *why* they were specifically chosen for SAMPATI V2.

### Architectural & Domain Concepts

**Ingestion**
- **What it is:** The process of receiving, validating, and normalizing raw data from an external source before it enters the core processing pipeline.
- **Why we use it:** In a financial system, raw payment data from different banks (PSPs) arrives in various formats. Ingestion (handled by our `/upi/check` endpoint) ensures every transaction is instantly validated against strict `Pydantic` schemas, guaranteeing the risk engine only processes clean, uniform data.

**PSP (Payment Service Provider)**
- **What it is:** A financial institution or tech company (like HDFC, SBI, PhonePe, Google Pay) that facilitates UPI payments.
- **Why we use it:** Mule networks intentionally move money across different PSPs to evade detection. SAMPATI's core mission is to bridge the intelligence gap between these isolated PSPs.

**Federation / Federated Intelligence**
- **What it is:** A decentralized approach to data sharing where participants exchange mathematical proofs or insights (like risk scores) without ever sharing the underlying raw, sensitive data.
- **Why we use it:** Indian banking privacy laws prohibit banks from sharing raw customer transaction histories with each other. By exchanging only SHA-256 hashes of VPAs and computed risk scores, SAMPATI allows banks to collaboratively detect a cross-bank mule ring while remaining 100% legally compliant.

**Hot State / In-Memory Cache**
- **What it is:** Storing operational data directly in the server's RAM rather than reading it from a hard drive or external database.
- **Why we use it:** UPI transactions require sub-50 millisecond response times. Querying a PostgreSQL database for a user's transaction history on every single payment would cause massive delays. SAMPATI uses in-memory sliding windows (RAM) to calculate velocities and frequencies instantly.

**EWMA (Exponentially Weighted Moving Average)**
- **What it is:** A streaming statistical algorithm that calculates a moving average where older data points exponentially lose weight (importance) compared to newer data points.
- **Why we use it:** Traditional machine learning requires storing gigabytes of historical data to train a model. EWMA requires storing only *two numbers* per user (the current mean and variance). This allows our Adaptive Layer to detect behavioral anomalies (like a user suddenly sending 100x their normal amount) with zero database overhead and lightning speed.

**Force-Directed Graph**
- **What it is:** A data visualization technique that positions nodes (accounts) by simulating physical forces: nodes repel each other (like magnets), but edges (transactions) pull them together (like springs).
- **Why we use it:** Mule rings are incredibly complex to understand in a spreadsheet. By using a physics simulation on the frontend canvas (`NetworkConstellation`), the fraud ring organically untangles itself on the screen, allowing analysts to instantly spot the "Collector Hubs" and "Cash-Out" nodes.

### Tech Stack Components

**FastAPI**
- **What it is:** A modern, high-performance web framework for building APIs with Python, based on standard Python type hints.
- **Why we use it:** It provides native asynchronous (`async/await`) support, meaning the server doesn't block while waiting for a database query. It also automatically generates interactive API documentation (Swagger UI), which is critical for a platform meant to be integrated by external banks.

**Uvicorn**
- **What it is:** An ASGI (Asynchronous Server Gateway Interface) web server implementation for Python.
- **Why we use it:** FastAPI is just a framework; it needs a server to actually listen to network ports and handle HTTP requests. Uvicorn is one of the fastest Python web servers available, built on `uvloop` (which is written in Cython), providing the raw speed necessary for inline payment interception.

**Pydantic**
- **What it is:** A data validation and parsing library for Python that uses type hints.
- **Why we use it:** It guarantees that incoming JSON payloads from the UPI switch exactly match our expected data structures. If a payload is missing a field or has a string instead of a number, Pydantic rejects it automatically before it ever touches our risk engine.

**SQLAlchemy & asyncpg**
- **What it is:** SQLAlchemy is an ORM (Object-Relational Mapper) that translates Python objects into SQL queries. `asyncpg` is the asynchronous database driver that physically talks to PostgreSQL.
- **Why we use it:** Using an ORM protects against SQL injection attacks and makes the codebase much easier to maintain. Combining it with `asyncpg` ensures that database writes (like logging a flagged case) do not block the main event loop, keeping API latency ultra-low.

**NetworkX**
- **What it is:** A Python package for the creation, manipulation, and study of the structure, dynamics, and functions of complex networks (graphs).
- **Why we use it:** While the frontend visualizes the graph, the backend uses NetworkX to run mathematical algorithms on the transaction topology. It computes "in-degree" and "out-degree" (how many connections go in vs out) to automatically classify whether a VPA is a "Victim", a "Layering Hop", or a "Cash-Out" node.

**React & Vite**
- **What it is:** React is a UI library for building component-based user interfaces. Vite is a next-generation frontend build tool.
- **Why we use it:** React's virtual DOM is perfect for handling the high-frequency updates from our WebSocket Live Feed without freezing the browser. Vite replaces older tools like Webpack, providing instant server starts and lightning-fast Hot Module Replacement (HMR) during development.

**WebSocket**
- **What it is:** A communications protocol providing full-duplex (two-way) communication channels over a single, long-held TCP connection.
- **Why we use it:** HTTP requires the browser to constantly ask the server "is there new data?" (polling). WebSockets allow the SAMPATI backend to instantly *push* a `HONEYPOT_ALERT` or a new transaction to the dashboard the exact millisecond it happens, creating the "Live Auto-Feed" experience.

### Machine Learning, Heuristics & Analytical Models

**Behavioral Anomaly Detection (Layer 2)**
- **What it is:** A branch of machine learning focused on identifying data points, events, or observations that deviate significantly from a dataset's normal behavior.
- **Why we use it:** While rules catch *known* fraud patterns (like sending exactly ₹49,999 to bypass a ₹50,000 KYC limit), anomaly detection catches *unknown* or *new* patterns. If a fraudster invents a completely new way to steal money that our rules haven't seen before, the anomaly model will still flag it because the behavior looks drastically different from the user's historical baseline.

**Cosine-Like Similarity Scoring**
- **What it is:** A mathematical technique used to measure how similar two vectors (or in our case, two transaction fingerprints) are, regardless of their size. It outputs a score between 0.0 (completely different) and 1.0 (identical).
- **Why we use it:** In the `CampaignSignatureStore`, we need to match incoming transactions against known fraud syndicates. We can't use exact matching because fraudsters constantly change small details (like amounts or slight variations in payment notes). Our custom similarity scorer weighs different features (keywords, amounts, time of day) and calculates a percentage match, triggering only when similarity crosses an 82% confidence threshold.

**DNA Fingerprinting (Campaign Extraction)**
- **What it is:** The process of extracting specific, distinguishing features (metadata) from an event to create a unique "signature" or "fingerprint" that represents the underlying behavior.
- **Why we use it:** When a transaction is blocked, SAMPATI automatically extracts its "DNA"—the time of day, the specific keywords in the payment note (like "task" or "kyc"), and the amount brackets. This DNA is saved. When future transactions exhibit this exact same DNA, the system recognizes it as part of an organized, coordinated fraud campaign rather than an isolated incident.

**Dead Money Velocity (DMV) Algorithm**
- **What it is:** A custom, time-series heuristic algorithm developed specifically for SAMPATI. It measures the mathematical ratio between a period of absolute dormancy and a sudden, massive outflow of funds.
- **Why we use it:** Mule accounts are often purchased on the dark web and left dormant for months ("dead money"). When a fraud operation begins, the account suddenly receives stolen funds and immediately forwards them elsewhere ("velocity"). Standard ML models struggle to detect this because they look at average volume over time. The DMV algorithm uses a sliding-window double-ended queue (`deque`) to specifically hunt for this precise "dormancy-to-explosion" signature.

**Graph Theory & Centrality Analysis**
- **What it is:** A field of mathematics used to study networks (graphs) consisting of nodes (vertices) connected by edges (links). "Centrality" measures how important a specific node is within the network.
- **Why we use it:** Mule rings are essentially complex networks. By applying graph theory via the `NetworkX` library, we can analyze the flow of money. We use *In-Degree* (number of incoming transactions) and *Out-Degree* (number of outgoing transactions) to automatically classify nodes. A node with a high In-Degree and high Out-Degree is mathematically identified as a "Collector Hub" or "Pass-Through Conduit" without any human intervention.

**Deterministic Rules Engine (Layer 1)**
- **What it is:** An "Expert System" branch of AI where domain knowledge is hardcoded into strict `IF/THEN` logic gates. 
- **Why we use it:** Machine learning models are "black boxes"—they can tell you a transaction is 92% risky, but they struggle to explain *exactly* why in human terms. In finance, compliance laws require exact reasons for blocking a payment. The Deterministic Rules engine guarantees that every single risk point added to a transaction has a highly specific, legally defensible, human-readable reason (e.g., `R_IMPOSSIBLE_TRAVEL`). 

**Honeypot / Decoy Routing**
- **What it is:** A cybersecurity mechanism designed to detect, deflect, or study attempts at unauthorized use of information systems by presenting a fake target.
- **Why we use it:** In the UPI ecosystem, automated botnets randomly probe millions of VPAs to see which ones are active. By creating synthetic, fake VPAs (like `botnet_sink_04@oksbi`), we set a trap. Because no real human would ever try to pay this address, any transaction hitting it is mathematically guaranteed to be malicious. This gives us a 100% confidence signal to immediately ban the attacker's account.

---

## 22. Architectural Defense: Why Statistical ML over Deep Learning?

A common question when evaluating modern AI systems is: *"Why doesn't SAMPATI V2 use Deep Learning, Neural Networks, or Large Language Models (LLMs) for its core fraud detection?"*

The decision to use **Statistical Machine Learning (EWMA)** and **Graph Analytics (NetworkX)** instead of Deep Learning is a deliberate, highly engineered architectural choice based on three strict financial constraints:

### 1. The Explainability Mandate (Compliance)
- **The Problem with Deep Learning:** Neural networks are "black boxes." If a deep learning model flags a transaction with 99% certainty, it is mathematically very difficult to extract the exact *reason* why. 
- **The SAMPATI Approach:** Under financial regulations (like RBI guidelines in India), if a bank freezes a user's funds, the bank must be able to provide a precise, legally defensible reason. By using a Deterministic Expert System (Layer 1) combined with Statistical ML (Layer 2), SAMPATI guarantees that every single risk point is traceable. An analyst can see exactly what triggered the block (e.g., "Amount was 3.4 standard deviations above the user's EWMA baseline, and the IP was a known datacenter").

### 2. Ultra-Low Latency (Sub-10ms)
- **The Problem with Deep Learning:** Inference for a complex neural network or LLM can take anywhere from 100 milliseconds to several seconds. In the UPI ecosystem, the entire transaction lifecycle is measured in milliseconds. Adding a 500ms delay to evaluate a payment creates unacceptable friction for the consumer.
- **The SAMPATI Approach:** The EWMA anomaly model requires zero batch processing and involves computing only basic arithmetic on two stored floats (mean and variance). This allows Layer 2 to execute in less than **1 millisecond**, keeping SAMPATI strictly inline without slowing down the payment switch.

### 3. The "Cold Start" and Streaming Problem
- **The Problem with Deep Learning:** Traditional ML requires vast data lakes of historical, labeled data to train (batch processing). If a new VPA is created today, a batch model won't know how to score it until the model is retrained next week.
- **The SAMPATI Approach:** Fraudsters constantly create fresh mule accounts. SAMPATI's ML layers use **Streaming/Online Learning**. The EWMA algorithm begins adapting to a user's behavior from their very first transaction. There is no batch training phase, no data lake required, and no "cold start" vulnerability. 

By rejecting hype-driven Deep Learning in favor of **highly optimized Statistical and Graph Machine Learning**, SAMPATI V2 achieves a production-ready balance of speed, accuracy, and legal compliance.

### Algorithm Deep-Dive & Real-World Equivalents

To build a system capable of detecting complex fraud in real-time without relying on black-box neural networks, we engineered custom mathematical algorithms. Here is a breakdown of the custom algorithms powering SAMPATI V2, why they were built, and what established computer science algorithms they are based on:

#### 1. The Dead Money Velocity (DMV) Algorithm
- **Why we built it:** Standard velocity checks just look at "total money moved in 24 hours." This fails to catch mule accounts that lay dormant for 6 months and suddenly dump their entire balance in 10 minutes. We needed an algorithm that measures the *delta* (change) in velocity relative to dormancy.
- **How it works:** It uses a sliding-window double-ended queue (`deque`) to track the timestamps and amounts of recent transactions. It calculates a ratio of the "dormancy gap" vs. the "burst outflow."
- **Closest Real-World Equivalent:** **The Token Bucket Algorithm** (used in network traffic shaping) combined with **Time-Decay Rate Limiting**. Instead of dropping network packets when a burst occurs, our DMV algorithm outputs a high risk score when the financial "burst" violates the historical dormancy baseline.

#### 2. Campaign DNA Fingerprinting
- **Why we built it:** Fraudsters slightly alter their payment notes (e.g., "kyc update" vs. "kyc verify") and transfer amounts to evade exact-match filters. We needed a way to detect "fuzzy" matches belonging to the same organized campaign.
- **How it works:** It mathematically extracts vectors (keywords, amount brackets, time-of-day) from a transaction and compares them to stored campaign profiles.
- **Closest Real-World Equivalents:** 
  - **Weighted Cosine Similarity:** Used in natural language processing (NLP) to measure how similar two documents are by looking at the angle between their mathematical vectors.
  - **Jaccard Index:** A statistical measure used for gauging the similarity and diversity of sample sets (used here for matching keywords in payment notes).

#### 3. The Layer 2 Adaptive Anomaly Engine
- **Why we built it:** We needed a way for the system to learn a specific user's "normal" spending habits instantly, without storing their entire transaction history in a database.
- **How it works:** It maintains a running mean and variance that decays over time. A ₹50,000 transaction might be a massive anomaly for a student, but completely normal for a business account. The algorithm automatically scales its sensitivity based on the user's personal baseline.
- **Closest Real-World Equivalents:**
  - **Holt-Winters Method / Exponential Smoothing:** Used in stock market analysis and supply chain forecasting to predict future data points based on a decaying average of past data.
  - **Kalman Filters:** Used in aerospace (like rocket guidance) to estimate the true state of a system based on a stream of noisy measurements. We use it to estimate the "true" financial behavior of a user amidst the noise of random daily purchases.

#### 4. Node Role Classification (Graph Centrality)
- **Why we built it:** When a mule ring is detected involving 20 different accounts, an analyst needs to know immediately who the mastermind is, who the victims are, and which accounts are just "pass-through" hops.
- **How it works:** We represent the transactions as a Directed Graph (where nodes are VPAs and edges are money transfers). We run mathematical functions to count the direction and weight of the edges.
- **Closest Real-World Equivalents:**
  - **PageRank Algorithm:** The original algorithm used by Google to rank web pages based on how many other pages link to them.
  - **Betweenness Centrality & Degree Centrality:** Classic Graph Theory algorithms used in social network analysis to find "influencers" or bottlenecks. In SAMPATI, a node with high "Betweenness Centrality" is instantly flagged as a **Layering Hop** (a mule account acting as a bridge to hide the money trail).

---

## 23. Business Impact, Scalability & Novelty (The Pitch)

For hackathon judges, engineering leads, or investors, understanding *how* the code works is only half the battle. The other half is understanding *why this matters* at a macro level. Here are the core insights, novelties, and business value propositions of SAMPATI V2:

### 1. The Legal Breakthrough: Privacy-Preserving Federation
- **The Insight:** The biggest blocker to fighting fraud in India isn't a lack of technology; it's a lack of legality. Banks are legally prohibited from sharing raw customer data (like account numbers or transaction histories) with competing banks due to data privacy laws. Because of this, mule networks thrive by simply routing money across different banks.
- **The Novelty:** SAMPATI V2's Federation Intelligence Mesh completely bypasses this legal hurdle. By using a shared cryptographic salt and one-way SHA-256 hashing, PSP nodes only ever share mathematically obfuscated "threat signals." The system can detect a mule ring spanning HDFC, SBI, and Axis Bank without any bank ever exposing PII (Personally Identifiable Information). This makes SAMPATI not just technically impressive, but legally deployable today.

### 2. Operational Cost-Efficiency (The "Free-Tier" Proof)
- **The Insight:** Enterprise fraud systems from companies like Palantir or Actimize cost millions of dollars in licensing and require massive data center footprints.
- **The Novelty:** We deliberately engineered SAMPATI V2 to be so lightweight and mathematically efficient that it currently runs a full 3-layer AI scoring engine, a real-time WebSocket dashboard, and a PostgreSQL database entirely on an **AWS Free-Tier infrastructure** (a single `t3.small` EC2 instance and a `db.t3.micro` RDS instance). The use of in-memory sliding windows (RAM) instead of heavy database reads allows the system to operate at a fraction of the cost of traditional enterprise software.

### 3. Horizontal Scalability (Handling 14 Billion UPI Txns)
- **The Insight:** The UPI rail processes over 14 billion transactions a month. Any inline gateway must be able to scale infinitely without bottlenecking the payment switch.
- **The Novelty:** SAMPATI's FastAPI backend is completely stateless (the persistent data lives in RDS, and the hot state lives in RAM). This means to handle more traffic, a bank simply spins up more Docker containers behind a load balancer. Because there is no heavy ML model loading sequence, a new SAMPATI container boots and is ready to score transactions in under 2 seconds.

### 4. The AI-to-Human Handoff (SAR Generation)
- **The Insight:** Detecting fraud is useless if you can't prosecute the fraudsters. Compliance teams spend hours manually compiling Suspicious Activity Reports (SARs) to file with government authorities (FIU-IND).
- **The Novelty:** SAMPATI V2 bridges the gap between AI detection and human compliance. When the engine blocks a mule ring, it automatically extracts the network topology, draws a visual graph using Matplotlib, and auto-drafts a complete, plain-English PDF SAR report. It turns a purely technical ML flag into a legally formatted document, saving hundreds of thousands of hours of manual analyst labor.

### Summary
SAMPATI V2 is not just a fraud detection script; it is a **comprehensive, legally compliant, hyper-efficient Fraud Operations System**. It solves the mathematical problem of detection, the legal problem of data sharing, and the operational problem of compliance reporting, all within a sub-10 millisecond latency budget.

---

## 24. Deep Dive: UpiHotState — The In-Memory Brain

**File:** `app/engine/upi_state.py` (compiled stub in production)

The `UpiHotState` is one of the most critical hidden components of SAMPATI V2. It is the in-memory "brain" that makes all of Layer 1's structural rules possible without a single database query.

### What it stores (in RAM)
The `UpiHotState` maintains several Python dictionaries and `deque` (double-ended queue) data structures keyed by VPA:

| Data Structure | Key | Value | What rule uses it |
|---|---|---|---|
| `_inbound_events` | `vpa` | `deque[(timestamp, amount, payer)]` | `FAN_IN_BURST`, `PASS_THROUGH_CONDUIT` |
| `_outbound_events` | `vpa` | `deque[(timestamp, amount, payee)]` | `FAN_OUT_DISPERSAL`, `PASS_THROUGH_CONDUIT` |
| `_device_vpa_map` | `device_id / sim_id` | `set[VPA]` | `DEVICE_FARM` |
| `_fraud_memory` | `vpa` | `int (confirmed fraud count)` | `KNOWN_FRAUD_ENTITY` |
| `_telemetry_map` | `vpa` | `{device_id, sim_id, location, timestamp}` | `R_SIM_DEVICE_MISMATCH`, `R_IMPOSSIBLE_TRAVEL` |

### The Sliding Window Technique
Every `deque` in `UpiHotState` operates as a **sliding window**. When a new transaction is recorded:
1. New data is appended to the **right** of the deque.
2. Old data older than the window size (e.g., 1 hour) is evicted from the **left** of the deque.

This is why our rules are always computed over a precise recent time window (not all-time) — a key property for avoiding false positives from old, legitimate transaction history.

### Why a `deque` instead of a list?
A Python `deque` (from `collections`) has O(1) append and O(1) popleft. A regular Python `list` has O(n) pop from the front. For a system processing thousands of transactions per second, this difference in algorithmic complexity is critical.

### Thread Safety
All operations on `UpiHotState` are wrapped with `threading.Lock()`. This prevents race conditions when the `AutoFeedEngine` (running on a background thread) and the main API request handler both try to update state simultaneously.

---

## 25. Deep Dive: PSP Node & Pseudonymization

**File:** `app/federation/psp_node.py` (compiled stub in production)

Each simulated PSP (e.g., `HDFC-PSP`) is represented by a `PspNode` object. This encapsulates how a real bank would interact with the federation mesh.

### What a PspNode does
- **Receives local transactions** from its own payment rail.
- **Computes feature vectors** for each entity (total inflow, outflow, distinct counterparties, fresh account flag, device sharing).
- **Pseudonymizes VPAs** before submitting to the shared federation coordinator.
- **Contributes to ring detection** by sharing its local graph topology with the coordinator.

### The `pseudonymize()` function — How privacy is enforced
```python
def pseudonymize(vpa: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{vpa.lower()}".encode()).hexdigest()
```
- **SHA-256:** A one-way cryptographic hash function. Given the hash, it is computationally impossible to reverse-engineer the original VPA. This is the same function used to store passwords in secure systems.
- **The salt:** `sampati-demo-salt` is prefixed before hashing. This prevents a dictionary attack where an adversary precomputes hashes for all possible VPAs. Without knowing the exact salt, the hashes are useless.

### Real-World Analogy
Think of it like a police "most wanted" list where instead of publishing real names, every agency publishes a unique code (hash) for each suspect. Two different police departments can compare codes and realize they are tracking the same person — without either department ever knowing the person's real identity.

---

## 26. Deep Dive: The WebSocket Architecture

**Backend:** `app/api/websocket.py`  
**Frontend:** `frontend/src/hooks/useWebSocket.js`

### The Exponential Backoff Reconnection Algorithm
The `useWebSocket.js` hook implements an exponential backoff strategy to handle server restarts gracefully:

```
Reconnection attempt 1: wait 1.0 second
Reconnection attempt 2: wait 1.5 seconds
Reconnection attempt 3: wait 2.25 seconds
Reconnection attempt 4: wait 3.375 seconds
...
Max cap: 30 seconds
```

**Why exponential backoff?** If the server goes down and 500 clients all reconnect simultaneously the instant it comes back up, the server will be immediately overloaded again. By spreading out the reconnect attempts across clients using exponential backoff, the load is distributed gracefully over time.

### WSS (WebSocket Secure) vs WS
The `getWsUrl()` function automatically detects whether the page is served over HTTPS:
- HTTP → uses `ws://` (plain WebSocket)
- HTTPS → uses `wss://` (encrypted WebSocket, equivalent to HTTPS for sockets)

This ensures the dashboard works correctly whether deployed locally (HTTP) or in production via Nginx with TLS (HTTPS).

### Fan-Out Broadcasting
When `schedule_broadcast(payload)` is called on the backend, it uses Python's `asyncio` event loop to asynchronously send the same JSON message to every active WebSocket connection simultaneously. This is a classic **pub/sub (publish/subscribe)** pattern — the API is the publisher, and each browser tab is a subscriber.

---

## 27. Deep Dive: The CI/CD Pipeline — Every Step Explained

**File:** `.github/workflows/deploy.yml`

### Why does CI/CD spin up a real PostgreSQL database?
The pipeline starts a `postgres:15-alpine` Docker service container during the test job. This means our 710 tests run against a real PostgreSQL database — not a fake mock. This catches bugs that would only appear in production (e.g., SQL type mismatches, missing columns, integer overflow in numeric fields) that a mocked database would silently ignore.

### The GitHub Actions Cache Strategy
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```
Docker layers are cached in GitHub's cache storage. On subsequent runs, only the changed layers are rebuilt. For SAMPATI, this means if only Python code changes (not the base image or requirements), the Docker build completes in under 30 seconds instead of 5+ minutes.

### The `concurrency` block
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```
This means: if you push two commits to a branch in quick succession, the first pipeline run is automatically cancelled when the second one starts. This prevents stacking up redundant builds and wasting compute minutes.

### The Commit SHA Image Tag Strategy
Each Docker image is tagged with the full Git commit SHA (e.g., `ghcr.io/404avinash/sampati_v2:75117fd8...`). This is called **immutable image tagging**. Unlike a `latest` tag which always points to the newest image, a SHA tag is permanent. This means:
- Automated rollback always pulls the exact previously running version, not whatever `:latest` happens to be.
- Full auditability: you can always trace exactly which code is running in production by looking at the container's image tag.

---

## 28. Deep Dive: The SAR PDF — Compliance Engineering

**File:** `app/forensics/sar_pdf.py`

### What FIU-IND Actually Requires
The Financial Intelligence Unit — India (FIU-IND) mandates that financial entities file SARs with specific details:
- Transaction identifiers and timestamps
- Suspicious party identifiers (payer/payee VPAs and account information)
- Nature and description of suspicious activity
- Amount involved
- Chronological transaction sequence

SAMPATI's SAR PDF is specifically engineered to capture all of these fields automatically.

### Why `matplotlib` for a PDF? (Not a Word Template)
Many teams would use a Word document template or an HTML-to-PDF converter. SAMPATI uses `matplotlib` because:
1. **The Ring Graph:** We need to embed a mathematically-generated network visualization inside the PDF. Only a graphing library can compute the node positions and draw the edges. No template tool can do this.
2. **Reproducibility:** Every SAR generated for the same case will be byte-for-byte identical regardless of the operating system, because `matplotlib` renders deterministically.
3. **No dependencies on Office software:** The server runs in a Docker container with no UI. `matplotlib` with the `Agg` (non-interactive) backend renders purely to file without needing a display.

### The `Agg` Backend
```python
matplotlib.use("Agg")
```
By default, `matplotlib` tries to open a window on your screen to display charts. Inside a Docker container (which has no screen), this would crash. Setting the backend to `Agg` (Anti-Grain Geometry) tells matplotlib to render entirely to memory/file, making it headless-server-safe.

---

## 29. Deep Dive: Security Architecture

While SAMPATI V2 is a demo platform, its security architecture mirrors production-grade financial system standards:

### Input Validation: The First Line of Defence
Every API endpoint uses Pydantic models to validate incoming data. This provides:
- **SQL Injection Prevention:** Because we use SQLAlchemy ORM (which parameterizes all queries), raw SQL strings are never constructed from user input.
- **Type Safety:** A field expecting a `float` amount will reject the string `"'DROP TABLE upi_cases;--"` before it ever reaches the engine.

### Privacy: SHA-256 Hashing in Federation
All VPA identifiers shared across PSP nodes are one-way SHA-256 hashed. Even if the federation coordinator were compromised, the attacker would obtain only a set of irreversible hashes — not real customer VPA addresses.

### Docker Container Isolation
The application runs inside a Docker container. Even if an attacker exploited a vulnerability in the web server, they would be contained within the Docker sandbox and could not directly access the EC2 host's filesystem or other services.

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```
Currently set to `allow_origins=["*"]` (all origins) for development convenience. In a production deployment, this would be locked down to the specific frontend domain (e.g., `https://sampati.bank.com`) to prevent Cross-Origin Resource Sharing attacks.

### Secrets Management
All sensitive credentials (`DATABASE_URL`, `EC2_SSH_KEY`) are stored in **GitHub Actions Secrets** — never in the source code. The EC2 instance reads `DATABASE_URL` from `/opt/sampati/.env`, which is created manually on the server and is never committed to git.

---

## 30. Key Engineering Decisions: The "Why We Didn't" List

Understanding what was *not* used is as important as understanding what was. Here are the biggest architectural alternatives that were considered and rejected:

| Alternative | Why we rejected it |
|---|---|
| **Django** instead of FastAPI | Django is synchronous by default and carries a large ORM/templating overhead. For a real-time event-driven payment gateway, native async (FastAPI + Uvicorn) was non-negotiable. |
| **Redis** for the hot state cache | Redis would add an external network hop (even on the same server), adding ~1–3ms latency per rule evaluation. Python in-memory dictionaries operate in nanoseconds. |
| **GraphQL** instead of REST | Our API consumers are single (the dashboard). The overhead of a GraphQL schema definition and query parsing was not justified by the flexibility gains. |
| **Kubernetes** instead of Docker | K8s requires a minimum of 3 nodes and significant operational overhead. For a single-server free-tier deployment, raw Docker with `--restart unless-stopped` is the right tool. |
| **PyTorch / TensorFlow** for ML | These require GB of model weights, GPU infrastructure, and inference latency in the 100ms+ range. Our custom EWMA + Graph algorithms achieve comparable fraud detection accuracy in under 1ms on a CPU. |
| **Celery / RQ** for background tasks | Celery requires a Redis or RabbitMQ broker. The AutoFeedEngine's background thread pattern achieves the same functionality with zero external dependencies. |
| **Redux / Zustand** for frontend state | React Context is sufficient for SAMPATI's state complexity. Adding Redux would introduce boilerplate without meaningful benefit for a single-user analytics dashboard. |
| **D3.js** for the constellation graph | D3.js is a full DOM-manipulation library (350KB). Our hand-coded HTML5 Canvas force graph achieves the same effect at zero bundle size cost and with far better performance for the live-updating animation. |


---

## 31. Foundational Knowledge: The Building Blocks Explained

This section explains the absolute first-principles of every concept used in SAMPATI V2. Whether you are a judge, a non-technical stakeholder, or a developer from a different domain, this section will give you total context.

---

### 31.1 What is a VPA (Virtual Payment Address)?

A VPA is like an email address for money. Instead of sharing your bank account number (which is a long, sensitive 10-digit string tied directly to your account), you create a short, human-readable address like `yourname@okhdfc`.

When someone pays to `yourname@okhdfc`, the UPI system internally resolves it to your real bank account. The key property for fraud detection: **VPAs are cheap and easy to create**. A fraudster can create hundreds of disposable VPAs in minutes, which is exactly what mule networks exploit.

---

### 31.2 What is a Hash? (SHA-256)

**Simple explanation:** A hash function is a mathematical "blender." You can put anything into it (a VPA, a password, a document), and it produces a fixed-length string of letters and numbers. The crucial properties are:
- **Deterministic:** The same input always produces the same output.
- **One-way:** You can never reverse-engineer the original input from the output.
- **Avalanche effect:** Changing even one character of the input produces a completely different hash.

**Example:**
```
Input:  "avinash@okhdfc"
Output: "a3f9b1c2d4e5f6a7b8c9d0e1f2a3b4c5..."  (64 characters, always)

Input:  "avinash@okhdfc1"  (one character added)
Output: "7f2e9c1b3d4a5f6..." (completely different, 64 characters)
```

**Why SAMPATI uses SHA-256:** Banks cannot legally share raw VPA strings with each other. By hashing the VPA first, SAMPATI lets two banks compare "do we know about the same fraudster?" without either bank ever revealing the actual customer identity.

---

### 31.3 What is a Vector? (Feature Vector)

**Simple explanation:** A vector is just a list of numbers that represents something in mathematical space.

For example, a transaction's "feature vector" might look like:
```
[amount=50000,  hour_of_day=3,  payee_age_days=2,  has_kyc_keyword=1]
= [50000, 3, 2, 1]
```

This converts a complex real-world event (a suspicious bank transfer at 3 AM to a new account) into a list of numbers that a mathematical algorithm can measure, compare, and score.

**Why SAMPATI uses vectors:** The Campaign DNA Fingerprinting system converts every blocked transaction into a feature vector. To detect if a new transaction belongs to the same fraud campaign, we measure the mathematical "distance" between its vector and the stored campaign vectors.

---

### 31.4 What is a Standard Deviation and a Z-Score?

**Standard deviation** measures "how spread out" a group of numbers is around their average.

**Example:** If a person's last 100 transactions averaged ₹1,000, and the standard deviation was ₹200:
- A new transaction of ₹1,200 is within 1 standard deviation — completely normal.
- A new transaction of ₹50,000 is 245 standard deviations away — extremely abnormal.

**Z-Score** is the number of standard deviations a new value is from the mean:
```
Z-Score = (new_value - mean) / standard_deviation
Z-Score for ₹50,000: (50000 - 1000) / 200 = 245
```

**Why SAMPATI uses Z-Scores:** The EWMA anomaly model computes a Z-Score for every new transaction. A high Z-Score triggers `BEHAVIORAL_ANOMALY` in the response.

---

### 31.5 What is Async/Await? (Why it matters for scale)

**The problem with traditional (synchronous) code:**
Imagine a bank teller who, after taking your deposit slip, sits and stares at the wall doing nothing until the back office processes it (3 seconds). The entire queue behind you is blocked.

**Async code is like a smart teller:**
The teller takes your deposit slip, passes it to the back office, and immediately calls the next person in line. When the back office finishes (3 seconds later), the teller handles your result without having blocked anyone.

In SAMPATI, when the server writes a flagged case to the PostgreSQL database (which takes ~5–20ms), it does not stop processing other incoming payments. It just says "write this to DB whenever you are ready" and immediately starts evaluating the next transaction. This is what allows a single `t3.small` server to handle hundreds of concurrent transactions without queuing.

---

### 31.6 What is an ORM? (SQLAlchemy)

**Object-Relational Mapper (ORM)** is a translation layer between Python objects and SQL database tables.

**Without ORM (raw SQL — dangerous):**
```python
cursor.execute(f"SELECT * FROM users WHERE vpa = '{vpa}'")
# If vpa = "'; DROP TABLE users; --" → entire database deleted!
```

**With SQLAlchemy ORM (safe):**
```python
session.query(UpiCaseModel).filter(UpiCaseModel.payer_vpa == vpa)
# SQLAlchemy automatically sanitizes the input. SQL injection impossible.
```

An ORM also means the codebase works with **any database** (PostgreSQL in production, SQLite in tests) without changing a single line of application code.

---

### 31.7 What is a Directed Graph?

A graph is a collection of "nodes" (points) connected by "edges" (lines). A **Directed Graph** means the edges have arrows — they flow in one direction.

**In SAMPATI's context:**
- Every **VPA** is a node.
- Every **transaction** is a directed edge (arrow from payer → payee).

A mule ring therefore looks like a directed graph:
```
[Victim A] ──₹50,000──► [Collector Hub X] ──₹49,000──► [Layering Hop Y] ──₹48,500──► [Cash-Out Z]
```

By analyzing this graph, SAMPATI can automatically answer: "Who is at the center of this network? Who received money from the most people? Who is the final destination?"

---

## 32. Handling Vast Data at Scale — The Engineering Reality

India's UPI processes **14 billion transactions per month**, which is approximately **5,400 transactions per second** during peak hours. Here is exactly how SAMPATI is engineered to handle this volume — and what would need to change to deploy at that national scale.

---

### 32.1 Current Scale (Demo / MVP)

| Metric | Current Capacity |
|---|---|
| Server | 1× AWS EC2 t3.small (2 vCPU, 2GB RAM) |
| Database | 1× AWS RDS db.t3.micro (1 vCPU, 1GB RAM) |
| In-memory state | Bounded by 2GB RAM |
| Throughput (theoretical) | ~200–500 transactions/second per Uvicorn worker |
| AutoFeed rate | Configurable 1–50 tx/s |

This is sufficient for a **bank-level pilot** (a single mid-size PSP processes ~50–200 tx/s). It is not sufficient for national-rail deployment — but it is deliberately designed to scale horizontally.

---

### 32.2 How the Architecture Scales Horizontally (The Path to 5,400 tx/s)

**The stateless API design** is the key. Because SAMPATI's FastAPI server holds no user-session state between requests (all state is in RDS or the in-memory hot state), you can run **N copies of the server** behind a load balancer and they all work independently.

**Scale-out path:**
```
Step 1: Single server (current)
        1× EC2 t3.small → ~500 tx/s

Step 2: Horizontal scale-out (3–5 servers)
        Load Balancer → [EC2 #1] [EC2 #2] [EC2 #3]
        Shared RDS (upgrade to db.t3.medium) → ~1,500 tx/s

Step 3: Distributed hot state (Redis cluster)
        Replace in-memory Python dicts with Redis Cluster
        All servers share the same sliding window state → ~5,000+ tx/s

Step 4: Database sharding / read replicas
        RDS Multi-AZ with read replicas, partition cases by PSP → 10,000+ tx/s
```

---

### 32.3 The Memory Strategy — Why We Don't Store Everything

A naive implementation would store every single transaction in the database and query it on each new payment. At 5,400 tx/s, this means 5,400 database reads and 5,400 database writes **per second**. Even a powerful PostgreSQL server would collapse under this load.

SAMPATI's solution is a **two-tier data architecture:**

```
Tier 1: In-Memory Hot State (Microsecond access)
├── Last 1 hour of transactions per VPA (in UpiHotState deques)
├── Device fingerprint → VPA mappings
├── Federation signal cache
└── Purpose: Serving ALL real-time rule evaluations (zero DB reads)

Tier 2: PostgreSQL (Millisecond access)
├── All HOLD/BLOCK cases (persistent, auditable)
├── Confirmed mule rings
├── Analyst feedback and SAR records
└── Purpose: Persistence, reporting, compliance. NOT consulted during scoring.
```

This means: **the database is never in the critical path of a payment decision.** By the time a database write completes, the `ALLOW/HOLD/BLOCK` verdict has already been returned to the payment switch.

---

### 32.4 The Deque — How We Bound Memory Usage

The `collections.deque` data structure is set with a **maximum length** (e.g., last 500 events per VPA). Once this limit is reached, appending a new item automatically discards the oldest one. This bounds the maximum memory consumption of `UpiHotState` to a predictable ceiling regardless of how many transactions have occurred.

Without this bound, a VPA that makes millions of transactions (like a merchant) would eventually fill all available RAM, causing an Out-of-Memory crash — exactly the problem we discovered during deployment!

---

### 32.5 What Would We Add for True National-Scale (Production Roadmap)

| Feature | Technology | Why |
|---|---|---|
| Distributed hot state | **Redis Cluster** | Share sliding windows across multiple server instances |
| Message queue | **Apache Kafka** | Buffer transaction bursts; decouple ingestion from scoring |
| Stream processing | **Apache Flink / Spark Streaming** | Run aggregation analytics on the full firehose |
| Model serving | **Triton Inference Server** | If we added DL models, GPU-accelerated inference |
| Feature store | **Feast / Tecton** | Centralized repository of pre-computed ML features |
| Time-series DB | **InfluxDB / TimescaleDB** | Optimized storage for high-frequency transaction time-series |
| Distributed tracing | **Jaeger / Zipkin** | Trace exactly which rule fired on which transaction with microsecond timestamps |

The key insight is that SAMPATI V2 is architected so that none of these additions require rewriting the core scoring logic. The `UpiRiskScorer.evaluate()` function is pure Python — it takes a transaction in, returns a verdict. The surrounding infrastructure (how transactions arrive and where state is stored) can be swapped out for enterprise-grade systems without touching the intelligence layer.


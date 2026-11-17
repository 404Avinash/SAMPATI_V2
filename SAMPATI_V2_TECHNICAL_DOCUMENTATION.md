# SAMPATI V2: Master Technical Specification & Architecture Manual
## Autonomous Distributed UPI Mule-Network Interception Platform

**Document Version:** 2.0.0  
**Classification:** Sovereign Financial Technology Specification / Technical Documentation  
**Target Architecture:** India Unified Payments Interface (UPI) & Digital Payments Intelligence Platform (DPIP)  
**System Repository:** `404Avinash/SAMPATI_V2`  
**Execution Runtime:** Python 3.14 (FastAPI + AsyncPG + NumPy) / Node.js (React 18 + Vite 5 + Tailwind CSS)  
**Verification Baseline:** 977 Pytest Suite (0 Failures), Strict ESLint (`--max-warnings 0`), Clean Production Vite Bundle  
**Date:** September 2026  

---

# Table of Contents
1. [Executive Summary & Architecture Philosophy](#1-executive-summary--architecture-philosophy)
   - 1.1 High-Velocity UPI Payment Defense-in-Depth
   - 1.2 Sub-5ms Inline Decision Budget vs. Asynchronous Operations
   - 1.3 Human-in-the-Loop Explainability & Regulatory Compliance
   - 1.4 Core Architectural Pillars
2. [Complete Repository Layout & Directory Index](#2-complete-repository-layout--directory-index)
   - 2.1 Top-Level Architecture & Root Artifacts
   - 2.2 Backend Application Directory (`/app`)
   - 2.3 Frontend Application Directory (`/frontend`)
   - 2.4 Test Suite Catalog (`/tests`)
   - 2.5 Configuration & Deployment Artifacts
3. [Frontend Architecture (React 18 + Vite 5)](#3-frontend-architecture-react-18--vite-5)
   - 3.1 Build Tooling, Vite Proxy & Strict Code Quality
   - 3.2 Client-Side Routing & Page Hierarchy (React Router v6.28.0)
   - 3.3 State Management, Ambient Traffic & Sliding-Window Bucketing
   - 3.4 Visualizers & Physics Engine
     - 3.4.1 Custom HTML5 Canvas Physics Engine (`NetworkConstellation.jsx`)
     - 3.4.2 Geodetic Indian Mule Corridors Map (`GeoMuleMap.jsx`)
     - 3.4.3 Metric Charts, Velocity Areas & Dead Money Velocity Arc Gauges
   - 3.5 Forensic UI, 3-Tier Image Fallback & Gemini AI Copilot
   - 3.6 Styling System & Sovereign FinTech Design Tokens
   - 3.7 Networking Layer: Self-Healing WebSockets & Binary PDF Streaming
4. [Backend Architecture & Service Ecosystem (FastAPI)](#4-backend-architecture--service-ecosystem-fastapi)
   - 4.1 Application Lifecycle, Async Lifespan & Configuration Management
   - 4.2 Single-Page Application (SPA) Fallback Handler & Static Mounts
   - 4.3 API Router Catalog & Complete 63-Endpoint Taxonomy
   - 4.4 Service Layer Architecture
     - 4.4.1 `UpiCaseService`
     - 4.4.2 `FraudGraphService` (NetworkX Multi-Entity Directed Graph)
     - 4.4.3 `ThreatIntelService` (Regex Extraction & Syndicate Clustering)
     - 4.4.4 `AutoFeedEngine` (Daemon Traffic Generator)
     - 4.4.5 `InstitutionalAdapterService` (NPCI MuleHunter & DPIP Registry)
     - 4.4.6 `NotificationService` (FCM HTTP v1 & Hermetic Mock)
     - 4.4.7 `GeminiAssistantService` (Autonomous AI Investigator)
   - 4.5 Data Models, Pydantic Schemas & SQLAlchemy 2.0 ORM Persistence
5. [End-to-End Data Pipeline & Real-Time Flow](#5-end-to-end-data-pipeline--real-time-flow)
   - 5.1 Inline Transaction Processing Flow (Ingress to Egress)
   - 5.2 Real-Time WebSocket Broadcasting Hub & Connection Management
   - 5.3 Dashboard Telemetry Aggregation & Latency Percentiles ($p_{50}, p_{90}, p_{99}$)
6. [Database & Cache Infrastructure](#6-database--cache-infrastructure)
   - 6.1 PostgreSQL Relational Storage & Connection Pooling
   - 6.2 Relational DDL, Compound Indices & Dynamic JSONB Forensics
   - 6.3 Dual-Mode Operation & In-Memory Fallback (`AsyncDatabaseStore`)
   - 6.4 Redis Hot State Engine, Key Schema & Sliding-Window Velocity
   - 6.5 Distributed Idempotency Locks & In-Process `UpiHotState`
7. [Machine Learning & Generative AI Engine Breakdown](#7-machine-learning--generative-ai-engine-breakdown)
   - 7.1 Layer 1: Deterministic Rules Engine & Mathematical Formulations
     - 7.1.1 13 Heuristic Rule Catalog & Point Allocations
     - 7.1.2 Dead Money Velocity (DMV) Engine Formulation
     - 7.1.3 Impossible Travel Haversine Kinematics & Subnet CIDR Traps
     - 7.1.4 Fraud Campaign DNA Fingerprinting & Cosine Matching
   - 7.2 Layer 2: Unsupervised Anomaly Detection (Isolation Forest in Pure NumPy)
     - 7.2.1 Mathematical Path Length Factor $c(n)$ & Anomaly Score $s(x,n)$
     - 7.2.2 13 Standardized Aligned Behavioral Features
     - 7.2.3 Contamination Baseline & Zero-Regression Calibration Function
   - 7.3 Layer 3: Supervised Classification (Random Forest in Pure NumPy)
     - 7.3.1 Decision Tree Bagging, Gini Impurity & Balanced Bootstrap Sampling
     - 7.3.2 Probability Calibration Curve
     - 7.3.3 PaySim Benchmark Performance (F1: 0.9627, 83.3% FN Reduction)
   - 7.4 Ensemble Scoring Logic, Linear Combination & Safety Override Floors
   - 7.5 Layer 4: Generative AI & Google Gemini Integration
     - 7.5.1 Multi-Model Failover Cascade & HTTP REST Architecture
     - 7.5.2 Deep Context Injection & Encyclopedia Knowledge Base
     - 7.5.3 Autonomous Agentic Tool Calling & Offline Intent Routing
     - 7.5.4 45x Multimodal Visual Token Economy Compression
     - 7.5.5 Statutory FIU-IND Form 17B SAR 2-Page PDF Pipeline
8. [Operational Guide, Verification & Tooling](#8-operational-guide-verification--tooling)
   - 8.1 Verification Command Matrix & Test Results
   - 8.2 Safe-Push Automated Zero-Friction Protocol
   - 8.3 Operational Runbooks & Troubleshooting

---

# 1. Executive Summary & Architecture Philosophy

## 1.1 High-Velocity UPI Payment Defense-in-Depth
India's Unified Payments Interface (UPI), orchestrated by the National Payments Corporation of India (NPCI), processes tens of thousands of transactions per second, representing the largest and fastest real-time retail payment railway on earth. However, the extreme velocity and near-zero settlement friction of UPI have been aggressively exploited by sophisticated cybercrime syndicates. Organized rings execute multi-hop smurfing, digital arrest scams, task-fraud schemes, and mule layering, routing illicit proceeds through dozens of compromised intermediary accounts within minutes before cashing out via ATMs or crypto-rails.

**SAMPATI V2** (*Synchronous Anti-Mule Platform for Account Tracking & Interception*) is an institutional-grade, real-time fraud defense platform engineered specifically for this operational environment. Rather than relying on a single monolithic scoring algorithm, SAMPATI V2 institutes a rigorous **Multi-Layer Defense Architecture**:

```
                       [ Incoming UPI Transaction ]
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    INLINE DECISION GATE (< 5ms SLA)                       │
│                                                                           │
│  Layer 1: Deterministic Heuristics (< 0.3ms)                              │
│  • Synthetic Honeypot VPA Traps (Immediate BLOCK, 100 pts)                │
│  • Kinematic Impossible Travel Velocity (Haversine v > 1000 km/h)         │
│  • Hardware Device / SIM Telemetry Mismatch & Datacenter CIDR Blocks      │
│  • Dead Money Velocity (DMV) Tracker (Dormancy vs. Burst Drain)           │
│  • Campaign DNA Matching & Pass-Through Conduits                          │
│                                   │                                       │
│  Layer 2: Unsupervised Anomaly Detection (< 0.5ms)                         │
│  • Pure NumPy Isolation Forest (50 iTrees, sub-sample=128, height<=7)     │
│  • Evaluates 13 standardized behavioral features against clean baselines   │
│  • Zero-Regression Guarantee (< 0.50 score contributes 0 risk points)     │
│                                   │                                       │
│  Layer 3: Supervised Classification (< 0.6ms)                             │
│  • Pure NumPy Random Forest (30 Balanced Trees, Gini Impurity splits)     │
│  • Resolves subtle mule fraud; reduces False Negatives by 83.3%           │
│                                   │                                       │
│  Ensemble Scoring & Hard Override Floors (< 0.2ms)                        │
│  • Linear combination: Combined = Rule + Adaptive + Network + ML          │
│  • Strict Hard Floors: If Network >= 0.70 or ML >= 0.85 -> Force HOLD    │
│  • Action Gating: >= 70 BLOCK | >= 45 HOLD | < 45 ALLOW                  │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│       LAYER 4: GENERATIVE AI & AUTONOMOUS FORENSIC COPILOT                │
│                                                                           │
│  • Autonomous Google Gemini 1.5 Flash Reasoning Engine                    │
│  • Deep Context Injection: Live Case Dossier + Rule Encyclopedia KB      │
│  • Agentic Tool Dispatch: Freezes VPAs, forces Federation rounds, sim      │
│  • 45x Multimodal Token Compression (258 vision tiles vs 15k JSON tokens) │
│  • Statutory FIU-IND Form 17B SAR 2-Page Vector PDF Compilation           │
│  • Deterministic Offline Intent Routing (Zero-Degradation sans API Key)   │
└───────────────────────────────────────────────────────────────────────────┘
```

## 1.2 Sub-5ms Inline Decision Budget vs. Asynchronous Operations
In retail payment switching, strict Service Level Agreements (SLAs) dictate that any pre-debit fraud evaluation must return an authorization verdict in **under 10 milliseconds**, with SAMPATI V2 establishing an internal inline processing ceiling of **$< 5\text{ms}$** (empirically executing in $1.2\text{ms} - 1.5\text{ms}$).

To honor this constraint without compromising security:
1. **Synchronous Inline Path**:
   - Executes Layer 1 (Rules), Layer 2 (Isolation Forest), Layer 3 (Random Forest), and in-memory hot state lookups entirely in pure Python and NumPy without disk I/O or external network RPCs.
   - Operates in-process with zero C-runtime or external engine overhead.
   - Emits an immediate binary verdict (`ALLOW`, `HOLD`, `BLOCK`) directly back to the payment switch.
2. **Asynchronous Background Path**:
   - Cross-PSP federated graph rounds, database transaction logging (PostgreSQL `asyncpg`), WebSocket push broadcasts, deep forensic graph visualization generation, and Layer 4 Generative AI briefings operate out-of-band via asynchronous background tasks (`asyncio.create_task` and worker threads).
   - This prevents heavy database transactions or LLM API latencies ($\sim 800\text{ms}$) from ever blocking the real-time payment authorization rail.

## 1.3 Human-in-the-Loop Explainability & Regulatory Compliance
Freezing a sovereign citizen's bank account or intercepting an active financial transaction under Indian law (Prevention of Money Laundering Act, 2002; Section 12, and RBI Master Directions on Cyber Fraud) requires strict legal justification. Black-box deep learning models that cannot provide deterministic, explainable rationale are legally indefensible and create severe regulatory liabilities.

SAMPATI V2 guarantees **Human-in-the-Loop (HITL) Explainability**:
- **Deterministic Point Allocation**: Every blocked or held transaction provides an itemized breakdown of exact rule codes triggered (e.g., `R_HONEYPOT_HIT (+100)`, `PASS_THROUGH_CONDUIT (+30)`, `DMV_RAPID_DRAIN (+25)`).
- **Algorithmic Transparency**: The system includes a built-in Encyclopedia Knowledge Base (`app/engine/encyclopedia_kb.py`) detailing the exact mathematical formulation, plain-English rationale, and statutory typology mapping for every rule.
- **Investigator Console**: Human compliance officers are provided with interactive, real-time investigation tools: dynamic force-directed cluster topologies, geographic movement maps, AI-generated executive briefings, and one-click generation of statutory Suspicious Activity Reports (SAR).
- **Immutable Feedback Loop**: Analysts can confirm fraud or dismiss false positives via `/upi/cases/{case_id}/feedback`, which automatically updates the in-memory fraud memory, updates account baselines, and syncs hotlisted entities to the national Digital Payments Intelligence Platform (DPIP).

## 1.4 Core Architectural Pillars
SAMPATI V2 is constructed on five core engineering pillars:
1. **Ultra-Low Latency**: Pure NumPy vectorized inference and in-process deque/sorted-set sliding windows deliver $<2\text{ms}$ evaluation times on commodity CPU hardware.
2. **Zero-Regression Guarantee**: Unsupervised anomaly detection is calibrated so that clean retail traffic ($s \le 0.50$) contributes exactly **0 risk points**, preventing false positive inflation on legitimate banking volume.
3. **Resilience & Dual-Mode Fallbacks**: Every external infrastructure component features an automatic, zero-configuration in-memory fallback (PostgreSQL $\leftrightarrow$ `AsyncDatabaseStore`, Redis $\leftrightarrow$ `InMemoryStore` / `UpiHotState`, Gemini AI $\leftrightarrow$ Encyclopedia KB, FCM HTTP v1 $\leftrightarrow$ `MockFcmProvider`).
4. **Privacy-Preserving Consortium Federation**: Financial institutions collaborate without sharing Personally Identifiable Information (PII) or customer names. All cross-PSP indicators are exchanged as salted SHA-256 hashes of Virtual Payment Addresses (`hash_vpa(vpa)`), adhering to RBI privacy mandates.
5. **Deterministic Offline Readiness**: If external internet connectivity is severed or cloud LLM APIs experience outages, the built-in deterministic intent router and SVG topology visualizers allow the entire platform to function offline without degradation.

---

# 2. Complete Repository Layout & Directory Index

## 2.1 Top-Level Architecture & Root Artifacts
The repository root (`/home/avi/Downloads/Sampati_v2`) is organized as follows:

| Path / File | Type | Description |
|---|---|---|
| `app/` | Directory | FastAPI backend application, ML engines, adapters, database models, and service layer |
| `frontend/` | Directory | React 18 + Vite 5 Single Page Application (SPA), visualizers, and state contexts |
| `tests/` | Directory | Comprehensive automated test suite (977 unit, boundary, stress, and E2E tests) |
| `static/` | Directory | Static assets, dynamic forensic graphs (`static/upi_cases/`), and export artifacts |
| `data/` | Directory | Reference data files and seed corpuses |
| `deploy/` | Directory | Cloud deployment templates and infrastructure configuration |
| `AGENTS.md` | File | Repository operational rules, test suite guidelines, and automated safe-push protocol |
| `PROJECT.md` | File | Project milestones, feature inventory, interface contracts, and code layout standards |
| `ARCHITECTURE.md` | File | High-level system topology, module interfaces, and design specifications |
| `ENCYCLOPEDIA.md` | File | Exhaustive fraud typology manual, algorithmic formulations, and statutory definitions |
| `SAMPATI_DEEP_DIVE.md` | File | In-depth technical breakdown of ML algorithms, math models, and database design |
| `SAFE_PUSH_WORKFLOW.md`| File | Zero-friction automated validation, linting, build, and Git push sequence |
| `TEST_INFRA.md` | File | Test runner configuration, fixture setup, and mock environment architecture |
| `pyproject.toml` | File | Python project configuration, dependencies, and pytest settings |
| `requirements.txt` | File | Minimal pinned pip requirements for backend dependencies |
| `Dockerfile` | File | Multi-stage production container image bundling backend and pre-built frontend SPA |
| `docker-compose.yml` | File | Multi-container orchestration (FastAPI application, PostgreSQL, Redis) |

## 2.2 Backend Application Directory (`/app`)
The backend is structured as an asynchronous micro-monolith in `/home/avi/Downloads/Sampati_v2/app`:

```
app/
├── main.py                          # Application gateway, lifespan, CORS, SPA fallback handler, root endpoints
├── config.pyc                       # Pydantic Settings model loading environment configuration
├── adapters/                        # Institutional signal adapters
│   ├── __init__.py
│   ├── dpip.py                      # Digital Payments Intelligence Platform (DPIP) client adapter
│   ├── npci.py                      # Simulated NPCI MuleHunter switch telemetry adapter
│   ├── psp.py                       # Simulated peer PSP fraud signal adapter
│   └── service.py                   # InstitutionalAdapterService aggregating external signals
├── api/                             # FastAPI API route modules
│   ├── __init__.pyc
│   ├── adapters.py                  # Endpoints for institutional adapters (/adapters)
│   ├── cases.pyc                    # Legacy case endpoints
│   ├── federation.py                # Consortium federation endpoints (/federation)
│   ├── gateway.pyc                  # Core gateway routing endpoints
│   ├── intel.py                     # Early warning threat intelligence endpoints (/intel, /threat-intel)
│   ├── notifications.py             # Push notification endpoints (/notifications)
│   ├── synthetic.pyc                # Synthetic traffic injection endpoints (/synthetic)
│   ├── upi.py                       # Core real-time UPI interception endpoints (/upi)
│   └── websocket.py                 # Real-time WebSocket broadcasting hub (/ws, /ws/feed)
├── db/                              # Relational database persistence
│   ├── __init__.pyc
│   ├── init_db.pyc                  # Database table creation helper
│   └── session.py                   # AsyncPG engine, connection pooling, AsyncDatabaseStore fallback
├── dpip/                            # Regulatory feeds
│   ├── __init__.pyc
│   └── feed.pyc                     # DPIP blacklist synchronization worker
├── engine/                          # Machine learning and rule engines
│   ├── __init__.py
│   ├── adaptive.pyc                 # Layer 2 EWMA adaptive behavioral baselining model
│   ├── campaign.py                  # Fraud Campaign Signature Store & Cosine DNA matching
│   ├── dmv.py                       # Dead Money Velocity (DMV) state machine & formulas
│   ├── encyclopedia_kb.py           # Algorithmic and Regulatory Rule Encyclopedia Knowledge Base
│   ├── honeypot.py                  # Synthetic Honeypot Registry & Decoy VPA Trap Manager
│   ├── isolation_forest.py          # Layer 2 Pure NumPy Isolation Forest Anomaly Detector
│   ├── redis_state.pyc              # Redis hot state client, sliding window ZSETs, locks
│   ├── rules.pyc                    # Legacy bulk payout heuristics
│   ├── scorer.pyc                   # Legacy composite risk scorer
│   ├── supervised_classifier.py     # Layer 3 Pure NumPy Random Forest Supervised Classifier
│   ├── train_supervised.py          # Supervised model training script & PaySim benchmark pipeline
│   ├── upi_rules.py                 # Layer 1 Deterministic Rules Engine (13 rules, Geo, CIDRs)
│   ├── upi_scorer.py                # Ensemble risk scorer, combination formulas, override floors
│   ├── upi_state.pyc                # In-memory thread-safe 1800s deque sliding window (UpiHotState)
│   └── artifacts/
│       └── supervised_fraud_model.pkl # Serialized pure NumPy trained Random Forest model
├── federation/                      # Cross-PSP consortium intelligence
│   ├── __init__.pyc
│   ├── coordinator.py               # FederatedCoordinator, privacy-preserving ring agglomeration
│   └── psp_node.pyc                 # Individual participating PSP node model
├── forensics/                       # Forensic artifacts and regulatory reporting
│   ├── __init__.py
│   ├── investigator.pyc             # Automated forensic investigation workflow
│   ├── renderer.pyc                 # Network topology graph image rendering
│   ├── sar_pdf.py                   # FIU-IND Form 17B Suspicious Activity Report 2-page PDF generator
│   ├── service.pyc                  # Forensics service coordinator
│   ├── token_economy.pyc            # Multimodal token economy compression calculations
│   └── upi_sar.pyc                  # Markdown SAR narrative synthesis
├── models/                          # Data models and schemas
│   ├── __init__.pyc
│   ├── db_models.pyc                # Legacy ORM models
│   ├── pydantic_models.pyc          # Legacy Pydantic schemas
│   ├── threat_intel.py              # Threat intelligence models, regex extractors, graph schemas
│   ├── upi_models.py                # Core UPI transactions, evaluation responses, and rule hit models
│   └── upi_persistence.py           # SQLAlchemy 2.0 ORM models (upi_cases, mule_rings, feedback, stats)
├── services/                        # Service layer orchestration
│   ├── __init__.pyc
│   ├── autofeed.py                  # AutoFeedEngine: Background synthetic traffic generator
│   ├── gemini_service.py            # Layer 4 Google Gemini GenAI Copilot & agentic tool executor
│   ├── graph_service.py             # FraudGraphService: Multi-entity NetworkX directed graph
│   ├── notification_service.py      # Push notification service (FCM HTTP v1 & Mock)
│   ├── threat_intel_service.py      # Early warning threat intelligence ingest & campaign clustering
│   └── upi_cases.py                 # UpiCaseService: Central case manager, telemetry, & analytics
└── synthetic/                       # Test data generation
    └── __init__.pyc
```

## 2.3 Frontend Application Directory (`/frontend`)
The frontend is a modern, modular React 18 Single Page Application located in `/home/avi/Downloads/Sampati_v2/frontend`:

```
frontend/
├── index.html                       # HTML5 entry point, Google Fonts (Source Serif 4, Inter, IBM Plex Mono)
├── package.json                     # Frontend dependencies, scripts (dev, build, lint, preview)
├── package-lock.json                # Pinned dependency lockfile (cleanly resolved)
├── vite.config.js                   # Vite build configuration & backend development proxy
├── tailwind.config.js               # Tailwind design system tokens, colors, keyframes, typography
├── postcss.config.js                # PostCSS autoprefixer configuration
├── .eslintrc.cjs                    # Strict ESLint configuration (--max-warnings 0 rule)
├── dist/                            # Production build bundle (dist/index.html, dist/assets/)
└── src/
    ├── main.jsx                     # Concurrent React root mount, StrictMode
    ├── App.jsx                      # Context providers, React Router DOM route hierarchy
    ├── index.css                    # Tailwind directives, custom scrollbars, animations
    ├── layouts/
    │   └── MainLayout.jsx           # App layout wrapper: Navbar, Outlet, CaseDrawer, ToastContainer, Footer
    ├── pages/
    │   ├── OverviewPage.jsx         # Executive dashboard, KPI tiles, ambient velocity, topology preview
    │   ├── ThreatIntelPage.jsx      # Pre-transaction threat intelligence, 3-stage entity extractor
    │   ├── TopologyPage.jsx         # Dedicated topology workspace: Constellation, GeoMap, Dual Perspective
    │   ├── InvestigationsPage.jsx   # Case file triage, filtering, URL synchronization (:caseId)
    │   ├── AnalyticsPage.jsx        # Deep analytics: hourly/daily trends, workload heatmap, bank stats
    │   ├── SystemHealthPage.jsx     # SRE monitor: DB pool metrics, latency percentiles, Redis status
    │   └── SettingsPage.jsx         # Adaptive sensitivity presets, threshold tuning, CI/CD status
    ├── components/
    │   ├── CaseDrawer.jsx           # Slide-out case dossier, DMV gauge, rule breakdown, Gemini chat
    │   ├── ControlBar.jsx           # Live Auto-Feed toggle, TPS rate slider, synthetic batch injection
    │   ├── KpiStrip.jsx             # 7-tile high-impact KPI strip with animated useCountUp counters
    │   ├── LiveFeed.jsx             # Real-time transaction intercept table with CRT scanline effect
    │   ├── Masthead.jsx             # Institutional header banner with sensitivity badge
    │   ├── NetworkConstellation.jsx # Proprietary HTML5 Canvas force-directed physics engine
    │   ├── VerdictDonut.jsx         # Recharts donut chart for ALLOW/HOLD/BLOCK distribution
    │   ├── VerdictHistoryChart.jsx  # Recharts 30-second rolling transaction velocity area chart
    │   ├── VerdictVelocityChart.jsx # Re-export alias for VerdictHistoryChart
    │   ├── overview/
    │   │   └── GeoMuleMap.jsx       # Leaflet.js geodetic Indian Mule Corridors map with bearing arrows
    │   ├── investigations/
    │   │   ├── CaseAiCopilotView.jsx   # Gemini AI Copilot chat with actionable ToolExecutionCards
    │   │   ├── CaseDetailModal.jsx     # Deep modal case inspection view
    │   │   ├── CaseFilterBar.jsx       # Multi-criteria case filtering (verdict, status, risk slider)
    │   │   ├── CaseGeminiAssistantView.jsx # Dedicated Gemini view inside drawer
    │   │   ├── ForensicImageViewer.jsx # 3-tier fallback forensic topology image viewer
    │   │   ├── PayeeBreakdownTable.jsx # Transaction routing entity table (Collector, Hub, Hop, Cashout)
    │   │   ├── SarNarrativeView.jsx    # Rendered Markdown SAR narrative with token metrics
    │   │   └── StatusTransitionActions.jsx # HITL review actions (Review, Escalate, Confirm Fraud, Dismiss)
    │   ├── analytics/
    │   │   ├── AnalyticsSummaryKpis.jsx # Key aggregate metric cards
    │   │   ├── TimeSeriesVerdictChart.jsx # Hourly and daily multi-verdict area chart
    │   │   ├── FraudRateTrendChart.jsx  # Rolling fraud-to-legitimate ratio curve
    │   │   ├── TopFlaggedAccountsTable.jsx # High-risk accounts ranked by intercepted volume
    │   │   ├── BankDistributionChart.jsx # Flagged accounts categorized by sponsor bank
    │   │   ├── AnalystWorkloadHeatmap.jsx # 7x24 hour-of-week investigation workload matrix
    │   │   └── TopDmvAccountsTable.jsx  # Accounts exhibiting extreme Dead Money Velocity
    │   └── common/
    │       ├── Navbar.jsx           # Sticky navigation header with sovereign tricolor accent bar
    │       ├── ErrorBoundary.jsx    # React class-based error containment boundary with recovery
    │       ├── Modal.jsx            # Framer Motion animated modal container
    │       ├── MetricCard.jsx       # Standard KPI metric card with animated numerical transitions
    │       ├── StatusBadge.jsx      # Verdict, case status, and risk tier badge components
    │       ├── ToastContainer.jsx   # Fixed-position animated toast alert queue
    │       └── ScrollToTop.jsx      # Automatic scroll position reset on route change
    ├── context/
    │   ├── AppStateContext.jsx      # Central state store: stats, cases, verdictHistory, ambient engine
    │   └── ToastContext.jsx         # Imperative toast notification dispatch API
    ├── hooks/
    │   ├── useCountUp.js            # Cubic ease-out numerical transition animation hook
    │   └── useWebSocket.js          # Self-healing WebSocket hook with dynamic host resolution & backoff
    ├── services/
    │   └── api.js                   # Centralized REST client, error wrappers, formatters, and PDF downloader
    └── data/
        ├── india-geojson.json       # Geographic boundary GeoJSON reference
        └── india-topo.json          # Geographic boundary TopoJSON reference
```

## 2.4 Test Suite Catalog (`/tests`)
The test suite consists of **43 test modules** containing **977 automated tests**, providing exhaustive regression coverage:

- `tests/frontend_contracts_test.py`: Validates all frontend API contracts, endpoint schemas, and data structures.
- `tests/test_adversarial_m1.py` & `test_adversarial_m1_empirical.py`: Stress tests Layer 1 heuristics against adversarial evasion techniques.
- `tests/test_analytics.py`: Validates time-series aggregation, bank distribution, and workload heatmap endpoints.
- `tests/test_case_status.py`: Validates case lifecycle transitions, feedback recording, and DPIP publishing.
- `tests/test_challenger_m1_stress.py` & `test_challenger_stress.py`: High-concurrency transaction stress tests and toxic payload validation.
- `tests/test_cicd_pipeline.py`: Verifies pipeline integrity, environment configuration, and build scripts.
- `tests/test_e2e_gemini_assistant.py`: End-to-end testing of the Gemini AI Copilot, tool calls, and dossier compilation.
- `tests/test_e2e_suite.py`: Master end-to-end integration test validating inline scoring, case creation, and WebSocket emissions.
- `tests/test_empirical_challenger.py`: Empirical benchmarking of scoring latency, throughput, and memory bounds.
- `tests/test_encyclopedia_kb.py`: Validates completeness and accuracy of the rule Encyclopedia Knowledge Base.
- `tests/test_engine_sprint2.py`: Regression testing of core engine scoring updates and threshold gating.
- `tests/test_federation_api.py`: Validates cross-PSP federation endpoints, signal ingestion, and ring clustering.
- `tests/test_gemini_agentic_adversarial_challenge.py`: Adversarial prompt injection and tool execution validation for Gemini.
- `tests/test_gemini_assistant_agentic.py`: Validates Gemini autonomous function execution and parameter extraction.
- `tests/test_gemini_copilot.py`: Validates conversational AI context building, briefings, and offline fallback routing.
- `tests/test_geomulemap_contract.py`: Validates data structures, hub coordinates, and corridor contracts for the India Map.
- `tests/test_health_detailed.py`: Validates SRE health checks, connection pool telemetry, and latency percentiles.
- `tests/test_honeypot.py`: Validates the synthetic honeypot registry, hit detection, and deflected volume counters.
- `tests/test_institutional_adapters.py`: Tests simulated NPCI MuleHunter, DPIP, and PSP adapter integration.
- `tests/test_isolation_forest.py`: Tests the Pure NumPy Isolation Forest: $c(n)$ mathematical factor, path lengths, contamination baseline, and zero-regression calibration.
- `tests/test_m1_adversarial_stress.py`, `test_m1_empirical_challenger.py`, `test_m1_persistence.py`: Validates database persistence, transactions, and concurrency stress.
- `tests/test_m2_websocket.py`: Tests real-time WebSocket connection handling, channel subscription, and broadcast pruning.
- `tests/test_notifications_benchmark.py`: Benchmarks mobile push notification dispatch latency (FCM HTTP v1 vs. Mock).
- `tests/test_sprint2_e2e_suite.py`: Comprehensive regression suite across all Phase 2 features.
- `tests/test_supervised_model.py`: Validates the Pure NumPy Random Forest: Gini splits, balanced bootstrap sampling, calibration curve, and PaySim evaluation metrics.
- `tests/test_threat_intel_adversarial_challenger.py` & `test_threat_intel_r1.py`: Tests regex entity extraction, threat signal ingestion, and campaign clustering.
- `tests/test_tier1_features.py` through `test_tier5_adversarial.py`: Exhaustive multi-tier regression tests covering boundary conditions, complex combinations, and high-stress scenarios.

---

# 3. Frontend Architecture (React 18 + Vite 5)

## 3.1 Build Tooling, Vite Proxy & Strict Code Quality
The SAMPATI V2 Frontend is engineered for modern browsers utilizing **React 18.3.1**, **Vite 5.4.21**, and **Tailwind CSS 3.4.19**.

### Development Proxy Architecture
In development, the Vite development server proxies API and WebSocket requests to the FastAPI backend running on port 8000, eliminating CORS friction while matching production path routing:

```javascript
// frontend/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/upi": "http://localhost:8000",
      "/gateway": "http://localhost:8000",
      "/cases": "http://localhost:8000",
      "/stats": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
  build: {
    outDir: "dist",
  },
});
```

### Strict Code Quality & ESLint Protocol
The codebase strictly adheres to the rule `--max-warnings 0`. Configured via `frontend/.eslintrc.cjs`, the linter enforces:
- Zero unused imports or variables (`--report-unused-disable-directives`).
- Safe cleanup of mutable references in React hooks: In `useEffect` cleanup routines, mutable ref values (such as `stateRef.current` or `requestAnimationFrame` IDs) are captured into local closure variables before the return block, preventing memory leaks and stale closure bugs under React 18 Concurrent Mode double-invocations.

## 3.2 Client-Side Routing & Page Hierarchy (React Router v6.28.0)
Client-side routing is declared in `frontend/src/App.jsx` using `react-router-dom`:

```
<AppStateProvider>
  <ToastProvider>
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route element={<MainLayout />}>
          ├── /                              --> Navigate to /overview (replace)
          ├── /overview                      --> <OverviewPage />
          ├── /threat-intel                  --> <ThreatIntelPage />
          ├── /topology                      --> <TopologyPage />
          ├── /topology/:viewMode            --> <TopologyPage /> (constellation | geo | dual)
          ├── /investigations                --> <InvestigationsPage />
          ├── /investigations/:caseId        --> <InvestigationsPage /> (deep-linked case file)
          ├── /analytics                     --> <AnalyticsPage />
          ├── /health                        --> <SystemHealthPage />
          ├── /system-health                 --> Navigate to /health (replace)
          ├── /settings                      --> <SettingsPage />
          └── *                              --> Navigate to /overview (catch-all fallback)
```

### Persistent Layout Wrapper (`MainLayout.jsx`)
`MainLayout.jsx` establishes the persistent operations scaffolding:
1. **Top Navigation Bar (`Navbar.jsx`)**: Displays sovereign tricolor accent line (`#FF9933` saffron, `#FFFFFF` white, `#138808` green), live case count badge, adaptive sensitivity mode indicator, and real-time WebSocket connection status pill.
2. **Main Viewport (`<Outlet />`)**: Sandboxed within a responsive grid container (`max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6`).
3. **Global Slide-Out Case Drawer (`CaseDrawer.jsx`)**: Mounted at layout level, listening to global context state. Any component on any page can invoke `openCase(caseData)` to slide open the forensic dossier without prop drilling.
4. **Operations Footer**: Renders compliance pillars (*Privacy-preserving*, *Explainable*, *Human-in-the-loop*), deployment target (`AWS EC2 Mumbai · v2.1.0`), and current Git commit SHA (`c28be10`).

## 3.3 State Management, Ambient Traffic & Sliding-Window Bucketing
The frontend state architecture avoids heavyweight state management libraries (such as Redux) in favor of a clean, performant React Context design:

```
                  ┌──────────────────────────────────────────────┐
                  │          FastAPI Backend Ingestion           │
                  │  /upi/cases   /upi/stats   /ws/feed   Redis  │
                  └──────────────────────┬───────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
           HTTP REST (15s Poll)                        WebSocket Stream
            (Initial & Manual)                       (Sub-50ms Broadcast)
                   │                                           │
                   ▼                                           ▼
         ┌───────────────────────────────────────────────────────────┐
         │                    AppStateContext                        │
         │  • stats (evaluated, allowed, held, blocked, rings, dpip) │
         │  • cases (open investigation queue, max 150 items)        │
         │  • verdictHistory (30s rolling time-series)               │
         │  • autoFeedActive, autoFeedTps, autoFeedStats             │
         │  • sensitivity (adaptive threshold float)                 │
         │  • honeypotAlerts (5s self-dismissing queue)              │
         └─────────────┬───────────────────────────────┬─────────────┘
                       │                               │
                       ▼                               ▼
             Consumer Pages / Views         Global Drawer & Overlays
             (Overview, Topology, etc.)     (CaseDrawer, ToastContainer)
```

### A. Harmonic Ambient Traffic Generator (`calculateAmbientAllowTps`)
In production financial rails, transaction volume never drops to absolute zero. When the transaction simulator is idle, displaying a flatline rate of 0 TPS looks broken. `AppStateContext.jsx` implements an organic harmonic background wave (period $\approx 16\text{s}$) with micro-jitter on the `ALLOW` channel:

$$\text{Phase}(t) = \left(\frac{t}{2500}\right) \pmod{2\pi}$$

$$\text{Raw TPS}(t) = 3.3 + 1.1 \cdot \sin(\text{Phase}(t)) + \text{Jitter}_{[-0.4, +0.4]}$$

$$\text{Ambient ALLOW TPS}(t) = \text{clamp}(2, 5, \text{round}(\text{Raw TPS}(t)))$$

This creates an authentic "breathing" banking rail of 2–5 TPS. Real synthetic fraud bursts stack seamlessly on top of this baseline and decay gracefully back to it.

### B. 1-Second Discrete Bucket Accumulator
Under 50+ TPS transaction load, triggering a React re-render for every incoming WebSocket event would cause severe UI frame drops. `AppStateContext` decouples ingestion from rendering using a mutable reference:

```javascript
const currentBucketRef = useRef({ ALLOW: 0, HOLD: 0, BLOCK: 0, total: 0 });
```

A 1-second interval ticker reads `currentBucketRef.current`, combines it with the ambient baseline, appends a new data point to `verdictHistory` (strictly maintaining a 30-second window via `[...prev.slice(1), newPoint]`), and resets the accumulator bucket.

### C. Case Deduplication & 150-Item Sliding Window
Flagged cases arriving via WebSockets (`new_case` / `UPI_CASE_OPENED`) or REST polling are deduplicated by `case_id`. The list is capped at 150 cases (`[newCase, ...prev.slice(0, 149)]`), bounding browser memory consumption indefinitely.

### D. Animated Numerical Transitions (`useCountUp.js`)
KPI counters update dynamically without jarring number snaps using a cubic ease-out transfer function inside a `requestAnimationFrame` loop:

$$\text{progress}(t) = 1 - (1 - t)^3, \quad t \in [0, 1]$$

$$\text{value}(t) = \text{round}\Big(\text{start} + (\text{target} - \text{start}) \cdot \text{progress}(t)\Big)$$

## 3.4 Visualizers & Physics Engine

### 3.4.1 Custom HTML5 Canvas Physics Engine (`NetworkConstellation.jsx`, 1281 Lines)
`NetworkConstellation.jsx` bypasses external SVG graphing libraries (such as D3.js or Cytoscape) to achieve a locked 60 FPS rendering pipeline over hundreds of transaction nodes using pure HTML5 Canvas:

```
       [Center Gravity Pull]
                │
                ▼
        (Node: Center 0,0)
         ▲              ▲
         │              │
[Coulomb Repulsion]   [Hooke's Spring]
    (F = 950 / r²)      (F = -k(r - r₀))
         │              │
         ▼              ▼
  (Node: Payer) ──────> (Node: Hub) ──────> (Node: Cashout)
         │                     │                    │
         └───────── Edge Particle Flow ─────────────┘
                     (Speed ∝ Risk Score)
```

#### Physical Force Equations:
1. **Center Viewport Gravity**:
   $$F_{\text{gravity}, x} = \left(\frac{\text{width}}{2} - x\right) \cdot 0.001, \quad F_{\text{gravity}, y} = \left(\frac{\text{height}}{2} - y\right) \cdot 0.001$$
2. **Coulomb's Law Pairwise Node Repulsion**:
   $$r^2 = \max\left((x_j - x_i)^2 + (y_j - y_i)^2, 1.0\right)$$
   $$F_{\text{repulse}} = \frac{950}{r^2}, \quad F_x = \frac{x_j - x_i}{r} \cdot F_{\text{repulse}}, \quad F_y = \frac{y_j - y_i}{r} \cdot F_{\text{repulse}}$$
3. **Hooke's Law Dynamic Spring Tension with Rest-Length Harmonic Oscillation**:
   $$r_{\text{target}}(t) = 95 + 3.5 \cdot \sin\left(2t + (\text{edge.ts} \pmod{10})\right)$$
   $$F_{\text{spring}} = (r - r_{\text{target}}(t)) \cdot 0.006$$
4. **Velocity Damping & Boundary Reflection**:
   $$v_x \leftarrow v_x \cdot 0.85, \quad v_y \leftarrow v_y \cdot 0.85$$
   Positions are clamped within canvas boundary margins $[24, \text{dim} - 24]$.

#### Animated Particle Vectors & Glowing Halos:
- Animated particles traverse edges from Payer to Payee with speed proportional to risk:
  $$u(t) = \left(t \cdot \left(0.35 + \frac{\text{risk}}{100} \cdot 0.55\right) + \frac{p}{\text{dotCount}}\right) \pmod{1}$$
- High-risk transactions ($\ge 70$) render with double-pass glowing radial halos (`rgba(220, 38, 38, 0.25)` radius 5.0px, core 3.2px).
- Nodes pulsate according to verdict: `BLOCK` nodes scale by $2.2 + 0.45 \cdot \sin(4t)$ in crimson; `HOLD` nodes scale by $1.8 + 0.35 \cdot \sin(2.5t)$ in amber.

#### Spatial Interaction & Hit Detection:
- Translates screen coordinates to world space:
  $$x_{\text{world}} = \frac{x_{\text{screen}} - \text{offsetX}}{\text{scale}}, \quad y_{\text{world}} = \frac{y_{\text{screen}} - \text{offsetY}}{\text{scale}}$$
- Perpendicular distance edge hit detection threshold: $\le 7.0\text{px}$.
- Drag-vs-click discrimination: Mouse displacement $\le 4\text{px}$ triggers case selection; $> 4\text{px}$ pans the canvas.
- Mousewheel zoom centers on cursor position. Includes an interactive chronological timeline playback scrubber.

### 3.4.2 Geodetic Indian Mule Corridors Map (`GeoMuleMap.jsx`, 343 Lines)
Visualizes inter-state money laundering corridors across India using **Vanilla Leaflet.js with ArcGIS Esri World Light Gray Canvas raster tiles**.

#### Monitored Syndicate Hubs:
- **Delhi NCR** (Target Inflow Hub): $28.6139^\circ\text{N}, 77.2090^\circ\text{E}$
- **Mewat** (SIM-Swap & Phishing Epicenter): $27.9940^\circ\text{N}, 77.0500^\circ\text{E}$
- **Jamtara** (Social Engineering & Cyber Phishing Sink): $23.9628^\circ\text{N}, 86.8016^\circ\text{E}$
- **Ahmedabad** (Layering & Structuring Hub): $23.0225^\circ\text{N}, 72.5714^\circ\text{E}$
- **Mumbai** (Financial Capital Gateway Node): $19.0760^\circ\text{N}, 72.8777^\circ\text{E}$
- **Kolkata** (Eastern Relay & Dispersal Node): $22.5726^\circ\text{N}, 88.3639^\circ\text{E}$
- **Hyderabad** (Coordinating Switch Node): $17.3850^\circ\text{N}, 78.4867^\circ\text{E}$
- **Bengaluru** (Tech / Device Farm Nexus): $12.9716^\circ\text{N}, 77.5946^\circ\text{E}$
- **Chennai** (Southern Cashout Sink): $13.0827^\circ\text{N}, 80.2707^\circ\text{E}$

#### Directional Flow Arrows via Mercator Bearing Projection:
Calculates the precise screen bearing angle in degrees between geographic endpoints:

```javascript
function calculateBearing(lat1, lon1, lat2, lon2) {
  const radLat1 = (lat1 * Math.PI) / 180;
  const radLat2 = (lat2 * Math.PI) / 180;
  const radDlon = ((lon2 - lon1) * Math.PI) / 180;
  const y1 = Math.log(Math.tan(Math.PI / 4 + radLat1 / 2));
  const y2 = Math.log(Math.tan(Math.PI / 4 + radLat2 / 2));
  const dy = -(y2 - y1);
  const dx = radDlon;
  return (Math.atan2(dy, dx) * 180) / Math.PI;
}
```

An inline SVG chevron (`L.divIcon`) is positioned at a **55% parametric offset** along the corridor vector with `transform: rotate(${bearing}deg)`.

#### Stability Safeguards:
- `autoPan: false` on all popups prevents erratic map shifting when markers are clicked.
- `L.DomEvent.stopPropagation(e)` isolates map click events from parent drawer containers.
- Multi-stage size invalidation (`map.invalidateSize()` called on load, 60ms, 300ms, and via `ResizeObserver`) guarantees zero blank/grey tile artifacts.

### 3.4.3 Metric Charts, Velocity Areas & Dead Money Velocity Arc Gauges
- **Verdict Velocity Chart (`VerdictHistoryChart.jsx`)**: 30-second rolling Recharts `AreaChart` rendering rates of `ALLOW` (emerald `#0f7a3d`), `HOLD` (amber `#a8660a`), and `BLOCK` (crimson `#b3261e`) with dark monospace tooltips.
- **Verdict Distribution Donut (`VerdictDonut.jsx`)**: Recharts `PieChart` (`innerRadius=40`, `outerRadius=58`) displaying overall verdict proportions.
- **Dead Money Velocity Arc Gauge (`DmvArcGauge`)**: Custom SVG semicircular gauge in `CaseDrawer.jsx` mapping DMV scores $[0, 100]$ to angles $[-90^\circ, +90^\circ]$:
  $$\theta_{\text{needle}} = -90^\circ + \left(\frac{\text{score}}{100}\right) \cdot 180^\circ$$
  Smoothly animated with CSS transition `transform 1s cubic-bezier(0.34, 1.56, 0.64, 1)`.

## 3.5 Forensic UI, 3-Tier Image Fallback & Gemini AI Copilot

### 3-Tier Forensic Image Fallback (`ForensicImageViewer.jsx`)
When inspecting mule ring topologies:
- **Tier 1 (REST Dynamic)**: Requests `/upi/cases/${caseId}/graph.png` dynamically rendered by backend matplotlib.
- **Tier 2 (Static PNG Fallback)**: If Tier 1 fails, falls back to static cached snapshot `/static/upi_cases/${caseId}_ring.png`.
- **Tier 3 (SVG Vector Topology Fallback)**: If Tier 2 fails, automatically synthesizes an in-browser interactive vector topology (`SvgRingTopology`) rendering Fan-In victims, glowing center Hub, layering hops, and cashout exits with SVG quadratic bezier curves and arrow markers.
- Includes a full-screen Lightbox Zoom modal with escape key listeners.

### Interactive Gemini Copilot & Actionable Tool Execution Cards (`CaseAiCopilotView.jsx`)
The AI Copilot renders structured `ToolExecutionCard` components whenever the AI executes actions:
- **Federation Intelligence Round**: Displays participating nodes (`okaxis`, `okhdfcbank`, `okicici`), synced mule rings, and newly flagged entities.
- **Synthetic Batch Simulation**: Displays generated transactions, fraud ratios, and verdict breakdowns.
- **VPA & Transaction Interception**: Displays confirmation of `BLOCK` or `HOLD` debit freezes.
- **SAR PDF Export**: Provides a direct one-click download trigger.

## 3.6 Styling System & Sovereign FinTech Design Tokens
The design system (`frontend/tailwind.config.js`) enforces an authoritative, sovereign aesthetic tailored for financial operations:
- **Color Tokens**:
  - `ink`: `#0b1f3a` (900 deep navy), `#122a4d` (800 hover navy), `#193860` (700 active navy)
  - `saffron`: `#c8641e` (Sovereign saffron accent), `#e08a3e` (Light highlight)
  - `surface`: `#ffffff` (Card background), `#f4f6fa` (Muted slate canvas)
  - `hairline`: `#e1e6ee` (Crisp border token)
  - `verdict`: `allow` (`#0f7a3d` / `#e7f6ec`), `hold` (`#a8660a` / `#fdf1de`), `block` (`#b3261e` / `#fce8e6`)
- **Typography Tokens**:
  - `font-serif`: **Source Serif 4** for headings, case files, and legal SAR dossiers.
  - `font-sans`: **Inter** for clean, legible UI controls, buttons, and navigation.
  - `font-mono`: **IBM Plex Mono** for VPAs, hashes, latency metrics, IP addresses, and currency figures.
- **Keyframe Animations**: `pulse-ring` (pulsing block badges), `scan` (CRT monitor scanline on live feeds), and `shadow-glow` (saffron and crimson glow effects).

## 3.7 Networking Layer: Self-Healing WebSockets & Binary PDF Streaming
- **Dynamic Protocol & Host Resolution (`useWebSocket.js`)**: Automatically detects HTTP vs. HTTPS and connects via WS or WSS (`getWsUrl`).
- **Exponential Backoff Reconnection**: Reconnects with jittered delays capped at 30 seconds:
  $$\text{delay}(n) = \min\left(30.0, 1.0 \cdot 1.5^{\max(0, n)}\right)\text{ seconds}$$
- **Direct Binary PDF Blob Stream Export (`downloadSarPdf` in `api.js`)**: Fetches binary PDF streams, validates `Content-Type: application/pdf`, generates in-memory object URLs, triggers programmatic download, and cleans up object URLs without navigating away from the dashboard.

---

# 4. Backend Architecture & Service Ecosystem (FastAPI)

## 4.1 Application Lifecycle, Async Lifespan & Configuration Management
The backend application entry point is declared in `app/main.py` using FastAPI's modern asynchronous `lifespan` context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SAMPATI starting up ...")
    # 1. Initialize DB and validate connection pool
    db_ok = await init_db()
    
    # 2. Warm up in-memory lookup cache from PostgreSQL
    from app.services.upi_cases import get_upi_case_service
    svc = get_upi_case_service()
    if hasattr(svc, "sync_from_db"):
        await svc.sync_from_db()
        
    # 3. Trigger background demo seeding if fresh instance
    _is_test = os.environ.get("PYTEST_CURRENT_TEST") or "unittest" in sys.modules
    if not _is_test and not os.environ.get("SAMPATI_SKIP_DEMO_SEED"):
        from app.services.upi_cases import trigger_demo_seed
        trigger_demo_seed()
        
    yield
    
    # 4. Graceful shutdown: close connection pools
    await close_db()
    logger.info("SAMPATI shut down.")
```

### Configuration Management (`app/config.pyc`)
Managed via Pydantic `Settings` with automatic environment variable loading:
- `DATABASE_URL`: PostgreSQL connection URI or async SQLite fallback (`postgresql+asyncpg://...`).
- `REDIS_URL`: Redis URI (`redis://localhost:6379/0`).
- `GEMINI_API_KEY`: Google Generative AI API token.
- `RULE_ENGINE_SLA_MS`: SLA budget (default `10.0` ms).
- `MAX_BATCH_PAYEES`: Maximum batch limit (default `1000`).

## 4.2 Single-Page Application (SPA) Fallback Handler & Static Mounts
To prevent 404 errors when users refresh deep client-side routes (e.g., `/threat-intel`, `/topology/geo`, `/investigations/CASE-9021`), `app/main.py` installs a custom 404 exception handler:

```python
@app.exception_handler(404)
async def spa_fallback_404_handler(request: Request, exc: Any):
    path = request.url.path
    api_prefixes = (
        "/upi", "/federation", "/gateway", "/cases", "/synthetic",
        "/ws", "/health", "/api", "/stats", "/static", "/intel",
        "/threat-intel", "/adapters", "/notifications",
    )
    is_ui_page = path in ("/threat-intel", "/threat-intel/")
    is_api = any(path.startswith(prefix) for prefix in api_prefixes) and not is_ui_page
    has_extension = "." in path.split("/")[-1]

    if not is_api and not has_extension and os.path.isfile(_index_html):
        return FileResponse(_index_html)
    return JSONResponse(status_code=404, content={"detail": f"Path '{path}' not found"})
```

## 4.3 API Router Catalog & Complete 63-Endpoint Taxonomy
SAMPATI V2 exposes **63 discrete route endpoints** across 9 router groups:

### 1. Root Handlers (`app/main.py`)
- `GET /health`: Liveness probe (HTTP 200 OK / HTTP 503 if configured DB down).
- `GET /health/detailed`: Full SRE telemetry: DB pool stats, Redis latency, engine latency percentiles, WebSocket connections.
- `GET /stats/analytics`: Aggregated time-series verdict trends, rule frequencies, top flagged accounts, 7x24 heatmap.
- `PATCH /cases/{case_id}/status`: Updates case review status, records analyst notes, publishes to DPIP.
- `GET /cases/{case_id}/sar/pdf`: Generates and streams formal FIU-IND SAR PDF.
- `GET/POST /cases/{case_id}/ai-briefing`: Generates AI executive briefing and scam typology classification.
- `POST /cases/{case_id}/ai-chat`: Interactive contextual chat with Gemini Copilot.
- `GET/POST /cases/{case_id}/ai-sar`: Drafts statutory SAR narrative using LLM reasoning.
- `GET /api/info`: Service identity, version, and platform architectural pillars.

### 2. Core UPI Interception Router (`/upi` — `app/api/upi.py`)
- `POST /upi/check`: The inline pre-transaction gate evaluating transactions in $<2\text{ms}$. Broadcasts `UPI_EVALUATED` and `UPI_CASE_OPENED`.
- `POST /upi/federation/run`: Triggers cross-PSP consortium consensus, agglomerative clustering of mule rings, and automated SAR drafting.
- `GET /upi/rings`: Returns detected multi-PSP mule rings with member VPAs and volumes.
- `GET /upi/cases`: Paginated listing of flagged cases with multi-criteria filtering (`status`, `verdict`, `limit`, `offset`).
- `GET /upi/cases/{case_id}`: Deep case dossier with trigger transaction, rule hits, token economy, and topology metadata.
- `GET /upi/cases/{case_id}/graph.png`: Renders or retrieves static PNG topology visualizer.
- `GET /upi/cases/{case_id}/sar/pdf`: Downloads statutory PDF report.
- `POST /upi/cases/{case_id}/feedback`: Records analyst confirmation of fraud or false positive.
- `POST /upi/simulate`: Injects a burst of synthetic transactions with customizable fraud ratios.
- `POST /upi/autofeed/start`, `GET /upi/autofeed/status`, `POST /upi/autofeed/stop`: Background traffic simulator controls.
- `GET /upi/stats`: Real-time KPI telemetry counters (evaluated, allowed, held, blocked, rings, honeypot hits).
- `GET /upi/honeypots`: Registry of synthetic honeypot VPAs, lifetime hits, and deflected INR volume.

### 3. Federated Consortium Router (`/federation` — `app/api/federation.py`)
- `POST /federation/signal`: Ingests pseudonymized SHA-256 VPA risk signals from peer PSP nodes.
- `GET /federation/query`: Sub-5ms hot-cache query returning federated risk score, ring members, and reporting PSPs.
- `GET /federation/signals`: Lists all ingested federated risk signals.
- `POST /federation/run`: Executes cross-PSP consortium round.
- `GET /federation/honeypots`: Returns federated honeypot registry nodes.

### 4. Threat Intelligence Router (`/intel` & `/threat-intel` — `app/api/intel.py`)
- `POST /intel/signals`: Ingests unstructured SMS, WhatsApp phish, or fraud reports; extracts entities; runs campaign clustering.
- `GET /intel/signals`: Lists threat signals with pagination and severity filters.
- `GET /intel/signals/{signal_id}`: Retrieves single threat signal record.
- `GET /intel/graph`: Generates Central Fraud Graph topology (nodes, edges, weights) for Force Graph rendering.
- `GET /intel/campaigns`: Lists active syndicate campaigns with member signals and anchor keywords.
- `POST /intel/simulate`: Generates synthetic early-warning scam traffic.

### 5. Institutional Signal Adapters (`/adapters` — `app/api/adapters.py`)
- `GET /adapters/npci/mulehunter`: Queries simulated NPCI MuleHunter switch intelligence.
- `GET /adapters/dpip/registry`: Queries simulated DPIP Smart Registry by VPA or hash.
- `POST /adapters/dpip/registry`: Publishes hotlisted entity to DPIP.
- `POST /adapters/psp/simulate`: Simulates inbound fraud signals from peer PSP engines.
- `GET /adapters/signals/contributing`: Aggregates institutional signals for an account.

### 6. Mobile Push Notifications (`/notifications` — `app/api/notifications.py`)
- `POST /notifications/register`: Registers client FCM device tokens.
- `GET /notifications/tokens`: Returns list of active device tokens.
- `GET /notifications/history`: Audit log of dispatched push alerts.
- `GET /notifications/status`: Telemetry status of FCM delivery providers.

### 7. WebSocket Real-Time Router (`/ws` — `app/api/websocket.py`)
- Persistent bi-directional WebSocket connection (`/ws`, `/ws/feed`) distributing real-time verdicts, case events, and telemetry.

## 4.4 Service Layer Architecture

### 4.4.1 `UpiCaseService` (`app/services/upi_cases.py`)
The central coordinator managing state and scoring:
- Holds references to `UpiHotState`, `AdaptiveBehaviorModel`, `DmvTracker`, `CampaignSignatureStore`, `UpiIsolationForest`, and `FederatedCoordinator`.
- **Latency Tracking (`record_latency`)**: Maintains rolling buffers of up to 2,000 latencies, computing $p_{50}$, $p_{90}$, and $p_{99}$ percentiles.
- **Analytics Engine (`get_analytics`)**: Aggregates time-series buckets, rule frequencies, top flagged accounts, and a 7x24 workload heatmap.

### 4.4.2 `FraudGraphService` (`app/services/graph_service.py`)
Maintains a thread-safe, multi-entity knowledge graph using `networkx.DiGraph`:
- **7 Vertex Types (`NODE_TYPES`)**: `VPA`, `PHONE`, `URL`, `CAMPAIGN`, `CASE`, `SIGNAL`, `RING`.
- **5 Edge Types (`EDGE_TYPES`)**: `EXTRACTED_FROM`, `ASSOCIATED_WITH`, `TRANSACTED_TO`, `MEMBER_OF_CAMPAIGN`, `LINKED_TO_CASE`.
- Provides Breadth-First Search (BFS) subgraph extraction (`get_subgraph(entity_id, max_depth=2)`) for visual rendering.

### 4.4.3 `ThreatIntelService` (`app/services/threat_intel_service.py`)
Coordinates early warning threat ingestion:
- Uses compiled regex patterns (`PHONE_REGEX`, `UPI_REGEX`, `URL_REGEX`, `TAG_PATTERNS`) to parse raw text.
- Performs campaign clustering against syndicate anchors (`CAMP-KYC-PHISH-01`, `CAMP-SMURF-BURST-02`, `CAMP-INVESTMENT-03`).

### 4.4.4 `AutoFeedEngine` (`app/services/autofeed.py`)
A background daemon thread generating synthetic traffic at configurable rates (0.1 to 50.0 TPS), mixing authentic retail payments with adversarial patterns.

### 4.4.5 `InstitutionalAdapterService` (`app/adapters/service.py`)
Simulates external national infrastructure, providing simulated NPCI MuleHunter scores, DPIP registry queries, and multi-bank churn signals.

### 4.4.6 `NotificationService` (`app/services/notification_service.py`)
Dispatches critical push alerts on `BLOCK` verdicts via Google Firebase Cloud Messaging (FCM) HTTP v1 API or an in-memory mock provider.

### 4.4.7 `GeminiAssistantService` (`app/services/gemini_service.py`)
Autonomous GenAI forensic investigator utilizing `gemini-1.5-flash` (with failover cascade), executing agentic tools and synthesizing statutory SAR narratives.

## 4.5 Data Models, Pydantic Schemas & SQLAlchemy 2.0 ORM Persistence

### Core Pydantic Schemas (`app/models/upi_models.py`)
- `UpiTransaction`: Incoming transaction payload (txn_id, amount, payer_vpa, payee_vpa, device_id, sim_id, ip, location).
- `UpiEvaluationResponse`: Evaluation verdict response (risk_score, action, reasons, rule_breakdown, adaptive_score, network_score, ml_anomaly_score, supervised_fraud_score, dmv_score, execution_latency_ms).

### SQLAlchemy 2.0 ORM Persistence Models (`app/models/upi_persistence.py`)
- `UpiCaseModel` (`upi_cases`): Stores flagged cases with JSONB triggers, rule hits, topology, and token economy indicators.
- `MuleRingModel` (`mule_rings`): Stores detected mule rings, participating VPAs, and aggregate volume.
- `CaseFeedbackModel` (`case_feedback`): Audit log of compliance officer resolutions and DPIP publishing status.
- `AggregateStatsModel` (`aggregate_stats`): Persistent key-value store for cumulative platform KPIs.
- `ThreatSignalModel` (`threat_signals`): Threat intelligence records, extracted entities, and syndicate campaign links.

---

# 5. End-to-End Data Pipeline & Real-Time Flow

## 5.1 Inline Transaction Processing Flow (Ingress to Egress)
The sequence diagram below traces the end-to-end evaluation lifecycle of a transaction through SAMPATI V2:

```
Client              FastAPI (/upi/check)      UpiCaseService            UpiRiskScorer             Postgres / Redis         WebSocket Hub
  │                         │                       │                         │                         │                    │
  │── 1. POST /upi/check ──►│                       │                         │                         │                    │
  │   (UpiTransaction)      │── 2. evaluate(txn) ──►│                         │                         │                    │
  │                         │                       │── 3. Query Federation ─►│ (FederatedCoordinator)  │                    │
  │                         │                       │◄── network_score ───────│                         │                    │
  │                         │                       │                         │                         │                    │
  │                         │                       │── 4. evaluate() ───────►│                         │                    │
  │                         │                       │                         │── L1: Rules Check       │                    │
  │                         │                       │                         │── L2: Adaptive EWMA     │                    │
  │                         │                       │                         │── DMV: Velocity & Drain │                    │
  │                         │                       │                         │── L4: Isolation Forest  │                    │
  │                         │                       │                         │── Supervised RF Prob    │                    │
  │                         │                       │                         │── Action Thresholding   │                    │
  │                         │                       │◄── EvaluationResponse ──│                         │                    │
  │                         │                       │                         │                         │                    │
  │                         │                       │── 5. Record Telemetry ───────────────────────────►│ (Update Slid. Wind)│
  │                         │                       │                         │                         │                    │
  │                         │                       │── 6. If HOLD/BLOCK: _open_case()                  │                    │
  │                         │                       │      Persist Case ───────────────────────────────►│ (INSERT upi_cases) │
  │                         │                       │                                                   │                    │
  │                         │                       │── 7. Real-Time Broadcast ─────────────────────────────────────────────►│
  │                         │                       │      - UPI_EVALUATED                                                   │── Broadcast
  │                         │                       │      - new_case (if flagged)                                           │   to all
  │                         │                       │      - stats_update                                                    │   browsers
  │                         │◄── 8. Return Response ┤                                                                        │
  │◄── 9. JSON Response ────│                       │                                                                        │
```

## 5.2 Real-Time WebSocket Broadcasting Hub & Connection Management
The WebSocket hub (`app/api/websocket.py`) manages concurrent browser connections via `ConnectionManager`:
- **Thread Safety**: Uses an `asyncio.Lock()` to serialize connection registration and pruning.
- **Dead Connection Pruning**: Sockets that fail during `send_json()` (due to client disconnection or timeout) are automatically added to an eviction list and pruned cleanly without interrupting broadcasts to other clients.
- **Event Channels**:
  - `UPI_EVALUATED`: Broadcasts the full scoring breakdown and rule contributions for every processed transaction.
  - `new_case`: Broadcasts complete formatted case dossiers when a transaction is placed on `HOLD` or `BLOCK`.
  - `UPI_CASE_OPENED`: Compact event payload alerting dashboard badges.
  - `stats_update`: Live aggregate telemetry (evaluated count, held, blocked, active rings, honeypot hits).
  - `FEDERATION_ROUND`: Broadcasts results of consortium consensus rounds.

## 5.3 Dashboard Telemetry Aggregation & Latency Percentiles ($p_{50}, p_{90}, p_{99}$)
- **Rolling Window Latencies**: Maintained in an in-memory deque of up to 2,000 latencies. Percentiles are calculated via `numpy.percentile`:
  $$p_{50} = \text{percentile}(50), \quad p_{90} = \text{percentile}(90), \quad p_{99} = \text{percentile}(99)$$
- Typically, $p_{50} \approx 1.2\text{ms}$, $p_{90} \approx 1.8\text{ms}$, and $p_{99} < 3.5\text{ms}$, well within the $< 10\text{ms}$ banking SLA.

---

# 6. Database & Cache Infrastructure

## 6.1 PostgreSQL Relational Storage & Connection Pooling
Optimized for AWS RDS PostgreSQL (`db.t3.micro`), which enforces an 87-connection limit:

```python
# app/db/session.py
pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
pool_timeout = float(os.getenv("DB_POOL_TIMEOUT", "30.0"))

_engine = create_async_engine(
    db_url,
    echo=False,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=pool_timeout,
    pool_recycle=pool_recycle,
    pool_pre_ping=True,
)
```

- **URL Normalization**: Converts `postgres://` or `postgresql://` URIs to `postgresql+asyncpg://`.
- **Pre-Ping Liveness (`pool_pre_ping=True`)**: Executes `SELECT 1` before checking out connections from the pool to discard stale connections.
- **Connection Recycling (`pool_recycle=1800`)**: Recycles connections every 30 minutes to prevent resource exhaustion on low-memory RDS instances.

## 6.2 Relational DDL, Compound Indices & Dynamic JSONB Forensics
The PostgreSQL schema defines 5 primary tables:

```sql
-- Core case table for flagged transactions
CREATE TABLE upi_cases (
    case_id VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    verdict VARCHAR(16) NOT NULL,
    risk_score INTEGER NOT NULL,
    payer_vpa VARCHAR(128),
    payee_vpa VARCHAR(128),
    amount NUMERIC(14, 2),
    trigger_txn JSONB NOT NULL,
    rule_hits JSONB NOT NULL DEFAULT '[]',
    adaptive_score FLOAT NOT NULL DEFAULT 0.0,
    network_score FLOAT NOT NULL DEFAULT 0.0,
    ring_hash VARCHAR(64) REFERENCES mule_rings(ring_hash) ON DELETE SET NULL,
    ring_members_vpas JSONB DEFAULT '[]',
    token_economy JSONB,
    sar_markdown TEXT,
    visual_path VARCHAR(255),
    topology JSONB,
    resolution VARCHAR(64),
    investigated_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

CREATE INDEX ix_upi_cases_case_id ON upi_cases (case_id);
CREATE INDEX ix_upi_cases_created_at ON upi_cases (created_at);
CREATE INDEX ix_upi_cases_status ON upi_cases (status);
CREATE INDEX ix_upi_cases_verdict ON upi_cases (verdict);
CREATE INDEX ix_upi_cases_status_created ON upi_cases (status, created_at);
CREATE INDEX ix_upi_cases_verdict_created ON upi_cases (verdict, created_at);
```

## 6.3 Dual-Mode Operation & In-Memory Fallback (`AsyncDatabaseStore`)
When running without PostgreSQL or if the database is unreachable, the system automatically switches to `AsyncDatabaseStore` (`app/db/session.py`):
- Emulates asynchronous session operations using thread-safe Python dictionaries and lists.
- Implements exact method signatures (`save_flagged_case`, `list_flagged_cases`, `update_case_forensics`), allowing local testing and CI test suites to pass without a database daemon.

## 6.4 Redis Hot State Engine, Key Schema & Sliding-Window Velocity
The hot cache layer (`app/engine/redis_state.pyc`) provides sub-millisecond account profiling and sliding-window velocity aggregation:

| Key Schema Pattern | Redis Type | TTL | Description |
|---|---|---|---|
| `cms:session:{account}:{batch}` | String / Flag | 60–300s | Distributed idempotency lock for transaction batches |
| `cms:account:{account}:profile` | Hash / JSON | Persistent | Rolling account profile (lifetime txns, risk status) |
| `cms:account:{account}:velocity` | Sorted Set (`ZSET`)| 86400s | Sliding-window transaction timestamps for velocity scoring |
| `cms:account:{account}:payees` | Set (`SET`) | 30 days | Known beneficiary VPAs to detect first-time payee anomalies |

### Sliding Window Implementation via Redis Sorted Sets:
1. **Record Event**: `ZADD cms:account:{account_id}:velocity <timestamp> <txn_id>`
2. **Prune Expired Events**: `ZREMRANGEBYSCORE cms:account:{account_id}:velocity -inf (<now> - 3600)`
3. **Count Velocity**: `ZCARD cms:account:{account_id}:velocity`

## 6.5 Distributed Idempotency Locks & In-Process `UpiHotState`
- **Distributed Concurrency Lock**: `acquire_batch_lock` uses atomic Redis `SET ... NX EX` operations to prevent duplicate transaction evaluation during concurrent bursts.
- **In-Memory Hot State (`UpiHotState` — `app/engine/upi_state.pyc`)**: Maintains an in-process, thread-safe 30-minute sliding window (`WINDOW_SECONDS = 1800.0`):
  - Inbound and outbound flows stored in `defaultdict(deque)`.
  - Evicts timestamps older than 1800s via `deque.popleft()` on every ingress event.
  - Queries `inbound_stats` and `outbound_stats` in $< 0.05\text{ms}$.

---

# 7. Machine Learning & Generative AI Engine Breakdown

## 7.1 Layer 1: Deterministic Rules Engine & Mathematical Formulations

### 7.1.1 13 Heuristic Rule Catalog & Point Allocations

| Rule Code | Description | Severity | Points | Trigger Threshold / Formula |
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

### 7.1.2 Dead Money Velocity (DMV) Engine Formulation (`app/engine/dmv.py`)
Quantifies the hallmark signature of dormant mule accounts suddenly liquidating funds:

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

### 7.1.3 Impossible Travel Haversine Kinematics & Subnet CIDR Traps
- **Great-Circle Distance**: Calculated via spherical Haversine formula ($R = 6371\,\text{km}$):
  $$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right), \quad d = 2R \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$
  Trips exceeding $1000\,\text{km/h}$ over distances $> 50\,\text{km}$, or $> 100\,\text{km}$ in $< 3\,\text{minutes}$, trigger `R_IMPOSSIBLE_TRAVEL` (+35 pts).
- **Subnet CIDR Traps**: Origin IP addresses are matched against compiled CIDR blocks of cloud hosters, datacenters, and Tor exit nodes using `ipaddress.ip_network`.

### 7.1.4 Fraud Campaign DNA Fingerprinting & Cosine Matching (`app/engine/campaign.py`)
Computes cosine similarity between transaction behavioral vectors and active syndicate campaign signatures:
$$\text{Similarity}(\text{txn}, \text{campaign}) = 0.35 \cdot S_{\text{keyword}} + 0.30 \cdot S_{\text{amount}} + 0.15 \cdot S_{\text{temporal}} + 0.20 \cdot S_{\text{vpa}}$$
A similarity score $\ge 0.82$ triggers `R_CAMPAIGN_MATCH` (+30 pts). Blocked transactions are automatically clustered into active or new campaigns (`CAMP-AUTO-xxxx`).

## 7.2 Layer 2: Unsupervised Anomaly Detection (Isolation Forest in Pure NumPy)

### 7.2.1 Mathematical Path Length Factor $c(n)$ & Anomaly Score $s(x,n)$
Implemented from first principles in pure NumPy based on the canonical Liu, Ting, Zhou (ICDM 2008) algorithm. Anomalous points are isolated near the root of recursive binary trees:

$$c(n) = 2\left(\ln(n - 1) + \gamma\right) - \frac{2(n - 1)}{n} \quad \text{for } n > 2$$
where $\gamma \approx 0.5772156649$ (Euler-Mascheroni constant), $c(2) = 1.0$, and $c(n) = 0.0$ for $n \le 1$.

Anomaly score across $m$ isolation trees:
$$s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$$
- As $\mathbb{E}(h(x)) \to 0 \implies s \to 1$ (High anomaly confidence).
- As $\mathbb{E}(h(x)) \to c(n) \implies s \to 0.5$ (Normal instance).

### 7.2.2 13 Standardized Aligned Behavioral Features
Both Layer 2 and Layer 3 share an identical 13-dimensional numerical feature extraction vector:
1. `amount`: Raw transaction amount in INR.
2. `log_amount`: Natural logarithm $\ln(1 + \text{amount})$.
3. `hour_fraction`: Floating point hour of day $[0.0, 24.0)$.
4. `hour_sin`: Cyclical trigonometric encoding: $\sin(2\pi \cdot \text{hour} / 24)$.
5. `hour_cos`: Cyclical trigonometric encoding: $\cos(2\pi \cdot \text{hour} / 24)$.
6. `is_night`: Binary nocturnal indicator (1.0 if hour $<5$ or $\ge 23$).
7. `payer_account_age_days`: Payer account age clamped to $[0, 365]$.
8. `payee_vpa_age_days`: Payee handle age clamped to $[0, 365]$.
9. `payee_is_new_for_payer`: Binary novelty flag (first transfer between pair).
10. `payer_velocity_count_30m`: Inbound/outbound transaction count in 30-minute window.
11. `payer_velocity_amount_30m`: Cumulative outflow amount in 30-minute window.
12. `device_vpa_count`: Distinct VPAs bound to payer hardware device.
13. `dmv_score`: Dead Money Velocity score $[0.0, 100.0]$.

### 7.2.3 Contamination Baseline & Zero-Regression Calibration Function
- **Training Parameters**: 50 trees (`n_trees=50`), subsample size 128 (`max_samples=128`), height limit $h_{\max} = \lceil \log_2(128) \rceil = 7$.
- **Synthetic Contamination**: Fitted on 700 baseline retail transactions with a calibrated **3.5% contamination rate** of extreme multivariate anomalies.
- **Zero-Regression Calibration Function**:
  $$\text{Normalized Score}(s) = \begin{cases}
  \max(0.0, s \times 0.96) & \text{if } s \le 0.50 \\
  \min\left(1.0, 0.50 + \frac{s - 0.50}{0.15} \times 0.40\right) & \text{if } s > 0.50
  \end{cases}$$
  Guarantees that clean legitimate retail traffic ($s \le 0.50$) normalizes to $\le 0.48$, contributing **0 risk points** to the ensemble.

## 7.3 Layer 3: Supervised Classification (Random Forest in Pure NumPy)

### 7.3.1 Decision Tree Bagging, Gini Impurity & Balanced Bootstrap Sampling
Implemented in pure NumPy to catch subtle fraud patterns that evade unsupervised models:
- **`PureNumpyStandardScaler`**: Normalizes features to zero-mean unit-variance: $z = \frac{x - \mu}{\sigma}$.
- **`PureNumpyDecisionTree`**: Binary decision tree using **Gini Impurity** splitting:
  $$I_G(p) = 2p(1 - p), \quad \Delta I_G = I_{G,\text{parent}} - \frac{n_L}{n}I_{G,L} - \frac{n_R}{n}I_{G,R}$$
- **`PureNumpySupervisedClassifier`**: Ensemble of 30 trees (`n_estimators=30`, `max_depth=6`). At each split, subsamples $k = \lceil \sqrt{13} \rceil = 4$ random features.
- **Balanced Bootstrap Sampling**: Draws training samples with inverse class weights to address class imbalance:
  $$w_{\text{pos}} = \frac{N}{2 N_{\text{pos}}}, \quad w_{\text{neg}} = \frac{N}{2 N_{\text{neg}}}$$

### 7.3.2 Probability Calibration Curve
$$\text{Calibrated Probability}(P) = \begin{cases}
\max(0.0, P \times 0.35) & \text{if } P \le 0.30 \\
0.10 + \frac{P - 0.30}{0.20} \times 0.35 & \text{if } 0.30 < P < 0.50 \\
\min\left(1.0, \max\left(0.50, 0.50 + \frac{P - 0.50}{0.25} \times 0.40\right)\right) & \text{if } P \ge 0.50
\end{cases}$$

### 7.3.3 PaySim Benchmark Performance (F1: 0.9627, 83.3% FN Reduction)
Trained and evaluated on 5,000 benchmark records aligned with the Kaggle/PaySim mobile money schema:

| Evaluation Metric | Measured Value | Benchmark Target | Result |
|---|---|---|---|
| **Precision** | **0.9793** | $\ge 0.8500$ | **PASS [✓]** |
| **Recall** | **0.9467** | $\ge 0.8500$ | **PASS [✓]** |
| **F1 Score** | **0.9627** | $\ge 0.8500$ | **PASS [✓]** |
| **Accuracy** | **0.9890** | $\ge 0.9000$ | **PASS [✓]** |
| **False Positive Rate (FPR)** | **0.35%** | $< 1.50\%$ | **PASS [✓]** |

**False Negative Reduction**: Missed fraud cases dropped from 48 / 150 under the Unsupervised baseline down to 8 / 150 under the Supervised Random Forest, representing an **83.33% relative reduction in False Negatives**.

## 7.4 Ensemble Scoring Logic, Linear Combination & Safety Override Floors

### Score Combination Formula:
$$S_{\text{risk}} = \min\left(100, \max\left(0, S_{\text{rule}} + P_{\text{adaptive}} + P_{\text{network}} + P_{\text{ml}}\right)\right)$$

Where:
- $S_{\text{rule}} = \min\left(100, \sum_{h \in \text{hits}} h.\text{points}\right)$ (Layer 1 deterministic points)
- $P_{\text{adaptive}} = \text{int}(S_{\text{adaptive}} \times 25)$ (Layer 2 adaptive points, max 25)
- $P_{\text{network}} = \text{int}(S_{\text{network}} \times 40)$ (Layer 3 federated graph points, max 40)
- $P_{\text{ml}} = \begin{cases} \min\left(25, \max\left(0, \text{int}\left(\text{round}\left(\frac{S_{\text{ml}} - 0.50}{0.50} \times 25\right)\right)\right)\right) & \text{if } S_{\text{ml}} > 0.50 \\ 0 & \text{if } S_{\text{ml}} \le 0.50 \end{cases}$

### Decision Thresholds & Safety Override Floors:
- $\text{Score} \ge 70 \implies \mathbf{BLOCK}$
- $45 \le \text{Score} < 70 \implies \mathbf{HOLD}$
- $\text{Score} < 45 \implies \mathbf{ALLOW}$

#### Mandatory Override Floors:
To prevent sophisticated multi-vector attacks from bypassing individual channels:
$$\text{If } S_{\text{network}} \ge 0.70 \lor S_{\text{ml}} \ge 0.85 \lor S_{\text{supervised}} \ge 0.85 \implies \text{Force } \mathbf{HOLD} \; (S_{\text{risk}} \leftarrow \max(S_{\text{risk}}, 45))$$

## 7.5 Layer 4: Generative AI & Google Gemini Integration

### 7.5.1 Multi-Model Failover Cascade & HTTP REST Architecture
The `GeminiAssistantService` communicates directly with the Google Generative Language API via asynchronous `httpx.AsyncClient` calls (`v1beta`), removing dependencies on heavy external SDKs:
- **Model Cascade**: `gemini-1.5-flash` $\to$ `gemini-1.5-flash-8b` $\to$ `gemini-2.0-flash` $\to$ `gemini-1.5-pro`.
- **Failover Logic**: Automatically cascades across the hierarchy if HTTP 404, 429 (rate-limit), 500, 502, 503, or 504 errors are encountered.

### 7.5.2 Deep Context Injection & Encyclopedia Knowledge Base
When analyzing a case, `build_case_dossier_text(case_data)` compiles an exhaustive dossier incorporating:
- Complete trigger transaction DNA (IDs, VPAs, amounts, timestamps).
- Hardware fingerprints (Device ID, SIM IMSI, IP, location).
- Itemized rule breakdowns and DMV scores.
- Mule ring network constellation topology.
- Relevant statutory and algorithmic definitions extracted directly from the Encyclopedia Knowledge Base (`app/engine/encyclopedia_kb.py`).

### 7.5.3 Autonomous Agentic Tool Calling & Offline Intent Routing
Gemini is equipped with function declarations (`GEMINI_TOOL_DECLARATIONS`) allowing it to execute real platform operations autonomously:
1. `block_vpa_or_transaction`: Places debit restrictions, escalates case in PostgreSQL, updates in-memory fraud memory, and publishes to DPIP.
2. `trigger_federation_round`: Executes cross-PSP consortium consensus round across participating banks.
3. `export_sar_pdf`: Compiles and streams the statutory SAR PDF artifact.
4. `simulate_transactions`: Injects test traffic bursts.

#### Deterministic Offline Intent Router:
When offline or if `GEMINI_API_KEY` is not provisioned, the service falls back to `_match_intent(question, case_data)`. Using regex intent patterns, it executes the identical underlying tools deterministically, returning structured Markdown responses with zero platform degradation.

### 7.5.4 45x Multimodal Visual Token Economy Compression
Analyzing multi-node fraud rings requires processing complex transaction ledgers. Ingesting raw JSON into an LLM context window consumes massive token budgets.

SAMPATI V2 implements **Multimodal Context Compression**:
1. Renders the mule ring topology into a high-contrast visual diagram (`render_ring_png`).
2. Gemini processes the image tile at a fixed cost of **258 vision tokens** + **75 prompt tokens** = **333 tokens**.
3. A raw text ledger of 500 transactions consumes $\approx 15,000\text{ tokens}$.
4. **Compression Ratio**: $45.0\text{x}$ token reduction with $> 97.8\%$ cost savings.

### 7.5.5 Statutory FIU-IND Form 17B SAR 2-Page PDF Pipeline (`app/forensics/sar_pdf.py`)
Generates publication-quality regulatory filings formatted to Financial Intelligence Unit - India (FIU-IND) standards:
- **Engine**: Pure headless matplotlib vector graphics (`matplotlib.backends.backend_pdf.PdfPages`).
- **Page 1: Executive Dossier & Forensic Metadata**:
  - Color-coded header banner (`#991b1b` for `BLOCK`, `#b45309` for `HOLD`, `#1e3a8a` for `ALLOW`).
  - Standardized Case Identifier, FIU-IND / RBI DPIP Form 17B header, and status badges.
  - Case Assessment Summary box (Risk score, DMV score, campaign tags, ring hash).
  - Trigger Transaction DNA and explainable rule breakdown with point allocations.
  - Token economy indicators (financial velocity, turnover ratio, conduit forward ratio).
- **Page 2: Formal SAR Narrative & Compliance Disclosure**:
  - Embedded high-resolution PNG graph visualization of the mule syndicate constellation.
  - Multi-paragraph regulatory narrative detailing Modus Operandi, Layering Hops, and Victim Origins.
  - Statutory declarations and prescribed enforcement actions under Section 12 of the Prevention of Money Laundering Act (PMLA).

---

# 8. Operational Guide, Verification & Tooling

## 8.1 Verification Command Matrix & Test Results
SAMPATI V2 includes automated test suites and linters validating the entire repository:

```bash
# 1. Full Backend Pytest Suite (977 Tests)
./.venv/bin/pytest

# 2. Python Ruff Linter (Clean Code Standards)
./.venv/bin/ruff check app tests

# 3. Frontend ESLint (Zero-Warning Enforcement)
cd frontend && npm run lint

# 4. Frontend Production Build (Vite 5 Bundle)
cd frontend && npm run build
```

### Measured Verification Results (September 2026):
- **Pytest Suite**: **977 passed**, 0 failures, 6 external library deprecation warnings in 159.62s.
- **Ruff Linter**: All checks passed cleanly (`0 errors`).
- **Frontend ESLint**: **0 warnings** (`--max-warnings 0` strictly satisfied).
- **Frontend Build**: **1392 modules transformed**, production bundle generated in 14.18s (`dist/index.html`, `dist/assets/`).

## 8.2 Safe-Push Automated Zero-Friction Protocol
Per repository guidelines in `AGENTS.md` and `SAFE_PUSH_WORKFLOW.md`, code modifications must pass the automated validation sequence prior to committing and pushing:

```bash
# Step 1: Run Pytest + Ruff + Frontend Lint + Frontend Build
./.venv/bin/pytest && ./.venv/bin/ruff check app tests && cd frontend && npm run lint && npm run build && cd ..

# Step 2: Stage, Commit, and Push via SSH
git add .
git commit -m "<type>(<scope>): <concise message>"
git push origin main
```

*Note*: Git authentication must use SSH (`git@github.com:404Avinash/SAMPATI_V2.git`) to prevent non-interactive credential prompts in headless CI/CD runners.

## 8.3 Operational Runbooks & Troubleshooting

### 1. In-Memory Mode vs. Database Mode
- If PostgreSQL is offline or `DATABASE_URL` is omitted, the backend logs:
  `Operating in in-memory fallback mode.`
  All API endpoints remain fully functional via `AsyncDatabaseStore`.

### 2. Redis Cache Offline
- If Redis is unreachable, the system transparently routes sliding window operations to `InMemoryStore` and `UpiHotState`. No configuration changes are required.

### 3. Missing Gemini API Key
- If `GEMINI_API_KEY` is omitted, the Layer 4 AI Copilot transparently switches to the deterministic offline intent router and Encyclopedia Knowledge Base, allowing full demonstration and testing of investigations without external network calls.

### 4. Running the Development Stack
```bash
# Start backend on port 8000
./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal, start frontend on port 5173
cd frontend && npm run dev
```

---

# Conclusion
SAMPATI V2 delivers an authoritative, high-throughput financial crime defense platform purpose-built for India's real-time UPI rails. By harmonizing sub-millisecond deterministic heuristics, pure NumPy machine learning models, privacy-preserving cross-PSP federation, and autonomous Generative AI investigations, SAMPATI V2 establishes a new technical benchmark for low-latency fraud interception, explainable compliance, and sovereign financial resilience.

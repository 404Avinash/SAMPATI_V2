# SAMPATI V2 — Comprehensive Backend, Data Pipeline, Database & Cache Architectural Survey

**Document Target**: `/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_be/report.md`  
**Classification**: High-Precision Technical Architecture Documentation  
**Repository**: `404Avinash/SAMPATI_V2`  
**Surveyed Codebase**: `/home/avi/Downloads/Sampati_v2/app`  
**Author**: Backend & Data Pipeline Architecture Explorer Subagent  

---

## Executive Summary

**SAMPATI V2** (*Synchronous Anti-Mule Platform for Account Tracking & Interception*) is a high-throughput, sub-millisecond fraud defense and mule-network interception platform purpose-built for India's Unified Payments Interface (UPI) ecosystem.

Architecturally, the backend is structured as an asynchronous micro-monolith built on **FastAPI**, **SQLAlchemy 2.0 (asyncpg)**, and **Redis**. It features:
1. **Multi-Layer Hybrid ML/Deterministic Scoring Engine**: An inline decision pipeline combining 13 deterministic financial rules, adaptive EWMA behavioral baselining, cross-PSP graph network scoring, Dead Money Velocity (DMV) tracking, a pure NumPy Unsupervised Isolation Forest, and a pure NumPy Supervised Random Forest.
2. **Dual-Tier Hot State & Distributed Cache**: Sub-millisecond sliding-window velocity tracking and distributed session idempotency locking backed by Redis (with pure in-memory failover fallback).
3. **Cold Relational Persistence**: An asynchronous database layer engineered for AWS RDS PostgreSQL (`db.t3.micro`), utilizing JSONB schemas for dynamic forensic payloads and compound indices for real-time querying.
4. **Autonomous AI Forensics & Regulatory Reporting**: Generative AI integration via Google Gemini (with deterministic and Encyclopedia KB fallbacks) that autonomously classifies scam typologies, answers investigator queries, executes agentic tools, and generates FIU-IND / RBI DPIP compliant Suspicious Activity Reports (SARs) rendered into publication-ready PDFs.
5. **Real-Time Reactive Streaming Hub**: Persistent WebSocket push channels distributing live transaction evaluations, newly opened cases, and KPI telemetry directly into the React frontend.

```
                    ┌────────────────────────────────────────────────────────┐
                    │                   Incoming Traffic                     │
                    │      (UPI App, Mobile Client, Synthetic Stream)       │
                    └──────────────────────────┬─────────────────────────────┘
                                               │
                                       HTTP REST / WebSockets
                                               │
                                               ▼
     ┌─────────────────────────────────────────────────────────────────────────────────┐
     │                      FastAPI Application Gateway (main.py)                      │
     │   CORS Middleware  │  SPA Fallback Handler  │  Subsystem Health  │  Lifespan    │
     └───────────────────┬─────────────────────────────┬───────────────────────────────┘
                         │                             │
          ┌──────────────┴──────────────┐              │ WebSocket Push
          ▼                             ▼              ▼
┌──────────────────┐          ┌───────────────────┐ ┌──────────────────────────────────┐
│  REST API Layer  │          │   Service Layer   │ │ WebSocket Connection Manager     │
│  /upi            │          │  UpiCaseService   │ │  Active Socket Registry          │
│  /federation     │◄────────►│  FraudGraphService│ │  Dead Connection Pruning         │
│  /intel          │          │  ThreatIntelSvc   │ │  Broadcast Channels:             │
│  /adapters       │          │  GeminiAssistant  │ │   - UPI_EVALUATED, new_case      │
│  /notifications  │          │  AutoFeedEngine   │ │   - stats_update, FEDERATION     │
└──────────────────┘          └─────────┬─────────┘ └──────────────────────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────────────┐
│ Inline Scoring Gate  │    │  Hot Cache Layer     │    │  Cold Persistence (Postgres) │
│ L1: Deterministic    │    │  RedisHotState       │    │  AWS RDS PostgreSQL          │
│ L2: Adaptive EWMA    │◄──►│  (Sorted Sets TTL)   │    │  SQLAlchemy 2.0 / asyncpg    │
│ L3: Federated Graph  │    │  UpiHotState         │    │  Tables:                     │
│ L4: Isolation Forest │    │  (1800s Slid. Window)│    │   - upi_cases (JSONB)        │
│     Supervised RF    │    │  Idempotency Locks   │    │   - mule_rings               │
│     DMV Engine       │    │  Pub/Sub Channels    │    │   - case_feedback            │
│     Honeypot Trap    │    │  InMemoryStore Fallbk│    │   - threat_signals           │
└──────────────────────┘    └──────────────────────┘    └──────────────────────────────┘
```

---

## 1. Application Lifecycle & Configuration

### 1.1 Application Entry Point (`app/main.py`)

The central entry point is instantiated in `app/main.py` lines 182–190:
```python
app = FastAPI(
    title="SAMPATI UPI Mule-Network Interception Gateway",
    description=(
        "Real-time UPI mule-network interception with federated ring detection, "
        "SAR generation, and DPIP integration."
    ),
    version="2.0.0",
    lifespan=lifespan if FASTAPI_AVAILABLE else None,
)
```

The module gracefully handles environment constraints with comprehensive fallback mock classes if FastAPI or SQLAlchemy are missing during isolated component testing.

### 1.2 Async Lifespan Management (`app/main.py:141-180`)

SAMPATI V2 utilizes FastAPI's modern `lifespan` context manager protocol:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SAMPATI starting up ...")
    try:
        db_ok = await init_db()
        if db_ok:
            logger.info("Database initialized successfully with active connection pool.")
        else:
            logger.info("Operating in in-memory fallback mode.")
    except Exception as exc:
        logger.warning("DB init skipped (in-memory mode): %s", exc)

    # Sync existing cases and rings from DB into service cache if available
    try:
        from app.services.upi_cases import get_upi_case_service
        svc = get_upi_case_service()
        if hasattr(svc, "sync_from_db"):
            await svc.sync_from_db()
    except Exception as exc:
        logger.warning("DB state sync skipped: %s", exc)

    # Trigger background demo seeding if fresh instance (skip during test runs)
    _is_test = os.environ.get("PYTEST_CURRENT_TEST") or "unittest" in sys.modules or any("test_" in arg for arg in sys.argv)
    if not _is_test and not os.environ.get("SAMPATI_SKIP_DEMO_SEED"):
        try:
            from app.services.upi_cases import trigger_demo_seed
            trigger_demo_seed()
        except Exception as exc:
            logger.warning("Startup demo seed trigger skipped: %s", exc)

    yield

    try:
        await close_db()
    except Exception as exc:
        logger.warning("DB close error: %s", exc)
    logger.info("SAMPATI shut down.")
```

#### Lifecycle Phase Analysis:
1. **Startup Table Validation (`init_db`)**: Connects via `get_engine()`, validates connectivity, and issues `Base.metadata.create_all` across all persistence models.
2. **State Warm-Up (`sync_from_db`)**: Queries PostgreSQL for the latest 200 cases and 500 mule rings, hydrating the in-memory lookup cache to guarantee sub-millisecond API responses even immediately after cold restart.
3. **Idempotent Demo Seeding (`trigger_demo_seed`)**: If the database is empty and not running under `pytest`, a non-blocking background daemon generates 150 synthetic transactions across legitimate, smurfing, and fan-out patterns, initializing baseline metrics.
4. **Shutdown Cleanup (`close_db`)**: Gracefully disposes of the SQLAlchemy `AsyncEngine` pool, closing all open PostgreSQL connections.

### 1.3 Middleware & CORS Configuration (`app/main.py:192-200`)

To support decoupled frontend SPA architectures (React/Vite) running on arbitrary local or cloud origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 1.4 Single Page Application (SPA) Routing & Fallback Handler (`app/main.py:440-488`)

SAMPATI V2 serves both its REST/WebSocket APIs and the pre-built React frontend bundle from a single unified server. To prevent 404 errors when users refresh deep client-side routes (e.g., `/threat-intel`, `/cases/CASE-01`), a custom exception handler is installed:
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
    return JSONResponse(
        status_code=404,
        content={"detail": getattr(exc, "detail", f"Path '{path}' not found")},
    )
```

Static mounts are ordered deterministically:
- `/static` mounted to `static/` (forensic PNG graphs, SAR artifacts).
- `/` mounted to `frontend/dist/` (`html=True`).

### 1.5 Configuration Management (`app/config.pyc`)

Configuration is managed via Pydantic model `Settings` with automatic environment variable extraction:

| Setting Key | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | `str` | `sqlite+aiosqlite:///./sampati.db` | PostgreSQL connection URI or SQLite async fallback |
| `REDIS_URL` | `str` | `redis://localhost:6379/0` | Redis hot cache connection URI |
| `GEMINI_API_KEY`| `Optional[str]` | `None` | Google Generative AI API token for Layer 4 |
| `CORS_ORIGINS` | `List[str]` | `["*"]` | Permitted cross-origin endpoints |
| `HOST` | `str` | `0.0.0.0` | Bind interface |
| `PORT` | `int` | `8000` | HTTP port |
| `ARTIFACTS_DIR` | `str` | `static/cases` | Storage directory for forensic graphs |
| `ENVIRONMENT` | `str` | `development` | Runtime environment tier |
| `MAX_BATCH_PAYEES` | `int` | `1000` | Max payees in bulk payout checks |
| `RULE_ENGINE_SLA_MS` | `float`| `10.0` | Max latency SLA budget for rule execution |

---

## 2. API Routers & Endpoint Taxonomy

SAMPATI V2 exposes **63 discrete route endpoints** across 9 router groups and direct root handlers.

```
FastAPI Router Root (app)
├── Direct Root Handlers (/health, /stats, /cases, /api/info)
├── [Router] /upi                     (app/api/upi.py)
├── [Router] /federation              (app/api/federation.py)
├── [Router] /gateway                 (app/api/gateway.pyc)
├── [Router] /cases                   (app/api/cases.pyc)
├── [Router] /synthetic               (app/api/synthetic.pyc)
├── [Router] /ws                      (app/api/websocket.py)
├── [Router] /intel, /threat-intel    (app/api/intel.py)
├── [Router] /adapters                (app/api/adapters.py)
└── [Router] /notifications           (app/api/notifications.py)
```

### 2.1 Direct Root Handlers (`app/main.py`)

| Method | Path | Function | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | `health_check()` | System liveness probe returning HTTP 200 if healthy or in-memory, HTTP 503 if configured DB fails. |
| `GET` | `/health/detailed` | `detailed_health_check()` | Full telemetry: DB pool stats, Redis ping latency, engine latency percentiles, WebSocket count. |
| `GET` | `/stats/analytics` | `get_analytics_root()` | Aggregated time-series verdict trends, rule frequencies, top flagged accounts, 7x24 heatmap. |
| `PATCH`| `/cases/{case_id}/status` | `update_case_status_root()` | Update case review status, record analyst resolution, trigger DPIP registry publication. |
| `GET` | `/cases/{case_id}/sar/pdf`| `get_case_sar_pdf_root()` | Dynamic generation and streaming of formal FIU-IND SAR PDF document. |
| `GET/POST`| `/cases/{case_id}/ai-briefing` | `get_case_ai_briefing_root()` | Generates AI executive briefing and scam typology classification using Google Gemini. |
| `POST` | `/cases/{case_id}/ai-chat` | `chat_with_case_ai_root()` | Interactive contextual chat with Gemini Copilot with agentic tool execution. |
| `GET/POST`| `/cases/{case_id}/ai-sar` | `get_case_ai_sar_root()` | Drafts statutory SAR narrative using LLM reasoning. |
| `GET` | `/api/info` | `api_info()` | Service identity, version, and platform architectural pillars. |

### 2.2 UPI Interception Router (`/upi` — `app/api/upi.py`)

Primary operational endpoints governing real-time transaction processing:

- `POST /upi/check`: The inline pre-transaction gate evaluating transactions in $<2\text{ms}$. Broadcasts `UPI_EVALUATED` and `UPI_CASE_OPENED`.
- `POST /upi/federation/run`: Triggers cross-PSP consortium consensus, agglomerative clustering of mule rings, and automated SAR drafting.
- `GET /upi/rings`: Returns all detected multi-PSP mule rings with member VPAs and volume.
- `GET /upi/cases`: Paginated listing of flagged cases with multi-criteria filtering (`status`, `verdict`, `limit`, `offset`).
- `GET /upi/cases/{case_id}`: Deep case dossier with trigger transaction, rule hits, token economy, and topology metadata.
- `GET /upi/cases/{case_id}/graph.png`: Renders or retrieves static PNG topology visualizer.
- `GET /upi/cases/{case_id}/sar/pdf`: Downloads statutory PDF report.
- `POST /upi/cases/{case_id}/feedback`: Human-in-the-loop analyst feedback endpoint confirming fraud or false positives, updating in-memory fraud memory.
- `POST /upi/simulate`: Generates a burst of synthetic transactions with custom fraud ratios.
- `POST /upi/autofeed/start`, `GET /upi/autofeed/status`, `POST /upi/autofeed/stop`: Background traffic simulator controls.
- `GET /upi/stats`: Real-time KPI telemetry counters (evaluated, allowed, held, blocked, rings, honeypot hits).
- `GET /upi/honeypots`: Registry of synthetic honeypot VPAs, lifetime hits, and deflected INR volume.

### 2.3 Federated Intelligence Router (`/federation` — `app/api/federation.py`)

Consortium privacy-preserving signal sharing:
- `POST /federation/signal`: Ingests pseudonymized SHA-256 VPA risk signals from peer PSP nodes.
- `GET /federation/query`: Sub-5ms hot-cache query returning federated risk score, ring members, and reporting PSPs.
- `GET /federation/signals`: Lists all ingested federated risk signals.
- `POST /federation/run`: Executes cross-PSP consortium round.
- `GET /federation/honeypots`: Returns federated honeypot registry nodes.

### 2.4 Threat Intelligence Router (`/intel` & `/threat-intel` — `app/api/intel.py`)

Pre-transaction early warning mesh:
- `POST /intel/signals`: Ingests unstructured SMS, WhatsApp phish, or fraud reports; extracts entities; runs campaign clustering.
- `GET /intel/signals`: Lists threat signals with pagination and severity filters.
- `GET /intel/signals/{signal_id}`: Retrieves single threat signal record.
- `GET /intel/graph`: Generates Central Fraud Graph topology (nodes, edges, weights) for Force Graph rendering.
- `GET /intel/campaigns`: Lists active syndicate campaigns with member signals and anchor keywords.
- `POST /intel/simulate`: Generates synthetic early-warning scam traffic.

### 2.5 Institutional Signal Adapters (`/adapters` — `app/api/adapters.py`)

- `GET /adapters/npci/mulehunter`: Queries simulated NPCI MuleHunter switch intelligence.
- `GET /adapters/dpip/registry`: Queries simulated DPIP Smart Registry by VPA or hash.
- `POST /adapters/dpip/registry`: Publishes hotlisted entity to DPIP.
- `POST /adapters/psp/simulate`: Simulates inbound fraud signals from peer PSP engines (PhonePe, Paytm, etc.).
- `GET /adapters/signals/contributing`: Aggregates institutional signals for an account.

### 2.6 Mobile Push Notifications Router (`/notifications` — `app/api/notifications.py`)

- `POST /notifications/register`: Registers client FCM device tokens.
- `GET /notifications/tokens`: Returns list of active device tokens.
- `GET /notifications/history`: Audit log of dispatched push alerts.
- `GET /notifications/status`: Telemetry status of FCM delivery providers.

### 2.7 WebSocket Real-Time Router (`/ws`, `/ws/`, `/ws/feed` — `app/api/websocket.py`)

- Dual-endpoint WebSocket connection handling client subscription, ping/pong heartbeats, and live metric streams.

---

## 3. Service Layer Architecture

```
                                  UpiCaseService (Singleton)
          ┌───────────────────────────────────┼───────────────────────────────────┐
          │                                   │                                   │
          ▼                                   ▼                                   ▼
┌───────────────────┐               ┌───────────────────┐               ┌───────────────────┐
│ UpiRiskScorer     │               │ FederatedCoord    │               │ GeminiAssistant   │
│ - Rule Engine     │               │ - PSP Nodes       │               │ - Executive Brief │
│ - Adaptive EWMA   │               │ - Ring Detection  │               │ - Agentic Tools   │
│ - Isolation Forest│               │ - Privacy Salt    │               │ - SAR Narrative   │
│ - Supervised RF   │               │ - Hot Signal Map  │               │ - Q&A Chat        │
└─────────┬─────────┘               └─────────┬─────────┘               └─────────┬─────────┘
          │                                   │                                   │
          ▼                                   ▼                                   ▼
┌───────────────────┐               ┌───────────────────┐               ┌───────────────────┐
│ FraudGraphService │               │ AutoFeedEngine    │               │ NotificationSvc   │
│ - NetworkX DiGraph│               │ - Background Loop │               │ - FCM HTTP v1     │
│ - Multi-Entity Map│               │ - Traffic Injector│               │ - Mock Provider   │
│ - BFS Subgraph Gen│               │ - Burst Modulator │               │ - Token Registry  │
└───────────────────┘               └───────────────────┘               └───────────────────┘
```

### 3.1 `UpiCaseService` (`app/services/upi_cases.py`)

The central transaction coordinator and business logic engine.
- **State Management**: Holds references to `UpiHotState`, `AdaptiveBehaviorModel`, `DmvTracker`, `CampaignSignatureStore`, `UpiIsolationForest`, and `FederatedCoordinator`.
- **Latency Tracking (`record_latency`)**: Maintains a rolling buffer of up to 2,000 execution latencies, calculating $p_{50}$, $p_{90}$, $p_{99}$, min, max, and average latencies.
- **Throughput Metrics (`get_throughput_metrics`)**: Evaluates rolling 60-second throughput and transactions per second.
- **Analytics Engine (`get_analytics`)**: Aggregates time-series buckets (hourly/daily), rule frequency rankings, top flagged accounts with bank extraction, and a $7 \times 24$ workload heatmap.
- **Case Lifecycle Management**: Opens cases on `HOLD`/`BLOCK`, builds visual graphs, generates token economy metrics, drafts SAR narratives, and coordinates DB persistence.

### 3.2 `FraudGraphService` (`app/services/graph_service.py`)

Maintains a thread-safe, multi-entity knowledge graph using `networkx.DiGraph`.
- **Vertices (`NODE_TYPES`)**: `VPA`, `PHONE`, `URL`, `CAMPAIGN`, `CASE`, `SIGNAL`, `RING`.
- **Directed Edges (`EDGE_TYPES`)**:
  - `EXTRACTED_FROM`: `PHONE` / `VPA` / `URL` $\to$ `SIGNAL`
  - `ASSOCIATED_WITH`: `PHONE` $\to$ `VPA`
  - `TRANSACTED_TO`: `Payer VPA` $\to$ `Payee VPA`
  - `MEMBER_OF_CAMPAIGN`: `SIGNAL` / `VPA` $\to$ `CAMPAIGN`
  - `LINKED_TO_CASE`: `VPA` / `SIGNAL` $\to$ `CASE`
- **Graph Operations**:
  - `add_threat_signal()`: Ingests structured signals, automatically creates entity nodes and links them with `EXTRACTED_FROM` edges.
  - `link_vpa_to_case()`: Connects accounts to investigative dossiers.
  - `get_subgraph(entity_id, max_depth=2)`: Uses Breadth-First Search (BFS) to extract localized fraud ego-networks for front-end rendering.
  - `export_graph()`: Serializes nodes and edges into JSON format for Canvas visualization.

### 3.3 `ThreatIntelService` (`app/services/threat_intel_service.py`)

Coordinates the pre-transaction early warning mesh:
- **Regex Entity Extraction**: Uses compiled regex patterns (`PHONE_REGEX`, `UPI_REGEX`, `URL_REGEX`, `TAG_PATTERNS`) to parse raw unstructured SMS or phishing text.
- **Syndicate Clustering**: Compares token sets of incoming threats against predefined syndicate anchors:
  - `CAMP-KYC-PHISH-01`: KYC Phishing Syndicate (keywords: sbi, icici, kyc, unblock, pan, suspension).
  - `CAMP-SMURF-BURST-02`: Micro-Smurfing Dispersal Ring (keywords: smurfing, dispersal, pass-through, micro-split).
  - `CAMP-INVESTMENT-03`: Task Scam / Investment Fraud Ring (keywords: telegram, part-time job, investment, bonus, crypto).
- **Bidirectional Sync**: Updates the `FraudGraphService` and broadcasts `THREAT_SIGNAL_INGESTED` events over WebSockets.

### 3.4 `AutoFeedEngine` (`app/services/autofeed.py`)

A daemon background generator executing inside a dedicated thread (`sampati-autofeed-worker`):
- **Rate Modulation**: Supports rates from $0.1$ to $50.0$ Transactions Per Second (TPS).
- **Traffic Composition**: Blends normal retail payments with synthetic adversarial patterns (honeypot hits, impossible travel, datacenter VPN transactions, structuring bursts).
- **Inline Feeding**: Pushes transactions directly through `UpiCaseService.evaluate()` and broadcasts updates in real time.

### 3.5 `InstitutionalAdapterService` (`app/adapters/service.py`)

Enriches inline transactions by simulating external national infrastructure:
- **NPCI MuleHunter**: Simulates switch-level pass-through velocity and multi-bank churn flags.
- **DPIP Smart Registry**: Simulates querying the national cybercrime blacklists with SHA-256 hash privacy.
- **Mock PSP Engines**: Injects simulated telemetry from participating banks (PhonePe, Paytm, GooglePay, BHIM).

### 3.6 `NotificationService` (`app/services/notification_service.py`)

Manages real-time mobile push notifications for compliance and emergency intervention:
- **Dual-Mode Provider**:
  - `MockFcmProvider`: In-memory thread-safe recorder for hermetic offline testing ($<0.1\text{ms}$ dispatch).
  - `HttpV1FcmProvider`: Live asynchronous `httpx` client communicating with Google Firebase Cloud Messaging HTTP v1 API (`https://fcm.googleapis.com/v1/projects/{project_id}/messages:send`).
- **Trigger**: Automatically invoked when any transaction receives a `BLOCK` verdict.

### 3.7 `GeminiAssistantService` (`app/services/gemini_service.py`)

Autonomous GenAI forensic investigator powered by `gemini-1.5-flash` with model failover cascade (`gemini-1.5-flash-8b`, `gemini-2.0-flash`, `gemini-1.5-pro`):
- **Executive Case Briefings (`generate_case_briefing`)**: Analyzes case features and outputs structured forensic summaries with scam classifications.
- **Statutory SAR Drafting (`generate_sar_report`)**: Generates formal narratives detailing modus operandi, transaction timeline, and regulatory violations.
- **Interactive Investigator Copilot (`chat_with_case_assistant`)**: Multi-turn contextual Q&A answering investigator questions.
- **Autonomous Agentic Tools**: Gemini can invoke platform actions via function calling or deterministic intent parsing:
  - `_execute_block_vpa_or_transaction`: Freezes accounts or transactions.
  - `_execute_trigger_federation_round`: Forces consortium consensus rounds.
  - `_execute_export_sar_pdf`: Exports case dossiers to PDF.
  - `_execute_simulate_transactions`: Injects test traffic bursts.
- **Hermetic Fallback**: When offline or if API keys are absent, falls back to the deterministic Encyclopedia Knowledge Base (`app/engine/encyclopedia_kb.py`).

---

## 4. Data Models & Schemas

### 4.1 Core Ingestion & Scoring Schemas (`app/models/upi_models.py`)

#### `UpiTransaction` (Incoming Payload)
```python
class UpiTransaction(BaseModel):
    txn_id: str                      # Unique UPI transaction reference
    timestamp: datetime              # UTC timestamp (default: utcnow)
    amount: float                    # Transfer amount in INR
    txn_type: str = "P2P"            # P2P, P2M, COLLECT
    payer_vpa: str                   # Payer Virtual Payment Address
    payer_psp: str = ""              # Auto-extracted PSP handle (e.g. oksbi)
    payer_account_age_days: int = 365# Age of payer account
    payee_vpa: str                   # Payee Virtual Payment Address
    payee_psp: str = ""              # Auto-extracted PSP handle
    payee_vpa_age_days: int = 365    # Age of payee VPA
    payee_is_new_for_payer: bool = False # First transfer flag
    device_id: str = ""              # Hardware fingerprint
    sim_id: str = ""                 # SIM card identifier
    note: str = ""                   # Remarks/memo
    ip: str = ""                     # Origin IP address
    location: str = ""               # "lat,lon" or city string
```

#### `UpiEvaluationResponse` (Decision Verdict)
```python
class UpiEvaluationResponse(BaseModel):
    txn_id: str                      # Transaction evaluated
    risk_score: int                  # Composite risk score [0, 100]
    action: str                      # Verdict: ALLOW, HOLD, BLOCK
    reasons: List[str]               # Triggered rule codes
    rule_breakdown: List[RuleHit]    # Per-rule score contributions
    rule_score: int                  # Layer 1 deterministic score
    adaptive_score: float            # Layer 2 adaptive score [0.0, 1.0]
    network_score: float             # Layer 3 federated graph score [0.0, 1.0]
    ml_anomaly_score: float          # Unsupervised Isolation Forest score [0.0, 1.0]
    supervised_fraud_score: float    # Supervised Random Forest score [0.0, 1.0]
    mock_npci_score: float           # Simulated NPCI MuleHunter score [0.0, 1.0]
    mock_dpip_threat_level: Union[float, int, str] # DPIP registry level
    contributing_signals: List[Dict[str, Any]]     # Institutional signal breakdown
    execution_latency_ms: float      # Decision latency in ms
    evaluated_at: datetime           # Timestamp
    case_id: Optional[str] = None    # Dossier identifier if HOLD or BLOCK
    dmv_score: float = 0.0           # Dead Money Velocity score [0, 100]
    campaign_id: Optional[str] = None# Matched fraud campaign ID
```

### 4.2 Threat Intelligence Models (`app/models/threat_intel.py`)

- `ExtractedEntities`: Normalizes phone numbers to `+91XXXXXXXXXX`, filters valid UPI handles excluding common email provider domains, strips URLs, and tags social engineering triggers.
- `ThreatSignalCreateRequest`: Request schema with pre-validation entity extraction and defensible confidence capping at $0.98$.
- `StandardFraudSignal`: Inter-institutional standardized signal schema with helper factories `from_psp()`, `from_npci()`, and `from_dpip()`.
- `GraphNode` & `GraphEdge`: Explicit vertex and relationship schemas for graph visualizers.

### 4.3 Database Persistence Models (`app/models/upi_persistence.py`)

SQLAlchemy 2.0 declarative models mapped to PostgreSQL:

| Model Class | Database Table | Primary Key | Key Columns |
| :--- | :--- | :--- | :--- |
| `UpiCaseModel` | `upi_cases` | `case_id` (`String(64)`) | `created_at`, `status`, `verdict`, `risk_score`, `payer_vpa`, `payee_vpa`, `amount`, `trigger_txn` (`JSONB`), `rule_hits` (`JSONB`), `ring_hash` (`FK`), `sar_markdown` (`Text`), `topology` (`JSONB`) |
| `MuleRingModel` | `mule_rings` | `ring_hash` (`String(64)`) | `detected_at`, `size`, `members` (`JSONB`), `psps` (`JSONB`), `total_amount`, `status` |
| `CaseFeedbackModel` | `case_feedback` | `id` (`Integer`, autoincrement) | `case_id` (`FK`), `confirmed_fraud` (`Boolean`), `resolution`, `notes`, `submitted_at`, `vpas_flagged` (`JSONB`), `dpip_published` (`JSONB`) |
| `AggregateStatsModel` | `aggregate_stats` | `stat_key` (`String(64)`) | `stat_value` (`Numeric(18,4)`), `metadata_json` (`JSONB`), `updated_at` |
| `ThreatSignalModel` | `threat_signals` | `id` (`Integer`, autoincrement) | `signal_id` (`String(64)`, unique), `source`, `phone`, `upi_id`, `url`, `tags` (`JSONB`), `severity`, `confidence`, `extracted_entities` (`JSONB`), `case_id` (`FK`), `ring_hash` (`FK`) |

---

## 5. End-to-End Data Pipeline & Evaluation Flow

### 5.1 Inline Transaction Processing Sequence

The sequence below depicts the complete end-to-end processing lifecycle of an incoming UPI transaction:

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

### 5.2 The 4-Layer Scoring Engine Breakdown

The evaluation logic executed in `UpiRiskScorer.evaluate()` (`app/engine/upi_scorer.py`):

$$\text{Combined Score} = \text{Rule Points} + \text{Adaptive Points} + \text{Network Points} + \text{ML Anomaly Points}$$

$$\text{Risk Score} = \min(100, \max(0, \text{Combined Score}))$$

```
                         ┌──────────────────────────────────────────────────┐
                         │             Incoming UpiTransaction              │
                         └────────────────────────┬─────────────────────────┘
                                                  │
                ┌─────────────────────────────────┼─────────────────────────────────┐
                │                                 │                                 │
                ▼                                 ▼                                 ▼
   ┌──────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
   │ Layer 1: Rules Engine    │      │ Layer 2: Adaptive EWMA   │      │ Layer 3: Federated Graph │
   │ 13 Deterministic Rules   │      │ Dynamic Payer Baselines  │      │ Cross-PSP Ring Scoring   │
   │ (0 - 100 Points)         │      │ (0 - 25 Points)          │      │ (0 - 40 Points)          │
   └────────────┬─────────────┘      └────────────┬─────────────┘      └────────────┬─────────────┘
                │                                 │                                 │
                └─────────────────────────────────┼─────────────────────────────────┘
                                                  │
                ┌─────────────────────────────────┴─────────────────────────────────┐
                │                                                                   │
                ▼                                                                   ▼
   ┌──────────────────────────┐                                        ┌──────────────────────────┐
   │ Dead Money Velocity (DMV)│                                        │ Layer 4: ML Models       │
   │ Dormancy + Burst Drain   │                                        │ Isolation Forest (0-25pt)│
   │ (0 - 100 DMV Score)      │                                        │ Supervised RF Classifier │
   └────────────┬─────────────┘                                        └────────────┬─────────────┘
                │                                                                   │
                └─────────────────────────────────┬─────────────────────────────────┘
                                                  │
                                                  ▼
                                 ┌─────────────────────────────────┐
                                 │ Decision Threshold Gate         │
                                 │ Risk >= 70           ==> BLOCK  │
                                 │ Risk >= 45 or Floored==> HOLD   │
                                 │ Risk <  45           ==> ALLOW  │
                                 └─────────────────────────────────┘
```

#### Layer 1: Deterministic Rules (`app/engine/upi_rules.py`)
1. `R_HONEYPOT_HIT` (+100 pts): Payee matches active synthetic honeypot trap. Immediate critical flag.
2. `R_IMPOSSIBLE_TRAVEL` (+35 pts): Distance between successive locations requires impossible travel speed ($>1000\text{ km/h}$). Calculated using spherical Haversine formula over geographic coordinates.
3. `R_SIM_DEVICE_MISMATCH` (+30 pts): Hardware device fingerprint or SIM identity swap detected on known account.
4. `R_DATACENTER_IP` (+25 pts): Origin IP falls within known AWS, GCP, Azure, DigitalOcean, or Tor Exit Node CIDR blocks (`ipaddress.ip_network`).
5. `R_CAMPAIGN_MATCH` (+30 pts): Transaction matches active fraud campaign DNA signatures.
6. `PASS_THROUGH_CONDUIT` (+30 pts): Fresh account ($<30\text{d}$) rapidly forwards $\ge 90\%$ of funds received within sliding window.
7. `FAN_IN_BURST` (+25 pts): Fresh payee collects from $\ge 5$ distinct payers within sliding window.
8. `FAN_OUT_DISPERSAL` (+25 pts): Fresh payer disperses funds to $\ge 5$ distinct payees.
9. `DEVICE_FARM` (+20 pts): Single device hardware or SIM fingerprint bound to $\ge 3$ distinct VPAs.
10. `NEW_ACCOUNT_HIGH_VALUE` (+15 to +50 pts): Fresh account moving high value ($\ge \text{Rs }10,000$).
11. `LIMIT_SKIRTING` (+10 pts): Amount sits suspiciously just below reporting thresholds (Rs 10k, 25k, 50k, 100k).
12. `NEW_PAYEE_VPA` (+25 pts): Payee registered $<15\text{ days}$ ago.
13. `KNOWN_FRAUD_ENTITY` (+35 pts): Payer or payee recorded in analyst-confirmed fraud memory.

#### Layer 2: Adaptive EWMA Anomaly Detection (`app/engine/adaptive.pyc`)
Tracks Exponentially Weighted Moving Averages (EWMA) of individual account behavior (transaction size, frequency, nocturnal distribution). Generates adaptive anomaly scores in $[0.0, 1.0]$, contributing up to 25 risk points.

#### Layer 3: Cross-PSP Federated Graph Network Score (`app/federation/coordinator.py`)
Consortium intelligence computed by aggregating pseudonymized feature shares across nodes:
$$\text{Score} = \text{Consortium Ring Suspicion} \times \text{Network Degree Weight}$$
Contributes up to 40 risk points.

#### Dead Money Velocity (DMV) Engine (`app/engine/dmv.py`)
Quantifies the hallmark signature of dormant mule accounts:
- **Dormancy Index** $D \in [0.0, 1.0]$: Elapsed days since prior outbound activity relative to a 30-day baseline:
  $$D = \min\left(1.0, \frac{\text{elapsed\_days}}{30.0}\right)$$
- **Burst Velocity Index** $V \in [0.0, 1.0]$: Rapid drainage of funds in a 1-hour window:
  $$V = 0.50 \times \text{drain\_ratio} + 0.30 \times \text{rate\_factor} + 0.20 \times \text{amt\_factor}$$
- **Composite DMV Score**:
  $$\text{Raw DMV} = 100 \times (0.40 \cdot D + 0.60 \cdot V)$$
  If $D \ge 0.5$ and $V \ge 0.4$, a synergistic multiplier is applied:
  $$\text{Final DMV} = \text{Raw DMV} \times (1.0 + 0.5 \cdot (D \cdot V))$$

#### Layer 4: Unsupervised Isolation Forest (`app/engine/isolation_forest.py`)
Implemented in pure NumPy from first principles based on the canonical Liu, Ting, Zhou (ICDM 2008) algorithm.
- Uses 13 standardized features (amounts, log amounts, cyclical hour sine/cosine, night flags, account ages, 1-hour velocity counts/amounts, device binding count, DMV score).
- Fits on a synthetic baseline of retail UPI transactions ($N \approx 700$, contamination $= 3.5\%$).
- Anomaly score derived via average path length $E(h(x))$ across isolation trees:
  $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
  where $c(n) = 2(\ln(n - 1) + 0.5772156649) - \frac{2(n - 1)}{n}$.

#### Supervised Random Forest Classifier (`app/engine/supervised_classifier.py`)
Pure NumPy bagged ensemble with random feature subsampling and Gini impurity splits. Generates calibrated fraud probabilities $P(\text{fraud} \mid x) \in [0.0, 1.0]$.

#### Verdict Decision Matrix:
- `BLOCK`: Composite Risk $\ge 70$.
- `HOLD`: Composite Risk $\in [45, 69]$, OR Network Score $\ge 0.70$, OR ML Anomaly Score $\ge 0.85$, OR Supervised Fraud Score $\ge 0.85$.
- `ALLOW`: Composite Risk $< 45$ and no floor triggers.

### 5.3 Real-Time Broadcasting Hub (`app/api/websocket.py`)

Real-time streaming is powered by `ConnectionManager`:
- **Thread Safety**: Uses an `asyncio.Lock()` to serialize registration and pruning across coroutines.
- **Dead Connection Pruning**: When `connection.send_json()` fails due to client disconnection or socket timeout, the connection is added to a purge list and pruned cleanly without interrupting the broadcast to remaining clients.
- **Payload Formatting**: Ensures ISO-8601 formatting for datetimes and serialization of NumPy floating types.
- **Event Channels**:
  - `UPI_EVALUATED`: Full scoring breakdown and rule contributions for every processed transaction.
  - `new_case`: Complete formatted case dossier whenever a transaction is placed on `HOLD` or `BLOCK`.
  - `UPI_CASE_OPENED`: Compact event payload alerting dashboard badges.
  - `stats_update`: Live aggregate telemetry (evaluated count, held, blocked, active rings, honeypot hits).
  - `FEDERATION_ROUND`: Results of consortium consensus rounds.

---

## 6. Database Layer (PostgreSQL)

### 6.1 Database Engine & Connection Lifecycle (`app/db/session.py`)

Optimized for cloud-hosted environments (AWS RDS PostgreSQL on `db.t3.micro` free tier, which enforces an 87-connection ceiling):
```python
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

#### Key Connection Policies:
1. **URL Normalization (`get_normalized_database_url`)**: Transparently converts `postgres://` or `postgresql://` connection strings into `postgresql+asyncpg://` for native asynchronous IO.
2. **Pre-Ping Liveness (`pool_pre_ping=True`)**: Issues a lightweight test statement (`SELECT 1`) before checking out connections from the pool, preventing stale connection errors after RDS maintenance or idle timeouts.
3. **Connection Recycling (`pool_recycle=1800`)**: Recycles connections after 30 minutes to prevent resource leakage on low-memory instances.
4. **Session Dependency (`get_db`)**: A FastAPI dependency generator yielding an isolated `AsyncSession` per request with automatic commit on success and rollback on exception.

### 6.2 Relational Schema & Table Definitions (`app/models/upi_persistence.py`)

#### Table: `upi_cases`
Stores every flagged transaction requiring human investigation or regulatory SAR filing.
```sql
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
CREATE INDEX ix_upi_cases_payer_vpa ON upi_cases (payer_vpa);
CREATE INDEX ix_upi_cases_payee_vpa ON upi_cases (payee_vpa);
CREATE INDEX ix_upi_cases_ring_hash ON upi_cases (ring_hash);
CREATE INDEX ix_upi_cases_status_created ON upi_cases (status, created_at);
CREATE INDEX ix_upi_cases_verdict_created ON upi_cases (verdict, created_at);
```

#### Table: `mule_rings`
Maintains detected multi-PSP syndicate clusters.
```sql
CREATE TABLE mule_rings (
    ring_hash VARCHAR(64) PRIMARY KEY,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    size INTEGER NOT NULL,
    members JSONB NOT NULL,
    psps JSONB NOT NULL,
    total_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'
);

CREATE INDEX ix_mule_rings_ring_hash ON mule_rings (ring_hash);
CREATE INDEX ix_mule_rings_detected_at ON mule_rings (detected_at);
```

#### Table: `case_feedback`
Maintains an immutable audit log of compliance officer resolutions:
```sql
CREATE TABLE case_feedback (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL REFERENCES upi_cases(case_id) ON DELETE CASCADE,
    confirmed_fraud BOOLEAN NOT NULL,
    resolution VARCHAR(64) NOT NULL,
    notes TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    vpas_flagged JSONB NOT NULL DEFAULT '[]',
    dpip_published JSONB
);

CREATE INDEX ix_case_feedback_case_id ON case_feedback (case_id);
```

#### Table: `threat_signals`
Pre-transaction early warning intelligence:
```sql
CREATE TABLE threat_signals (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(64) UNIQUE NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'external',
    phone VARCHAR(32),
    upi_id VARCHAR(128),
    url VARCHAR(512),
    tags JSONB NOT NULL DEFAULT '[]',
    raw_content TEXT,
    severity VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    confidence FLOAT NOT NULL DEFAULT 0.85,
    extracted_entities JSONB DEFAULT '{}',
    matched_campaign_id VARCHAR(64),
    matched_campaign_name VARCHAR(128),
    similarity_score FLOAT NOT NULL DEFAULT 0.0,
    case_id VARCHAR(64) REFERENCES upi_cases(case_id) ON DELETE SET NULL,
    ring_hash VARCHAR(64) REFERENCES mule_rings(ring_hash) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_threat_signals_signal_id ON threat_signals (signal_id);
CREATE INDEX ix_threat_signals_source_created ON threat_signals (source, created_at);
CREATE INDEX ix_threat_signals_severity_created ON threat_signals (severity, created_at);
CREATE INDEX ix_threat_signals_phone_created ON threat_signals (phone, created_at);
CREATE INDEX ix_threat_signals_upi_created ON threat_signals (upi_id, created_at);
```

### 6.3 Dual-Mode Database Operation & In-Memory Fallback

When `DATABASE_URL` is omitted or PostgreSQL is unreachable, the system automatically falls back to `AsyncDatabaseStore` (`app/db/session.py:211-280`):
- Uses thread-safe Python dictionaries (`accounts`, `batches`, `cases`, `payees`, `reports`) and lists (`audit_logs`).
- Emulates async session operations with identical signatures (`save_flagged_case`, `list_flagged_cases`, `update_case_forensics`).
- Allows the entire platform to operate with zero external database dependencies for local demonstrations and continuous integration test suites.

---

## 7. Cache & Hot State Layer (Redis)

### 7.1 Redis Architecture & Client Pooling (`app/engine/redis_state.pyc`)

The hot state layer provides sub-millisecond account profiling, sliding-window velocity aggregation, and distributed concurrency locking.
- **Client Initialization**: Built with `redis.from_url(redis_url, decode_responses=True, socket_timeout=1.0)` with connection pooling.
- **Dual-Mode Fallback**: If Redis is unreachable, all calls route cleanly to an internal `InMemoryStore` maintaining equivalent sorted sets, hashes, and lock semantics.

### 7.2 Redis Key Naming Schema

All Redis keys adhere to structured namespace conventions:

| Key Pattern | Redis Data Type | TTL | Purpose |
| :--- | :--- | :--- | :--- |
| `cms:session:{account_id}:{batch_id}` | String / Flag | 60–300s | Distributed idempotency lock for transaction/batch processing |
| `cms:session:{batch_id}` | String / Flag | 60–300s | Global batch lock fallback |
| `cms:account:{account_id}:profile` | Hash / JSON String | Persistent | Rolling account profile (total txns, avg size, risk status) |
| `cms:account:{account_id}:velocity` | Sorted Set (`ZSET`) | 86400s | Sliding-window transaction timestamps for velocity scoring |
| `cms:account:{account_id}:payees` | Set (`SET`) | 30 days | Known beneficiary VPAs to detect first-time payee anomalies |

### 7.3 Sliding Window Velocity Implementation

To evaluate burst velocities in sub-millisecond time without scanning disk storage, SAMPATI V2 leverages Redis Sorted Sets:
1. **Recording an Event**:
   ```
   ZADD cms:account:{account_id}:velocity <timestamp_epoch> <txn_id>
   ```
2. **Pruning Expired Window Events**:
   ```
   ZREMRANGEBYSCORE cms:account:{account_id}:velocity -inf (<now_epoch> - 3600)
   ```
3. **Counting Window Velocity**:
   ```
   ZCARD cms:account:{account_id}:velocity
   ```
   Or within custom intervals:
   ```
   ZCOUNT cms:account:{account_id}:velocity (<now_epoch> - 600) +inf
   ```

### 7.4 Distributed Concurrency Locking

To guarantee strict idempotency and prevent race conditions during rapid transaction bursts:
```python
def acquire_batch_lock(self, account_id: str, batch_id: str, timeout_sec: int = 300) -> bool:
    """Acquire atomic idempotency lock on in-flight batch.
    Requires BOTH account session lock and global batch lock.
    """
```
Uses atomic Redis `SET ... NX EX` operations. If a lock key already exists, concurrent attempts to re-evaluate the same batch/transaction are rejected immediately.

### 7.5 In-Memory Hot State (`UpiHotState` — `app/engine/upi_state.pyc`)

For UPI flow analysis, the engine maintains an in-process, thread-safe sliding window (`WINDOW_SECONDS = 1800.0` or 30 minutes):
- **Data Structures**:
  - `_inbound_flows`: `defaultdict(deque)` mapping VPA $\to$ `[(timestamp, payer_vpa, amount)]`
  - `_outbound_flows`: `defaultdict(deque)` mapping VPA $\to$ `[(timestamp, payee_vpa, amount)]`
  - `_device_map`: `defaultdict(set)` mapping hardware/SIM fingerprint $\to$ distinct VPAs
  - `_fraud_vpas`: `defaultdict(int)` mapping VPA $\to$ count of analyst-confirmed fraud incidents
- **Pruning**: Deques are evicted via binary timestamp comparison on every ingress event:
  $$\text{timestamp} < \text{now} - 1800.0 \implies \text{popleft()}$$
- **Telemetry Querying**:
  - `inbound_stats(vpa, now)` $\to$ `(count, distinct_payers, total_amount)` in $<0.05\text{ms}$.
  - `outbound_stats(vpa, now)` $\to$ `(count, distinct_payees, total_amount)` in $<0.05\text{ms}$.
  - `device_vpa_count(fingerprint)` $\to$ count of bound VPAs for device-farm detection.

---

## 8. Forensic Artifacts & SAR PDF Generation

### 8.1 PDF Rendering Architecture (`app/forensics/sar_pdf.py`)

Regulatory reporting requires generating publication-grade documents matching Financial Intelligence Unit - India (FIU-IND) standards.
- **Rendering Engine**: Uses `matplotlib.backends.backend_pdf.PdfPages` set to `Agg` (headless mode) to generate crisp vector PDF documents with zero external shell dependencies.
- **Page 1: Executive Dossier & Forensic Metadata**:
  - High-impact header banner color-coded by verdict (`#991b1b` for `BLOCK`, `#b45309` for `HOLD`, `#1e3a8a` for `ALLOW`).
  - Case Assessment Summary box: verdict, risk score, DMV score, campaign match, ring hash.
  - Trigger Transaction DNA: transaction ID, amount, payer/payee VPAs.
  - Explainable Rule Breakdown: list of triggered rules with exact point contributions.
  - Token Economy Indicators: financial velocity, turnover ratio, conduit forward ratio.
  - Embedded Network Graph Thumbnail: renders visual topology of the mule syndicate.
- **Page 2: Formal SAR Narrative & Compliance Disclosure**:
  - Regulatory disclosure headers citing PMLA 2002 and RBI Master Directions.
  - Full structured narrative generated dynamically or by Google Gemini.
  - Statutory declarations and digital signature audit blocks.

---

## 9. Architectural Verification & Quality Matrix

| Architectural Subsystem | Source Component | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **FastAPI App & Lifespan** | `app/main.py:141-190` | Verified `lifespan`, DB init, sync, shutdown | Passed |
| **Routing & SPA Fallback** | `app/main.py:440-488` | 63 endpoints validated, regex routing confirmed | Passed |
| **Settings & Environment** | `app/config.pyc` | Introspected all 10 configuration fields | Passed |
| **Postgres Async Pool** | `app/db/session.py:48-96` | Verified `asyncpg` engine, pool sizing, pre-ping | Passed |
| **Relational DDL & JSONB** | `app/models/upi_persistence.py` | Verified 5 tables, compound indices, relationships | Passed |
| **In-Memory DB Fallback** | `app/db/session.py:211-280` | Verified `AsyncDatabaseStore` methods | Passed |
| **Redis Hot State Manager** | `app/engine/redis_state.pyc` | Disassembled `acquire_batch_lock`, `record_velocity` | Passed |
| **UPI Sliding Window** | `app/engine/upi_state.pyc` | Verified 1800s deque sliding window | Passed |
| **Deterministic Rules (13)**| `app/engine/upi_rules.py` | Verified all 13 rules (Honeypot, Travel, SIM, DC) | Passed |
| **Dead Money Velocity** | `app/engine/dmv.py:145-199` | Validated Dormancy $D$ & Burst $V$ math formulation | Passed |
| **Unsupervised Isolation Forest** | `app/engine/isolation_forest.py` | Pure NumPy ICDM 2008 algorithm & 13 features | Passed |
| **Supervised Classifier** | `app/engine/supervised_classifier.py`| Pure NumPy Decision Tree & Random Forest | Passed |
| **Central Fraud Graph** | `app/services/graph_service.py` | NetworkX DiGraph nodes, edges, BFS extraction | Passed |
| **Threat Intel Mesh** | `app/services/threat_intel_service.py`| Regex extractors & syndicate clustering | Passed |
| **Institutional Adapters**| `app/adapters/service.py` | NPCI MuleHunter, DPIP Registry, Mock PSPs | Passed |
| **GenAI Forensic Copilot**| `app/services/gemini_service.py` | Agentic tool execution, briefing, SAR drafting | Passed |
| **FCM Push Notifications** | `app/services/notification_service.py`| Mock and HTTP v1 providers verified | Passed |
| **WebSocket Push Hub** | `app/api/websocket.py` | Thread-safe connection manager & dead socket prune | Passed |
| **SAR PDF Generator** | `app/forensics/sar_pdf.py` | Matplotlib PdfPages 2-page FIU-IND report | Passed |

---

## Conclusion

The backend architecture of SAMPATI V2 demonstrates exceptional engineering depth:
1. **Low Latency (<2ms Inline SLA)**: By running deterministic heuristics, pure NumPy machine learning inference, and sliding-window velocity checks in in-memory state, transactions are adjudicated well within real-time banking SLAs.
2. **Resilience & High Availability**: Complete dual-mode design across all subsystems—PostgreSQL $\leftrightarrow$ `AsyncDatabaseStore`, Redis $\leftrightarrow$ `InMemoryStore`, Gemini AI $\leftrightarrow$ Encyclopedia KB, FCM HTTP v1 $\leftrightarrow$ `MockFcmProvider`—guarantees uninterrupted execution under any deployment scenario.
3. **Comprehensive Observability**: Full telemetry encompassing latency percentiles, throughput counters, DB pool metrics, and active WebSocket tracking provides actionable operational visibility for compliance officers and platform operators alike.

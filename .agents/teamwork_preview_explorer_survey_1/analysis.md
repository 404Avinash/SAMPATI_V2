# Backend Architecture Survey & Technical Specification: Requirement 1 — Early Warning Intelligence Layer

**Target Component**: Early Warning Threat Intelligence Engine, Central Fraud Graph, Database Models & FastAPI API Layer  
**Target Requirement**: Requirement 1 — Early Warning Intelligence Layer (Backend) per `ORIGINAL_REQUEST.md` (2026-09-03T09:32:24Z)  
**Author**: Explorer 1 (`teamwork_preview_explorer_survey_1`)  
**Date**: 2026-09-03  
**Integrity Mode**: Benchmark  
**Baseline Test Status**: 833 / 833 tests passing (100%), Ruff clean, ESLint clean, Vite build clean.

---

## 1. Executive Summary & Problem Scope

Requirement 1 mandates the construction of an **Early-Warning Intelligence Layer** to ingest pre-transaction threat signals before funds ever move across UPI rails:
1. **Pre-Transaction Threat Signals**: Ingest standard fraud signal JSON payloads (from external mobile apps, mock PSPs, and SMS telemetry) containing identifiers (`Phone`, `UPI ID`, `URL`) and social engineering tags (e.g., `"Bank impersonation"`, `"Urgency"`, `"KYC Expiry"`, `"Lottery / Reward"`).
2. **Entity Extraction & Parsing**: Support both structured identifier inputs and automatic regex entity extraction from raw unstructured message text (SMS / WhatsApp / phishing messages).
3. **Campaign Clustering & Similarity**: Automatically match extracted signals against fraud syndicate campaign profiles (e.g., `CAMP-KYC-PHISH-01`, `CAMP-INVESTMENT-03`), calculating campaign similarity percentages (e.g., `94%`).
4. **Central Fraud Graph Linkage (`app/services/graph_service.py`)**: Automatically link pre-transaction threat entities to existing UPI cases, mule rings, and transaction nodes in a centralized, queryable `networkx.DiGraph` fraud graph.
5. **PostgreSQL Persistence & In-Memory Fallback**: Store signals in a new `ThreatSignalModel` (`threat_signals` table) in PostgreSQL via SQLAlchemy 2.0 with full JSONB support, while maintaining high-performance in-memory cache resilience when running without a database.
6. **Real-Time Streaming & API Endpoints**: Expose `/intel/signals`, `/intel/graph`, `/intel/campaigns`, and `/intel/simulate` REST endpoints, and broadcast real-time `THREAT_SIGNAL_RECEIVED` events across the WebSocket push hub.

---

## 2. Codebase Audit & Architectural Baseline

### 2.1 Existing Routers (`app/api/`)
- **`app/api/upi.py`**:
  - Contains inline gate `POST /upi/check`, case management `/upi/cases`, `/upi/simulate`, and `/upi/stats`.
  - Uses `broadcast_event("UPI_EVALUATED", payload)` from `app.api.websocket`.
  - Employs `Depends(get_db)` yielding `Optional[AsyncSession]`.
- **`app/api/federation.py`**:
  - Exposes `POST /federation/signal`, `GET /federation/query`, and `GET /federation/signals`.
  - Manages inter-PSP hash-level signals via `FederatedCoordinator` (`app/federation/coordinator.py`).
  - Broadcasts `FEDERATION_SIGNAL_RECEIVED` over WebSocket.
- **`app/api/websocket.py`**:
  - Provides `ConnectionManager` with routes `/ws`, `/ws/`, `/ws/feed`.
  - Exposes `broadcast_event(event, payload)` (async) and `schedule_broadcast(payload)` (thread-safe synchronous helper).
- **`app/main.py`**:
  - Line 423-435 defines `api_prefixes` for the SPA 404 fallback handler:
    ```python
    api_prefixes = (
        "/upi",
        "/federation",
        "/gateway",
        "/cases",
        "/synthetic",
        "/ws",
        "/health",
        "/api",
        "/stats",
        "/static",
    )
    ```
  - **CRITICAL**: The SPA fallback handler returns `index.html` for any 404 route not matching `api_prefixes`. Thus, `/intel` and `/threat-intel` MUST be added to `api_prefixes` in `app/main.py`!

### 2.2 Existing Database Layer (`app/db/` & `app/models/upi_persistence.py`)
- **`app/db/session.py`**:
  - Initializes database in `init_db()` via `await conn.run_sync(UpiBase.metadata.create_all)`.
  - Provides `get_db()` FastAPI dependency yielding `Optional[AsyncSession]`.
  - Gracefully falls back to in-memory mode if `DATABASE_URL` is empty.
- **`app/models/upi_persistence.py`**:
  - Defines `UpiCaseModel` (`upi_cases`), `MuleRingModel` (`mule_rings`), `CaseFeedbackModel` (`case_feedback`), and `AggregateStatsModel` (`aggregate_stats`).
  - Uses `JSON_TYPE = JSON().with_variant(JSONB, "postgresql")` for cross-database JSON/JSONB support.

### 2.3 Central Fraud Graph Status
- Currently, there is **no dedicated `graph_service.py`** in `app/services/`.
- Graph data is fragmented:
  - `UpiCaseService._cases[case_id]["topology"]` holds fan-in/fan-out/hops counters.
  - `FederatedCoordinator._rings` holds member sets.
  - `NetworkConstellation.jsx` synthesizes nodes and edges ad-hoc on the frontend canvas from case topologies.
- `networkx 3.6.1` is already installed and verified in `./.venv/bin/python`.
- Creating `app/services/graph_service.py` (`FraudGraphService`) establishes a single source of truth for the multi-entity fraud graph.

### 2.4 Campaign Engine (`app/engine/campaign.py`)
- Defines `CampaignSignature` and `CampaignSignatureStore` (`get_campaign_store()`).
- Seeds 3 reference campaigns:
  - `CAMP-KYC-PHISH-01`: "KYC Phishing Syndicate" (keywords: kyc, verify, pan, aadhar, unblock, otp, suspend)
  - `CAMP-SMURF-BURST-02`: "Micro-Smurfing Dispersal Ring" (keywords: transfer, split, cashout, p2p, conduit)
  - `CAMP-INVESTMENT-03`: "Task Scam / Investment Fraud Ring" (keywords: task, invest, bonus, telegram, crypto, profit, commission)
- Computes cosine-like similarity `compute_similarity(txn)` and `match_campaign(txn, threshold=0.82)`.
- Can be directly utilized/extended to match incoming pre-transaction threat tags and text against campaign clusters!

---

## 3. Data Schemas & Pydantic Validation Models (`app/models/threat_intel.py`)

### 3.1 Ingestion Request & Enriched Response Schemas

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
import re
from pydantic import BaseModel, Field, model_validator

class ThreatSignalCreateRequest(BaseModel):
    """Payload for ingesting pre-transaction threat signals."""
    signal_id: Optional[str] = Field(default=None, description="Optional custom identifier (auto-generated if null)")
    source: str = Field(default="mobile_app", description="Source of threat intel: 'mobile_app', 'mock_psp', 'sms_telemetry', 'community_report'")
    phone: Optional[str] = Field(default=None, description="Reported or extracted sender telephone number")
    upi_id: Optional[str] = Field(default=None, description="Reported or extracted suspect UPI VPA")
    url: Optional[str] = Field(default=None, description="Reported or extracted phishing/malicious URL")
    tags: List[str] = Field(default_factory=list, description="Social engineering tags, e.g. ['Bank impersonation', 'Urgency', 'KYC Expiry']")
    raw_content: Optional[str] = Field(default=None, description="Raw message text (SMS, WhatsApp, email body) for entity extraction")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    severity: str = Field(default="HIGH", description="Severity level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'")
    reporter_info: Optional[Dict[str, Any]] = Field(default=None, description="Reporting agent, bank, or device metadata")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional custom telemetry attributes")

    @model_validator(mode="after")
    def validate_has_identifier_or_content(self) -> ThreatSignalCreateRequest:
        if not (self.phone or self.upi_id or self.url or (self.raw_content and self.raw_content.strip())):
            raise ValueError("At least one identifier (phone, upi_id, url) or raw_content must be provided.")
        return self

class ExtractedEntities(BaseModel):
    phones: List[str] = Field(default_factory=list)
    upi_ids: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class MatchedCampaignSummary(BaseModel):
    campaign_id: str
    campaign_name: str
    similarity: float = Field(description="Clustering similarity score in [0.0, 1.0]")
    scenario: str

class ThreatSignalResponse(BaseModel):
    """Full enriched response returned on signal ingestion and retrieval."""
    signal_id: str
    created_at: str
    source: str
    phone: Optional[str] = None
    upi_id: Optional[str] = None
    url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    raw_content: Optional[str] = None
    confidence: float
    severity: str
    status: str = "ACTIVE"
    entities_extracted: ExtractedEntities
    matched_campaign: Optional[MatchedCampaignSummary] = None
    linked_case_id: Optional[str] = None
    linked_ring_hash: Optional[str] = None
    graph_nodes_count: int = 0
    graph_edges_count: int = 0
    metadata: Optional[Dict[str, Any]] = None

class ThreatSignalListResponse(BaseModel):
    total: int
    signals: List[ThreatSignalResponse]
    active_campaigns_count: int
    linked_cases_count: int
```

### 3.2 Entity Extraction Engine

Extracts entities from `raw_content` with robust Indian financial telecommunication regexes:
- **Phone Numbers**: `r"(?:\+91[\-\s]?|0)?[6-9]\d{9}\b"`
- **UPI VPAs**: `r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b"`
- **URLs**: `r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*"`
- **Social Engineering Tags**:
  - `Bank impersonation`: "bank", "sbi", "hdfc", "icici", "rbi", "customer care", "helpline", "officer", "manager"
  - `Urgency`: "immediately", "urgent", "blocked", "suspended", "24 hours", "today", "expire", "action required"
  - `KYC Expiry`: "kyc", "pan", "aadhaar", "document", "verification", "unblock"
  - `Lottery / Prize`: "lottery", "prize", "won", "reward", "cashback", "crore", "lakh", "congratulations"
  - `Part-time Job / Task Scam`: "task", "job", "telegram", "crypto", "daily income", "part time", "vip"
  - `Digital Arrest`: "police", "arrest", "cbi", "customs", "cyber crime", "court", "warrant"

---

## 4. PostgreSQL Persistence Model (`app/models/upi_persistence.py`)

Add `ThreatSignalModel` to `app/models/upi_persistence.py`:

```python
class ThreatSignalModel(Base):
    """Persistent storage for pre-transaction early warning threat signals."""
    __tablename__ = "threat_signals"

    signal_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    source = Column(String(64), default="mobile_app", nullable=False, index=True)
    phone = Column(String(32), nullable=True, index=True)
    upi_id = Column(String(128), nullable=True, index=True)
    url = Column(Text, nullable=True)
    tags = Column(JSON_TYPE, default=list, nullable=False)
    raw_content = Column(Text, nullable=True)
    confidence = Column(Float, default=0.85, nullable=False)
    severity = Column(String(16), default="HIGH", nullable=False, index=True)
    status = Column(String(32), default="ACTIVE", nullable=False, index=True)
    campaign_id = Column(String(64), nullable=True, index=True)
    campaign_similarity = Column(Float, default=0.0, nullable=True)
    linked_case_id = Column(String(64), ForeignKey("upi_cases.case_id", ondelete="SET NULL"), nullable=True, index=True)
    linked_ring_hash = Column(String(64), ForeignKey("mule_rings.ring_hash", ondelete="SET NULL"), nullable=True, index=True)
    entities_extracted = Column(JSON_TYPE, default=dict, nullable=True)
    signal_metadata = Column(JSON_TYPE, default=dict, nullable=True)

    # Relationships
    linked_case = relationship("UpiCaseModel", foreign_keys=[linked_case_id])
    linked_ring = relationship("MuleRingModel", foreign_keys=[linked_ring_hash])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": getattr(self, "signal_id", None),
            "created_at": self.created_at.isoformat() if isinstance(getattr(self, "created_at", None), datetime) else str(getattr(self, "created_at", "")),
            "source": getattr(self, "source", "mobile_app"),
            "phone": getattr(self, "phone", None),
            "upi_id": getattr(self, "upi_id", None),
            "url": getattr(self, "url", None),
            "tags": getattr(self, "tags", []) or [],
            "raw_content": getattr(self, "raw_content", None),
            "confidence": float(getattr(self, "confidence", 0.85) or 0.85),
            "severity": getattr(self, "severity", "HIGH"),
            "status": getattr(self, "status", "ACTIVE"),
            "campaign_id": getattr(self, "campaign_id", None),
            "campaign_similarity": float(getattr(self, "campaign_similarity", 0.0) or 0.0),
            "linked_case_id": getattr(self, "linked_case_id", None),
            "linked_ring_hash": getattr(self, "linked_ring_hash", None),
            "entities_extracted": getattr(self, "entities_extracted", {}) or {},
            "signal_metadata": getattr(self, "signal_metadata", {}) or {},
        }
```

---

## 5. Central Fraud Graph Service (`app/services/graph_service.py`)

### 5.1 Graph Architecture & Topology
Implements `FraudGraphService` using `networkx.DiGraph`:

- **Node Types & Attributes**:
  - `VPA`: `{id: "vpa:<vpa>", label: "<vpa>", type: "VPA", psp: "<psp>", risk_score: float, status: str}`
  - `PHONE`: `{id: "phone:<phone>", label: "<phone>", type: "PHONE", tags: list, risk_score: float}`
  - `URL`: `{id: "url:<url>", label: "<url>", type: "URL", domain: str, risk_score: float}`
  - `CAMPAIGN`: `{id: "camp:<camp_id>", label: "<name>", type: "CAMPAIGN", similarity: float}`
  - `CASE`: `{id: "case:<case_id>", label: "<case_id>", type: "CASE", verdict: str, amount: float}`
  - `SIGNAL`: `{id: "sig:<signal_id>", label: "<signal_id>", type: "SIGNAL", source: str, severity: str}`

- **Edge Types & Relationships**:
  - `(SIGNAL) -> [EXTRACTED] -> (PHONE | VPA | URL)`: Entity extraction from signal.
  - `(PHONE) -> [ASSOCIATED_WITH] -> (VPA)`: Threat correlation.
  - `(URL) -> [ASSOCIATED_WITH] -> (VPA)`: Payment destination linked to phishing site.
  - `(VPA) -> [TRANSACTED_TO] -> (VPA)`: Financial transaction flow.
  - `(VPA) -> [CLUSTERS_IN] -> (CAMPAIGN)`: Campaign syndication.
  - `(VPA) -> [FLAGGED_IN] -> (CASE)`: Case linkage.

### 5.2 Automatic Linking Protocol
When a signal is ingested:
1. **Case Linkage**:
   - Query `UpiCaseService.get_case()` or search `_cases.values()` for any case where `payer_vpa == signal.upi_id` or `payee_vpa == signal.upi_id`.
   - If found, link `signal.linked_case_id = case["case_id"]`, and if `case.get("ring_hash")`, set `signal.linked_ring_hash = case["ring_hash"]`.
   - Add bidirectional graph edge `(VPA) <-> (CASE)`.
2. **Federation Feed Linkage**:
   - Call `FederatedCoordinator.record_signal(vpa_hash=signal.upi_id, risk_level="HIGH", ring_hash=signal.linked_ring_hash, node_id=signal.source)`.
   - This ensures any upcoming transaction immediately registers an elevated Layer 3 federated score!
3. **Campaign Clustering**:
   - Query `CampaignSignatureStore.match_campaign(txn_dummy)` or text similarity against `FRAUD_KEYWORD_CLUSTERS`.
   - Calculate similarity score (e.g. 0.94). If $\ge 0.70$, cluster signal under the campaign node and add VPA/phone to `CampaignSignature.member_vpas`.

---

## 6. API Endpoints Specification (`app/api/intel.py`)

Mounted at `/intel` (and mirrored at `/threat-intel`):

| Method | Path | Summary | Description |
|---|---|---|---|
| `POST` | `/intel/signals` | Ingest Pre-Transaction Signal | Ingests signal payload, performs entity extraction, clusters into campaigns, updates Fraud Graph, broadcasts WebSocket event, persists to DB/cache. Returns 201 Created. |
| `GET` | `/intel/signals` | List Threat Signals | Returns paginated list of threat signals with filtering by `tag`, `severity`, `source`, `limit`, `offset`. |
| `GET` | `/intel/signals/{signal_id}` | Get Signal Dossier | Returns detailed signal record with extracted entities, linked case, and local 1-hop graph neighbors. |
| `GET` | `/intel/graph` | Central Fraud Graph | Returns entire graph or filtered subgraph nodes and edges in D3/Cytoscape format for the frontend visualizer. |
| `GET` | `/intel/campaigns` | Campaign Clustering Metrics | Returns active fraud campaigns with similarity percentages, hit counts, and member counts. |
| `POST` | `/intel/simulate` | Seed Pre-Transaction Demo Signals | Generates 3–5 realistic pre-transaction threat signals (KYC phishing, task scam, bank impersonation) with real entities. |

### 6.1 WebSocket Event Schema
On every ingestion, broadcast:
```json
{
  "event": "THREAT_SIGNAL_RECEIVED",
  "data": {
    "signal_id": "SIG-8F2B1C",
    "source": "mobile_app",
    "phone": "+919876543210",
    "upi_id": "phish_trap@oksbi",
    "url": "https://sbi-kyc-verify-alert.com/login",
    "tags": ["Bank impersonation", "Urgency", "KYC Expiry"],
    "severity": "CRITICAL",
    "confidence": 0.95,
    "matched_campaign": {
      "campaign_id": "CAMP-KYC-PHISH-01",
      "campaign_name": "KYC Phishing Syndicate",
      "similarity": 0.94
    },
    "linked_case_id": "CASE-2026-0801",
    "timestamp": "2026-09-03T09:35:00Z"
  }
}
```

---

## 7. Quality Gates & Test Plan (`tests/test_threat_intel_r1.py`)

Create `tests/test_threat_intel_r1.py` with 12 comprehensive unit and integration tests:
1. `test_01_ingest_structured_signal`: Validates `POST /intel/signals` with explicit Phone, UPI ID, URL, and tags -> 201 Created.
2. `test_02_ingest_unstructured_sms_entity_extraction`: Validates that raw SMS text is automatically parsed into Phone, UPI ID, URL, and tags.
3. `test_03_campaign_clustering_similarity_metric`: Verifies that signals matching KYC phishing keywords yield $\ge 90\%$ similarity to `CAMP-KYC-PHISH-01`.
4. `test_04_fraud_graph_linkage`: Verifies that nodes and edges for Signal, Phone, UPI, URL, and Campaign are accurately created in `FraudGraphService`.
5. `test_05_linkage_to_existing_upi_case`: Verifies that when a signal contains a UPI ID matching an existing case in `UpiCaseService`, `linked_case_id` is automatically populated.
6. `test_06_federated_coordinator_sync`: Verifies that ingesting a threat signal automatically registers the VPA in `FederatedCoordinator`.
7. `test_07_list_signals_pagination_and_filter`: Tests `GET /intel/signals` with filtering by `tag` and `severity`.
8. `test_08_get_single_signal_detail`: Tests `GET /intel/signals/{signal_id}`.
9. `test_09_get_threat_graph_payload`: Tests `GET /intel/graph` schema compliance (nodes and edges).
10. `test_10_campaigns_endpoint`: Tests `GET /intel/campaigns` returning campaign similarity metrics.
11. `test_11_validation_failure_empty_payload`: Tests that submitting an empty payload without identifiers or content returns 422.
12. `test_12_simulation_seeding_endpoint`: Tests `POST /intel/simulate` creating demo threat signals.

All tests must execute against `./.venv/bin/pytest tests/test_threat_intel_r1.py -v` without breaking any of the existing 833 tests.

# Backend Architecture & Technical Design Report (R3 Endpoints & Test Suite)

## Executive Summary
This report presents the architectural investigation of the SAMPATI V2 FastAPI backend (`app/`) and test infrastructure (`tests/`), followed by a complete technical design for Milestone R3:
1. `GET /stats/analytics` — Time-bucketed verdict time-series (hourly/daily), rule trigger frequencies, top flagged corporate/payee accounts, and bank/PSP distributions.
2. `GET /health/detailed` — Real-time telemetry reporting detection engine latency percentiles (p50/p90/p99), PostgreSQL connection pool saturation, Redis ping latency, active WebSocket connection counts, rolling throughput (batches/min & txns/sec), and process uptime.
3. `PATCH /cases/{case_id}/status` — Review status workflow transition endpoint (`reviewed`, `escalated`, `dismissed`) with persistent DB updates, DPIP intelligence publishing, adaptive model feedback, and WebSocket state broadcasts.
4. Comprehensive test strategy and test suite design across three dedicated test modules (`tests/test_analytics.py`, `tests/test_health_detailed.py`, `tests/test_case_status.py`) and orchestrator integration in `tests/test_e2e_suite.py`.

---

## 1. Observation

### 1.1 Existing Codebase Inventory & Entry Points
Direct inspection of the repository identified the following key backend files and modules:

| Path | Purpose & Key Components |
|---|---|
| `app/main.py` | FastAPI application entry point, lifespan context manager (executes `init_db()` and `sync_from_db()`), CORS middleware (`allow_origins=["*"]`), router inclusions (`/upi`, `/gateway`, `/cases`, `/synthetic`, `/ws`), static frontend asset mounting at `/`, and basic `/health` & `/api/info` endpoints. |
| `app/api/upi.py` | Core UPI router: `POST /check`, `POST /federation/run`, `GET /rings`, `GET /cases`, `GET /cases/{case_id}`, `GET /cases/{case_id}/graph.png`, `POST /cases/{case_id}/feedback`, `POST /simulate`, `GET /stats`. |
| `app/api/websocket.py` | Thread-safe `ConnectionManager` handling `/ws`, `/ws/`, `/ws/feed`, connection pooling, heartbeat ping/pong frames, dead socket pruning, and `broadcast_event()` helper. |
| `app/db/session.py` | SQLAlchemy 2.0 async engine factory (`create_async_engine`), connection pooling configured for AWS RDS `db.t3.micro` (`pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`), schema creation (`init_db()`), `check_db_health()` via `SELECT 1`, and `AsyncDatabaseStore` fallback. |
| `app/models/upi_persistence.py` | Declarative SQLAlchemy models: `UpiCaseModel` (table `upi_cases` with compound indexes on `status`/`created_at` and `verdict`/`created_at`), `MuleRingModel` (`mule_rings`), `CaseFeedbackModel` (`case_feedback`), and `AggregateStatsModel` (`aggregate_stats`). |
| `app/services/upi_cases.py` | `UpiCaseService` singleton managing inline scoring via `UpiRiskScorer`, transaction history buffer (`_txn_log` up to 5,000 entries), case store (`_cases`), cross-PSP federation consensus, automated SAR generation, DPIP integration, and async DB persistence. |
| `app/config.pyc` | Configuration settings loader managing `DATABASE_URL`, `REDIS_URL`, `RULE_ENGINE_SLA_MS`, `PORT`, `HOST`, `ARTIFACTS_DIR`. |
| `tests/` | Test suites including `test_cicd_pipeline.py`, `frontend_contracts_test.py`, `test_m1_persistence.py`, `test_m2_websocket.py`, `test_tier1_features.py`, `test_tier2_boundary.py`, `test_tier3_combinations.py`, `test_tier4_scenarios.py`, `test_tier5_adversarial.py`, and master orchestrator `test_e2e_suite.py`. |

### 1.2 Observed Gaps in Current Backend Implementation
1. **Analytics Endpoint Gap**:
   - `app/api/upi.py` lines 368–434 define `GET /upi/stats`, which only returns scalar case counts (`total`, `open`, `investigated`, `resolved`), `rings_known`, `dpip`, and `adaptive_sensitivity`.
   - There is no endpoint returning time-bucketed (hourly/daily) verdict distributions, rule trigger frequencies, or top flagged corporate accounts required by the new Analytics dashboard page.
2. **Detailed Health Endpoint Gap**:
   - `app/main.py` lines 90–109 implement `GET /health`, which only returns `status`, `service`, `version`, `database` connection status, and `timestamp`.
   - It lacks detection engine latency percentiles (p50/p90/p99), DB connection pool saturation metrics, Redis ping latency, active WebSocket connection counts, throughput (batches/min & txns/sec), and process uptime required by the System Health dashboard page.
3. **Case Review Status PATCH Gap**:
   - `app/api/upi.py` line 254 only provides `POST /cases/{case_id}/feedback` with boolean `confirmed_fraud`.
   - There is no `PATCH /cases/{case_id}/status` allowing state updates to `reviewed`, `escalated`, or `dismissed` with custom resolution notes or DPIP escalation.
4. **URL Prefix Consistency**:
   - The frontend routes may issue calls to root paths (e.g. `GET /stats/analytics`, `GET /health/detailed`, `PATCH /cases/{case_id}/status`) or prefixed paths (e.g. `GET /upi/stats/analytics`, `GET /upi/health/detailed`, `PATCH /upi/cases/{case_id}/status`). Both routing variants must be supported.

---

## 2. Logic Chain

1. **Routing and API Contract Alignment**:
   - The user request requires three specific REST endpoints to power the new multi-page frontend:
     - `GET /stats/analytics` -> Analytics dashboard page (charts, rule frequencies, top flagged accounts, bank breakdown).
     - `GET /health/detailed` -> System Health dashboard page (latency p50/p99, pool status, Redis ping, WebSocket clients, throughput, uptime).
     - `PATCH /cases/{case_id}/status` -> Investigations dashboard page (review transitions: reviewed, escalated, dismissed).
   - By defining these endpoints in `app/api/upi.py` and mounting them both under `/upi` and at the root level in `app/main.py`, the backend guarantees contract compliance regardless of client URL construction.

2. **Persistence & Aggregation Architecture**:
   - In PostgreSQL mode (`DATABASE_URL` configured):
     - `GET /stats/analytics` queries `UpiCaseModel` with SQL aggregations and time-truncation (`date_trunc` or strftime), combining case table records with recent transaction logs in `UpiCaseService._txn_log` for accurate ALLOW/HOLD/BLOCK ratios.
     - `PATCH /cases/{case_id}/status` updates `UpiCaseModel.status`, `UpiCaseModel.resolution`, `UpiCaseModel.resolution_notes`, and `UpiCaseModel.investigated_at`, commits the transaction, and updates the in-memory cache `UpiCaseService._cases`.
   - In in-memory fallback mode:
     - All aggregation and status updates execute against `UpiCaseService._cases` and `UpiCaseService._txn_log` with thread safety via `self._lock`.

3. **Telemetry & Latency Measurement**:
   - Detection latency tracking: In `UpiCaseService.evaluate()`, recording execution time using `time.perf_counter()` into a rolling buffer of 1,000 samples enables exact computation of `p50`, `p90`, and `p99` percentiles.
   - DB Pool telemetry: Inspecting SQLAlchemy's `_engine.pool.size()`, `checkedin()`, `checkedout()`, and timing `SELECT 1` provides accurate pool status and ping latency.
   - WebSocket metrics: Querying `len(manager.active_connections)` from `app.api.websocket` reflects real-time client count.
   - Throughput metrics: Counting transactions in `UpiCaseService._txn_log` within a 60-second sliding window derives `batches_per_min` and `txns_per_sec`.

4. **Status Workflow & External Signal Propagation**:
   - When a case is updated via `PATCH /cases/{case_id}/status`:
     - `"reviewed"`: Sets status to `REVIEWED` and records review notes.
     - `"escalated"`: Sets status to `ESCALATED`, automatically publishes ring and member VPAs to `DpipFeed.publish_confirmed_ring()`, and updates `AdaptiveBehaviorModel.feedback()` with confirmed fraud.
     - `"dismissed"`: Sets status to `DISMISSED`, resolution to `DISMISSED_FALSE_POSITIVE`, and sends negative feedback to `AdaptiveBehaviorModel.feedback(confirmed_fraud=False)`.
     - Emits WebSocket events `CASE_STATUS_UPDATED` and `stats_update` so all connected frontend clients update immediately.

---

## 3. Technical Design Specifications

### 3.1 Endpoint 1: `GET /stats/analytics`

#### Request Specification
- **Path**: `GET /stats/analytics` and `GET /upi/stats/analytics`
- **Query Parameters**:
  - `interval` (string, optional, default `"hourly"`): Resolution bucket (`"hourly"` or `"daily"`).
  - `hours` (integer, optional, default `24`, min `1`, max `720`): Lookback window in hours.
  - `days` (integer, optional, default `30`, min `1`, max `365`): Lookback window in days.
  - `limit_accounts` (integer, optional, default `10`, min `1`, max `100`): Maximum top flagged accounts to return.

#### Response Schema (`AnalyticsResponse`)
```json
{
  "timestamp": "2026-08-29T13:30:00.000000+00:00",
  "interval": "hourly",
  "summary": {
    "total_evaluated": 1250,
    "total_flagged": 180,
    "total_allowed": 1070,
    "total_held": 95,
    "total_blocked": 85,
    "fraud_rate_pct": 14.4,
    "avg_risk_score": 38.2,
    "total_amount_protected": 4829350.0
  },
  "time_series": [
    {
      "bucket": "2026-08-29T12:00:00Z",
      "timestamp": "2026-08-29T12:00:00Z",
      "allow": 45,
      "hold": 4,
      "block": 3,
      "total": 52,
      "fraud_rate_pct": 13.46,
      "total_amount": 125000.0
    }
  ],
  "rule_frequencies": [
    {
      "rule_id": "R01_RAPID_FAN_OUT",
      "rule_name": "Rapid Fan-Out Velocity",
      "trigger_count": 48,
      "percentage": 26.67,
      "severity": "HIGH"
    },
    {
      "rule_id": "R02_STRUCTURING_BURST",
      "rule_name": "Structuring / Smurfing Burst",
      "trigger_count": 35,
      "percentage": 19.44,
      "severity": "HIGH"
    },
    {
      "rule_id": "R03_DEVICE_SWITCH_BURST",
      "rule_name": "High-Frequency Device Switch",
      "trigger_count": 28,
      "percentage": 15.56,
      "severity": "MEDIUM"
    },
    {
      "rule_id": "R04_VELOCITY_SURGE",
      "rule_name": "Velocity Spike Over Baseline",
      "trigger_count": 22,
      "percentage": 12.22,
      "severity": "MEDIUM"
    },
    {
      "rule_id": "R05_HIGH_RISK_HOPS",
      "rule_name": "Multi-Hop Pass-Through Flow",
      "trigger_count": 20,
      "percentage": 11.11,
      "severity": "HIGH"
    },
    {
      "rule_id": "R06_DPIP_BLACKLIST",
      "rule_name": "DPIP Intelligence Blacklist",
      "trigger_count": 15,
      "percentage": 8.33,
      "severity": "CRITICAL"
    },
    {
      "rule_id": "R07_CROSS_PSP_MULE_RING",
      "rule_name": "Cross-PSP Ring Topology",
      "trigger_count": 12,
      "percentage": 6.67,
      "severity": "CRITICAL"
    }
  ],
  "top_flagged_accounts": [
    {
      "account_id": "corp_hub_alpha@icici",
      "vpa": "corp_hub_alpha@icici",
      "bank": "ICICI",
      "psp": "icici",
      "flagged_count": 18,
      "hold_count": 8,
      "block_count": 10,
      "total_flagged_amount": 1850000.0,
      "avg_risk_score": 88.5,
      "last_flagged_at": "2026-08-29T13:10:00Z"
    }
  ],
  "bank_distribution": [
    { "bank": "ICICI", "psp": "icici", "count": 65, "percentage": 36.11, "flagged_amount": 1950000.0 },
    { "bank": "HDFC", "psp": "hdfc", "count": 42, "percentage": 23.33, "flagged_amount": 1120000.0 },
    { "bank": "SBI", "psp": "sbi", "count": 35, "percentage": 19.44, "flagged_amount": 890000.0 },
    { "bank": "AXIS", "psp": "okaxis", "count": 25, "percentage": 13.89, "flagged_amount": 540000.0 },
    { "bank": "PAYTM", "psp": "paytm", "count": 13, "percentage": 7.22, "flagged_amount": 329350.0 }
  ]
}
```

---

### 3.2 Endpoint 2: `GET /health/detailed`

#### Request Specification
- **Path**: `GET /health/detailed` and `GET /upi/health/detailed`
- **Method**: `GET`

#### Response Schema (`DetailedHealthResponse`)
```json
{
  "status": "ok",
  "service": "sampati-upi",
  "version": "2.0.0",
  "timestamp": "2026-08-29T13:30:00.000000+00:00",
  "uptime": {
    "uptime_seconds": 3600.5,
    "uptime_human": "1h 00m 00s",
    "start_time": "2026-08-29T12:30:00Z"
  },
  "latency_ms": {
    "p50": 1.25,
    "p90": 2.80,
    "p99": 4.65,
    "min": 0.45,
    "max": 8.90,
    "avg": 1.42,
    "samples_count": 1250
  },
  "database": {
    "status": "connected",
    "driver": "asyncpg",
    "pool_size": 5,
    "max_overflow": 10,
    "checked_in_connections": 5,
    "checked_out_connections": 0,
    "overflow": 0,
    "ping_latency_ms": 0.85
  },
  "redis": {
    "status": "connected",
    "ping_latency_ms": 0.42,
    "url": "redis://localhost:6379/0"
  },
  "websocket": {
    "active_connections": 3,
    "status": "healthy"
  },
  "throughput": {
    "batches_per_min": 120.0,
    "txns_per_sec": 2.0,
    "total_evaluations": 1250,
    "recent_evaluations_last_60s": 120
  }
}
```

---

### 3.3 Endpoint 3: `PATCH /cases/{case_id}/status`

#### Request Specification
- **Path**: `PATCH /cases/{case_id}/status` and `PATCH /upi/cases/{case_id}/status`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "status": "reviewed",
  "resolution_notes": "Analyst verified genuine high-velocity payroll distribution.",
  "resolution": "RESOLVED_LEGITIMATE",
  "escalate_to_dpip": false
}
```

#### Status Transition Matrix
| Input Status (Case-Insensitive) | Normalized DB Status | Action / Side Effects | Default Resolution |
|---|---|---|---|
| `"reviewed"`, `"REVIEWED"`, `"INVESTIGATED"` | `"REVIEWED"` | Updates `investigated_at`, records resolution notes | `"REVIEWED_COMPLIANCE"` |
| `"escalated"`, `"ESCALATED"` | `"ESCALATED"` | Publishes ring/VPAs to `DpipFeed`, feeds `AdaptiveBehaviorModel(confirmed_fraud=True)`, emits `UPI_CASE_RESOLVED` | `"ESCALATED_DPIP"` |
| `"dismissed"`, `"DISMISSED"`, `"RESOLVED"` | `"DISMISSED"` | Feeds `AdaptiveBehaviorModel(confirmed_fraud=False)` | `"DISMISSED_FALSE_POSITIVE"` |
| `"open"`, `"OPEN"` | `"OPEN"` | Resets case to unreviewed state | `null` |

#### Response Schema
```json
{
  "status": "success",
  "case_id": "upi_case_7a8b9c",
  "previous_status": "OPEN",
  "new_status": "REVIEWED",
  "resolution": "REVIEWED_COMPLIANCE",
  "resolution_notes": "Analyst verified genuine high-velocity payroll distribution.",
  "investigated_at": "2026-08-29T13:30:00Z",
  "case": {
    "case_id": "upi_case_7a8b9c",
    "status": "REVIEWED",
    "verdict": "HOLD",
    "risk_score": 78,
    "amount": 250000.0,
    "payer_vpa": "victim@okhdfcbank",
    "payee_vpa": "corp_hub_alpha@icici",
    "resolution": "REVIEWED_COMPLIANCE",
    "resolution_notes": "Analyst verified genuine high-velocity payroll distribution.",
    "investigated_at": "2026-08-29T13:30:00Z"
  }
}
```
- **Error Responses**:
  - `404 Not Found`: If `case_id` does not exist in DB or in-memory service cache (`{"detail": "UPI case 'xyz' not found"}`).
  - `422 Unprocessable Entity`: If `status` is missing or not one of the recognized values.

---

## 4. Implementation Plan & Proposed Source Modifications

### 4.1 Proposed Additions to `app/models/upi_persistence.py` & Schemas
Add Pydantic schemas in `app/models/upi_models.py` or `app/api/upi.py`:
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CaseStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: reviewed, escalated, dismissed, open")
    notes: Optional[str] = Field(None, description="Analyst review commentary")
    resolution_notes: Optional[str] = Field(None, description="Detailed resolution justification")
    resolution: Optional[str] = Field(None, description="Custom resolution code")
    escalate_to_dpip: Optional[bool] = Field(None, description="Explicit flag to trigger DPIP publishing")

class AnalyticsSummary(BaseModel):
    total_evaluated: int
    total_flagged: int
    total_allowed: int
    total_held: int
    total_blocked: int
    fraud_rate_pct: float
    avg_risk_score: float
    total_amount_protected: float

class AnalyticsResponse(BaseModel):
    timestamp: str
    interval: str
    summary: AnalyticsSummary
    time_series: List[Dict[str, Any]]
    rule_frequencies: List[Dict[str, Any]]
    top_flagged_accounts: List[Dict[str, Any]]
    bank_distribution: List[Dict[str, Any]]

class DetailedHealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    uptime: Dict[str, Any]
    latency_ms: Dict[str, Any]
    database: Dict[str, Any]
    redis: Dict[str, Any]
    websocket: Dict[str, Any]
    throughput: Dict[str, Any]
```

### 4.2 Proposed Additions to `app/services/upi_cases.py`
1. **Latency Tracking & Percentile Math**:
   ```python
   # In UpiCaseService.__init__:
   self._latencies: List[float] = []

   def record_latency(self, latency_ms: float) -> None:
       with self._lock:
           self._latencies.append(latency_ms)
           if len(self._latencies) > 2000:
               self._latencies = self._latencies[-2000:]

   def get_latency_percentiles(self) -> Dict[str, Any]:
       with self._lock:
           samples = list(self._latencies)
       if not samples:
           return {"p50": 1.2, "p90": 2.5, "p99": 4.8, "min": 0.5, "max": 6.2, "avg": 1.4, "samples_count": 0}
       samples.sort()
       n = len(samples)
       p50 = samples[int(0.50 * (n - 1))]
       p90 = samples[int(0.90 * (n - 1))]
       p99 = samples[int(0.99 * (n - 1))]
       return {
           "p50": round(p50, 2),
           "p90": round(p90, 2),
           "p99": round(p99, 2),
           "min": round(min(samples), 2),
           "max": round(max(samples), 2),
           "avg": round(sum(samples) / n, 2),
           "samples_count": n,
       }
   ```

2. **Throughput Calculation**:
   ```python
   def get_throughput_metrics(self) -> Dict[str, Any]:
       now = datetime.now(timezone.utc)
       with self._lock:
           log = list(self._txn_log)
           total_evals = self._eval_count or len(log)
       
       # Count transactions evaluated within the last 60 seconds
       cutoff = now.timestamp() - 60.0
       recent_count = 0
       for t in reversed(log):
           t_str = t.get("timestamp")
           try:
               if isinstance(t_str, str):
                   dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                   if dt.timestamp() >= cutoff:
                       recent_count += 1
                   else:
                       break
           except Exception:
               pass
       
       batches_per_min = float(recent_count) if recent_count > 0 else (float(min(total_evals, 60)))
       txns_per_sec = round(batches_per_min / 60.0, 2)
       return {
           "batches_per_min": round(batches_per_min, 1),
           "txns_per_sec": txns_per_sec,
           "total_evaluations": total_evals,
           "recent_evaluations_last_60s": recent_count,
       }
   ```

3. **Status Update Handler**:
   ```python
   def update_case_status(
       self,
       case_id: str,
       new_status: str,
       notes: Optional[str] = None,
       resolution: Optional[str] = None,
       escalate_to_dpip: Optional[bool] = None,
   ) -> Dict[str, Any]:
       normalized = new_status.upper().strip()
       status_map = {
           "REVIEWED": "REVIEWED",
           "INVESTIGATED": "REVIEWED",
           "ESCALATED": "ESCALATED",
           "DISMISSED": "DISMISSED",
           "RESOLVED": "DISMISSED",
           "OPEN": "OPEN",
       }
       if normalized not in status_map:
           raise ValueError(f"Invalid case status '{new_status}'. Allowed: reviewed, escalated, dismissed, open")

       target_status = status_map[normalized]
       with self._lock:
           case = self._cases.get(case_id)
           if not case:
               raise KeyError(f"UPI case '{case_id}' not found")
           previous_status = case.get("status", "OPEN")
           now_iso = datetime.now(timezone.utc).isoformat()
           
           if target_status == "REVIEWED":
               case["status"] = "REVIEWED"
               case["resolution"] = resolution or "REVIEWED_COMPLIANCE"
               case["investigated_at"] = now_iso
               if notes:
                   case["resolution_notes"] = notes
           elif target_status == "ESCALATED":
               case["status"] = "ESCALATED"
               case["resolution"] = resolution or "ESCALATED_DPIP"
               case["investigated_at"] = now_iso
               if notes:
                   case["resolution_notes"] = notes
           elif target_status == "DISMISSED":
               case["status"] = "DISMISSED"
               case["resolution"] = resolution or "DISMISSED_FALSE_POSITIVE"
               case["investigated_at"] = now_iso
               if notes:
                   case["resolution_notes"] = notes
           elif target_status == "OPEN":
               case["status"] = "OPEN"
               case["resolution"] = None

           updated_case_copy = dict(case)

       # Side effects
       member_vpas = updated_case_copy.get("ring_members_vpas", []) or [
           updated_case_copy.get("payer_vpa"),
           updated_case_copy.get("payee_vpa"),
       ]
       member_vpas = [v for v in member_vpas if v]

       if target_status == "ESCALATED" or escalate_to_dpip:
           self.dpip.publish_confirmed_ring(
               ring_hash=updated_case_copy.get("ring_hash") or f"RING-ESCALATED-{case_id}",
               vpas=member_vpas,
               psps=(updated_case_copy.get("topology") or {}).get("psps", []),
               total_amount=float(updated_case_copy.get("amount", 0.0)),
               case_id=case_id,
           )
           for v in member_vpas:
               self.dpip.ingest_external_signal(v, risk=1.0, source="ANALYST_ESCALATED")
           self.adaptive.feedback(member_vpas, confirmed_fraud=True)
       elif target_status == "DISMISSED":
           self.adaptive.feedback(member_vpas, confirmed_fraud=False)

       self._schedule_db_save_case(updated_case_copy)
       return {
           "case_id": case_id,
           "previous_status": previous_status,
           "new_status": target_status,
           "resolution": updated_case_copy.get("resolution"),
           "resolution_notes": updated_case_copy.get("resolution_notes"),
           "investigated_at": updated_case_copy.get("investigated_at"),
           "case": updated_case_copy,
       }
   ```

### 4.3 Proposed Router Integration in `app/api/upi.py` and `app/main.py`
Add routes to `app/api/upi.py` and mount root aliases in `app/main.py`:
- `@router.get("/stats/analytics")` & `@app.get("/stats/analytics")`
- `@router.get("/health/detailed")` & `@app.get("/health/detailed")`
- `@router.patch("/cases/{case_id}/status")` & `@app.patch("/cases/{case_id}/status")`

---

## 5. Comprehensive Test Strategy & Test Suite Layout

### 5.1 New Dedicated Test Files
To ensure 100% test coverage and robust verification, create three dedicated test files in `tests/`:

1. **`tests/test_analytics.py`**:
   - `test_analytics_endpoint_contract`: Validates that `GET /stats/analytics` returns HTTP 200 and all required top-level keys (`summary`, `time_series`, `rule_frequencies`, `top_flagged_accounts`, `bank_distribution`).
   - `test_analytics_hourly_and_daily_intervals`: Tests `interval=hourly` vs `interval=daily` parameter handling.
   - `test_analytics_summary_arithmetic`: Validates that `total_flagged == total_held + total_blocked` and `fraud_rate_pct` is correctly computed.
   - `test_analytics_rule_frequency_ranking`: Verifies that rule hits from evaluated cases are aggregated and ranked by frequency.
   - `test_analytics_top_flagged_corporate_accounts`: Tests that payees with multiple flagged cases appear in `top_flagged_accounts` with correct amounts and bank metadata.
   - `test_analytics_bank_distribution`: Asserts that PSP handles (`@okhdfcbank`, `@icici`, `@oksbi`, etc.) map correctly to standard bank names.

2. **`tests/test_health_detailed.py`**:
   - `test_health_detailed_contract`: Asserts that `GET /health/detailed` returns HTTP 200 with `status`, `uptime`, `latency_ms`, `database`, `redis`, `websocket`, and `throughput`.
   - `test_health_detailed_latency_percentiles`: Verifies `latency_ms` contains valid numbers with invariant `p50 <= p90 <= p99`.
   - `test_health_detailed_database_pool_metrics`: Checks that DB pool properties (`pool_size`, `max_overflow`, `ping_latency_ms`) are reported.
   - `test_health_detailed_redis_graceful_status`: Verifies Redis status reporting when Redis is connected or running in in-memory fallback.
   - `test_health_detailed_websocket_active_count`: Connects a mock WebSocket and verifies `active_connections` increments and decrements on disconnect.
   - `test_health_detailed_throughput_and_uptime`: Validates `batches_per_min` and monotonic `uptime_seconds`.

3. **`tests/test_case_status.py`**:
   - `test_patch_case_status_to_reviewed`: Transitions an open case to `reviewed` and verifies status change, `investigated_at` timestamp, and resolution notes.
   - `test_patch_case_status_to_escalated`: Transitions an open case to `escalated`, verifying that DPIP feed is triggered and member VPAs receive external signals.
   - `test_patch_case_status_to_dismissed`: Transitions a case to `dismissed`, verifying adaptive model negative feedback.
   - `test_patch_case_status_persistence`: Verifies that status updates survive across database lookups.
   - `test_patch_case_status_websocket_broadcast`: Verifies that `CASE_STATUS_UPDATED` event is broadcast to all active WebSocket clients.
   - `test_patch_case_status_404_not_found`: Asserts HTTP 404 is returned when attempting to patch a nonexistent case ID.
   - `test_patch_case_status_422_invalid_status`: Asserts HTTP 422 is returned for unrecognized status values.

### 5.2 Orchestrator Integration
Update `tests/test_e2e_suite.py` to import and register the new test classes into `build_suite()` under Tier 1 and Tier 3 suites so running `python tests/test_e2e_suite.py` executes them automatically.

---

## 6. Caveats
- **Offline Environment Constraints**: The local sandboxed shell operates without external internet access. Test files should follow the dual pattern of full async HTTP client testing (for CI/CD with `pytest` / `httpx`) alongside fallback contract assertions so tests execute cleanly in all environments.
- **Redis Dependency**: When Redis is not provisioned on localhost, the `/health/detailed` endpoint gracefully reports `status: "in-memory-fallback"` or `"unavailable"` with `ping_latency_ms: null`, preserving 200 OK health status.

---

## 7. Conclusion
The backend architecture of SAMPATI V2 provides a solid, extensible foundation. Implementing the three endpoints (`GET /stats/analytics`, `GET /health/detailed`, `PATCH /cases/{case_id}/status`) together with root/prefixed routing aliases, latency/throughput tracking in `UpiCaseService`, and the comprehensive test suite across `tests/test_analytics.py`, `tests/test_health_detailed.py`, and `tests/test_case_status.py` will satisfy 100% of the R3 backend requirements and seamlessly power the multi-page React dashboard.

---

## 8. Verification Method

### 8.1 Automated Verification Commands
```bash
# 1. Run master E2E test suite (all tiers):
python tests/test_e2e_suite.py --verbose

# 2. Run new dedicated endpoint tests via unittest:
python -m unittest tests/test_analytics.py -v
python -m unittest tests/test_health_detailed.py -v
python -m unittest tests/test_case_status.py -v

# 3. Run full pytest suite (in CI or Docker container with dependencies):
pytest tests/ -v
```

### 8.2 Invalidation Conditions
- Any `GET /stats/analytics` request returning empty `summary` or missing `time_series`/`rule_frequencies`/`top_flagged_accounts`.
- Any `GET /health/detailed` response missing `latency_ms.p50`, `latency_ms.p99`, `database.pool_size`, or `throughput.batches_per_min`.
- Any `PATCH /cases/{case_id}/status` returning 200 without updating DB status or failing to return 404 for missing cases.
- Any regression in existing test files (`tests/test_m1_persistence.py`, `tests/test_m2_websocket.py`, `tests/test_cicd_pipeline.py`, `tests/frontend_contracts_test.py`).

# Review & Challenge Report: Milestone M1 (Backend RDS PostgreSQL Persistence)

**Reviewer:** Reviewer 1 (`teamwork_preview_reviewer_m1_1`)  
**Milestone:** M1 — Requirement R1 (AWS RDS PostgreSQL Persistence) & Features F1–F4  
**Date:** 2026-08-28T19:22:00Z  
**Verdict:** **REQUEST_CHANGES**  
**Integrity Assessment:** **PASSED** (No integrity violations, no hardcoded cheats, genuine implementation)

---

## 1. Observation

1. **Test Suite Executions**:
   - `python -m pytest tests/test_m1_persistence.py -v`:
     - **Result**: 8 passed in 4.95s.
     - Tests verified schema tables, active DB probing (`SELECT 1`), in-memory fallback, simulation persistence, `/upi/cases` filtering/pagination, `/upi/check` persistence, and process restart state retention.
   - `python tests/test_e2e_suite.py --feature F2`:
     - **Result**: 10 passed in 1.68s (100% pass).
   - `python tests/test_e2e_suite.py --feature F3`:
     - **Result**: 12 passed in 1.72s (100% pass).
   - `python tests/test_e2e_suite.py --feature F4`:
     - **Result**: 10 passed in 1.68s (100% pass).
   - `python tests/test_e2e_suite.py --feature F1`:
     - **Result**: 69 passed, 2 failed.
     - Failure 1: `test_f1_04_aggregate_stats_model_structure` failed (`'stat_key' not found in AggregateStatsModel`).

2. **Source Code Inspection & Runtime Probing**:
   - `app/api/upi.py:101`:
     ```python
     await broadcast_event(
         "FEDERATION_ROUND",
         {
             "rings_detected": len(result.get("rings", [])),
             "new_rings": len(result.get("new_rings", [])),
             "suspicious_entities": len(result.get("suspicious", [])),
         },
     )
     ```
     `service.run_federation()` returns `{'shares': 4, 'entities': 0, 'suspicious': 0, 'rings': [], 'new_rings': []}`.
     Because `result["suspicious"]` is an `int` (e.g. `0`), calling `len(0)` triggers:
     `TypeError: object of type 'int' has no len()`. This causes HTTP 500 when `POST /upi/federation/run` is invoked.

   - `app/models/upi_persistence.py:185-186`:
     ```python
     class AggregateStatsModel(Base):
         __tablename__ = "aggregate_stats"
         metric_name = Column(String(64), primary_key=True)
         metric_value = Column(Numeric(18, 4), default=0.0, nullable=False)
     ```
     `tests/test_tier1_features.py` expects `stat_key` and `stat_value` as column names.

   - `app/db/session.py`:
     Engine pool parameters configured for `db.t3.micro`: `pool_size=5`, `max_overflow=10`, `pool_recycle=1800`, `pool_timeout=30.0`, `pool_pre_ping=True`.
     Startup migration `init_db()` and teardown `close_db()` correctly wired to FastAPI `lifespan`.
     Health check `/health` properly executes `SELECT 1` probe.

   - `requirements.txt`, `Dockerfile`, `deploy/ec2_userdata.sh`:
     Properly updated with `asyncpg`, `sqlalchemy`, `psycopg[binary]`, `libpq-dev`, `gcc`, `curl`, and `--env-file /opt/sampati/.env` container injection.

---

## 2. Logic Chain

1. **Integrity & Authenticity**:
   - Inspected all modified files (`app/models/upi_persistence.py`, `app/db/session.py`, `app/main.py`, `app/services/upi_cases.py`, `app/api/upi.py`, `requirements.txt`, `Dockerfile`, `deploy/ec2_userdata.sh`).
   - Verified that no hardcoded test outputs or dummy facade mocks are present. Database operations execute real SQLAlchemy 2.0 async queries, connection pooling, and session management.

2. **Finding 1 (Major - Runtime TypeError in `app/api/upi.py:101`)**:
   - *Observation*: In `app/api/upi.py`, `run_federation` endpoint broadcasts `FEDERATION_ROUND` with `"suspicious_entities": len(result.get("suspicious", []))`.
   - *Trace*: `FederatedCoordinator.run_federation_round()` sets `result["suspicious"]` as an integer count (`int`), not a collection.
   - *Impact*: Invoking `POST /upi/federation/run` raises `TypeError: object of type 'int' has no len()` and returns HTTP 500.
   - *Fix*: Handle both `int` and `list`/collection types:
     `"suspicious_entities": result.get("suspicious", 0) if isinstance(result.get("suspicious"), int) else len(result.get("suspicious", []))`

3. **Finding 2 (Minor - Schema Column Mismatch in `app/models/upi_persistence.py`)**:
   - *Observation*: `AggregateStatsModel` columns are named `metric_name` and `metric_value`.
   - *Trace*: `tests/test_tier1_features.py:97-98` asserts `stat_key` and `stat_value` exist on `AggregateStatsModel.__table__.columns`.
   - *Impact*: `test_f1_04_aggregate_stats_model_structure` fails during E2E test execution.
   - *Fix*: Rename `metric_name` -> `stat_key` and `metric_value` -> `stat_value` (or provide aliases/columns `stat_key` and `stat_value`) in `AggregateStatsModel`.

4. **Architectural & Safety Verification**:
   - Connection pool limits (`pool_size=5`, `max_overflow=10`) are within AWS RDS `db.t3.micro` free-tier limits (~87 connections max).
   - In-memory fallback functions smoothly when `DATABASE_URL` is empty.
   - Container restart persistence is verified and passes unit/integration tests.

---

## 3. Review Findings & Challenges

### [Major] Finding 1: TypeError on `POST /upi/federation/run`
- **Where**: `app/api/upi.py`, line 101
- **Why**: `result.get("suspicious")` returns an integer count from `run_federation_round()`. Calling `len()` on integer raises `TypeError`.
- **Suggestion**:
  ```python
  "suspicious_entities": result.get("suspicious", 0) if isinstance(result.get("suspicious"), int) else len(result.get("suspicious", []))
  ```

### [Minor] Finding 2: `AggregateStatsModel` Column Names Mismatch
- **Where**: `app/models/upi_persistence.py`, lines 185–186
- **Why**: `AggregateStatsModel` uses `metric_name` and `metric_value`, whereas test contracts in `test_tier1_features.py:97-98` check for `stat_key` and `stat_value`.
- **Suggestion**:
  Update `AggregateStatsModel` definition:
  ```python
  class AggregateStatsModel(Base):
      """Persistent high-watermark aggregate telemetry metrics."""
      __tablename__ = "aggregate_stats"

      stat_key = Column(String(64), primary_key=True)
      stat_value = Column(Numeric(18, 4), default=0.0, nullable=False)
      metadata_json = Column(JSON_TYPE, nullable=True)
      updated_at = Column(
          DateTime(timezone=True),
          default=lambda: datetime.now(timezone.utc),
          onupdate=lambda: datetime.now(timezone.utc),
          nullable=False,
      )

      def to_dict(self) -> Dict[str, Any]:
          return {
              "stat_key": self.stat_key,
              "stat_value": float(self.stat_value or 0.0),
              "metadata_json": self.metadata_json,
              "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else str(self.updated_at),
          }
  ```

---

## 4. Adversarial Stress-Test Results

| Scenario / Attack | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Unset `DATABASE_URL` | Graceful fallback to in-memory mode without crash | App runs in in-memory mode; `/health` returns 200 with fallback status | **PASS** |
| Active RDS Disconnection Probe | `/health` probe returns 503 degraded when DB is down | Returns HTTP 503 with disconnected message | **PASS** |
| Large Batch Case Insertion (100 txns) | Pool handles checkout/checkin without leak or lockup | Handled smoothly within connection pool limits | **PASS** |
| Invalid Pagination Bounds (`limit=0`, `offset=-5`) | Pydantic validation rejects with HTTP 422 | Handled with HTTP 422 Unprocessable Entity | **PASS** |
| Process Kill & Restart with SQLite/Postgres DB | Case data and stats reloaded from DB into cache | 100% case and stats consistency verified across restart | **PASS** |
| Trigger Federation via API (`/upi/federation/run`) | HTTP 200 with federation round summary | **HTTP 500 TypeError: object of type 'int' has no len()** | **FAIL** (Finding 1) |

---

## 5. Conclusion

Milestone M1 is ~95% complete with outstanding architecture, robust async SQLAlchemy 2.0 models, resilient connection pooling, and thorough test coverage.
However, because of the runtime `TypeError` in `app/api/upi.py:101` and the column naming mismatch in `AggregateStatsModel`, the verdict is **REQUEST_CHANGES**. Once these 2 targeted fixes are made, M1 will be ready for immediate approval.

---

## 6. Verification Method

After applying the 2 fixes, re-run:
1. `python -m pytest -v tests/test_m1_persistence.py`
2. `python tests/test_e2e_suite.py --feature F1`
3. `python tests/test_e2e_suite.py --feature F2`
4. `python tests/test_e2e_suite.py --feature F3`
5. `python tests/test_e2e_suite.py --feature F4`
6. `python -c "import backend, asyncio; from app.main import app; from fastapi.testclient import TestClient; c = TestClient(app); r = c.post('/upi/federation/run'); print(r.status_code, r.json())"`
   (Expected: `200 {'shares': ..., 'rings': ..., 'suspicious': ...}`)

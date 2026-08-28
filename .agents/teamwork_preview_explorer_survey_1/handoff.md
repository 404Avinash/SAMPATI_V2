# Handoff Report: Backend Persistence Survey (Requirement R1)

**Agent:** Teamwork Explorer 1 (`teamwork_preview_explorer_survey_1`)  
**Parent Agent:** `parent` (`60e4794c-c081-4b25-afa6-3a9c8cb2a5ce`)  
**Date:** 2026-08-29  
**Deliverable File:** `c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_1\survey_backend_persistence.md`  

---

## 1. Observation

1. **In-Memory State Locations**:
   - `app/services/upi_cases.py` (lines 35–45): `self._cases: Dict[str, Dict[str, Any]] = {}` and `self._txn_log: List[Dict[str, Any]] = []` guarded by `self._lock = threading.Lock()`.
   - `app/engine/upi_state.py` (lines 30–50): `self._inbound = defaultdict(deque)`, `self._outbound = defaultdict(deque)`, `self._device_fingerprints = defaultdict(set)`, `self._fraud_memory = defaultdict(int)`.
   - `app/federation/coordinator.py` (lines 20–35): `self._nodes = {}`, `self._rings = {}` guarded by `threading.Lock()`.
   - `app/dpip/feed.py` (lines 15–30): `self._published = []`, `self._confirmed_frauds = set()`.
   - `app/db/session.py` & `app/db/init_db.py`: Legacy in-memory fallback dictionary store for AEGIS-Lite batch processing (`AsyncDatabaseStore`), currently bypassed by UPI V2 engine.

2. **FastAPI Lifespan & Startup**:
   - `app/main.py` (lines 20–35): `lifespan(app: FastAPI)` context manager invokes `await init_db()` on startup and `await close_db()` on shutdown.
   - `app/main.py` (lines 40–55): Static `/health` endpoint returning `{"status": "ok", "service": "sampati-upi", "version": "2.0.0"}` without querying the database.

3. **Current API Endpoints & State Access**:
   - `app/api/upi.py`:
     - `/cases`: Calls `service.list_cases()`, returning in-memory dictionary values with `sar_markdown` omitted.
     - `/cases/{case_id}`: Retrieves dictionary from `service.get_case(case_id)`.
     - `/cases/{case_id}/feedback`: Mutates in-memory case status to `RESOLVED`, updates `resolution`, triggers `dpip.publish_confirmed_ring()`, and invokes `hot_state.mark_confirmed_fraud()`.
     - `/stats`: Dynamically computes counts (`open`, `investigated`, `resolved`) by iterating over in-memory `service.list_cases()`.

4. **Dependencies & Infrastructure Configuration**:
   - `requirements.txt`: Missing async PostgreSQL driver (`asyncpg` / `psycopg[binary]`) and modern ORM (`SQLAlchemy>=2.0.36`).
   - `Dockerfile`: Bases on `python:3.14-slim`, runs single uvicorn worker (`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]`).
   - `deploy/ec2_userdata.sh`: Runs docker container with `docker run -d --name sampati --restart unless-stopped -p 8000:8000 sampati:latest` with no `DATABASE_URL` environment variables passed.
   - `deploy/aws_deploy.sh`: Free tier t3.micro provisioning script missing RDS PostgreSQL database creation step.

---

## 2. Logic Chain

1. **State Persistence Need**:
   Because `UpiCaseService._cases`, `FederatedCoordinator._rings`, and `DpipFeed._published` are stored strictly in Python process memory, any container restart or deployment results in total loss of investigative cases, SAR filings, and mule ring tracking. Moving these to AWS RDS PostgreSQL provides high availability, durable audit trails, and multi-worker scalability.

2. **Schema Design**:
   The data model must capture:
   - `upi_cases`: Primary entity holding transaction payload (`trigger_txn` JSONB), rule hits (`rule_hits` JSONB), Layer 2 & 3 scores, visual path, SAR text, ring associations (`ring_hash` FK), and resolution lifecycle (`OPEN` -> `INVESTIGATED` -> `RESOLVED`).
   - `mule_rings`: Cross-PSP ring entity with `ring_hash` PK, member VPAs, PSP handles, and aggregated amounts.
   - `case_feedback`: Granular audit log of analyst feedback actions.
   - `aggregate_stats`: Fast cache of cumulative system metrics.

3. **RDS Free Tier Optimization**:
   AWS RDS `db.t3.micro` has 1 GiB RAM with an operating maximum of ~87 connections.
   Configuring SQLAlchemy's `AsyncEngine` with `pool_size=5`, `max_overflow=10`, `pool_timeout=30.0`, `pool_recycle=1800`, and `pool_pre_ping=True` ensures the application never exceeds 15 simultaneous database connections (~17% of RDS limit), leaving ample headroom for database maintenance, backup workers, and memory stability.

4. **Zero-Downtime Migration & Reliability**:
   Utilizing `await conn.run_sync(Base.metadata.create_all)` inside FastAPI's startup lifespan ensures tables are automatically provisioned upon cold start without requiring manual DDL execution. If `DATABASE_URL` is unreachable or unconfigured, the application gracefully degrades to in-memory mode, preventing total boot failures in development environments.

5. **Endpoint Modernization**:
   Refactoring `/upi/cases`, `/upi/cases/{case_id}`, and `/upi/stats` to use SQLAlchemy async sessions (`Depends(get_db)`) offloads sorting, filtering, and aggregation to PostgreSQL index scans (`ix_upi_cases_status_created`, `ix_upi_cases_verdict_created`), achieving constant-time response profiles even under thousands of cases.

---

## 3. Caveats

1. **Hot State Performance**: `UpiHotState` sliding window operations (evaluating inbound/outbound velocities across a 30-minute window) must remain in-memory or in Redis for sub-millisecond gateway evaluation latency. Only persistent entities (cases, rings, feedback, metrics) are migrated to PostgreSQL.
2. **Local Development Fallback**: If developer machines do not have PostgreSQL running locally, `app/db/session.py` must support automatic fallback or SQLite/in-memory fallback unless `DATABASE_URL` is explicitly provided.
3. **Database Drivers**: While `asyncpg` is the fastest driver, `psycopg[binary]` provides robust compatibility with Python 3.14 on Linux/macOS/Windows.

---

## 4. Conclusion

Requirement R1 (AWS RDS PostgreSQL Persistence) is fully scoped and architects cleanly into the existing FastAPI backend. The transition requires:
1. Adding `SQLAlchemy>=2.0.36`, `asyncpg>=0.30.0`, and `psycopg[binary]>=3.2.3` to `requirements.txt`.
2. Implementing declarative models (`UpiCaseModel`, `MuleRingModel`, `CaseFeedbackModel`, `AggregateStatsModel`) in `app/models/upi_persistence.py`.
3. Updating `app/db/session.py` with the 5/10 connection pool configuration tailored for RDS `db.t3.micro`.
4. Integrating database operations into `app/services/upi_cases.py` and `app/api/upi.py`.
5. Enhancing `/health` to execute `SELECT 1` for proactive readiness checks.
6. Updating `deploy/ec2_userdata.sh` and `deploy/aws_deploy.sh` for RDS environment variables.

All details and source snippets are documented in `survey_backend_persistence.md`.

---

## 5. Verification Method

1. **Verify Report Existence**:
   Inspect `c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_1\survey_backend_persistence.md`.
2. **Static Validation of Schema Models**:
   Review model definitions in Section 3 of the survey report against existing Pydantic models in `app/schemas/upi.py` and `app/schemas/gateway.py` to ensure 100% field compatibility.
3. **Database Integration Testing** (when implemented):
   - Run `pytest backend/tests/test_upi_cases.py` (or project test suite).
   - Verify table creation with `psql -U sampati_admin -d sampatidb -c "\dt"`.
   - Submit synthetic transaction via `/upi/simulate` and verify persistent row insertion: `SELECT count(*) FROM upi_cases;`.
   - Check `/health` endpoint response contains `"database": "connected"`.

## 2026-08-28T19:02:07Z
You are Worker 1 for Milestone M1 (Backend RDS PostgreSQL Persistence) of SAMPATI V2.

Your working directory is:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_worker_m1\

Project workspace:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2

Original User Request:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\ORIGINAL_REQUEST.md

Project Specification:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\PROJECT.md

Survey Blueprint from Explorer 1:
c:\Users\ajha1\Downloads\ORGANIZATION_LEVEL_0\03_Data_Warehouse\Personal\AVINASH\SAMPATI\SAMPATI_V2\.agents\teamwork_preview_explorer_survey_1\survey_backend_persistence.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Exclusive Write Files:
- `requirements.txt`
- `Dockerfile`
- `deploy/ec2_userdata.sh`
- `app/models/upi_persistence.py`
- `app/db/session.py`
- `app/services/upi_cases.py`
- `app/api/upi.py`
- `app/main.py`

Your Task:
Implement Requirement R1 (AWS RDS PostgreSQL Persistence):
1. Update `requirements.txt` to include `sqlalchemy>=2.0.36`, `asyncpg>=0.30.0`, and `psycopg[binary]>=3.2.3`.
2. Create `app/models/upi_persistence.py` with SQLAlchemy 2.0 async declarative models (`UpiCaseModel`, `MuleRingModel`, `CaseFeedbackModel`, `AggregateStatsModel`) with JSONB attributes, relationships, and compound indexes.
3. Implement `app/db/session.py` with `create_async_engine`, RDS connection pooling for t3.micro (`pool_size=5`, `max_overflow=10`, `pool_recycle=1800`, `pool_pre_ping=True`), `get_db` async generator, `init_db()` for auto-creating tables on startup via `run_sync(Base.metadata.create_all)`, and graceful fallback if `DATABASE_URL` is unavailable or DB is unreachable.
4. Update `app/main.py` to hook `init_db()` into FastAPI `lifespan` startup, `close_db()` on shutdown, and modernize `/health` to actively probe the database connection via `SELECT 1` (returning 200 when healthy).
5. Update `app/services/upi_cases.py` and `app/api/upi.py` to persist cases, rings, and feedback into PostgreSQL, and query the DB for `/upi/cases`, `/upi/cases/{case_id}`, and `/upi/stats`.
6. Update `Dockerfile` and `deploy/ec2_userdata.sh` to support `DATABASE_URL` env passing.
7. Run Python syntax and unit tests to verify your implementation works cleanly.
8. Write `handoff.md` in your working directory and notify parent.

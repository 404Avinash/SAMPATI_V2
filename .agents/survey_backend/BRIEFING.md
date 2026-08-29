# BRIEFING — 2026-08-29T07:50:00Z

## Mission
Investigate FastAPI backend architecture and test suite to design R3 requirements: GET /stats/analytics, GET /health/detailed, PATCH /cases/{case_id}/status, and test suite additions.

## 🔒 My Identity
- Archetype: Explorer
- Roles: Backend Architecture & Endpoint Investigator
- Working directory: /home/avi/Downloads/Sampati_v2/.agents/survey_backend
- Original parent: c28be108-5e62-41d1-bc36-26b57ba15724
- Milestone: Backend Survey & Technical Design (R3)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze existing app/ structure, models, schemas, routers, dependencies, DB, Redis, WS manager, stats tracking
- Provide complete technical design, exact file paths, schemas, proposed code changes/patches, and verification strategy

## Current Parent
- Conversation ID: c28be108-5e62-41d1-bc36-26b57ba15724
- Updated: 2026-08-29T07:50:00Z

## Investigation State
- **Explored paths**:
  - `app/main.py` (FastAPI app, lifespan, CORS, static mounting, health probe)
  - `app/db/session.py` (AsyncEngine, sessionmaker, pool sizing for t3.micro, init_db, check_db_health, AsyncDatabaseStore)
  - `app/models/upi_persistence.py` (UpiCaseModel, MuleRingModel, CaseFeedbackModel, AggregateStatsModel, JSONB columns)
  - `app/api/upi.py` (check, federation/run, rings, cases, cases/{id}, feedback, simulate, stats)
  - `app/api/websocket.py` (ConnectionManager, broadcast, schedule_broadcast, ws routes)
  - `app/services/upi_cases.py` (UpiCaseService singleton, evaluation, SAR generation, DPIP integration, DB upsert)
  - `tests/test_e2e_suite.py`, `tests/test_cicd_pipeline.py`, `tests/frontend_contracts_test.py`, `tests/test_m1_persistence.py`, `tests/test_m2_websocket.py`, `tests/test_tier1_features.py`
  - `Dockerfile`, `.github/workflows/deploy.yml`, `PROJECT.md`, `TEST_INFRA.md`
- **Key findings**:
  - Existing persistence and WebSocket push architecture is solid and robust.
  - Three new endpoints required for R3: `GET /stats/analytics`, `GET /health/detailed`, `PATCH /cases/{case_id}/status`.
  - Aliases should be registered at both root (`/stats/analytics`, `/health/detailed`, `/cases/{case_id}/status`) and under `/upi` prefix (`/upi/stats/analytics`, `/upi/health/detailed`, `/upi/cases/{case_id}/status`) for maximum frontend resilience.
  - All metrics (latency percentiles p50/p99, throughput, DB pool stats, Redis ping, WebSocket connections, time-bucketed analytics, rule trigger frequencies, top flagged accounts, bank distribution) can be computed seamlessly with PostgreSQL and in-memory fallbacks.
  - Test suites (`tests/test_analytics.py`, `tests/test_health_detailed.py`, `tests/test_case_status.py`) can be structured to support both pytest in full environments and unittest with AST/fallback for maximum reliability.
- **Unexplored areas**: None. Full backend architecture and contract space mapped.

## Key Decisions Made
- Fully specified schema, logic, and data flow for all 3 endpoints.
- Designed comprehensive test suite with >= 15 tests across the 3 new endpoints.

## Artifact Index
- /home/avi/Downloads/Sampati_v2/.agents/survey_backend/DISPATCH.md — Task dispatches
- /home/avi/Downloads/Sampati_v2/.agents/survey_backend/BRIEFING.md — Persistent context & state
- /home/avi/Downloads/Sampati_v2/.agents/survey_backend/progress.md — Progress log & liveness heartbeat
- /home/avi/Downloads/Sampati_v2/.agents/survey_backend/handoff.md — 5-component handoff report

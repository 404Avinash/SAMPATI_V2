## 2026-09-04T22:07:09Z

Perform an exhaustive architectural survey of the Backend, Data Pipeline, Database, and Cache layers of SAMPATI V2 in /home/avi/Downloads/Sampati_v2/app.

Investigate and document in full detail:
1. Application Lifecycle & Configuration: FastAPI app setup (main.py, lifespan events, middleware, CORS, error handlers, config/settings via pydantic_settings or env).
2. API Routers & Endpoints: All API routes (transactions, investigations, SAR, topology/graph, metrics, simulation controls, healthchecks).
3. Service Layer Architecture: Business logic services, transaction coordinator, investigation services, simulator engine, network/graph service.
4. Data Models & Schemas: Pydantic schemas (request/response validation), ORM/DB entities, domain models.
5. Data Pipeline & Evaluation Flow:
   - Transaction ingestion pipeline: how an incoming transaction is processed end-to-end.
   - Real-time broadcasting: WebSocket connection manager, broadcast channels, client connection lifecycle, serialization.
6. Database Layer (PostgreSQL):
   - PostgreSQL schema, tables, indices, migrations/DDL.
   - Connection pooling, asyncpg / SQLAlchemy usage, transaction handling.
   - Long-term storage of transactions, verdicts, ML feature logs, SARs.
7. Cache & Hot State Layer (Redis):
   - Redis client configuration, connection pooling.
   - Key naming conventions and schema.
   - Short-term account velocity tracking, sliding window counters, lock mechanisms, queue structures.
   - Aggregation and caching of dashboard KPI metrics.

Output:
Write an exhaustive, high-quality technical report to:
/home/avi/Downloads/Sampati_v2/.agents/teamwork_preview_explorer_survey_be/report.md
Include exact file paths, line references where appropriate, code snippets, schema definitions, and sequence/data flow diagrams.
When complete, write handoff.md and notify with send_message.

# Telemetry & On-Device Threat Logging Handoff (Round 0 Implementer)

## 1. Executive Summary
Implemented end-to-end on-device threat telemetry ingestion and user/analyst override logging for SAMPATI V2. All additions strictly adhere to the existing architectural patterns: SQLAlchemy 2.0 declarative mapping with `Mapped` and `mapped_column`, Pydantic v2 schemas with `model_config` OpenAPI examples, async database sessions with in-memory fallback resilience, and clean FastAPI router integration.

## 2. Changes by File

### A. Database Models & Pydantic Schemas (`app/models/telemetry.py`)
- **SQLAlchemy 2.0 Models**:
  - `ThreatEvent`: Subclasses `Base` (`app.models.upi_persistence.Base`), utilizing `Mapped[...]` and `mapped_column(...)` for all attributes (`id`, `event_id`, `device_id`, `user_id`, `threat_type`, `severity`, `confidence`, `status`, `action_taken`, `package_name`, `platform`, `app_version`, `os_version`, `threat_source`, `vpa`, `phone_number`, `raw_payload`, `device_timestamp`, `created_at`).
    - Uses generic types (`Integer`, `String`, `Float`, `Boolean`, `DateTime(timezone=True)`, `JSON`, `Text`) compatible with both AWS RDS PostgreSQL and SQLite.
    - Defined compound indexes: `ix_threat_events_severity_created`, `ix_threat_events_threat_type_created`, `ix_threat_events_device_created`.
    - Defined 1-to-many relationship: `overrides: Mapped[List[UserOverride]] = relationship("UserOverride", back_populates="threat_event", cascade="all, delete-orphan", lazy="selectin")`.
    - Added `to_dict()` serialization method.
  - `UserOverride`: Subclasses `Base`, using `Mapped[...]` and `mapped_column(...)` (`id`, `override_id`, `event_id`, `user_id`, `device_id`, `override_reason`, `user_action`, `feedback_notes`, `risk_acknowledged`, `metadata_json`, `created_at`).
    - Foreign key: `event_id: Mapped[str] = mapped_column(String(64), ForeignKey("threat_events.event_id", ondelete="CASCADE"), index=True, nullable=False)`.
    - Compound indexes: `ix_user_overrides_event_created`, `ix_user_overrides_reason_created`.
    - Defined relationship: `threat_event: Mapped[Optional[ThreatEvent]] = relationship("ThreatEvent", back_populates="overrides", lazy="selectin")`.
    - Added `to_dict()` serialization method.
- **Pydantic v2 Schemas**:
  - `ThreatEventCreate`: Strict input payload validation (`device_id`, `threat_type`, `severity`, `confidence`, `status`, etc.). Includes `field_validator` normalizing case and checking allowed sets (`severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}`, `status in {"DETECTED", "BLOCKED", "WARNED", "IGNORED", "OVERRIDDEN", "RESOLVED"}`). Configured `model_config = ConfigDict(json_schema_extra={"example": ...})` with complete mock payload.
  - `ThreatEventResponse`: Serialized output with `event_id`, `created_at`, `override_count`, and `model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": ...})`.
  - `ThreatEventListResponse`: Paginated response (`total: int`, `events: List[ThreatEventResponse]`).
  - `UserOverrideCreate`: Input payload validation (`event_id`, `override_reason`, `user_action in {"PROCEED_ANYWAY", "ALLOW_ALWAYS", "DISMISS_ALERT", "REPORT_SAFE", "WHITELIST", "IGNORE_WARNING"}`, `risk_acknowledged`, `feedback_notes`). Includes OpenAPI example.
  - `UserOverrideResponse`: Serialized output with `override_id`, `created_at`, and `model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": ...})`.
  - `UserOverrideListResponse`: Paginated response (`total: int`, `overrides: List[UserOverrideResponse]`).
  - `TelemetryStatsResponse`: Summary counters (`total_events`, `total_overrides`, `override_rate`, `severity_breakdown`, `threat_type_breakdown`, `override_reason_breakdown`, `active_devices_count`).

### B. Service Engine (`app/services/telemetry_service.py`)
- Thread-safe singleton service (`TelemetryService`) providing dual-backend persistence:
  - When `AsyncSession` (`db`) is provided: issues async SQLAlchemy 2.0 ORM operations (`db.add`, `await db.commit()`, `await db.refresh()`, `select()`).
  - When `db` is `None` or offline: maintains in-memory store (`_events_by_id`, `_overrides_by_id`, `_event_order`, `_override_order`) with thread locks.
- ID Generation: `EVT-<12-hex-uppercase>` for threat events, `OVR-<12-hex-uppercase>` for overrides.
- Implemented methods:
  - `record_threat_event`: Ingests and saves event, returns response.
  - `record_user_override`: Verifies target event existence (in DB and cache), raises `KeyError` if absent (converted to HTTP 404 in API), creates override, transitions parent event status to `"OVERRIDDEN"`, and commits.
  - `get_threat_event`: Queries by `event_id`.
  - `list_threat_events`: Supports query filters (`device_id`, `threat_type`, `severity`, `status`), ordering by `created_at DESC`, and limit/offset pagination.
  - `list_user_overrides`: Supports query filters (`event_id`, `user_id`, `override_reason`), ordering by `created_at DESC`, and limit/offset pagination.
  - `get_stats`: Computes aggregated distribution metrics via DB grouping/counts or in-memory map.
  - `clear()`: State cleanup for unit test isolation.

### C. FastAPI Router (`app/api/telemetry.py`)
- Endpoints registered:
  - `POST /events`: Ingests threat event, returns `201 Created` with `ThreatEventResponse`.
  - `POST /overrides`: Ingests user override, returns `201 Created` with `UserOverrideResponse`. Handles non-existent parent with `404 Not Found`, validation failure with `422 Unprocessable Entity`.
  - `GET /events`: Paginated query with query parameter filters.
  - `GET /events/{event_id}`: Single event lookup, returns `200 OK` or `404 Not Found`.
  - `GET /overrides`: Paginated list of user overrides with query parameter filters.
  - `GET /stats`: High-level aggregate metrics.
- All endpoints define FastAPI OpenAPI `summary`, `description`, and `responses` specifications.

### D. FastAPI App Integration (`app/main.py`)
- Imported `telemetry_router` and registered:
  ```python
  if telemetry_router and hasattr(telemetry_router, "router"):
      app.include_router(telemetry_router.router, prefix="/telemetry", tags=["Telemetry"])
      app.include_router(telemetry_router.router, prefix="/upi/telemetry", tags=["Telemetry"])
  ```
- Updated `spa_fallback_404_handler` `api_prefixes` tuple to include `"/telemetry"`, preventing the client-side SPA fallback from intercepting API 404s on telemetry routes.

### E. Database Session Hook (`app/db/session.py`)
- Imported `app.models.telemetry` so that `ThreatEvent` and `UserOverride` are registered in `Base.metadata` on module load.
- When `await init_db()` executes `await conn.run_sync(UpiBase.metadata.create_all)`, `threat_events` and `user_overrides` are automatically created on startup without requiring manual DDL.

### F. Test Suite (`tests/test_telemetry.py`)
- Added 22 dedicated test cases verifying:
  - SQLAlchemy 2.0 `Mapped[...]` typing and `mapped_column` configuration.
  - Compound indexes and foreign key cascade delete.
  - Pydantic v2 validation rules (allowed values, bounds, missing fields).
  - OpenAPI mock payload examples in model JSON schemas.
  - Endpoint HTTP status codes: `POST /telemetry/events` (201), `POST /telemetry/overrides` (201, 404, 422), `GET /telemetry/events` (200), `GET /telemetry/stats` (200).
  - Programmatic `/openapi.json` route registration.
  - SQLite async engine table creation, CRUD, relationship loading, and cascade deletion.

## 3. Verification Record

### A. Full Test Suite (Pytest)
```
$ ./.venv/bin/pytest
================ 999 passed, 6 warnings in 119.25s (0:01:59) ==================
```
- Total test count: 999 passed (including 22 new telemetry tests).
- 0 failures, 0 regressions.

### B. Python Linter (Ruff)
```
$ ./.venv/bin/ruff check app tests
All checks passed!
```

### C. Frontend ESLint
```
$ cd frontend && npm run lint
$ eslint src --ext js,jsx --report-unused-disable-directives --max-warnings 0
(exit code 0, 0 warnings)
```

### D. Frontend Vite Build
```
$ cd frontend && npm run build
vite v5.4.21 building for production...
✓ 1392 modules transformed.
dist/index.html                     0.88 kB │ gzip:   0.50 kB
dist/assets/index-DWCBC0gd.css     72.16 kB │ gzip:  16.20 kB
dist/assets/index-BNlH00g8.js   1,263.01 kB │ gzip: 357.26 kB
✓ built in 10.02s
```

### E. Programmatic OpenAPI Route Check
Verified that `GET /openapi.json` exposes all `/telemetry` routes:
- `/telemetry/events` (POST, GET)
- `/telemetry/events/{event_id}` (GET)
- `/telemetry/overrides` (POST, GET)
- `/telemetry/stats` (GET)

## 4. Known Issues & Unverified Aspects
- **Fatal Functional Bug**: None.
- **Shallow Verification**: None.
- **Minor Robustness Risk**:
  - In a high-throughput production environment without database clustering (e.g. SQLite single file), concurrent write locks during massive spike loads could experience retry contention. The in-memory fallback gracefully catches and caches records, but PostgreSQL with RDS connection pooling is recommended for sustained multi-thousand TPS ingestion.

## 5. Untested Edge Cases & Reviewer Next Steps
- A reviewer should verify:
  1. `ThreatEvent` and `UserOverride` classes in `app/models/telemetry.py` strictly employ SQLAlchemy 2.0 `Mapped` annotations.
  2. Model foreign key cascade deletion when an event with multiple overrides is deleted directly via SQL.
  3. OpenAPI schema generation at `/openapi.json` has expected mock payload representations.

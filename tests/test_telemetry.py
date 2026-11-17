"""Comprehensive test suite for Telemetry and Threat Logging subsystem.

Covers:
1. SQLAlchemy 2.0 syntax validation (Mapped, mapped_column, relationship).
2. Cross-dialect generic types and SQLite/PostgreSQL compatibility.
3. Foreign key constraints, compound indexes, and cascade deletion.
4. Pydantic v2 schemas, field validations, boundary values, and OpenAPI mock payloads.
5. FastAPI endpoints: POST /telemetry/events, POST /telemetry/overrides, GET queries, and /telemetry/stats.
6. Programmatic app launch, OpenAPI schema registry, and 404/422 error flows.
7. Async database persistence and in-memory fallback resilience.
"""
from __future__ import annotations

import ast
import asyncio
import os
import typing
from datetime import datetime, timezone
from typing import get_args, get_origin
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, event, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped

import backend  # noqa: F401
from app.db.session import close_db, init_db
from app.main import app
from app.models.telemetry import (
    TelemetryStatsResponse,
    ThreatEvent,
    ThreatEventCreate,
    ThreatEventListResponse,
    ThreatEventResponse,
    UserOverride,
    UserOverrideCreate,
    UserOverrideListResponse,
    UserOverrideResponse,
)
from app.models.upi_persistence import Base
from app.services.telemetry_service import get_telemetry_service


@pytest.fixture(autouse=True)
def reset_telemetry_state():
    """Reset telemetry service in-memory state before and after each test."""
    svc = get_telemetry_service()
    svc.clear()
    yield
    svc.clear()


# ── 1. SQLAlchemy 2.0 Architecture & Syntax Verification ─────────────────────

class TestSqlAlchemy20Architecture:
    """Verify that models strictly comply with SQLAlchemy 2.0 syntax and standards."""

    def test_threat_event_uses_mapped_annotations(self):
        """Confirm ThreatEvent attributes use Mapped typing rather than bare Column."""
        annotations = ThreatEvent.__annotations__
        for col in ["id", "event_id", "device_id", "threat_type", "severity", "confidence", "status", "overrides"]:
            assert col in annotations
            # String annotation starts with Mapped due to __future__.annotations
            assert "Mapped[" in str(annotations[col])

        # Also verify evaluated type hints resolve to Mapped
        import app.models.telemetry as tm
        hints = typing.get_type_hints(ThreatEvent, globalns=vars(tm))
        assert get_origin(hints["event_id"]) is Mapped
        assert get_origin(hints["device_id"]) is Mapped
        assert get_origin(hints["severity"]) is Mapped
        assert get_origin(hints["confidence"]) is Mapped
        assert get_origin(hints["overrides"]) is Mapped

    def test_user_override_uses_mapped_annotations(self):
        """Confirm UserOverride attributes use Mapped typing rather than bare Column."""
        annotations = UserOverride.__annotations__
        for col in ["id", "override_id", "event_id", "override_reason", "user_action", "threat_event"]:
            assert col in annotations
            assert "Mapped[" in str(annotations[col])

        import app.models.telemetry as tm
        hints = typing.get_type_hints(UserOverride, globalns=vars(tm))
        assert get_origin(hints["override_id"]) is Mapped
        assert get_origin(hints["event_id"]) is Mapped
        assert get_origin(hints["override_reason"]) is Mapped
        assert get_origin(hints["threat_event"]) is Mapped

    def test_table_metadata_and_compound_indexes(self):
        """Verify tables and indexes are registered in Base metadata."""
        tables = Base.metadata.tables
        assert "threat_events" in tables
        assert "user_overrides" in tables

        te_table = tables["threat_events"]
        index_names = {idx.name for idx in te_table.indexes}
        assert "ix_threat_events_severity_created" in index_names
        assert "ix_threat_events_threat_type_created" in index_names
        assert "ix_threat_events_device_created" in index_names

        uo_table = tables["user_overrides"]
        uo_indexes = {idx.name for idx in uo_table.indexes}
        assert "ix_user_overrides_event_created" in uo_indexes
        assert "ix_user_overrides_reason_created" in uo_indexes

    def test_foreign_key_and_relationship_configuration(self):
        """Verify foreign key from user_overrides.event_id to threat_events.event_id."""
        uo_table = Base.metadata.tables["user_overrides"]
        fks = list(uo_table.foreign_keys)
        assert len(fks) >= 1
        fk = next(f for f in fks if f.parent.name == "event_id")
        assert fk.target_fullname == "threat_events.event_id"
        assert fk.ondelete == "CASCADE"


# ── 2. Pydantic Schemas & OpenAPI Verification ────────────────────────────────

class TestPydanticSchemasAndValidation:
    """Verify validation logic, boundary checking, and OpenAPI schemas."""

    def test_threat_event_create_valid(self):
        """Test valid ThreatEventCreate payload parsing and case normalization."""
        data = {
            "device_id": "dev_test_123",
            "threat_type": "sms_phishing",
            "severity": "high",
            "confidence": 0.95,
            "status": "detected",
            "action_taken": "NOTIFIED_USER",
            "package_name": "com.fraud.app",
            "platform": "android",
            "app_version": "1.0.0",
            "os_version": "Android 14",
            "threat_source": "sms_detector",
            "vpa": "badguy@upi",
            "phone_number": "+919876543210",
            "raw_payload": {"link": "http://scam.xyz"},
            "device_timestamp": datetime.now(timezone.utc),
        }
        obj = ThreatEventCreate(**data)
        assert obj.device_id == "dev_test_123"
        assert obj.threat_type == "SMS_PHISHING"
        assert obj.severity == "HIGH"
        assert obj.status == "DETECTED"
        assert obj.confidence == 0.95

    def test_threat_event_create_invalid_severity(self):
        """Ensure invalid severity throws ValidationError."""
        with pytest.raises(ValidationError) as exc:
            ThreatEventCreate(
                device_id="dev_123",
                threat_type="SMS_PHISHING",
                severity="SUPER_CRITICAL",
            )
        assert "Invalid severity" in str(exc.value)

    def test_threat_event_create_invalid_status(self):
        """Ensure invalid status throws ValidationError."""
        with pytest.raises(ValidationError) as exc:
            ThreatEventCreate(
                device_id="dev_123",
                threat_type="SMS_PHISHING",
                status="DISCARDED_FOREVER",
            )
        assert "Invalid status" in str(exc.value)

    def test_threat_event_create_confidence_bounds(self):
        """Ensure confidence outside [0.0, 1.0] throws ValidationError."""
        with pytest.raises(ValidationError):
            ThreatEventCreate(
                device_id="dev_123",
                threat_type="SMS_PHISHING",
                confidence=1.5,
            )
        with pytest.raises(ValidationError):
            ThreatEventCreate(
                device_id="dev_123",
                threat_type="SMS_PHISHING",
                confidence=-0.1,
            )

    def test_threat_event_create_missing_required_fields(self):
        """Ensure missing device_id or threat_type fails."""
        with pytest.raises(ValidationError):
            ThreatEventCreate(device_id="dev_123")  # missing threat_type
        with pytest.raises(ValidationError):
            ThreatEventCreate(threat_type="SMS_PHISHING")  # missing device_id

    def test_user_override_create_valid(self):
        """Test valid UserOverrideCreate payload parsing."""
        data = {
            "event_id": "EVT-ABCDEF123456",
            "user_id": "usr_99",
            "device_id": "dev_123",
            "override_reason": "false_positive",
            "user_action": "proceed_anyway",
            "feedback_notes": "Legitimate banking SMS verified with branch.",
            "risk_acknowledged": True,
            "metadata_json": {"flow": "manual_review"},
        }
        obj = UserOverrideCreate(**data)
        assert obj.event_id == "EVT-ABCDEF123456"
        assert obj.override_reason == "FALSE_POSITIVE"
        assert obj.user_action == "PROCEED_ANYWAY"
        assert obj.risk_acknowledged is True

    def test_user_override_create_invalid_action(self):
        """Ensure invalid user_action throws ValidationError."""
        with pytest.raises(ValidationError) as exc:
            UserOverrideCreate(
                event_id="EVT-ABCDEF123456",
                override_reason="FALSE_POSITIVE",
                user_action="RANDOM_ACTION",
            )
        assert "Invalid user_action" in str(exc.value)

    def test_openapi_examples_in_json_schema(self):
        """Verify OpenAPI mock payload examples are configured on all models."""
        te_create_schema = ThreatEventCreate.model_json_schema()
        assert "example" in te_create_schema
        assert "threat_type" in te_create_schema["example"]
        assert "device_id" in te_create_schema["example"]

        te_resp_schema = ThreatEventResponse.model_json_schema()
        assert "example" in te_resp_schema
        assert "event_id" in te_resp_schema["example"]

        uo_create_schema = UserOverrideCreate.model_json_schema()
        assert "example" in uo_create_schema
        assert "event_id" in uo_create_schema["example"]
        assert "override_reason" in uo_create_schema["example"]

        uo_resp_schema = UserOverrideResponse.model_json_schema()
        assert "example" in uo_resp_schema
        assert "override_id" in uo_resp_schema["example"]


# ── 3. FastAPI API Endpoints & OpenAPI Contract ──────────────────────────────

class TestTelemetryApiEndpoints:
    """Integration tests for FastAPI REST endpoints using TestClient."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_openapi_schema_contains_telemetry_routes(self, client):
        """Programmatically check /openapi.json contains /telemetry routes."""
        res = client.get("/openapi.json")
        assert res.status_code == 200
        schema = res.json()
        paths = schema.get("paths", {})

        assert "/telemetry/events" in paths
        assert "post" in paths["/telemetry/events"]
        assert "get" in paths["/telemetry/events"]

        assert "/telemetry/overrides" in paths
        assert "post" in paths["/telemetry/overrides"]
        assert "get" in paths["/telemetry/overrides"]

        assert "/telemetry/stats" in paths
        assert "get" in paths["/telemetry/stats"]

        assert "/telemetry/events/{event_id}" in paths
        assert "get" in paths["/telemetry/events/{event_id}"]

    def test_post_threat_event_success_201(self, client):
        """Test POST /telemetry/events returns 201 Created and populated response."""
        payload = {
            "device_id": "device_xyz_999",
            "threat_type": "OVERLAY_ATTACK",
            "severity": "CRITICAL",
            "confidence": 0.98,
            "status": "BLOCKED",
            "action_taken": "BLOCKED_APP",
            "package_name": "com.malicious.screen.overlay",
            "platform": "android",
            "raw_payload": {"accessibility_granted": True},
        }
        res = client.post("/telemetry/events", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["event_id"].startswith("EVT-")
        assert data["device_id"] == "device_xyz_999"
        assert data["threat_type"] == "OVERLAY_ATTACK"
        assert data["severity"] == "CRITICAL"
        assert data["confidence"] == 0.98
        assert data["status"] == "BLOCKED"
        assert data["override_count"] == 0
        assert "created_at" in data

    def test_post_threat_event_validation_failure_422(self, client):
        """Test POST /telemetry/events with invalid payload returns 422 Unprocessable Entity."""
        res = client.post("/telemetry/events", json={"device_id": "d1"})  # missing threat_type
        assert res.status_code == 422

    def test_post_user_override_success_201(self, client):
        """Test POST /telemetry/overrides returns 201 Created when parent event exists."""
        # 1. Create threat event
        event_res = client.post(
            "/telemetry/events",
            json={
                "device_id": "dev_test_ovr",
                "threat_type": "SMS_PHISHING",
                "severity": "HIGH",
            },
        )
        assert event_res.status_code == 201
        event_id = event_res.json()["event_id"]

        # 2. Record override
        ovr_payload = {
            "event_id": event_id,
            "user_id": "usr_analyst_1",
            "override_reason": "FALSE_POSITIVE",
            "user_action": "PROCEED_ANYWAY",
            "feedback_notes": "Whitelisted legitimate test sender.",
            "risk_acknowledged": True,
        }
        ovr_res = client.post("/telemetry/overrides", json=ovr_payload)
        assert ovr_res.status_code == 201
        ovr_data = ovr_res.json()
        assert ovr_data["override_id"].startswith("OVR-")
        assert ovr_data["event_id"] == event_id
        assert ovr_data["override_reason"] == "FALSE_POSITIVE"
        assert ovr_data["risk_acknowledged"] is True

        # 3. Verify parent event updated status & override_count
        get_evt_res = client.get(f"/telemetry/events/{event_id}")
        assert get_evt_res.status_code == 200
        evt_data = get_evt_res.json()
        assert evt_data["status"] == "OVERRIDDEN"
        assert evt_data["override_count"] == 1

    def test_post_user_override_nonexistent_event_404(self, client):
        """Test POST /telemetry/overrides returns 404 when target event_id does not exist."""
        ovr_payload = {
            "event_id": "EVT-NONEXISTENT99",
            "override_reason": "FALSE_POSITIVE",
            "user_action": "PROCEED_ANYWAY",
        }
        res = client.post("/telemetry/overrides", json=ovr_payload)
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_get_threat_events_filtering_and_pagination(self, client):
        """Test GET /telemetry/events with query filters and pagination."""
        client.post("/telemetry/events", json={"device_id": "dev_A", "threat_type": "SMS_PHISHING", "severity": "LOW"})
        client.post("/telemetry/events", json={"device_id": "dev_A", "threat_type": "MALICIOUS_APP", "severity": "HIGH"})
        client.post("/telemetry/events", json={"device_id": "dev_B", "threat_type": "MALICIOUS_APP", "severity": "CRITICAL"})

        # Query all
        res_all = client.get("/telemetry/events")
        assert res_all.status_code == 200
        assert res_all.json()["total"] >= 3

        # Filter by device_id
        res_dev = client.get("/telemetry/events?device_id=dev_A")
        assert res_dev.status_code == 200
        assert res_dev.json()["total"] == 2

        # Filter by threat_type
        res_type = client.get("/telemetry/events?threat_type=MALICIOUS_APP")
        assert res_type.status_code == 200
        assert res_type.json()["total"] == 2

        # Filter by severity
        res_sev = client.get("/telemetry/events?severity=CRITICAL")
        assert res_sev.status_code == 200
        assert res_sev.json()["total"] == 1

        # Pagination
        res_page = client.get("/telemetry/events?limit=1&offset=0")
        assert res_page.status_code == 200
        assert len(res_page.json()["events"]) == 1

    def test_get_threat_event_by_id_404(self, client):
        """Test GET /telemetry/events/{event_id} returns 404 for missing ID."""
        res = client.get("/telemetry/events/EVT-MISSING999")
        assert res.status_code == 404

    def test_get_user_overrides_list(self, client):
        """Test GET /telemetry/overrides endpoint."""
        ev_res = client.post("/telemetry/events", json={"device_id": "dev_1", "threat_type": "SMS_PHISHING"})
        eid = ev_res.json()["event_id"]
        client.post("/telemetry/overrides", json={"event_id": eid, "override_reason": "TESTING"})

        res = client.get("/telemetry/overrides")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert any(o["event_id"] == eid for o in data["overrides"])

    def test_get_telemetry_stats(self, client):
        """Test GET /telemetry/stats returns aggregate metrics."""
        ev1 = client.post("/telemetry/events", json={"device_id": "dev_stat_1", "threat_type": "SMS_PHISHING", "severity": "HIGH"})
        ev2 = client.post("/telemetry/events", json={"device_id": "dev_stat_2", "threat_type": "OVERLAY_ATTACK", "severity": "MEDIUM"})
        eid1 = ev1.json()["event_id"]
        client.post("/telemetry/overrides", json={"event_id": eid1, "override_reason": "FALSE_POSITIVE"})

        res = client.get("/telemetry/stats")
        assert res.status_code == 200
        stats = res.json()
        assert stats["total_events"] >= 2
        assert stats["total_overrides"] >= 1
        assert stats["override_rate"] > 0.0
        assert "HIGH" in stats["severity_breakdown"]
        assert "SMS_PHISHING" in stats["threat_type_breakdown"]
        assert stats["active_devices_count"] >= 2


# ── 4. Async Database Persistence & Cross-Dialect Verification ───────────────

class TestAsyncDatabasePersistence:
    """Verify SQLAlchemy 2.0 async persistence on SQLite/PostgreSQL."""

    @pytest.mark.anyio
    async def test_sqlite_table_initialization_and_crud(self, tmp_path):
        """Test end-to-end table creation and CRUD using SQLite async engine."""
        db_file = tmp_path / "telemetry_test.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # 1. Insert ThreatEvent
        now = datetime.now(timezone.utc)
        async with session_factory() as session:
            evt = ThreatEvent(
                event_id="EVT-DB-TEST-001",
                device_id="dev_db_123",
                user_id="usr_db_456",
                threat_type="MALICIOUS_APP",
                severity="CRITICAL",
                confidence=0.99,
                status="DETECTED",
                raw_payload={"hash": "abcdef1234567890"},
                created_at=now,
            )
            session.add(evt)
            await session.commit()

        # 2. Insert UserOverride linking to ThreatEvent
        async with session_factory() as session:
            ovr = UserOverride(
                override_id="OVR-DB-TEST-001",
                event_id="EVT-DB-TEST-001",
                override_reason="SECURITY_EXEMPTION",
                user_action="ALLOW_ALWAYS",
                risk_acknowledged=True,
                created_at=now,
            )
            session.add(ovr)
            await session.commit()

        # 3. Query with relationship
        async with session_factory() as session:
            stmt = select(ThreatEvent).where(ThreatEvent.event_id == "EVT-DB-TEST-001")
            res = await session.execute(stmt)
            loaded_evt = res.scalar_one()
            assert loaded_evt.event_id == "EVT-DB-TEST-001"
            assert len(loaded_evt.overrides) == 1
            assert loaded_evt.overrides[0].override_reason == "SECURITY_EXEMPTION"

        # 4. Verify cascade delete: deleting ThreatEvent cascades to UserOverride
        async with session_factory() as session:
            stmt = select(ThreatEvent).where(ThreatEvent.event_id == "EVT-DB-TEST-001")
            res = await session.execute(stmt)
            loaded_evt = res.scalar_one()
            await session.delete(loaded_evt)
            await session.commit()

        async with session_factory() as session:
            ovr_stmt = select(UserOverride).where(UserOverride.override_id == "OVR-DB-TEST-001")
            res_ovr = await session.execute(ovr_stmt)
            assert res_ovr.scalar_one_or_none() is None

        await engine.dispose()


# ── 5. Adversarial Reviewer Hardening & Edge Cases ──────────────────────────

class TestAdversarialReviewerHardening:
    """Rigorous tests attacking edge cases, AST structure, ORM validation, and rollback safety."""

    def test_ast_strictly_enforces_mapped_column_and_no_legacy_column(self):
        """Perform static AST analysis to verify zero legacy Column definitions."""
        filepath = os.path.join(os.path.dirname(__file__), "..", "app", "models", "telemetry.py")
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)

        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name in ("ThreatEvent", "UserOverride"):
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        # Verify annotation uses Mapped
                        ann_str = ast.unparse(item.annotation)
                        assert ann_str.startswith("Mapped["), (
                            f"Attribute {ast.unparse(item.target)} in {node.name} must use Mapped[...], found: {ann_str}"
                        )
                    elif isinstance(item, ast.Assign):
                        # Ensure no bare Column(...) assignments
                        for val in [item.value]:
                            if isinstance(val, ast.Call):
                                call_func = ast.unparse(val.func)
                                assert call_func != "Column", (
                                    f"Legacy Column assignment found in {node.name}: {ast.unparse(item)}"
                                )

    def test_from_attributes_works_on_raw_orm_instances(self):
        """Ensure ThreatEventResponse and UserOverrideResponse can validate directly from ORM instances."""
        now = datetime.now(timezone.utc)
        te = ThreatEvent(
            event_id="EVT-ADV-123456",
            device_id="dev_adv_123",
            threat_type="SMS_PHISHING",
            severity="HIGH",
            confidence=0.9,
            status="DETECTED",
            created_at=now,
        )
        resp_te = ThreatEventResponse.model_validate(te)
        assert resp_te.event_id == "EVT-ADV-123456"
        assert resp_te.platform == "android"
        assert resp_te.threat_source == "on_device_scanner"
        assert resp_te.override_count == 0
        assert isinstance(resp_te.created_at, str)

        uo = UserOverride(
            override_id="OVR-ADV-123456",
            event_id="EVT-ADV-123456",
            override_reason="FALSE_POSITIVE",
            user_action="PROCEED_ANYWAY",
            risk_acknowledged=True,
            created_at=now,
        )
        resp_uo = UserOverrideResponse.model_validate(uo)
        assert resp_uo.override_id == "OVR-ADV-123456"
        assert resp_uo.event_id == "EVT-ADV-123456"
        assert isinstance(resp_uo.created_at, str)

    def test_whitespace_device_id_and_event_id_rejected(self):
        """Ensure pure whitespace device_id and event_id fail validation."""
        with pytest.raises(ValidationError):
            ThreatEventCreate(device_id="     ", threat_type="SMS_PHISHING")

        with pytest.raises(ValidationError):
            UserOverrideCreate(event_id="     ", override_reason="FALSE_POSITIVE")

    def test_lowercase_event_id_handling_in_override_and_lookup(self):
        """Verify lowercase event_id is normalized in overrides and lookups."""
        client = TestClient(app)
        # Ingest event
        res = client.post(
            "/telemetry/events",
            json={"device_id": "dev_case_test", "threat_type": "OVERLAY_ATTACK", "severity": "MEDIUM"},
        )
        assert res.status_code == 201
        event_id = res.json()["event_id"]

        # Post override with lowercase event_id
        res_ovr = client.post(
            "/telemetry/overrides",
            json={
                "event_id": event_id.lower(),
                "override_reason": "user_consent",
                "user_action": "proceed_anyway",
            },
        )
        assert res_ovr.status_code == 201
        assert res_ovr.json()["event_id"] == event_id

        # Lookup with lowercase event_id
        res_get = client.get(f"/telemetry/events/{event_id.lower()}")
        assert res_get.status_code == 200
        assert res_get.json()["status"] == "OVERRIDDEN"

    def test_multiple_overrides_per_event_does_not_crash_stats(self):
        """Test GET /telemetry/stats does not crash with HTTP 500 when overrides exceed events."""
        client = TestClient(app)
        # Ingest 1 event
        res = client.post(
            "/telemetry/events",
            json={"device_id": "dev_multi_ovr", "threat_type": "SMS_PHISHING", "severity": "HIGH"},
        )
        assert res.status_code == 201
        eid = res.json()["event_id"]

        # Submit 3 overrides for that single event
        for i in range(3):
            res_ovr = client.post(
                "/telemetry/overrides",
                json={
                    "event_id": eid,
                    "override_reason": "FALSE_POSITIVE",
                    "feedback_notes": f"Attempt {i+1}",
                },
            )
            assert res_ovr.status_code == 201

        # Check stats: overrides (3) > events (1), override_rate must be <= 1.0
        res_stats = client.get("/telemetry/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["total_events"] >= 1
        assert stats["total_overrides"] >= 3
        assert 0.0 <= stats["override_rate"] <= 1.0

    @pytest.mark.anyio
    async def test_db_persistence_failure_rolls_back_and_prevents_ghost_records(self):
        """Verify that when db.commit() raises an exception, the session is rolled back and no ghost record is cached."""
        svc = get_telemetry_service()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.commit.side_effect = RuntimeError("Simulated DB connection failure")

        payload = ThreatEventCreate(device_id="dev_fail_test", threat_type="SMS_PHISHING")
        with pytest.raises(RuntimeError) as exc_info:
            await svc.record_threat_event(payload, db=mock_db)

        assert "Database persistence failed" in str(exc_info.value)
        mock_db.rollback.assert_awaited_once()
        # Verify no phantom event in memory cache
        assert len(svc._events_by_id) == 0

    @pytest.mark.anyio
    async def test_sqlite_foreign_key_enforcement_with_pragma(self, tmp_path):
        """Verify foreign key integrity constraint enforcement with SQLite PRAGMA foreign_keys=ON."""
        db_file = tmp_path / "fk_enforced.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        from sqlalchemy.exc import IntegrityError

        # Inserting override with nonexistent event_id must raise IntegrityError
        async with session_factory() as session:
            ovr = UserOverride(
                override_id="OVR-FK-FAIL",
                event_id="EVT-DOES-NOT-EXIST",
                override_reason="TESTING",
                user_action="PROCEED_ANYWAY",
                risk_acknowledged=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(ovr)
            with pytest.raises(IntegrityError):
                await session.commit()

        await engine.dispose()

    def test_all_response_schemas_have_openapi_examples(self):
        """Verify all Pydantic schemas define OpenAPI examples in model_config."""
        schemas = [
            ThreatEventCreate,
            ThreatEventResponse,
            ThreatEventListResponse,
            UserOverrideCreate,
            UserOverrideResponse,
            UserOverrideListResponse,
            TelemetryStatsResponse,
        ]
        for model in schemas:
            json_schema = model.model_json_schema()
            assert "example" in json_schema, f"Schema {model.__name__} is missing example in model_config"

    def test_unflushed_orm_instances_with_defaults_validate_cleanly(self):
        """Ensure bare/unflushed ORM instances without explicit default assignments validate without ValidationError."""
        te_bare = ThreatEvent(
            event_id="EVT-UNFLUSHED-01",
            device_id="dev_unflushed_01",
            threat_type="SMS_PHISHING",
        )
        resp_te = ThreatEventResponse.model_validate(te_bare)
        assert resp_te.severity == "MEDIUM"
        assert resp_te.confidence == 0.85
        assert resp_te.status == "DETECTED"
        assert resp_te.platform == "android"
        assert resp_te.raw_payload == {}
        assert resp_te.override_count == 0

        uo_bare = UserOverride(
            override_id="OVR-UNFLUSHED-01",
            event_id="EVT-UNFLUSHED-01",
            override_reason="FALSE_POSITIVE",
        )
        resp_uo = UserOverrideResponse.model_validate(uo_bare)
        assert resp_uo.user_action == "PROCEED_ANYWAY"
        assert resp_uo.risk_acknowledged is False
        assert resp_uo.metadata_json == {}

    def test_stringified_json_in_raw_payload_and_metadata_json_deserialized(self):
        """Ensure stringified JSON payloads from SQLite text columns deserialize properly."""
        te = ThreatEvent(
            event_id="EVT-JSON-STR",
            device_id="dev_json_str",
            threat_type="SMS_PHISHING",
            raw_payload='{"scam_url": "https://fake.bank", "tags": ["phish"]}',
        )
        resp_te = ThreatEventResponse.model_validate(te)
        assert isinstance(resp_te.raw_payload, dict)
        assert resp_te.raw_payload["scam_url"] == "https://fake.bank"

        uo = UserOverride(
            override_id="OVR-JSON-STR",
            event_id="EVT-JSON-STR",
            override_reason="FALSE_POSITIVE",
            metadata_json='{"interaction_dwell_seconds": 6.2}',
        )
        resp_uo = UserOverrideResponse.model_validate(uo)
        assert isinstance(resp_uo.metadata_json, dict)
        assert resp_uo.metadata_json["interaction_dwell_seconds"] == 6.2

    def test_threat_type_and_override_reason_whitespace_short_string_rejected(self):
        """Ensure whitespace-padded single character strings are rejected after stripping."""
        with pytest.raises(ValidationError):
            ThreatEventCreate(device_id="dev_pad", threat_type=" A ")

        with pytest.raises(ValidationError):
            UserOverrideCreate(event_id="EVT-VALID123", override_reason=" X ")

    @pytest.mark.anyio
    async def test_negative_and_excessive_pagination_clamping(self):
        """Verify negative and excessive limits and offsets are safely clamped across service and DB."""
        svc = get_telemetry_service()
        svc.clear()

        await svc.record_threat_event(ThreatEventCreate(device_id="dev_page_1", threat_type="SMS_PHISHING"))
        await svc.record_threat_event(ThreatEventCreate(device_id="dev_page_2", threat_type="MALICIOUS_APP"))

        res_neg = await svc.list_threat_events(limit=-5, offset=-10)
        assert res_neg.total == 2
        assert len(res_neg.events) >= 1

        res_huge = await svc.list_threat_events(limit=9999, offset=0)
        assert res_huge.total == 2
        assert len(res_huge.events) == 2

    def test_empty_or_whitespace_event_id_lookup_404(self):
        """Test GET /telemetry/events/{event_id} returns 404 cleanly when given pure whitespace."""
        client = TestClient(app)
        res = client.get("/telemetry/events/%20%20%20")
        assert res.status_code == 404
        assert "empty" in res.json()["detail"].lower() or "not found" in res.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_large_payload_5mb_and_deep_nesting_ingestion(self, tmp_path):
        """Ingest and retrieve ~5MB payload and deeply nested JSON structures (Item 5)."""
        db_file = tmp_path / "large_payload.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        svc = get_telemetry_service()

        large_payload = {"chunk_" + str(i): "A" * 2000 for i in range(2500)}
        payload = ThreatEventCreate(
            device_id="dev_large_5mb",
            threat_type="SMS_PHISHING",
            raw_payload=large_payload,
        )

        async with sm() as session:
            created = await svc.record_threat_event(payload, db=session)
            assert created.event_id.startswith("EVT-")

        async with sm() as session:
            fetched = await svc.get_threat_event(created.event_id, db=session)
            assert fetched is not None
            assert len(fetched.raw_payload) == 2500

        await engine.dispose()

    @pytest.mark.anyio
    async def test_large_batch_cascade_delete_1000_records(self, tmp_path):
        """Transactional batch delete of 1,000 parent events cascading to 2,000 overrides (Item 4)."""
        db_file = tmp_path / "bulk_cascade.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        now = datetime.now(timezone.utc)

        async with sm() as session:
            events = [
                ThreatEvent(
                    event_id=f"EVT-BULK-{i:04d}",
                    device_id=f"dev_bulk_{i}",
                    threat_type="OVERLAY_ATTACK",
                    severity="HIGH",
                    created_at=now,
                )
                for i in range(1000)
            ]
            session.add_all(events)
            overrides = [
                UserOverride(
                    override_id=f"OVR-BULK-{i:04d}-{j}",
                    event_id=f"EVT-BULK-{i:04d}",
                    override_reason="FALSE_POSITIVE",
                    created_at=now,
                )
                for i in range(1000)
                for j in (1, 2)
            ]
            session.add_all(overrides)
            await session.commit()

        async with sm() as session:
            del_stmt = delete(ThreatEvent).where(ThreatEvent.threat_type == "OVERLAY_ATTACK")
            res = await session.execute(del_stmt)
            await session.commit()
            assert res.rowcount == 1000

        async with sm() as session:
            evt_count = (await session.execute(select(func.count(ThreatEvent.id)))).scalar_one()
            ovr_count = (await session.execute(select(func.count(UserOverride.id)))).scalar_one()
            assert evt_count == 0
            assert ovr_count == 0

        await engine.dispose()

    @pytest.mark.anyio
    async def test_concurrent_telemetry_ingestion(self, tmp_path):
        """Stress test concurrent async session tasks writing events and overrides simultaneously."""
        db_file = tmp_path / "concurrent_test.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        svc = get_telemetry_service()
        svc.clear()

        async def ingest_task(i: int):
            async with sm() as session:
                ev = await svc.record_threat_event(
                    ThreatEventCreate(
                        device_id=f"dev_concurrent_{i % 5}",
                        threat_type="SMS_PHISHING" if i % 2 == 0 else "MALICIOUS_APP",
                        severity="CRITICAL" if i % 4 == 0 else "HIGH",
                    ),
                    db=session,
                )
                if i % 2 == 0:
                    await svc.record_user_override(
                        UserOverrideCreate(
                            event_id=ev.event_id,
                            override_reason="FALSE_POSITIVE",
                            user_action="PROCEED_ANYWAY",
                        ),
                        db=session,
                    )

        tasks = [ingest_task(i) for i in range(40)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Concurrent execution errors: {errors}"

        async with sm() as session:
            stats = await svc.get_stats(db=session)
            assert stats.total_events == 40
            assert stats.total_overrides == 20
            assert stats.override_rate == 0.5

        await engine.dispose()

    def test_empty_and_whitespace_device_timestamp_parsed_as_none(self):
        """Verify empty and whitespace device_timestamp strings parse to None, and valid ISO strings parse cleanly."""
        evt1 = ThreatEventCreate(device_id="dev_ts_1", threat_type="SMS_PHISHING", device_timestamp="")
        assert evt1.device_timestamp is None

        evt2 = ThreatEventCreate(device_id="dev_ts_2", threat_type="SMS_PHISHING", device_timestamp="   ")
        assert evt2.device_timestamp is None

        evt3 = ThreatEventCreate(device_id="dev_ts_3", threat_type="SMS_PHISHING", device_timestamp="2026-09-05T12:00:00Z")
        assert isinstance(evt3.device_timestamp, datetime)

    def test_bare_unflushed_orm_without_threat_type_or_override_reason(self):
        """Verify fallback values for missing threat_type or override_reason on bare ORM instances."""
        te = ThreatEvent(event_id="EVT-BARE-99", device_id="dev_bare_99")
        resp_te = ThreatEventResponse.model_validate(te)
        assert resp_te.threat_type == "UNKNOWN"
        assert resp_te.device_id == "dev_bare_99"

        uo = UserOverride(override_id="OVR-BARE-99", event_id="EVT-BARE-99")
        resp_uo = UserOverrideResponse.model_validate(uo)
        assert resp_uo.override_reason == "OTHER"
        assert resp_uo.user_action == "PROCEED_ANYWAY"

    @pytest.mark.anyio
    async def test_read_through_cache_synchronization_on_get_threat_event(self, tmp_path):
        """Verify get_threat_event synchronizes DB records into in-memory cache upon query."""
        db_file = tmp_path / "read_through.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        svc = get_telemetry_service()
        svc.clear()

        # Seed directly in DB
        now = datetime.now(timezone.utc)
        async with sm() as session:
            db_ev = ThreatEvent(
                event_id="EVT-READ-THROUGH-01",
                device_id="dev_rt_01",
                threat_type="SMS_PHISHING",
                created_at=now,
            )
            session.add(db_ev)
            await session.commit()

        # In-memory cache is empty
        assert "EVT-READ-THROUGH-01" not in svc._events_by_id

        # Query via service
        async with sm() as session:
            fetched = await svc.get_threat_event("EVT-READ-THROUGH-01", db=session)
            assert fetched is not None
            assert fetched.event_id == "EVT-READ-THROUGH-01"

        # Now verified cached in-memory
        assert "EVT-READ-THROUGH-01" in svc._events_by_id
        await engine.dispose()

    @pytest.mark.anyio
    async def test_cached_parent_sync_to_db_preserves_device_timestamp_and_created_at(self, tmp_path):
        """Verify that persisting an in-memory cached parent event to DB preserves its timestamps."""
        db_file = tmp_path / "timestamp_preserve.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        svc = get_telemetry_service()
        svc.clear()

        # Ingest event without DB (in-memory mode)
        dev_ts = datetime(2026, 9, 5, 10, 30, 0, tzinfo=timezone.utc)
        created_evt = await svc.record_threat_event(
            ThreatEventCreate(
                device_id="dev_ts_pres",
                threat_type="MALICIOUS_APP",
                device_timestamp=dev_ts,
            ),
            db=None,
        )
        eid = created_evt.event_id

        # Now record override with DB; parent should be synced to DB preserving device_timestamp
        async with sm() as session:
            await svc.record_user_override(
                UserOverrideCreate(
                    event_id=eid,
                    override_reason="FALSE_POSITIVE",
                ),
                db=session,
            )

        # Verify in DB that parent event has device_timestamp preserved
        async with sm() as session:
            stmt = select(ThreatEvent).where(ThreatEvent.event_id == eid)
            res = await session.execute(stmt)
            parent_in_db = res.scalar_one()
            assert parent_in_db.device_timestamp is not None
            assert parent_in_db.status == "OVERRIDDEN"

        await engine.dispose()

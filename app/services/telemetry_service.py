"""Service layer for on-device threat telemetry ingestion and user override management.

Provides thread-safe in-memory caching and persistent PostgreSQL/SQLite storage
via SQLAlchemy 2.0 AsyncSession. Supports graceful fallback when database is offline.
"""
from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = Any  # type: ignore
    select = None  # type: ignore
    func = None  # type: ignore

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
    utcnow,
)

logger = logging.getLogger("sampati.services.telemetry")


class TelemetryService:
    """Thread-safe telemetry and override aggregation engine with async DB backing."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events_by_id: Dict[str, Dict[str, Any]] = {}
        self._overrides_by_id: Dict[str, Dict[str, Any]] = {}
        self._event_order: List[str] = []
        self._override_order: List[str] = []

    def clear(self) -> None:
        """Reset all in-memory telemetry state for testing."""
        with self._lock:
            self._events_by_id.clear()
            self._overrides_by_id.clear()
            self._event_order.clear()
            self._override_order.clear()

    # ── Threat Event Operations ───────────────────────────────────────────────

    async def record_threat_event(
        self,
        payload: ThreatEventCreate,
        db: Optional[AsyncSession] = None,
    ) -> ThreatEventResponse:
        """Ingest a new threat telemetry event and persist to DB/cache."""
        event_id = f"EVT-{uuid.uuid4().hex[:12].upper()}"
        now = utcnow()
        created_at_iso = now.isoformat()

        dev_ts_str: Optional[str] = None
        if payload.device_timestamp:
            if isinstance(payload.device_timestamp, datetime):
                dev_ts_str = payload.device_timestamp.isoformat()
            else:
                dev_ts_str = str(payload.device_timestamp)

        event_data: Dict[str, Any] = {
            "event_id": event_id,
            "device_id": payload.device_id,
            "user_id": payload.user_id,
            "threat_type": payload.threat_type,
            "severity": payload.severity,
            "confidence": float(payload.confidence),
            "status": payload.status,
            "action_taken": payload.action_taken,
            "package_name": payload.package_name,
            "platform": payload.platform,
            "app_version": payload.app_version,
            "os_version": payload.os_version,
            "threat_source": payload.threat_source,
            "vpa": payload.vpa,
            "phone_number": payload.phone_number,
            "raw_payload": payload.raw_payload or {},
            "device_timestamp": dev_ts_str,
            "created_at": created_at_iso,
            "override_count": 0,
        }

        # Persist to database if session available
        if db is not None and SQLALCHEMY_AVAILABLE:
            try:
                db_model = ThreatEvent(
                    event_id=event_id,
                    device_id=payload.device_id,
                    user_id=payload.user_id,
                    threat_type=payload.threat_type,
                    severity=payload.severity,
                    confidence=float(payload.confidence),
                    status=payload.status,
                    action_taken=payload.action_taken,
                    package_name=payload.package_name,
                    platform=payload.platform,
                    app_version=payload.app_version,
                    os_version=payload.os_version,
                    threat_source=payload.threat_source,
                    vpa=payload.vpa,
                    phone_number=payload.phone_number,
                    raw_payload=payload.raw_payload or {},
                    device_timestamp=payload.device_timestamp,
                    created_at=now,
                )
                db.add(db_model)
                await db.commit()
                await db.refresh(db_model)
                logger.info("Persisted threat event %s to database", event_id)
            except Exception as exc:
                await db.rollback()
                logger.error("Failed to persist threat event %s to database: %s", event_id, exc)
                raise RuntimeError(f"Database persistence failed: {exc}") from exc

        # Cache in-memory only after successful DB persist or when in offline mode
        with self._lock:
            self._events_by_id[event_id] = event_data
            self._event_order.append(event_id)

        return ThreatEventResponse(**event_data)

    async def get_threat_event(
        self,
        event_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[ThreatEventResponse]:
        """Retrieve a specific threat event by unique event_id."""
        target_id = event_id.strip().upper() if (event_id and event_id.strip()) else ""
        if not target_id:
            return None
        if db is not None and SQLALCHEMY_AVAILABLE:
            try:
                stmt = select(ThreatEvent).where(ThreatEvent.event_id == target_id)
                res = await db.execute(stmt)
                model = res.scalar_one_or_none()
                if model:
                    resp = ThreatEventResponse.model_validate(model)
                    with self._lock:
                        if target_id not in self._events_by_id:
                            self._events_by_id[target_id] = resp.model_dump()
                            if target_id not in self._event_order:
                                self._event_order.append(target_id)
                    return resp
            except Exception as exc:
                logger.warning("DB lookup failed for event %s: %s", target_id, exc)

        # Fallback to in-memory cache
        with self._lock:
            data = self._events_by_id.get(target_id)
            if data:
                return ThreatEventResponse(**data)
        return None

    async def list_threat_events(
        self,
        limit: int = 50,
        offset: int = 0,
        device_id: Optional[str] = None,
        threat_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> ThreatEventListResponse:
        """List and filter threat events with pagination."""
        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        norm_device = device_id.strip() if (device_id and device_id.strip()) else None
        norm_type = threat_type.strip().upper() if (threat_type and threat_type.strip()) else None
        norm_sev = severity.strip().upper() if (severity and severity.strip()) else None
        norm_status = status.strip().upper() if (status and status.strip()) else None

        if db is not None and SQLALCHEMY_AVAILABLE:
            try:
                stmt = select(ThreatEvent)
                count_stmt = select(func.count(ThreatEvent.id))

                if norm_device:
                    stmt = stmt.where(ThreatEvent.device_id == norm_device)
                    count_stmt = count_stmt.where(ThreatEvent.device_id == norm_device)
                if norm_type:
                    stmt = stmt.where(ThreatEvent.threat_type == norm_type)
                    count_stmt = count_stmt.where(ThreatEvent.threat_type == norm_type)
                if norm_sev:
                    stmt = stmt.where(ThreatEvent.severity == norm_sev)
                    count_stmt = count_stmt.where(ThreatEvent.severity == norm_sev)
                if norm_status:
                    stmt = stmt.where(ThreatEvent.status == norm_status)
                    count_stmt = count_stmt.where(ThreatEvent.status == norm_status)

                total_res = await db.execute(count_stmt)
                total = total_res.scalar_one() or 0

                stmt = stmt.order_by(ThreatEvent.created_at.desc()).offset(safe_offset).limit(safe_limit)
                rows_res = await db.execute(stmt)
                models = rows_res.scalars().all()

                events = [ThreatEventResponse.model_validate(m) for m in models]
                return ThreatEventListResponse(total=total, events=events)
            except Exception as exc:
                logger.warning("DB list failed for threat events: %s. Falling back to cache.", exc)

        # Fallback to in-memory cache
        with self._lock:
            filtered: List[Dict[str, Any]] = []
            for eid in reversed(self._event_order):
                item = self._events_by_id.get(eid)
                if item is None:
                    continue
                if norm_device and item.get("device_id") != norm_device:
                    continue
                if norm_type and item.get("threat_type") != norm_type:
                    continue
                if norm_sev and item.get("severity") != norm_sev:
                    continue
                if norm_status and item.get("status") != norm_status:
                    continue
                filtered.append(item)

            total = len(filtered)
            paginated = filtered[safe_offset : safe_offset + safe_limit]
            return ThreatEventListResponse(
                total=total,
                events=[ThreatEventResponse(**d) for d in paginated],
            )

    # ── User Override Operations ──────────────────────────────────────────────

    async def record_user_override(
        self,
        payload: UserOverrideCreate,
        db: Optional[AsyncSession] = None,
    ) -> UserOverrideResponse:
        """Record user/analyst override against an existing threat event."""
        target_event_id = payload.event_id.strip().upper()
        parent_model: Optional[ThreatEvent] = None
        override_id = f"OVR-{uuid.uuid4().hex[:12].upper()}"
        now = utcnow()
        created_at_iso = now.isoformat()

        # Check DB first if session available
        if db is not None and SQLALCHEMY_AVAILABLE:
            try:
                stmt = select(ThreatEvent).where(ThreatEvent.event_id == target_event_id)
                res = await db.execute(stmt)
                parent_model = res.scalar_one_or_none()
            except Exception as exc:
                logger.warning("DB check for parent event %s failed: %s", target_event_id, exc)

        # If not in DB, check in-memory cache
        cached_parent: Optional[Dict[str, Any]] = None
        with self._lock:
            cached_parent = self._events_by_id.get(target_event_id)

        if parent_model is None and cached_parent is None:
            raise KeyError(f"Threat event '{target_event_id}' not found")

        override_data: Dict[str, Any] = {
            "override_id": override_id,
            "event_id": target_event_id,
            "user_id": payload.user_id,
            "device_id": payload.device_id,
            "override_reason": payload.override_reason,
            "user_action": payload.user_action,
            "feedback_notes": payload.feedback_notes,
            "risk_acknowledged": payload.risk_acknowledged,
            "metadata_json": payload.metadata_json or {},
            "created_at": created_at_iso,
        }

        # Persist to database first
        if db is not None and SQLALCHEMY_AVAILABLE:
            try:
                # If parent was only in cache, persist parent to DB first to satisfy foreign key
                if parent_model is None and cached_parent is not None:
                    cached_dev_ts = None
                    if cached_parent.get("device_timestamp"):
                        try:
                            cached_dev_ts = datetime.fromisoformat(cached_parent["device_timestamp"])
                        except Exception:
                            cached_dev_ts = None

                    cached_created_at = now
                    if cached_parent.get("created_at"):
                        try:
                            cached_created_at = datetime.fromisoformat(cached_parent["created_at"])
                        except Exception:
                            cached_created_at = now

                    parent_model = ThreatEvent(
                        event_id=target_event_id,
                        device_id=cached_parent["device_id"],
                        user_id=cached_parent.get("user_id"),
                        threat_type=cached_parent["threat_type"],
                        severity=cached_parent["severity"],
                        confidence=float(cached_parent["confidence"]),
                        status="OVERRIDDEN",
                        action_taken=cached_parent.get("action_taken"),
                        package_name=cached_parent.get("package_name"),
                        platform=cached_parent.get("platform", "android"),
                        app_version=cached_parent.get("app_version"),
                        os_version=cached_parent.get("os_version"),
                        threat_source=cached_parent.get("threat_source", "on_device_scanner"),
                        vpa=cached_parent.get("vpa"),
                        phone_number=cached_parent.get("phone_number"),
                        raw_payload=cached_parent.get("raw_payload", {}),
                        device_timestamp=cached_dev_ts,
                        created_at=cached_created_at,
                    )
                    db.add(parent_model)
                elif parent_model is not None:
                    parent_model.status = "OVERRIDDEN"

                db_override = UserOverride(
                    override_id=override_id,
                    event_id=target_event_id,
                    user_id=payload.user_id,
                    device_id=payload.device_id,
                    override_reason=payload.override_reason,
                    user_action=payload.user_action,
                    feedback_notes=payload.feedback_notes,
                    risk_acknowledged=payload.risk_acknowledged,
                    metadata_json=payload.metadata_json or {},
                    created_at=now,
                )
                db.add(db_override)
                await db.commit()
                await db.refresh(db_override)
                logger.info("Persisted user override %s for event %s", override_id, target_event_id)
            except Exception as exc:
                await db.rollback()
                logger.error("Failed to persist user override %s to database: %s", override_id, exc)
                raise RuntimeError(f"Database persistence failed: {exc}") from exc

        # Update in-memory cache only after DB commit succeeds or in in-memory mode
        with self._lock:
            self._overrides_by_id[override_id] = override_data
            self._override_order.append(override_id)
            if target_event_id in self._events_by_id:
                self._events_by_id[target_event_id]["override_count"] = (
                    self._events_by_id[target_event_id].get("override_count", 0) + 1
                )
                self._events_by_id[target_event_id]["status"] = "OVERRIDDEN"
            elif parent_model is not None:
                self._events_by_id[target_event_id] = parent_model.to_dict()
                self._events_by_id[target_event_id]["status"] = "OVERRIDDEN"
                self._events_by_id[target_event_id]["override_count"] = parent_model.override_count
                if target_event_id not in self._event_order:
                    self._event_order.append(target_event_id)

        return UserOverrideResponse(**override_data)

    async def list_user_overrides(
        self,
        limit: int = 50,
        offset: int = 0,
        event_id: Optional[str] = None,
        user_id: Optional[str] = None,
        override_reason: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> UserOverrideListResponse:
        """List and filter user overrides with pagination."""
        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        norm_event = event_id.strip().upper() if (event_id and event_id.strip()) else None
        norm_user = user_id.strip() if (user_id and user_id.strip()) else None
        norm_reason = override_reason.strip().upper() if (override_reason and override_reason.strip()) else None

        if db is not None and SQLALCHEMY_AVAILABLE:
            try:
                stmt = select(UserOverride)
                count_stmt = select(func.count(UserOverride.id))

                if norm_event:
                    stmt = stmt.where(UserOverride.event_id == norm_event)
                    count_stmt = count_stmt.where(UserOverride.event_id == norm_event)
                if norm_user:
                    stmt = stmt.where(UserOverride.user_id == norm_user)
                    count_stmt = count_stmt.where(UserOverride.user_id == norm_user)
                if norm_reason:
                    stmt = stmt.where(UserOverride.override_reason == norm_reason)
                    count_stmt = count_stmt.where(UserOverride.override_reason == norm_reason)

                total_res = await db.execute(count_stmt)
                total = total_res.scalar_one() or 0

                stmt = stmt.order_by(UserOverride.created_at.desc()).offset(safe_offset).limit(safe_limit)
                rows_res = await db.execute(stmt)
                models = rows_res.scalars().all()

                overrides = [UserOverrideResponse.model_validate(m) for m in models]
                return UserOverrideListResponse(total=total, overrides=overrides)
            except Exception as exc:
                logger.warning("DB list failed for overrides: %s. Falling back to cache.", exc)

        # Fallback to in-memory cache
        with self._lock:
            filtered: List[Dict[str, Any]] = []
            for oid in reversed(self._override_order):
                item = self._overrides_by_id.get(oid)
                if item is None:
                    continue
                if norm_event and item.get("event_id") != norm_event:
                    continue
                if norm_user and item.get("user_id") != norm_user:
                    continue
                if norm_reason and item.get("override_reason") != norm_reason:
                    continue
                filtered.append(item)

            total = len(filtered)
            paginated = filtered[safe_offset : safe_offset + safe_limit]
            return UserOverrideListResponse(
                total=total,
                overrides=[UserOverrideResponse(**d) for d in paginated],
            )

    # ── Telemetry Aggregate Statistics ────────────────────────────────────────

    async def get_stats(self, db: Optional[AsyncSession] = None) -> TelemetryStatsResponse:
        """Compute aggregated telemetry metrics and override distribution."""
        if db is not None and SQLALCHEMY_AVAILABLE:
            try:
                tot_events = (await db.execute(select(func.count(ThreatEvent.id)))).scalar_one() or 0
                tot_overrides = (await db.execute(select(func.count(UserOverride.id)))).scalar_one() or 0

                # Count distinct events marked as OVERRIDDEN
                overridden_res = await db.execute(
                    select(func.count(ThreatEvent.id)).where(ThreatEvent.status == "OVERRIDDEN")
                )
                overridden_count = overridden_res.scalar_one() or 0

                # Severity breakdown
                sev_res = await db.execute(
                    select(ThreatEvent.severity, func.count(ThreatEvent.id)).group_by(ThreatEvent.severity)
                )
                severity_map = {row[0]: row[1] for row in sev_res.all()}

                # Threat type breakdown
                type_res = await db.execute(
                    select(ThreatEvent.threat_type, func.count(ThreatEvent.id)).group_by(ThreatEvent.threat_type)
                )
                threat_type_map = {row[0]: row[1] for row in type_res.all()}

                # Reason breakdown
                rsn_res = await db.execute(
                    select(UserOverride.override_reason, func.count(UserOverride.id)).group_by(UserOverride.override_reason)
                )
                reason_map = {row[0]: row[1] for row in rsn_res.all()}

                # Active devices
                dev_res = await db.execute(select(func.count(func.distinct(ThreatEvent.device_id))))
                active_devs = dev_res.scalar_one() or 0

                raw_rate = float(overridden_count / tot_events) if tot_events > 0 else 0.0
                rate = min(1.0, max(0.0, raw_rate))
                return TelemetryStatsResponse(
                    total_events=tot_events,
                    total_overrides=tot_overrides,
                    override_rate=round(rate, 4),
                    severity_breakdown=severity_map,
                    threat_type_breakdown=threat_type_map,
                    override_reason_breakdown=reason_map,
                    active_devices_count=active_devs,
                )
            except Exception as exc:
                logger.warning("DB stats computation failed: %s. Falling back to in-memory stats.", exc)

        with self._lock:
            tot_events = len(self._events_by_id)
            tot_overrides = len(self._overrides_by_id)
            overridden_count = sum(
                1 for ev in self._events_by_id.values()
                if ev.get("status") == "OVERRIDDEN" or ev.get("override_count", 0) > 0
            )
            sev_counts: Dict[str, int] = {}
            type_counts: Dict[str, int] = {}
            reason_counts: Dict[str, int] = {}
            unique_devices = set()

            for ev in self._events_by_id.values():
                s = ev.get("severity", "MEDIUM")
                sev_counts[s] = sev_counts.get(s, 0) + 1
                t = ev.get("threat_type", "UNKNOWN")
                type_counts[t] = type_counts.get(t, 0) + 1
                dev = ev.get("device_id")
                if dev:
                    unique_devices.add(dev)

            for ov in self._overrides_by_id.values():
                r = ov.get("override_reason", "OTHER")
                reason_counts[r] = reason_counts.get(r, 0) + 1

            raw_rate = float(overridden_count / tot_events) if tot_events > 0 else 0.0
            rate = min(1.0, max(0.0, raw_rate))
            return TelemetryStatsResponse(
                total_events=tot_events,
                total_overrides=tot_overrides,
                override_rate=round(rate, 4),
                severity_breakdown=sev_counts,
                threat_type_breakdown=type_counts,
                override_reason_breakdown=reason_counts,
                active_devices_count=len(unique_devices),
            )


# Global singleton instance
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Retrieve or initialize the global TelemetryService singleton."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service

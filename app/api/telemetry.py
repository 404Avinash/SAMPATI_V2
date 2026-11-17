"""FastAPI Router for Telemetry & On-Device Threat Logging.

Endpoints:
- POST /events: Ingest on-device threat telemetry events (e.g. SMS phishing, malicious app)
- POST /overrides: Record user or investigator feedback override on a threat event
- GET /events: Query and filter ingested threat telemetry events with pagination
- GET /events/{event_id}: Retrieve detailed threat event metadata
- GET /overrides: Query and filter user overrides with pagination
- GET /stats: Retrieve aggregate telemetry counters and override distribution metrics
"""
from __future__ import annotations

import logging
from typing import Any, Optional

try:
    from fastapi import APIRouter, Depends, HTTPException, Query, status
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    class APIRouter:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.routes = []

        def get(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

        def post(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

    def Depends(f=None):  # type: ignore
        return None

    def Query(default=None, **kwargs):  # type: ignore
        return default

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: Any = None):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")

    class status:  # type: ignore
        HTTP_200_OK = 200
        HTTP_201_CREATED = 201
        HTTP_404_NOT_FOUND = 404
        HTTP_422_UNPROCESSABLE_ENTITY = 422
        HTTP_500_INTERNAL_SERVER_ERROR = 500

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = Any  # type: ignore

try:
    from app.db.session import get_db
except Exception:
    async def get_db():  # type: ignore
        yield None

from app.models.telemetry import (
    TelemetryStatsResponse,
    ThreatEventCreate,
    ThreatEventListResponse,
    ThreatEventResponse,
    UserOverrideCreate,
    UserOverrideListResponse,
    UserOverrideResponse,
)
from app.services.telemetry_service import get_telemetry_service

logger = logging.getLogger("sampati.api.telemetry")

router = APIRouter(tags=["Telemetry"])


@router.post(
    "/events",
    response_model=ThreatEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest on-device threat telemetry event",
    description=(
        "Ingest a real-time on-device threat detection event (e.g. SMS phishing, "
        "malicious app, screen overlay attack, accessibility service abuse). "
        "Records event details, triggers automated risk categorization, and stores "
        "persistently in database with async connection pooling."
    ),
    responses={
        201: {
            "description": "Threat event successfully ingested and recorded",
            "model": ThreatEventResponse,
        },
        422: {
            "description": "Validation error on payload schema or field constraints",
        },
    },
)
async def ingest_threat_event(
    payload: ThreatEventCreate,
    db: Optional[AsyncSession] = Depends(get_db),
) -> ThreatEventResponse:
    """Ingest an on-device threat detection telemetry record."""
    try:
        service = get_telemetry_service()
        return await service.record_threat_event(payload, db=db)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to ingest threat event: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error ingesting threat event: {exc}",
        )


@router.post(
    "/overrides",
    response_model=UserOverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record user or investigator threat override",
    description=(
        "Log a user or compliance investigator override on a detected threat event. "
        "Records user action (e.g. PROCEED_ANYWAY, REPORT_SAFE), override reason "
        "(FALSE_POSITIVE, USER_CONSENT), notes, and risk acknowledgment state. "
        "Updates parent event lifecycle state and persists to database."
    ),
    responses={
        201: {
            "description": "User override successfully recorded and linked",
            "model": UserOverrideResponse,
        },
        404: {
            "description": "Referenced threat event ID does not exist",
        },
        422: {
            "description": "Validation error on payload schema or field constraints",
        },
    },
)
async def record_user_override(
    payload: UserOverrideCreate,
    db: Optional[AsyncSession] = Depends(get_db),
) -> UserOverrideResponse:
    """Record a user or investigator feedback override on an existing threat event."""
    try:
        service = get_telemetry_service()
        return await service.record_user_override(payload, db=db)
    except KeyError as key_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(key_err).strip("'"),
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to record user override: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error recording user override: {exc}",
        )


@router.get(
    "/events",
    response_model=ThreatEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="List threat telemetry events",
    description=(
        "Retrieve paginated list of on-device threat telemetry events with optional "
        "filtering by device_id, threat_type, severity, and status."
    ),
)
async def list_threat_events(
    limit: int = Query(default=50, ge=1, le=500, description="Max events to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    device_id: Optional[str] = Query(default=None, description="Filter by reporting device ID"),
    threat_type: Optional[str] = Query(default=None, description="Filter by threat category"),
    severity: Optional[str] = Query(default=None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status: DETECTED, BLOCKED, WARNED, IGNORED, OVERRIDDEN, RESOLVED"),
    db: Optional[AsyncSession] = Depends(get_db),
) -> ThreatEventListResponse:
    """List ingested threat telemetry events with filtering and pagination."""
    try:
        service = get_telemetry_service()
        return await service.list_threat_events(
            limit=limit,
            offset=offset,
            device_id=device_id,
            threat_type=threat_type,
            severity=severity,
            status=status_filter,
            db=db,
        )
    except Exception as exc:
        logger.exception("Failed to list threat events: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error listing threat events: {exc}",
        )


@router.get(
    "/events/{event_id}",
    response_model=ThreatEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get threat telemetry event details",
    description="Retrieve full metadata for a specific threat telemetry event by its EVT-XXXXXXXX identifier.",
    responses={
        200: {
            "description": "Threat event details successfully retrieved",
            "model": ThreatEventResponse,
        },
        404: {
            "description": "Threat event with specified event_id not found",
        },
    },
)
async def get_threat_event(
    event_id: str,
    db: Optional[AsyncSession] = Depends(get_db),
) -> ThreatEventResponse:
    """Retrieve full details of a specific threat telemetry event."""
    try:
        norm_id = event_id.strip().upper()
        if not norm_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Threat event ID cannot be empty",
            )
        service = get_telemetry_service()
        event = await service.get_threat_event(norm_id, db=db)
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Threat event '{norm_id}' not found",
            )
        return event
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve threat event %s: %s", event_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error retrieving threat event: {exc}",
        )


@router.get(
    "/overrides",
    response_model=UserOverrideListResponse,
    status_code=status.HTTP_200_OK,
    summary="List threat event user overrides",
    description="Retrieve paginated list of user or investigator overrides with optional filtering.",
)
async def list_user_overrides(
    limit: int = Query(default=50, ge=1, le=500, description="Max overrides to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    event_id: Optional[str] = Query(default=None, description="Filter by target threat event ID"),
    user_id: Optional[str] = Query(default=None, description="Filter by submitting user ID"),
    override_reason: Optional[str] = Query(default=None, description="Filter by override reason"),
    db: Optional[AsyncSession] = Depends(get_db),
) -> UserOverrideListResponse:
    """List recorded user overrides with filtering and pagination."""
    try:
        service = get_telemetry_service()
        return await service.list_user_overrides(
            limit=limit,
            offset=offset,
            event_id=event_id,
            user_id=user_id,
            override_reason=override_reason,
            db=db,
        )
    except Exception as exc:
        logger.exception("Failed to list user overrides: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error listing user overrides: {exc}",
        )


@router.get(
    "/stats",
    response_model=TelemetryStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregate telemetry and override statistics",
    description=(
        "Compute high-level summary metrics across all ingested threat events and "
        "user overrides, including breakdown by severity, threat category, override "
        "reason, and count of distinct active reporting devices."
    ),
)
async def get_telemetry_stats(
    db: Optional[AsyncSession] = Depends(get_db),
) -> TelemetryStatsResponse:
    """Retrieve aggregate telemetry and override statistics."""
    try:
        service = get_telemetry_service()
        return await service.get_stats(db=db)
    except Exception as exc:
        logger.exception("Failed to get telemetry stats: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error computing telemetry stats: {exc}",
        )

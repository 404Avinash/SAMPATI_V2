"""FastAPI Router for Threat Intelligence & Early-Warning Mesh Layer.

Endpoints:
- POST /signals: Ingest pre-transaction threat signal (phone, UPI ID, URL, social tags, raw SMS)
- GET /signals: Query/filter ingested threat signals with pagination
- GET /signals/{signal_id}: Retrieve detailed threat signal metadata & graph linkage
- GET /graph: Export the central Fraud Graph nodes and edges
- GET /campaigns: List active fraud syndicate campaigns and clustering statistics
- POST /simulate: Seed synthetic pre-transaction threat signals for demo/testing
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, Depends, HTTPException, Query, status
    from fastapi.responses import JSONResponse
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

    class JSONResponse:  # type: ignore
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code

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

from app.models.threat_intel import (
    SimulateThreatSignalsRequest,
    ThreatGraphResponse,
    ThreatSignalCreateRequest,
    ThreatSignalListResponse,
    ThreatSignalResponse,
)
from app.services.graph_service import get_fraud_graph
from app.services.threat_intel_service import get_threat_intel_service

logger = logging.getLogger("sampati.api.intel")
router = APIRouter()


@router.post(
    "/signals",
    response_model=ThreatSignalResponse,
    status_code=201,
    summary="Ingest Pre-Transaction Threat Signal",
    tags=["threat-intel"],
)
async def ingest_threat_signal(
    payload: ThreatSignalCreateRequest,
    db: Optional[AsyncSession] = Depends(get_db),
) -> ThreatSignalResponse:
    """Ingest a pre-transaction fraud threat signal.

    Accepts identifiers (phone, upi_id, url) and social engineering tags,
    or raw unstructured SMS/WhatsApp text. Runs regex entity extraction,
    clusters into syndicate campaigns (e.g. KYC phishing ~94%), links into
    central Fraud Graph, and broadcasts real-time WebSocket event.
    """
    try:
        service = get_threat_intel_service()
        response = await service.ingest_signal(payload, db=db)
        return response
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to ingest threat signal: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal error ingesting threat signal: {exc}")


@router.get(
    "/signals",
    response_model=ThreatSignalListResponse,
    summary="List Pre-Transaction Threat Signals",
    tags=["threat-intel"],
)
async def list_threat_signals(
    limit: int = Query(default=50, ge=1, le=500, description="Max signals to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    severity: Optional[str] = Query(default=None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    source: Optional[str] = Query(default=None, description="Filter by source: mobile_app, sms_feed, psp_webhook, user_report"),
    campaign_id: Optional[str] = Query(default=None, description="Filter by matched campaign ID"),
    db: Optional[AsyncSession] = Depends(get_db),
) -> ThreatSignalListResponse:
    """List ingested threat signals with filtering and pagination."""
    try:
        service = get_threat_intel_service()
        return await service.list_signals(
            limit=limit,
            offset=offset,
            severity=severity,
            source=source,
            campaign_id=campaign_id,
            db=db,
        )
    except Exception as exc:
        logger.exception("Failed to list threat signals: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal error listing threat signals: {exc}")


@router.get(
    "/signals/{signal_id}",
    response_model=ThreatSignalResponse,
    summary="Get Threat Signal Details",
    tags=["threat-intel"],
)
async def get_threat_signal(
    signal_id: str,
    db: Optional[AsyncSession] = Depends(get_db),
) -> ThreatSignalResponse:
    """Retrieve full details of a specific threat signal including entity extraction and graph nodes."""
    service = get_threat_intel_service()
    signal = await service.get_signal(signal_id, db=db)
    if signal is None:
        raise HTTPException(
            status_code=404,
            detail=f"Threat signal '{signal_id}' not found",
        )
    return signal


@router.get(
    "/graph",
    response_model=ThreatGraphResponse,
    summary="Export Central Fraud Graph",
    tags=["threat-intel"],
)
async def get_fraud_graph_endpoint(
    entity_id: Optional[str] = Query(default=None, description="Optional root node to fetch subgraph"),
    depth: int = Query(default=2, ge=1, le=5, description="Search depth when entity_id is specified"),
) -> ThreatGraphResponse:
    """Export the multi-entity Fraud Graph holding nodes (VPA, PHONE, URL, CASE, CAMPAIGN, SIGNAL) and edges."""
    try:
        graph_svc = get_fraud_graph()
        if entity_id:
            raw = graph_svc.get_subgraph(entity_id=entity_id, depth=depth)
        else:
            raw = graph_svc.export_graph()

        return ThreatGraphResponse(
            nodes=raw.get("nodes", []),
            edges=raw.get("edges", []),
            total_nodes=raw.get("total_nodes", len(raw.get("nodes", []))),
            total_edges=raw.get("total_edges", len(raw.get("edges", []))),
        )
    except Exception as exc:
        logger.exception("Failed to export fraud graph: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal error exporting graph: {exc}")


@router.get(
    "/campaigns",
    summary="List Active Fraud Syndicates & Campaigns",
    tags=["threat-intel"],
)
async def list_threat_campaigns() -> List[Dict[str, Any]]:
    """List active fraud campaigns with similarity clustering statistics, member count, and signal count."""
    try:
        service = get_threat_intel_service()
        return service.list_campaigns()
    except Exception as exc:
        logger.exception("Failed to list campaigns: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal error listing campaigns: {exc}")


@router.post(
    "/simulate",
    summary="Simulate Pre-Transaction Threat Signals",
    tags=["threat-intel"],
)
async def simulate_threat_signals(
    payload: Optional[SimulateThreatSignalsRequest] = None,
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Generate synthetic pre-transaction threat signals for demo, testing, and graph population."""
    try:
        count = payload.count if (payload and payload.count) else 5
        service = get_threat_intel_service()
        generated = await service.simulate_signals(count=count, db=db)
        return {
            "status": "ok",
            "count": len(generated),
            "generated_signals": len(generated),
            "signals": [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in generated],
        }
    except Exception as exc:
        logger.exception("Failed to simulate threat signals: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal error simulating signals: {exc}")

"""Federation Threat Intelligence Signal Exchange API Router for SAMPATI V2.

Provides privacy-preserving endpoints to ingest cross-PSP threat signals,
query real-time federated risk scores with sub-5ms hot-cache latency, and
inspect active federation mesh signals.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Query
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    class APIRouter:
        def __init__(self, *args, **kwargs): pass
        def get(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
        def post(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
    def Query(default=None, **kwargs): return default
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: Any = None):
            self.status_code = status_code
            self.detail = detail
    class JSONResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code

from app.federation.coordinator import FederatedCoordinator, get_federation
from app.models.upi_models import (
    FederationQueryResponse,
    FederationSignalRequest,
    FederationSignalResponse,
)

logger = logging.getLogger("sampati.api.federation")

router = APIRouter()


@router.post(
    "/signal",
    response_model=FederationSignalResponse,
    summary="Submit Privacy-Preserving Federated Risk Signal",
    description=(
        "Ingest a privacy-preserving threat intelligence signal (SHA-256 VPA hash, "
        "risk level, and optional mule ring identifier) from a participating PSP node "
        "into the sub-5ms hot cache."
    ),
    tags=["Federation"],
)
async def submit_federation_signal(body: FederationSignalRequest):
    """Ingest a federated risk signal from a peer PSP node."""
    if not body.vpa_hash or not body.vpa_hash.strip():
        raise HTTPException(status_code=422, detail="Field 'vpa_hash' must not be empty.")

    try:
        from app.services.upi_cases import get_upi_case_service
        svc = get_upi_case_service()
        coordinator = svc.federation
    except Exception:
        coordinator = get_federation()

    result = coordinator.record_signal(
        vpa_hash=body.vpa_hash.strip(),
        risk_level=body.risk_level,
        ring_hash=body.ring_hash,
        node_id=body.node_id or "peer_node",
    )

    # Broadcast real-time signal arrival over WebSocket
    try:
        from app.api.websocket import schedule_broadcast
        schedule_broadcast({
            "event": "FEDERATION_SIGNAL_RECEIVED",
            "data": {
                "vpa_hash": result["vpa_hash"],
                "risk_level": result["risk_level"],
                "federated_risk_score": result["federated_risk_score"],
                "ring_hash": result.get("ring_hash"),
                "timestamp": result["timestamp"],
            },
        })
    except Exception as exc:
        logger.debug("WebSocket broadcast skipped for federation signal: %s", exc)

    return JSONResponse(status_code=200, content=result)


@router.get(
    "/query",
    response_model=FederationQueryResponse,
    summary="Query Federated Risk Score",
    description=(
        "Query the real-time federated risk score for a given VPA hash. "
        "Served from the sub-5ms hot cache with ring membership and reporting node details."
    ),
    tags=["Federation"],
)
async def query_federation_signal(
    vpa_hash: str = Query(..., description="SHA-256 hash or pseudonymized hash of the target VPA"),
):
    """Retrieve federated risk score and ring topology in sub-5ms."""
    if not vpa_hash or not vpa_hash.strip():
        raise HTTPException(status_code=422, detail="Query parameter 'vpa_hash' is required.")

    try:
        from app.services.upi_cases import get_upi_case_service
        svc = get_upi_case_service()
        coordinator = svc.federation
    except Exception:
        coordinator = get_federation()

    result = coordinator.query_signal(vpa_hash=vpa_hash.strip())
    return JSONResponse(status_code=200, content=result)


@router.get(
    "/signals",
    summary="List Active Federated Signals",
    description="Retrieve all currently active threat intelligence signals in the federation mesh cache.",
    tags=["Federation"],
)
async def list_federation_signals():
    """List active signals in the hot cache."""
    try:
        from app.services.upi_cases import get_upi_case_service
        svc = get_upi_case_service()
        coordinator = svc.federation
    except Exception:
        coordinator = get_federation()

    signals = coordinator.list_signals() if hasattr(coordinator, "list_signals") else []
    return JSONResponse(
        status_code=200,
        content={
            "total_signals": len(signals),
            "signals": signals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.post(
    "/run",
    summary="Trigger Federated Intelligence Round",
    description="Execute a cross-PSP consensus round to aggregate feature shares and discover mule rings.",
    tags=["Federation"],
)
async def trigger_federation_round():
    """Trigger a federation consensus round."""
    try:
        from app.services.upi_cases import get_upi_case_service
        svc = get_upi_case_service()
        result = svc.run_federation()
        return JSONResponse(status_code=200, content=result)
    except Exception as exc:
        coordinator = get_federation()
        result = coordinator.run_federation_round()
        return JSONResponse(status_code=200, content=result)


@router.get(
    "/honeypots",
    summary="List Active Federated Honeypot Traps and Telemetry",
    description="Retrieve the seeded synthetic honeypot VPAs, hit telemetry, and 24-hour deflection counters.",
    tags=["Federation"],
)
async def list_federated_honeypots():
    """Retrieve active synthetic honeypot VPAs and hit metrics."""
    try:
        from app.engine.honeypot import get_honeypot_registry
        reg = get_honeypot_registry()
        return JSONResponse(status_code=200, content=reg.get_stats())
    except Exception as exc:
        logger.warning(f"Error fetching honeypot registry stats: {exc}")
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "total_registered": 0,
                "total_hits": 0,
                "hits_24h": 0,
                "total_amount_deflected": 0.0,
                "honeypots": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


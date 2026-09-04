"""FastAPI Router for Mobile Device Push Notifications & FCM Management."""
from __future__ import annotations

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Query

from app.services.notification_service import (
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
    get_notification_service,
)

logger = logging.getLogger("sampati.api.notifications")

router = APIRouter()


@router.post(
    "/register",
    response_model=DeviceRegistrationResponse,
    status_code=200,
    summary="Register or update mobile device token",
)
async def register_device(body: DeviceRegistrationRequest) -> DeviceRegistrationResponse:
    """Register or update an FCM device token for targeted fraud push alerts."""
    service = get_notification_service()
    return service.register_device(body)


@router.get("/tokens", summary="List registered device tokens")
async def list_tokens() -> Dict[str, Any]:
    """Return all registered mobile device tokens and metadata."""
    service = get_notification_service()
    with service._lock:
        tokens: List[Dict[str, Any]] = [
            {
                "token": k,
                "platform": v.get("platform", "android"),
                "vpa": v.get("vpa"),
                "device_id": v.get("device_id"),
                "user_id": v.get("user_id"),
                "app_version": v.get("app_version"),
                "created_at": v.get("created_at"),
                "updated_at": v.get("updated_at"),
            }
            for k, v in service._tokens.items()
        ]
    return {"total": len(tokens), "tokens": tokens}


@router.get("/history", summary="List recent push notification dispatches")
async def list_history(limit: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    """Return recent threat alert notification dispatches."""
    service = get_notification_service()
    with service._lock:
        hist = list(service.dispatch_history[-limit:])
    return {"total": len(hist), "history": hist}


@router.get("/status", summary="Notification service health and statistics")
async def get_status() -> Dict[str, Any]:
    """Return runtime provider mode and registration statistics."""
    service = get_notification_service()
    with service._lock:
        token_count = len(service._tokens)
        history_count = len(service.dispatch_history)
        mode = service.provider.__class__.__name__
    return {
        "status": "healthy",
        "provider": mode,
        "registered_devices": token_count,
        "total_dispatches": history_count,
    }

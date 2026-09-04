"""Push Notification Service & FCM Integration for SAMPATI V2.

Provides device token registration, threat alert dispatching, and dual-mode
FCM providers: MockFcmProvider (zero-credential hermetic testing/demo) and
HttpV1FcmProvider (live Google Cloud FCM HTTP v1 API).
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

import httpx
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger("sampati.services.notification")


def utcnow() -> datetime:
    """Return current UTC timezone-aware datetime."""
    return datetime.now(timezone.utc)


class DeviceRegistrationRequest(BaseModel):
    """Payload for registering or updating a mobile device push token."""

    device_token: str = Field(..., min_length=10, description="FCM registration token")
    platform: str = Field(default="android", description="Device platform: android, ios, web")
    device_id: Optional[str] = Field(default=None, description="Hardware device identifier")
    user_id: Optional[str] = Field(default=None, description="User or customer ID")
    vpa: Optional[str] = Field(default=None, description="Primary associated UPI VPA")
    app_version: Optional[str] = Field(default="2.0.0", description="Client mobile app version")

    @model_validator(mode="before")
    @classmethod
    def handle_token_alias(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "device_token" not in values and "token" in values:
                values["device_token"] = values["token"]
        return values


class DeviceRegistrationResponse(BaseModel):
    """Response returned after registering or updating a device token."""

    status: str = Field(..., description="'registered' for new tokens or 'updated' for existing")
    device_token: str
    platform: str
    registered_at: datetime = Field(default_factory=utcnow)
    total_registered_devices: int


class NotificationPayload(BaseModel):
    """Standard threat notification payload dispatched to client devices."""

    risk_score: int
    verdict: str
    top_reason: str
    target_vpa: Optional[str] = None
    title: str = "SAMPATI Threat Alert"
    body: str = ""
    data: Dict[str, str] = Field(default_factory=dict)
    dispatched_at: datetime = Field(default_factory=utcnow)


class DispatchResult(BaseModel):
    """Result of dispatching push notifications across registered devices."""

    success: bool
    dispatched_count: int
    payload: NotificationPayload
    latency_ms: float
    mode: str  # "mock" or "http_v1"


class FcmProvider(Protocol):
    """Protocol for FCM delivery providers."""

    async def send(self, tokens: List[str], payload: NotificationPayload) -> DispatchResult:
        ...


class MockFcmProvider:
    """In-memory mock provider for hermetic testing and offline operation.

    Records all token dispatches in a thread-safe list with sub-millisecond execution.
    """

    def __init__(self) -> None:
        self.dispatches: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    async def send(self, tokens: List[str], payload: NotificationPayload) -> DispatchResult:
        t0 = time.perf_counter()
        record = {
            "tokens": list(tokens),
            "payload": payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
            "timestamp": utcnow().isoformat(),
        }
        with self._lock:
            self.dispatches.append(record)
        t1 = time.perf_counter()
        latency_ms = max(0.001, (t1 - t0) * 1000.0)

        return DispatchResult(
            success=True,
            dispatched_count=len(tokens),
            payload=payload,
            latency_ms=round(latency_ms, 3),
            mode="mock",
        )


class HttpV1FcmProvider:
    """Live Google Cloud FCM HTTP v1 client using asynchronous httpx.

    Dispatches messages to:
    https://fcm.googleapis.com/v1/projects/{project_id}/messages:send
    Falls back gracefully if live credentials are not provided.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        service_account_json: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> None:
        self.project_id = (
            project_id
            or os.getenv("FCM_PROJECT_ID")
            or os.getenv("FIREBASE_PROJECT_ID")
            or "sampati-v2"
        )
        self.service_account_json = service_account_json or os.getenv("FCM_SERVICE_ACCOUNT_JSON")
        self.auth_token = auth_token or os.getenv("FCM_AUTH_TOKEN")
        self.endpoint = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
        self.dispatches: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    async def send(self, tokens: List[str], payload: NotificationPayload) -> DispatchResult:
        t0 = time.perf_counter()
        dispatched_count = 0
        success = True

        if not tokens:
            t1 = time.perf_counter()
            return DispatchResult(
                success=True,
                dispatched_count=0,
                payload=payload,
                latency_ms=round(max(0.001, (t1 - t0) * 1000.0), 3),
                mode="http_v1",
            )

        headers = {
            "Content-Type": "application/json",
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        # If live credentials are provided, post to FCM HTTP v1; otherwise record dispatch
        if self.auth_token:
            async with httpx.AsyncClient(timeout=3.0) as client:
                for token in tokens:
                    msg = {
                        "message": {
                            "token": token,
                            "notification": {
                                "title": payload.title,
                                "body": payload.body,
                            },
                            "data": payload.data,
                        }
                    }
                    try:
                        resp = await client.post(self.endpoint, json=msg, headers=headers)
                        if resp.status_code in (200, 201):
                            dispatched_count += 1
                        else:
                            logger.warning("FCM HTTP v1 returned %s: %s", resp.status_code, resp.text)
                    except Exception as exc:
                        logger.warning("FCM HTTP v1 connection error: %s", exc)
                        success = False
        else:
            # Emulated live mode without active bearer token
            dispatched_count = len(tokens)

        t1 = time.perf_counter()
        latency_ms = max(0.001, (t1 - t0) * 1000.0)

        record = {
            "tokens": list(tokens),
            "payload": payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
            "timestamp": utcnow().isoformat(),
            "dispatched_count": dispatched_count,
        }
        with self._lock:
            self.dispatches.append(record)

        return DispatchResult(
            success=success,
            dispatched_count=dispatched_count,
            payload=payload,
            latency_ms=round(latency_ms, 3),
            mode="http_v1",
        )


class NotificationService:
    """Core notification management service maintaining device registries and alert dispatches."""

    def __init__(self, provider: Optional[FcmProvider] = None) -> None:
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        if provider is not None:
            self.provider = provider
        elif os.getenv("FCM_MODE", "").lower() == "http_v1" and (
            os.getenv("FCM_PROJECT_ID") or os.getenv("FIREBASE_PROJECT_ID")
        ):
            self.provider = HttpV1FcmProvider()
        else:
            self.provider = MockFcmProvider()

        self.dispatch_history: List[Dict[str, Any]] = []

    def register_device(self, req: DeviceRegistrationRequest) -> DeviceRegistrationResponse:
        """Register or update an FCM device token in a thread-safe manner."""
        with self._lock:
            exists = req.device_token in self._tokens
            now = utcnow()
            record = {
                "device_token": req.device_token,
                "platform": req.platform,
                "device_id": req.device_id,
                "user_id": req.user_id,
                "vpa": req.vpa,
                "app_version": req.app_version,
                "updated_at": now.isoformat(),
                "created_at": (
                    self._tokens[req.device_token]["created_at"]
                    if exists
                    else now.isoformat()
                ),
            }
            self._tokens[req.device_token] = record
            status = "updated" if exists else "registered"
            total = len(self._tokens)

        return DeviceRegistrationResponse(
            status=status,
            device_token=req.device_token,
            platform=req.platform,
            registered_at=now,
            total_registered_devices=total,
        )

    def get_registered_tokens(self, vpa: Optional[str] = None) -> List[str]:
        """Return registered device tokens.

        If a specific VPA is provided and matching devices exist, targets those devices.
        If no match or VPA is omitted, returns all registered tokens (broadcast mode).
        """
        with self._lock:
            if not vpa:
                return list(self._tokens.keys())
            matched = [t for t, rec in self._tokens.items() if rec.get("vpa") == vpa]
            return matched if matched else list(self._tokens.keys())

    async def dispatch_threat_alert(
        self,
        risk_score: int,
        verdict: str,
        top_reason: str,
        target_vpa: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DispatchResult:
        """Construct and dispatch a real-time threat alert push notification."""
        t_start = time.perf_counter()
        tokens = self.get_registered_tokens(target_vpa)
        meta = metadata or {}

        body_text = f"Risk Score: {risk_score}/100 | Verdict: {verdict} | Reason: {top_reason}"
        payload = NotificationPayload(
            risk_score=risk_score,
            verdict=verdict,
            top_reason=top_reason,
            target_vpa=target_vpa,
            title="SAMPATI Threat Alert",
            body=body_text,
            data={
                "risk_score": str(risk_score),
                "verdict": str(verdict),
                "top_reason": str(top_reason),
                "target_vpa": str(target_vpa or ""),
                **{k: str(v) for k, v in meta.items()},
            },
        )

        result = await self.provider.send(tokens, payload)
        t_end = time.perf_counter()
        result.latency_ms = round((t_end - t_start) * 1000.0, 3)

        with self._lock:
            self.dispatch_history.append(
                {
                    "dispatched_at": utcnow().isoformat(),
                    "payload": (
                        payload.model_dump()
                        if hasattr(payload, "model_dump")
                        else payload.dict()
                    ),
                    "tokens_count": len(tokens),
                    "latency_ms": result.latency_ms,
                    "mode": result.mode,
                }
            )
            if len(self.dispatch_history) > 1000:
                self.dispatch_history = self.dispatch_history[-1000:]

        return result

    def clear(self) -> None:
        """Clear all registered tokens and dispatch history (useful for test isolation)."""
        with self._lock:
            self._tokens.clear()
            self.dispatch_history.clear()
            if hasattr(self.provider, "dispatches"):
                self.provider.dispatches.clear()


_notification_service_instance: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Return singleton NotificationService instance."""
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService()
    return _notification_service_instance


def set_notification_service(instance: Optional[NotificationService]) -> None:
    """Override singleton NotificationService instance for tests."""
    global _notification_service_instance
    _notification_service_instance = instance

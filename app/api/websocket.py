"""Backend Real-Time WebSocket Push Hub for SAMPATI V2.

Provides a thread-safe ConnectionManager handling active client connections,
multi-route WebSocket endpoints (/ws, /ws/, /ws/feed), heartbeat ping/pong handling,
dead socket pruning, and real-time event broadcasting to frontend dashboards.
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("sampati.websocket")
router = APIRouter()
FASTAPI_AVAILABLE = True


class ConnectionManager:
    """Thread-safe WebSocket connection manager with exception resilience."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection and add to active pool."""
        try:
            await websocket.accept()
        except Exception as exc:
            logger.debug("WebSocket accept skipped or failed: %s", exc)

        async with self._lock:
            if websocket not in self.active_connections:
                self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Active: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from active pool."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected. Active: %d", len(self.active_connections))

    async def broadcast(self, message: Union[Dict[str, Any], List[Any], str]) -> None:
        """Broadcast a message or JSON event payload to all active WebSocket clients.

        Prunes any failing/dead connections automatically with full exception safety.
        """
        if not self.active_connections:
            return

        async with self._lock:
            connections = list(self.active_connections)

        dead_connections: List[WebSocket] = []

        for connection in connections:
            try:
                if isinstance(message, (dict, list)):
                    if hasattr(connection, "send_json"):
                        await connection.send_json(message)
                    elif hasattr(connection, "send_text"):
                        await connection.send_text(json.dumps(message, default=str))
                else:
                    if hasattr(connection, "send_text"):
                        await connection.send_text(str(message))
                    elif hasattr(connection, "send_json"):
                        await connection.send_json({"message": str(message)})
            except Exception as exc:
                logger.debug("Failed to send message to WebSocket client %s: %s", connection, exc)
                dead_connections.append(connection)

        if dead_connections:
            async with self._lock:
                for dead in dead_connections:
                    if dead in self.active_connections:
                        self.active_connections.remove(dead)
            logger.info("Pruned %d dead WebSocket connection(s). Active: %d", len(dead_connections), len(self.active_connections))

    async def broadcast_event(
        self,
        event: str,
        data: Any,
        stats: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Helper to broadcast standard SAMPATI event payloads."""
        payload: Dict[str, Any] = {
            "event": event,
            "data": data,
        }
        if stats is not None:
            payload["stats"] = stats
        await self.broadcast(payload)


manager = ConnectionManager()
ws_manager = manager


def schedule_broadcast(payload: Dict[str, Any]) -> None:
    """Schedule asynchronous broadcast on the active event loop or background thread."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(payload))
    except RuntimeError:
        try:
            loop = asyncio.new_event_loop()
            t = threading.Thread(
                target=lambda: loop.run_until_complete(manager.broadcast(payload)),
                daemon=True,
            )
            t.start()
        except Exception as exc:
            logger.debug("schedule_broadcast failed: %s", exc)


async def broadcast_event(
    event_type: str,
    payload: Any,
    stats: Optional[Dict[str, Any]] = None,
) -> None:
    """Global coroutine for broadcasting structured SAMPATI events."""
    await manager.broadcast_event(event_type, payload, stats=stats)


def get_redis_state():
    """Stub for legacy backwards compatibility."""
    return None


@router.websocket("/ws")
@router.websocket("/ws/")
@router.websocket("/ws/feed")
async def websocket_feed_endpoint(websocket: WebSocket) -> None:
    """Real-time threat feed and telemetry streaming endpoint."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, dict):
                        if parsed.get("type") == "ping" or parsed.get("event") == "ping":
                            await websocket.send_json({
                                "type": "pong",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                        elif parsed.get("action") == "get_stats":
                            from app.services.upi_cases import get_upi_case_service
                            svc = get_upi_case_service()
                            await websocket.send_json({
                                "event": "stats_update",
                                "data": svc.get_current_stats(),
                            })
                except Exception:
                    # Ignore non-JSON or unsupported incoming client messages
                    pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as exc:
        logger.debug("WebSocket client connection ended with error: %s", exc)
        await manager.disconnect(websocket)


# Alias for legacy references
websocket_dashboard_endpoint = websocket_feed_endpoint

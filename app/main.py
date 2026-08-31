"""FastAPI application entry point for SAMPATI — UPI mule-network interception."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict

# bootstrap the backend.app.* -> app.* redirector
import backend  # noqa: F401

try:
    from fastapi import Depends, FastAPI, HTTPException, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse, Response
    from fastapi.staticfiles import StaticFiles
    from starlette.exceptions import HTTPException as StarletteHTTPException
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    class FastAPI:
        def __init__(self, *args, **kwargs):
            self.title = kwargs.get("title", "SAMPATI")
            self.description = kwargs.get("description", "")
            self.version = kwargs.get("version", "2.0.0")
            self.routes = []

        def add_middleware(self, *args, **kwargs): pass
        def include_router(self, *args, **kwargs): pass
        def get(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
        def post(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
        def patch(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
        def exception_handler(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
        def mount(self, *args, **kwargs): pass

    class CORSMiddleware: pass
    class FileResponse:
        def __init__(self, path, media_type=None):
            self.path = path
            self.media_type = media_type
    class JSONResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code
    class StaticFiles:
        def __init__(self, *args, **kwargs): pass
    def Depends(f=None): return None
    def Query(default=None, **kwargs): return default
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: Any = None):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")
    class StarletteHTTPException(HTTPException): pass
    class Request: pass

# legacy AEGIS-Lite routers (loaded from pyc if dependencies available)
try:
    from app.api import cases, gateway, synthetic, websocket
except Exception:
    cases = gateway = synthetic = websocket = None

# UPI mule-network router
from app.api import federation as federation_router
from app.api import upi as upi_router
from app.models.upi_models import CaseStatusUpdateRequest

# DB + settings
try:
    from app.config import get_settings
    settings = get_settings()
except Exception:
    settings = None

try:
    from app.db.session import check_db_health, close_db, init_db
except Exception:
    async def check_db_health() -> Dict[str, Any]:
        return {
            "connected": False,
            "status": "in-memory-fallback",
            "message": "DATABASE_URL not configured (running in in-memory mode)",
        }

    async def close_db() -> None:
        pass

    async def init_db() -> bool:
        return False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sampati.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SAMPATI starting up ...")
    try:
        db_ok = await init_db()
        if db_ok:
            logger.info("Database initialized successfully with active connection pool.")
        else:
            logger.info("Operating in in-memory fallback mode.")
    except Exception as exc:
        logger.warning("DB init skipped (in-memory mode): %s", exc)

    # Sync existing cases and rings from DB into service cache if available
    try:
        from app.services.upi_cases import get_upi_case_service
        svc = get_upi_case_service()
        if hasattr(svc, "sync_from_db"):
            await svc.sync_from_db()
    except Exception as exc:
        logger.warning("DB state sync skipped: %s", exc)

    yield

    try:
        await close_db()
    except Exception as exc:
        logger.warning("DB close error: %s", exc)
    logger.info("SAMPATI shut down.")


app = FastAPI(
    title="SAMPATI UPI Mule-Network Interception Gateway",
    description=(
        "Real-time UPI mule-network interception with federated ring detection, "
        "SAR generation, and DPIP integration."
    ),
    version="2.0.0",
    lifespan=lifespan if FASTAPI_AVAILABLE else None,
)

if FASTAPI_AVAILABLE:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(upi_router.router, prefix="/upi", tags=["UPI"])
app.include_router(federation_router.router, prefix="/federation", tags=["federation"])
if gateway and hasattr(gateway, "router"):
    app.include_router(gateway.router, prefix="/gateway", tags=["Gateway"])
if cases and hasattr(cases, "router"):
    app.include_router(cases.router, prefix="/cases", tags=["Cases"])
if synthetic and hasattr(synthetic, "router"):
    app.include_router(synthetic.router, prefix="/synthetic", tags=["Synthetic"])
if websocket and hasattr(websocket, "router"):
    app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/health", tags=["System"])
async def health_check():
    """Liveness & readiness probe verifying application and DB connectivity."""
    db_health = await check_db_health()
    is_connected = db_health.get("connected", False)
    db_url_set = bool(os.getenv("DATABASE_URL", "").strip())

    # If DB is configured, health requires active connection.
    # If DB is not configured, in-memory mode is healthy.
    status_code = 200 if (is_connected or not db_url_set) else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if status_code == 200 else "degraded",
            "service": "sampati-upi",
            "version": "2.0.0",
            "database": db_health.get("message", "connected" if is_connected else "disconnected"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/health/detailed", tags=["System"])
async def detailed_health_check():
    """Detailed real-time subsystem health, DB pool stats, Redis ping, and latency percentiles."""
    from app.services.upi_cases import get_upi_case_service
    svc = get_upi_case_service()
    health_data = svc.get_detailed_health()
    return JSONResponse(status_code=200, content=health_data)


@app.get("/stats/analytics", tags=["Analytics"])
async def get_analytics_root(
    interval: str = Query("hourly", description="Aggregation bucket interval: 'hourly' or 'daily'"),
    hours: int = Query(24, ge=1, le=720, description="Hours lookback window"),
    days: int = Query(30, ge=1, le=365, description="Days lookback window"),
    limit_accounts: int = Query(10, ge=1, le=100, description="Max top flagged accounts to return"),
):
    """Aggregated time-series verdict distributions, rule trigger frequencies, and top flagged accounts."""
    from app.services.upi_cases import get_upi_case_service
    svc = get_upi_case_service()
    analytics_data = svc.get_analytics(
        interval=interval,
        hours=hours,
        days=days,
        limit_accounts=limit_accounts,
    )
    return JSONResponse(status_code=200, content=analytics_data)


@app.patch("/cases/{case_id}/status", tags=["Cases"])
async def update_case_status_root(
    case_id: str,
    body: CaseStatusUpdateRequest,
):
    """Update case review status (reviewed, escalated, dismissed, open), trigger DPIP & model feedback."""
    from app.services.upi_cases import get_upi_case_service
    svc = get_upi_case_service()
    try:
        result = svc.update_case_status(
            case_id=case_id,
            new_status=body.status,
            notes=body.notes,
            resolution_notes=body.resolution_notes,
            resolution=body.resolution,
            escalate_to_dpip=body.escalate_to_dpip,
        )
        return JSONResponse(status_code=200, content=result)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"UPI case '{case_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/cases/{case_id}/sar/pdf", tags=["Cases"])
async def get_case_sar_pdf_root(case_id: str):
    """Export complete Suspicious Activity Report (SAR) for a case as a PDF document."""
    from app.services.upi_cases import get_upi_case_service
    svc = get_upi_case_service()
    case = svc.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"UPI case '{case_id}' not found")
    from app.forensics.sar_pdf import build_sar_pdf
    pdf_bytes = build_sar_pdf(case)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="SAR_{case_id}.pdf"'},
    )



@app.get("/api/info", tags=["System"])
async def api_info():
    return {
        "title": app.title,
        "version": app.version,
        "pillars": ["inline-gate", "federated-intelligence", "visual-forensics", "dpip-loop"],
    }


# Static frontend mount and SPA fallback handling
_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
_index_html = os.path.join(_dist, "index.html")

if FASTAPI_AVAILABLE:
    @app.exception_handler(404)
    async def spa_fallback_404_handler(request: Request, exc: Any):
        """Serve SPA index.html on direct client-side route navigation while preserving API 404s."""
        path = request.url.path
        api_prefixes = ("/upi", "/federation", "/gateway", "/cases", "/synthetic", "/ws", "/health", "/api", "/stats")
        is_api = any(path.startswith(prefix) for prefix in api_prefixes)
        has_extension = "." in path.split("/")[-1]

        if not is_api and not has_extension and os.path.isfile(_index_html):
            return FileResponse(_index_html)
        return JSONResponse(
            status_code=404,
            content={"detail": getattr(exc, "detail", f"Path '{path}' not found")},
        )

    if os.path.isdir(_dist):
        app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")

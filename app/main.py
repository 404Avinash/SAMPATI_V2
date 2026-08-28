"""FastAPI application entry point for SAMPATI — UPI mule-network interception."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# bootstrap the backend.app.* -> app.* redirector
import backend  # noqa: F401

# legacy AEGIS-Lite routers (loaded from pyc)
from app.api import cases, gateway, synthetic, websocket

# UPI mule-network router
from app.api import upi as upi_router

# DB + settings
from app.config import get_settings
from app.db.session import check_db_health, close_db, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sampati.main")
settings = get_settings()


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
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upi_router.router, prefix="/upi",      tags=["UPI"])
app.include_router(gateway.router,    prefix="/gateway",   tags=["Gateway"])
app.include_router(cases.router,      prefix="/cases",     tags=["Cases"])
app.include_router(synthetic.router,  prefix="/synthetic", tags=["Synthetic"])
app.include_router(websocket.router,                       tags=["WebSocket"])


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


@app.get("/api/info", tags=["System"])
async def api_info():
    return {
        "title": app.title,
        "version": app.version,
        "pillars": ["inline-gate", "federated-intelligence", "visual-forensics", "dpip-loop"],
    }


# Static frontend mount LAST — must come after API routes to avoid shadowing them
_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")

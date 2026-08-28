"""Database session management and connection lifecycle for SAMPATI V2.

Engineered for AWS RDS PostgreSQL (db.t3.micro free tier) with async connection
pooling, pre-ping liveness, automatic schema creation, and graceful fallback.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.models.upi_persistence import Base as UpiBase

logger = logging.getLogger("sampati.db")

# Re-export Base for compatibility
Base = UpiBase

# Global singleton handles
_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None
_is_db_ready: bool = False


def get_normalized_database_url() -> Optional[str]:
    """Retrieve and normalize DATABASE_URL for async drivers."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return None
    # Normalize postgres/postgresql schemes to asyncpg driver
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://") and not url.startswith("sqlite+"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def get_engine() -> Optional[AsyncEngine]:
    """Obtain or initialize the global AsyncEngine singleton."""
    global _engine, _sessionmaker
    if _engine is not None:
        return _engine

    db_url = get_normalized_database_url()
    if not db_url:
        logger.info("DATABASE_URL is not set. Operating in in-memory fallback mode.")
        return None

    try:
        # Tuning parameters optimized for RDS db.t3.micro (max ~87 connections)
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
        pool_timeout = float(os.getenv("DB_POOL_TIMEOUT", "30.0"))

        if "sqlite" in db_url:
            _engine = create_async_engine(
                db_url,
                echo=False,
                connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
            )
        else:
            _engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                pool_pre_ping=True,
            )

        _sessionmaker = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info(f"Initialized AsyncEngine with pool_size={pool_size}, max_overflow={max_overflow}")
        return _engine
    except Exception as exc:
        logger.error(f"Failed to create AsyncEngine: {exc}. Falling back to in-memory mode.")
        _engine = None
        _sessionmaker = None
        return None


def get_sessionmaker() -> Optional[async_sessionmaker[AsyncSession]]:
    """Obtain the async_sessionmaker instance."""
    global _sessionmaker
    if _sessionmaker is None:
        get_engine()
    return _sessionmaker


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """FastAPI dependency yielding an async database session if available."""
    sm = get_sessionmaker()
    if sm is None:
        yield None
        return

    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


get_session = get_db  # Alias for backward compatibility


async def init_db() -> bool:
    """Initialize database tables on application startup via Base.metadata.create_all."""
    global _is_db_ready
    eng = get_engine()
    if eng is None:
        _is_db_ready = False
        return False

    try:
        async with eng.begin() as conn:
            # Create UPI persistence tables
            await conn.run_sync(UpiBase.metadata.create_all)
            
            # Optionally create legacy tables if available
            try:
                from app.models.db_models import Base as LegacyBase
                await conn.run_sync(LegacyBase.metadata.create_all)
            except Exception:
                pass

        _is_db_ready = True
        logger.info("Successfully connected to RDS PostgreSQL and validated all schema tables.")
        return True
    except Exception as exc:
        _is_db_ready = False
        logger.error(f"PostgreSQL initialization failed: {exc}. Operating in in-memory fallback mode.")
        return False


async def close_db() -> None:
    """Dispose engine connections on application shutdown."""
    global _engine, _sessionmaker, _is_db_ready
    if _engine is not None:
        try:
            await _engine.dispose()
            logger.info("Disposed database connection pool cleanly.")
        except Exception as exc:
            logger.warning(f"Error disposing database engine: {exc}")
        finally:
            _engine = None
            _sessionmaker = None
            _is_db_ready = False


async def check_db_health() -> Dict[str, Any]:
    """Actively probe the database connection via SELECT 1."""
    eng = get_engine()
    if eng is None:
        return {
            "connected": False,
            "status": "in-memory-fallback",
            "message": "DATABASE_URL not configured (running in in-memory mode)",
        }

    try:
        async with eng.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            scalar = result.scalar()
            if scalar == 1:
                return {
                    "connected": True,
                    "status": "connected",
                    "message": "PostgreSQL connection pool healthy",
                }
            return {
                "connected": False,
                "status": "unexpected-result",
                "message": f"Unexpected health check probe output: {scalar}",
            }
    except Exception as exc:
        return {
            "connected": False,
            "status": "disconnected",
            "message": f"Health check probe failed: {exc}",
        }


def is_db_ready() -> bool:
    """Check if the database has been successfully initialized."""
    return _is_db_ready


# ── Legacy AEGIS-Lite Compatibility Store ─────────────────────────────────────

class AsyncDatabaseStore:
    """Fallback in-memory store for legacy AEGIS-Lite batch processing."""

    def __init__(self) -> None:
        self.accounts: Dict[str, Any] = {}
        self.batches: Dict[str, Any] = {}
        self.cases: Dict[str, Any] = {}
        self.audit_logs: List[Any] = []
        self.payees: Dict[str, Any] = {}
        self.reports: Dict[str, Any] = {}

    async def save_corporate_account(self, account: Any) -> None:
        key = getattr(account, "account_id", str(account))
        self.accounts[key] = account

    async def get_corporate_account(self, account_id: str) -> Optional[Any]:
        return self.accounts.get(account_id)

    async def save_payout_batch(self, batch: Any) -> None:
        key = getattr(batch, "batch_id", str(batch))
        self.batches[key] = batch

    async def get_payout_batch(self, batch_id: str) -> Optional[Any]:
        return self.batches.get(batch_id)

    async def save_flagged_case(self, case: Any) -> None:
        key = getattr(case, "case_id", str(case))
        self.cases[key] = case

    async def get_flagged_case(self, case_id: str) -> Optional[Any]:
        return self.cases.get(case_id)

    async def update_case_forensics(self, case_id: str, report: Any, metrics: Any = None) -> None:
        if case_id in self.cases:
            case = self.cases[case_id]
            if hasattr(case, "forensic_report"):
                case.forensic_report = report
            if hasattr(case, "token_metrics"):
                case.token_metrics = metrics

    async def list_flagged_cases(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        min_risk: Optional[float] = None,
    ) -> List[Any]:
        cases = list(self.cases.values())
        if status:
            cases = [c for c in cases if getattr(c, "status", None) == status]
        if min_risk is not None:
            cases = [c for c in cases if getattr(c, "risk_score", 0) >= min_risk]
        return cases[offset : offset + limit]

    async def save_audit_log(self, log: Any) -> None:
        self.audit_logs.append(log)

    async def get_audit_logs(self, limit: int = 50) -> List[Any]:
        return self.audit_logs[-limit:]

    async def clear(self) -> None:
        self.accounts.clear()
        self.batches.clear()
        self.cases.clear()
        self.audit_logs.clear()
        self.payees.clear()
        self.reports.clear()


db_store = AsyncDatabaseStore()

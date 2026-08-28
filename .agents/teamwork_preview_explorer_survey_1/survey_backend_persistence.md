# Architecture & Implementation Survey: AWS RDS PostgreSQL Persistence (Requirement R1)

**Author:** Teamwork Explorer 1  
**Project:** SAMPATI V2 UPI Mule Ring Detection Switch  
**Date:** 2026-08-29  
**Target:** Production-Grade AWS RDS PostgreSQL Persistence Engine  

---

## 1. Executive Summary

SAMPATI V2 is a real-time UPI switch-level fraud prevention and mule-ring detection platform. In its current implementation, while high-performance inline scoring operates within sub-millisecond latencies, critical business state—including flagged UPI cases, mule ring topologies, SAR markdown filings, analyst feedback annotations, and aggregate system statistics—resides exclusively in volatile Python memory structures (`threading.Lock` protected dictionaries and sliding window deques).

This document delivers an exhaustive investigation of the existing backend architecture and provides a comprehensive blueprint to migrate SAMPATI V2 to **AWS RDS PostgreSQL (Free Tier `db.t3.micro`)** with zero-downtime resilience, connection-pool optimization tailored to AWS memory constraints, async database access via `SQLAlchemy 2.0` + `asyncpg`, automatic schema initialization on startup, and health probe verification.

---

## 2. In-Memory State Inventory & Analysis

A comprehensive audit of the backend reveals all locations where state is held in ephemeral Python runtime objects:

### 2.1 `app/services/upi_cases.py` (`UpiCaseService`)
- **State Stored**:
  - `self._cases: Dict[str, Dict[str, Any]]`: Dictionary mapping `case_id` (e.g., `CASE-UPI-20260828-A3F9`) to full case records containing trigger transaction data, risk scores, rule hit details, adaptive and network scores, SAR filings, token economy calculations, visualization paths, and ring topology.
  - `self._txn_log: List[Dict[str, Any]]`: In-memory list storing the latest evaluated transactions.
- **Concurrency Protection**: Protected by `self._lock = threading.Lock()`.
- **Vulnerability**: Any container restart, EC2 spot termination, or deployment wipes all investigative history, SAR reports, and case statuses.

### 2.2 `app/engine/upi_state.py` (`UpiHotState`)
- **State Stored**:
  - `self._inbound: DefaultDict[str, Deque[Tuple[datetime, str, float]]]`: Sliding window of inbound payments per VPA.
  - `self._outbound: DefaultDict[str, Deque[Tuple[datetime, str, float]]]`: Sliding window of outbound payments per VPA.
  - `self._device_fingerprints: DefaultDict[str, Set[str]]`: Device-to-VPA mapping for device velocity checks.
  - `self._fraud_memory: DefaultDict[str, int]`: Feedback memory tracking VPAs flagged by human analysts.
- **Lifecycle**: Window is 1800.0 seconds (30 minutes). Hot sliding window state should remain in-memory for sub-millisecond inline scoring, but `_fraud_memory` (analyst feedback) must be seeded from PostgreSQL on service initialization.

### 2.3 `app/federation/coordinator.py` (`FederatedCoordinator`)
- **State Stored**:
  - `self._nodes: Dict[str, FederatedNode]`: Local and remote PSP node definitions.
  - `self._rings: Dict[str, Dict[str, Any]]`: Discovered cross-PSP mule rings keyed by deterministic `ring_hash` (e.g., `RING-UPI-A82F19E4`).
- **Concurrency Protection**: Protected by `self._lock = threading.Lock()`.
- **Persistence Target**: `mule_rings` table in PostgreSQL.

### 2.4 `app/dpip/feed.py` (`DpipFeed`)
- **State Stored**:
  - `self._published: List[Dict[str, Any]]`: Registry of ring warnings published to the National Fraud Intelligence Exchange.
  - `self._confirmed_frauds: Set[str]`: Set of confirmed fraud VPAs.
- **Persistence Target**: `case_feedback` and `dpip_events` tables in PostgreSQL.

### 2.5 Legacy `app/db/session.py` & `app/db/init_db.py`
- **State Stored**:
  - Contains an `AsyncDatabaseStore` fallback dictionary store for AEGIS-Lite batch processing (`CorporateAccount`, `PayoutBatch`, `Payee`, `FlaggedCase`, `ForensicReport`, `TokenMetricsRecord`, `AuditLog`).
  - UPI V2 currently does not use these legacy tables and operates fully disconnected from `app.db`.

---

## 3. Target PostgreSQL Data Models & Schema Design

To support all UPI fraud detection operations, SAR reporting, mule ring visualization, analyst workflows, and aggregate telemetry, the following relational schemas are designed for PostgreSQL 15/16.

### 3.1 Entity-Relationship Overview
```
┌─────────────────────────┐           1:N           ┌─────────────────────────┐
│       upi_cases         │ ◄────────────────────── │      case_feedback      │
├─────────────────────────┤                         ├─────────────────────────┤
│ case_id (PK)            │                         │ id (PK)                 │
│ ring_hash (FK nullable) │                         │ case_id (FK)            │
│ trigger_txn (JSONB)     │                         │ resolution              │
│ rule_hits (JSONB)       │                         │ confirmed_fraud         │
│ topology (JSONB)        │                         │ vpas_flagged (JSONB)    │
│ sar_markdown (TEXT)     │                         └─────────────────────────┘
└───────────┬─────────────┘
            │ N:1
            ▼
┌─────────────────────────┐                         ┌─────────────────────────┐
│       mule_rings        │                         │     aggregate_stats     │
├─────────────────────────┤                         ├─────────────────────────┤
│ ring_hash (PK)          │                         │ stat_key (PK)           │
│ members (JSONB)         │                         │ stat_value (JSONB/NUM)  │
│ psps (JSONB)            │                         │ updated_at              │
│ total_amount (NUMERIC)  │                         └─────────────────────────┘
└─────────────────────────┘
```

### 3.2 SQLAlchemy 2.0 Declarative Models (`app/models/upi_persistence.py`)

```python
"""
SQLAlchemy 2.0 Declarative Models for SAMPATI V2 Database Persistence.
Optimized for AWS RDS PostgreSQL with JSONB support and compound indexing.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UpiCaseModel(Base):
    __tablename__ = "upi_cases"

    case_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    status = Column(String(32), default="OPEN", nullable=False, index=True)  # OPEN, INVESTIGATED, RESOLVED
    verdict = Column(String(16), nullable=False, index=True)  # ALLOW, HOLD, BLOCK
    risk_score = Column(Integer, nullable=False)
    
    # Financial and Entity context
    payer_vpa = Column(String(128), nullable=True, index=True)
    payee_vpa = Column(String(128), nullable=True, index=True)
    amount = Column(Numeric(14, 2), nullable=True)
    
    # Detailed payloads stored in optimized JSONB
    trigger_txn = Column(JSONB, nullable=False)
    rule_hits = Column(JSONB, default=list, nullable=False)
    
    # Layer 2 & 3 scores
    adaptive_score = Column(Float, default=0.0, nullable=False)
    network_score = Column(Float, default=0.0, nullable=False)
    
    # Mule Ring association
    ring_hash = Column(String(64), ForeignKey("mule_rings.ring_hash"), nullable=True, index=True)
    ring_members_vpas = Column(JSONB, default=list, nullable=True)
    
    # Layer 4 Visual Forensics & SAR
    token_economy = Column(JSONB, nullable=True)
    sar_markdown = Column(Text, nullable=True)
    visual_path = Column(String(255), nullable=True)
    topology = Column(JSONB, nullable=True)
    
    # Analyst Workflow Resolution
    resolution = Column(String(64), nullable=True)  # CONFIRMED_FRAUD, DISMISSED_FALSE_POSITIVE
    investigated_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    mule_ring = relationship("MuleRingModel", back_populates="cases")
    feedbacks = relationship("CaseFeedbackModel", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_upi_cases_status_created", "status", "created_at"),
        Index("ix_upi_cases_verdict_created", "verdict", "created_at"),
    )


class MuleRingModel(Base):
    __tablename__ = "mule_rings"

    ring_hash = Column(String(64), primary_key=True, index=True)
    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    size = Column(Integer, nullable=False)
    members = Column(JSONB, nullable=False)  # List of member VPAs or node descriptors
    psps = Column(JSONB, nullable=False)     # Distinct PSP handles involved
    total_amount = Column(Numeric(14, 2), default=0.0, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, DISMANTLED, ARCHIVED

    # Relationships
    cases = relationship("UpiCaseModel", back_populates="mule_ring")


class CaseFeedbackModel(Base):
    __tablename__ = "case_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("upi_cases.case_id"), nullable=False, index=True)
    confirmed_fraud = Column(Boolean, nullable=False)
    resolution = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    submitted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    vpas_flagged = Column(JSONB, default=list, nullable=False)
    dpip_published = Column(JSONB, nullable=True)

    # Relationships
    case = relationship("UpiCaseModel", back_populates="feedbacks")


class AggregateStatsModel(Base):
    __tablename__ = "aggregate_stats"

    metric_name = Column(String(64), primary_key=True)
    metric_value = Column(Numeric(18, 4), default=0.0, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

### 3.3 Raw PostgreSQL DDL
```sql
-- PostgreSQL DDL for SAMPATI V2 Database Schema

CREATE TABLE IF NOT EXISTS mule_rings (
    ring_hash VARCHAR(64) PRIMARY KEY,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    size INTEGER NOT NULL,
    members JSONB NOT NULL DEFAULT '[]'::jsonb,
    psps JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'
);
CREATE INDEX IF NOT EXISTS ix_mule_rings_detected_at ON mule_rings(detected_at DESC);

CREATE TABLE IF NOT EXISTS upi_cases (
    case_id VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    verdict VARCHAR(16) NOT NULL,
    risk_score INTEGER NOT NULL,
    payer_vpa VARCHAR(128),
    payee_vpa VARCHAR(128),
    amount NUMERIC(14, 2),
    trigger_txn JSONB NOT NULL,
    rule_hits JSONB NOT NULL DEFAULT '[]'::jsonb,
    adaptive_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    network_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    ring_hash VARCHAR(64) REFERENCES mule_rings(ring_hash) ON DELETE SET NULL,
    ring_members_vpas JSONB DEFAULT '[]'::jsonb,
    token_economy JSONB,
    sar_markdown TEXT,
    visual_path VARCHAR(255),
    topology JSONB,
    resolution VARCHAR(64),
    investigated_at TIMESTAMPTZ,
    resolution_notes TEXT
);
CREATE INDEX IF NOT EXISTS ix_upi_cases_created_at ON upi_cases(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_upi_cases_status_created ON upi_cases(status, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_upi_cases_verdict_created ON upi_cases(verdict, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_upi_cases_ring_hash ON upi_cases(ring_hash);

CREATE TABLE IF NOT EXISTS case_feedback (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL REFERENCES upi_cases(case_id) ON DELETE CASCADE,
    confirmed_fraud BOOLEAN NOT NULL,
    resolution VARCHAR(64) NOT NULL,
    notes TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vpas_flagged JSONB NOT NULL DEFAULT '[]'::jsonb,
    dpip_published JSONB
);
CREATE INDEX IF NOT EXISTS ix_case_feedback_case_id ON case_feedback(case_id);

CREATE TABLE IF NOT EXISTS aggregate_stats (
    metric_name VARCHAR(64) PRIMARY KEY,
    metric_value NUMERIC(18, 4) NOT NULL DEFAULT 0,
    metadata_json JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Connection Pooling & AWS RDS Free Tier (`db.t3.micro`) Optimization

### 4.1 RDS Free Tier Resource Realities
- **RAM**: 1 GiB on `db.t3.micro`.
- **Default Max Connections Formula**:
  $$\text{max\_connections} = \min\left(\frac{\text{DBInstanceClassMemory}}{9531392}, 5000\right) \approx \frac{1073741824}{9531392} \approx 112$$
  Accounting for superuser/system reservations, the usable connection pool limit is approximately **87 connections**.
- **Memory Pressure**: Each active PostgreSQL backend process consumes 5–10 MB of RAM. Running 80+ active client connections on 1 GB of RAM risks triggering Linux OOM killer on RDS or heavy swap thrashing.

### 4.2 SQLAlchemy Async Connection Pool Architecture
To guarantee maximum throughput while staying strictly under RDS constraints:
- **Pool Size (`pool_size`)**: 5 connections.
- **Max Overflow (`max_overflow`)**: 10 connections (Total burst ceiling: 15 connections, utilizing less than 20% of the RDS hard limit).
- **Pool Timeout (`pool_timeout`)**: 30.0 seconds.
- **Pool Recycle (`pool_recycle`)**: 1800 seconds (30 minutes) to prevent stale socket leaks through AWS VPC NAT gateways.
- **Pre-Ping (`pool_pre_ping=True`)**: Emits `SELECT 1` on checkout to transparently recover from transient RDS restarts or connection drops.

### 4.3 Database Module Implementation (`app/db/session.py`)

```python
"""
Database session management and connection lifecycle for SAMPATI V2.
"""
from __future__ import annotations
import os
import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from app.models.upi_persistence import Base

logger = logging.getLogger("sampati.db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/sampati"
)

# Normalize URL for asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    global engine, AsyncSessionLocal
    if engine is None:
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=30.0,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency for transactional DB sessions."""
    get_engine()
    assert AsyncSessionLocal is not None
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> bool:
    """Initialize database tables on application startup."""
    try:
        eng = get_engine()
        async with eng.begin() as conn:
            # Create all tables defined in Base
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Successfully connected to PostgreSQL and validated tables.")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}. Operating in degraded mode.")
        return False


async def close_db() -> None:
    """Dispose engine connections on application shutdown."""
    global engine
    if engine is not None:
        await engine.dispose()
        logger.info("Disposed database connection pool.")
```

---

## 5. Dependency & Deployment Specification Changes

### 5.1 `requirements.txt`
Add modern asynchronous PostgreSQL driver and SQLAlchemy ORM:
```diff
--- requirements.txt (current)
+++ requirements.txt (proposed)
@@ -1,6 +1,8 @@
 fastapi>=0.115.0
 uvicorn[standard]>=0.32.0
 pydantic>=2.9.0
+sqlalchemy>=2.0.36
+asyncpg>=0.30.0
+psycopg[binary]>=3.2.3
 python-multipart>=0.0.12
 requests>=2.32.0
 pillow>=10.4.0
```

### 5.2 `Dockerfile`
The existing `python:3.14-slim` base is compatible with pure wheel builds of `asyncpg` and `SQLAlchemy`. Add libpq dependencies if psycopg C extensions are preferred:
```dockerfile
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY backend/ backend/
COPY static/ static/
COPY frontend/dist/ frontend/dist/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 5.3 `deploy/ec2_userdata.sh`
Update user data bootstrap script to accept and pass `DATABASE_URL` to Docker:
```bash
#!/bin/bash
set -euo pipefail

# SAMPATI V2 Production EC2 Userdata Bootstrap
echo "=== Starting SAMPATI V2 EC2 Bootstrap with RDS PostgreSQL ==="

# Update & Install Docker
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker

# Environment configuration
mkdir -p /opt/sampati
cat << 'EOF' > /opt/sampati/.env
# AWS RDS PostgreSQL Connection String
DATABASE_URL=postgresql+asyncpg://sampati_admin:StrongPassword123@sampati-db.c123456789.ap-south-1.rds.amazonaws.com:5432/sampatidb
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
FASTAPI_ENV=production
EOF

# Run Docker container with environment file and port mapping
docker run -d \
    --name sampati \
    --restart unless-stopped \
    --env-file /opt/sampati/.env \
    -p 8000:8000 \
    sampati:latest

echo "=== SAMPATI V2 Deployment Complete ==="
```

### 5.4 AWS RDS Free Tier Provisioning CLI Guide
To launch the free-tier RDS instance via AWS CLI:
```bash
aws rds create-db-instance \
    --db-instance-identifier sampati-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 16.3 \
    --master-username sampati_admin \
    --master-user-password "StrongPassword123" \
    --allocated-storage 20 \
    --storage-type gp2 \
    --no-publicly-accessible \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-name sampatidb \
    --backup-retention-period 7 \
    --region ap-south-1
```

---

## 6. Route & Service Modernization Plan

### 6.1 `UpiCaseService` Database Integration
Refactor `app/services/upi_cases.py` to persist all generated cases and rings:
1. **Case Creation (`_open_case`)**:
   - Write `UpiCaseModel` directly to PostgreSQL via `AsyncSession`.
   - Update in-memory cache/sliding window only for hot fraud scoring.
2. **Federation Ring Registration (`run_federation`)**:
   - Write new `MuleRingModel` rows with ON CONFLICT DO UPDATE for idempotency.
   - Associate newly discovered rings with existing cases (`UPDATE upi_cases SET ring_hash = :hash`).
3. **Feedback Submission (`submit_feedback`)**:
   - Write `CaseFeedbackModel` record.
   - Update `UpiCaseModel.status = 'RESOLVED'`, `resolution = ...`, `investigated_at = ...`.
   - Seed `UpiHotState._fraud_memory` and notify `DpipFeed`.

### 6.2 Endpoint Modernization

#### A. `/upi/cases` (`GET`)
- **Current**: Returns all cases in Python memory with `sar_markdown` omitted.
- **Modernized**: Paginated SQL query with optional filtering:
  ```python
  @router.get("/cases")
  async def list_upi_cases(
      status: Optional[str] = None,
      verdict: Optional[str] = None,
      limit: int = 50,
      offset: int = 0,
      db: AsyncSession = Depends(get_db),
  ):
      query = select(UpiCaseModel).order_by(UpiCaseModel.created_at.desc())
      if status:
          query = query.where(UpiCaseModel.status == status)
      if verdict:
          query = query.where(UpiCaseModel.verdict == verdict)
      
      total_count = await db.scalar(select(func.count()).select_from(query.subquery()))
      result = await db.execute(query.limit(limit).offset(offset))
      items = result.scalars().all()
      
      return {
          "count": total_count,
          "items": [
              {
                  "case_id": c.case_id,
                  "created_at": c.created_at.isoformat(),
                  "status": c.status,
                  "verdict": c.verdict,
                  "risk_score": c.risk_score,
                  "trigger_txn": c.trigger_txn,
                  "rule_hits": c.rule_hits,
                  "adaptive_score": c.adaptive_score,
                  "network_score": c.network_score,
                  "ring_hash": c.ring_hash,
                  "ring_members_vpas": c.ring_members_vpas or [],
                  "token_economy": c.token_economy,
                  "visual_path": c.visual_path,
                  "topology": c.topology,
                  "resolution": c.resolution,
                  "investigated_at": c.investigated_at.isoformat() if c.investigated_at else None,
              }
              for c in items
          ],
      }
  ```

#### B. `/upi/cases/{case_id}` (`GET`)
- **Modernized**: Fetches single record by PK:
  ```python
  @router.get("/cases/{case_id}")
  async def get_upi_case(case_id: str, db: AsyncSession = Depends(get_db)):
      result = await db.execute(select(UpiCaseModel).where(UpiCaseModel.case_id == case_id))
      case = result.scalar_one_or_none()
      if not case:
          raise HTTPException(status_code=404, detail="UPI Case not found")
      return {
          "case_id": case.case_id,
          "created_at": case.created_at.isoformat(),
          "status": case.status,
          "verdict": case.verdict,
          "risk_score": case.risk_score,
          "trigger_txn": case.trigger_txn,
          "rule_hits": case.rule_hits,
          "adaptive_score": case.adaptive_score,
          "network_score": case.network_score,
          "ring_hash": case.ring_hash,
          "ring_members_vpas": case.ring_members_vpas or [],
          "token_economy": case.token_economy,
          "sar_markdown": case.sar_markdown,
          "visual_path": case.visual_path,
          "topology": case.topology,
          "resolution": case.resolution,
          "investigated_at": case.investigated_at.isoformat() if case.investigated_at else None,
      }
  ```

#### C. `/upi/stats` (`GET`)
- **Modernized**: Efficient aggregation queries executed directly in PostgreSQL:
  ```python
  @router.get("/stats")
  async def upi_stats(db: AsyncSession = Depends(get_db)):
      # Case counts by status
      status_counts = dict(
          await db.execute(
              select(UpiCaseModel.status, func.count(UpiCaseModel.case_id))
              .group_by(UpiCaseModel.status)
          )
      )
      
      # Distinct rings count
      rings_count = await db.scalar(select(func.count(MuleRingModel.ring_hash)))
      
      total_cases = sum(status_counts.values())
      
      return {
          "cases": {
              "total": total_cases,
              "open": status_counts.get("OPEN", 0),
              "investigated": status_counts.get("INVESTIGATED", 0),
              "resolved": status_counts.get("RESOLVED", 0),
          },
          "rings_known": rings_count or 0,
          "dpip": get_dpip().stats(),
          "adaptive_sensitivity": get_adaptive_model().sensitivity,
      }
  ```

#### D. `/health` (`GET`)
- **Current**: Static dictionary `{"status": "ok", "service": "sampati-upi", "version": "2.0.0"}`.
- **Modernized**: Active DB readiness probe verifying connection pool availability:
  ```python
  @app.get("/health")
  async def health_check():
      db_status = "connected"
      try:
          eng = get_engine()
          async with eng.connect() as conn:
              await conn.execute(text("SELECT 1"))
      except Exception as e:
          db_status = f"disconnected: {str(e)}"

      status_code = 200 if "disconnected" not in db_status else 503
      return JSONResponse(
          status_code=status_code,
          content={
              "status": "ok" if status_code == 200 else "degraded",
              "service": "sampati-upi",
              "version": "2.0.0",
              "database": db_status,
              "timestamp": datetime.now(timezone.utc).isoformat(),
          }
      )
  ```

---

## 7. Migration & Rollback Strategy

1. **Dual-Mode Startup**: If `DATABASE_URL` is unset or database connection fails, the application logs a warning and smoothly falls back to in-memory dictionaries so development and testing can proceed seamlessly.
2. **Schema Creation**: Automated `Base.metadata.create_all` during FastAPI `lifespan` startup eliminates manual migration friction on first deployment.
3. **Graceful Teardown**: `await engine.dispose()` on application shutdown cleanly terminates open pool connections before SIGKILL.

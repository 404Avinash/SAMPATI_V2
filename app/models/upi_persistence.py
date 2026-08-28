"""SQLAlchemy 2.0 Declarative Models for SAMPATI V2 Database Persistence.

Optimized for AWS RDS PostgreSQL with JSONB support, compound indexing,
and graceful cross-dialect compatibility.
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
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Use native JSONB for PostgreSQL while maintaining JSON compatibility for SQLite/testing
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class UpiCaseModel(Base):
    """Persistent storage for flagged UPI interception cases."""
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
    trigger_txn = Column(JSON_TYPE, nullable=False)
    rule_hits = Column(JSON_TYPE, default=list, nullable=False)

    # Layer 2 & 3 scores
    adaptive_score = Column(Float, default=0.0, nullable=False)
    network_score = Column(Float, default=0.0, nullable=False)

    # Mule Ring association
    ring_hash = Column(String(64), ForeignKey("mule_rings.ring_hash", ondelete="SET NULL"), nullable=True, index=True)
    ring_members_vpas = Column(JSON_TYPE, default=list, nullable=True)

    # Layer 4 Visual Forensics & SAR
    token_economy = Column(JSON_TYPE, nullable=True)
    sar_markdown = Column(Text, nullable=True)
    visual_path = Column(String(255), nullable=True)
    topology = Column(JSON_TYPE, nullable=True)

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

    def to_dict(self, include_sar: bool = True) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        d = {
            "case_id": self.case_id,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "status": self.status,
            "verdict": self.verdict,
            "risk_score": self.risk_score,
            "payer_vpa": self.payer_vpa,
            "payee_vpa": self.payee_vpa,
            "amount": float(self.amount) if self.amount is not None else (self.trigger_txn.get("amount") if isinstance(self.trigger_txn, dict) else None),
            "trigger_txn": self.trigger_txn,
            "rule_hits": self.rule_hits or [],
            "adaptive_score": float(self.adaptive_score or 0.0),
            "network_score": float(self.network_score or 0.0),
            "ring_hash": self.ring_hash,
            "ring_members_vpas": self.ring_members_vpas or [],
            "token_economy": self.token_economy,
            "visual_path": self.visual_path,
            "topology": self.topology,
            "resolution": self.resolution,
            "investigated_at": self.investigated_at.isoformat() if isinstance(self.investigated_at, datetime) else (str(self.investigated_at) if self.investigated_at else None),
            "resolution_notes": self.resolution_notes,
        }
        if include_sar:
            d["sar_markdown"] = self.sar_markdown
        return d


class MuleRingModel(Base):
    """Persistent registry of discovered cross-PSP mule rings."""
    __tablename__ = "mule_rings"

    ring_hash = Column(String(64), primary_key=True, index=True)
    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    size = Column(Integer, nullable=False)
    members = Column(JSON_TYPE, nullable=False)  # List of member VPAs or node descriptors
    psps = Column(JSON_TYPE, nullable=False)     # Distinct PSP handles involved
    total_amount = Column(Numeric(14, 2), default=0.0, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, DISMANTLED, ARCHIVED

    # Relationships
    cases = relationship("UpiCaseModel", back_populates="mule_ring")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        return {
            "ring_hash": self.ring_hash,
            "detected_at": self.detected_at.isoformat() if isinstance(self.detected_at, datetime) else str(self.detected_at),
            "size": self.size,
            "members": self.members or [],
            "psps": self.psps or [],
            "total_amount": float(self.total_amount or 0.0),
            "status": self.status,
        }


class CaseFeedbackModel(Base):
    """Audit log of human investigator resolutions and feedback."""
    __tablename__ = "case_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("upi_cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    confirmed_fraud = Column(Boolean, nullable=False)
    resolution = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    submitted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    vpas_flagged = Column(JSON_TYPE, default=list, nullable=False)
    dpip_published = Column(JSON_TYPE, nullable=True)

    # Relationships
    case = relationship("UpiCaseModel", back_populates="feedbacks")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "confirmed_fraud": self.confirmed_fraud,
            "resolution": self.resolution,
            "notes": self.notes,
            "submitted_at": self.submitted_at.isoformat() if isinstance(self.submitted_at, datetime) else str(self.submitted_at),
            "vpas_flagged": self.vpas_flagged or [],
            "dpip_published": self.dpip_published,
        }


class AggregateStatsModel(Base):
    """Persistent high-watermark aggregate telemetry metrics."""
    __tablename__ = "aggregate_stats"

    stat_key = Column(String(64), primary_key=True)
    stat_value = Column(Numeric(18, 4), default=0.0, nullable=False)
    metadata_json = Column(JSON_TYPE, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def metric_name(self) -> str:
        return self.stat_key

    @metric_name.setter
    def metric_name(self, value: str) -> None:
        self.stat_key = value

    @property
    def metric_value(self) -> Any:
        return self.stat_value

    @metric_value.setter
    def metric_value(self, value: Any) -> None:
        self.stat_value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        return {
            "stat_key": self.stat_key,
            "stat_value": float(self.stat_value or 0.0),
            "metric_name": self.stat_key,
            "metric_value": float(self.stat_value or 0.0),
            "metadata_json": self.metadata_json,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else str(self.updated_at),
        }

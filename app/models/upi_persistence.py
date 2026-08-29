"""SQLAlchemy 2.0 Declarative Models for SAMPATI V2 Database Persistence.

Optimized for AWS RDS PostgreSQL with JSONB support, compound indexing,
and graceful cross-dialect compatibility.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
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
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
    JSON_TYPE = JSON().with_variant(JSONB, "postgresql")
except ImportError:
    SQLALCHEMY_AVAILABLE = False

    class _Base:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    Base = _Base  # type: ignore

    def Column(*args, **kwargs):
        return None

    def relationship(*args, **kwargs):
        return None

    def Index(*args, **kwargs):
        return None

    def ForeignKey(*args, **kwargs):
        return None

    class _TypeMock:
        def __init__(self, *args, **kwargs):
            pass

        def with_variant(self, *args, **kwargs):
            return self

    String = Integer = Float = DateTime = JSON = Numeric = Text = Boolean = JSONB = JSON_TYPE = _TypeMock  # type: ignore


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
    status = Column(String(32), default="OPEN", nullable=False, index=True)  # OPEN, REVIEWED, ESCALATED, DISMISSED, INVESTIGATED, RESOLVED
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
    resolution = Column(String(64), nullable=True)  # REVIEWED_COMPLIANCE, ESCALATED_DPIP, DISMISSED_FALSE_POSITIVE
    investigated_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    mule_ring = relationship("MuleRingModel", back_populates="cases")
    feedbacks = relationship("CaseFeedbackModel", back_populates="case", cascade="all, delete-orphan")

    if SQLALCHEMY_AVAILABLE:
        __table_args__ = (
            Index("ix_upi_cases_status_created", "status", "created_at"),
            Index("ix_upi_cases_verdict_created", "verdict", "created_at"),
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self, include_sar: bool = True) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        def _safe_f(v, default=0.0):
            try:
                return float(v)
            except Exception:
                return default

        def _safe_i(v, default=0):
            try:
                return int(v)
            except Exception:
                return default

        amt_val = getattr(self, "amount", None)
        if amt_val is not None:
            amt = _safe_f(amt_val, None)
        elif isinstance(getattr(self, "trigger_txn", None), dict):
            amt = _safe_f(self.trigger_txn.get("amount"), None)
        else:
            amt = None

        d = {
            "case_id": getattr(self, "case_id", None) if not hasattr(getattr(self, "case_id", None), "name") else None,
            "created_at": self.created_at.isoformat() if isinstance(getattr(self, "created_at", None), datetime) else str(getattr(self, "created_at", "")),
            "status": getattr(self, "status", "OPEN") if isinstance(getattr(self, "status", None), str) else "OPEN",
            "verdict": getattr(self, "verdict", "HOLD") if isinstance(getattr(self, "verdict", None), str) else "HOLD",
            "risk_score": _safe_i(getattr(self, "risk_score", 0), 0),
            "payer_vpa": getattr(self, "payer_vpa", None) if isinstance(getattr(self, "payer_vpa", None), str) else None,
            "payee_vpa": getattr(self, "payee_vpa", None) if isinstance(getattr(self, "payee_vpa", None), str) else None,
            "amount": amt,
            "trigger_txn": getattr(self, "trigger_txn", {}) if isinstance(getattr(self, "trigger_txn", None), dict) else {},
            "rule_hits": getattr(self, "rule_hits", None) if isinstance(getattr(self, "rule_hits", None), list) else [],
            "adaptive_score": _safe_f(getattr(self, "adaptive_score", 0.0), 0.0),
            "network_score": _safe_f(getattr(self, "network_score", 0.0), 0.0),
            "ring_hash": getattr(self, "ring_hash", None) if isinstance(getattr(self, "ring_hash", None), str) else None,
            "ring_members_vpas": getattr(self, "ring_members_vpas", None) if isinstance(getattr(self, "ring_members_vpas", None), list) else [],
            "token_economy": getattr(self, "token_economy", None) if isinstance(getattr(self, "token_economy", None), dict) else None,
            "visual_path": getattr(self, "visual_path", None) if isinstance(getattr(self, "visual_path", None), str) else None,
            "topology": getattr(self, "topology", None) if isinstance(getattr(self, "topology", None), dict) else None,
            "resolution": getattr(self, "resolution", None) if isinstance(getattr(self, "resolution", None), str) else None,
            "investigated_at": self.investigated_at.isoformat() if isinstance(getattr(self, "investigated_at", None), datetime) else (str(self.investigated_at) if getattr(self, "investigated_at", None) and not hasattr(getattr(self, "investigated_at", None), "name") else None),
            "resolution_notes": getattr(self, "resolution_notes", None) if isinstance(getattr(self, "resolution_notes", None), str) else None,
        }
        if include_sar:
            d["sar_markdown"] = getattr(self, "sar_markdown", None) if isinstance(getattr(self, "sar_markdown", None), str) else None
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        return {
            "ring_hash": getattr(self, "ring_hash", None),
            "detected_at": self.detected_at.isoformat() if isinstance(getattr(self, "detected_at", None), datetime) else str(getattr(self, "detected_at", "")),
            "size": getattr(self, "size", 0),
            "members": getattr(self, "members", None) or [],
            "psps": getattr(self, "psps", None) or [],
            "total_amount": float(getattr(self, "total_amount", 0.0) or 0.0),
            "status": getattr(self, "status", "ACTIVE"),
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        return {
            "id": getattr(self, "id", None),
            "case_id": getattr(self, "case_id", None),
            "confirmed_fraud": getattr(self, "confirmed_fraud", False),
            "resolution": getattr(self, "resolution", ""),
            "notes": getattr(self, "notes", None),
            "submitted_at": self.submitted_at.isoformat() if isinstance(getattr(self, "submitted_at", None), datetime) else str(getattr(self, "submitted_at", "")),
            "vpas_flagged": getattr(self, "vpas_flagged", None) or [],
            "dpip_published": getattr(self, "dpip_published", None),
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def metric_name(self) -> str:
        return getattr(self, "stat_key", "")

    @metric_name.setter
    def metric_name(self, value: str) -> None:
        self.stat_key = value

    @property
    def metric_value(self) -> Any:
        return getattr(self, "stat_value", 0.0)

    @metric_value.setter
    def metric_value(self, value: Any) -> None:
        self.stat_value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a JSON-serializable dictionary."""
        return {
            "stat_key": getattr(self, "stat_key", ""),
            "stat_value": float(getattr(self, "stat_value", 0.0) or 0.0),
            "metric_name": getattr(self, "stat_key", ""),
            "metric_value": float(getattr(self, "stat_value", 0.0) or 0.0),
            "metadata_json": getattr(self, "metadata_json", None),
            "updated_at": self.updated_at.isoformat() if isinstance(getattr(self, "updated_at", None), datetime) else str(getattr(self, "updated_at", "")),
        }

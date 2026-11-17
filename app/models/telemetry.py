"""SQLAlchemy 2.0 Declarative Models and Pydantic Schemas for Telemetry & On-Device Threat Logging.

Engineered for SAMPATI V2 with SQLAlchemy 2.0 style (Mapped, mapped_column, relationship),
cross-dialect PostgreSQL and SQLite compatibility using generic types, and Pydantic v2
input/response schemas with OpenAPI model_config examples and field validations.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseModel, Field  # type: ignore
    PYDANTIC_V2 = False

    class ConfigDict(dict):  # type: ignore
        pass

    def field_validator(*args, **kwargs):  # type: ignore
        def decorator(f):
            return f
        return decorator

try:
    from sqlalchemy import (
        Boolean,
        DateTime,
        Float,
        ForeignKey,
        Index,
        Integer,
        JSON,
        String,
        Text,
    )
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Mapped = Any  # type: ignore

    def mapped_column(*args, **kwargs):  # type: ignore
        return None

    def relationship(*args, **kwargs):  # type: ignore
        return None

from app.models.upi_persistence import Base


def utcnow() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


# ── SQLAlchemy 2.0 Persistent Database Models ─────────────────────────────────

class ThreatEvent(Base):
    """Persistent storage for on-device detected threat events.

    Uses SQLAlchemy 2.0 Mapped annotations, generic types for cross-database
    compatibility (PostgreSQL and SQLite), and relationships to UserOverride.
    """
    __tablename__ = "threat_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique threat event identifier (e.g. EVT-XXXXXXXXXXXX)",
    )
    device_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        doc="Unique client or hardware-derived device identifier",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        index=True,
        nullable=True,
        doc="Optional user or account identifier associated with the device",
    )
    threat_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        doc="Threat classification (SMS_PHISHING, MALICIOUS_APP, OVERLAY_ATTACK, etc.)",
    )
    severity: Mapped[str] = mapped_column(
        String(32),
        default="MEDIUM",
        index=True,
        nullable=False,
        doc="Threat severity level: LOW, MEDIUM, HIGH, CRITICAL",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.85,
        nullable=False,
        doc="Detection confidence score in [0.0, 1.0]",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="DETECTED",
        index=True,
        nullable=False,
        doc="Event lifecycle state: DETECTED, BLOCKED, WARNED, IGNORED, OVERRIDDEN, RESOLVED",
    )
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Automated mitigation applied on-device (e.g. NOTIFIED_USER, BLOCKED_APP)",
    )
    package_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Target package name or bundle identifier if app-related",
    )
    platform: Mapped[str] = mapped_column(
        String(32),
        default="android",
        nullable=False,
        doc="Client operating system platform (android, ios, web)",
    )
    app_version: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        doc="Client application version",
    )
    os_version: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        doc="Operating system version string",
    )
    threat_source: Mapped[str] = mapped_column(
        String(64),
        default="on_device_scanner",
        nullable=False,
        doc="Detection subsystem or engine origin",
    )
    vpa: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        doc="Intercepted or associated UPI Virtual Payment Address",
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        doc="Associated phone number extracted from threat context",
    )
    raw_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Detailed JSON telemetry payload or diagnostic metadata",
    )
    device_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Client device timestamp when threat was observed",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
        index=True,
        doc="UTC server reception timestamp",
    )

    # SQLAlchemy 2.0 Relationships
    overrides: Mapped[List[UserOverride]] = relationship(
        "UserOverride",
        back_populates="threat_event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    if SQLALCHEMY_AVAILABLE:
        __table_args__ = (
            Index("ix_threat_events_severity_created", "severity", "created_at"),
            Index("ix_threat_events_threat_type_created", "threat_type", "created_at"),
            Index("ix_threat_events_device_created", "device_id", "created_at"),
        )

    @property
    def override_count(self) -> int:
        """Safe property accessor for override count."""
        try:
            return len(self.overrides) if hasattr(self, "overrides") and self.overrides else 0
        except Exception:
            return 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize model instance to a JSON-compatible dictionary."""
        dev_ts = self.device_timestamp
        if isinstance(dev_ts, datetime):
            dev_ts_str = dev_ts.isoformat()
        else:
            dev_ts_str = str(dev_ts) if dev_ts else None

        created = self.created_at
        if isinstance(created, datetime):
            created_str = created.isoformat()
        else:
            created_str = str(created) if created else utcnow().isoformat()

        raw = self.raw_payload
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = {}
        elif not isinstance(raw, dict):
            raw = {}

        return {
            "event_id": self.event_id,
            "device_id": self.device_id,
            "user_id": self.user_id,
            "threat_type": self.threat_type,
            "severity": self.severity,
            "confidence": float(self.confidence or 0.0),
            "status": self.status,
            "action_taken": self.action_taken,
            "package_name": self.package_name,
            "platform": self.platform or "android",
            "app_version": self.app_version,
            "os_version": self.os_version,
            "threat_source": self.threat_source or "on_device_scanner",
            "vpa": self.vpa,
            "phone_number": self.phone_number,
            "raw_payload": raw,
            "device_timestamp": dev_ts_str,
            "created_at": created_str,
            "override_count": self.override_count,
        }


class UserOverride(Base):
    """Persistent storage for user or investigator feedback overrides on threat events.

    Uses SQLAlchemy 2.0 Mapped annotations and generic types for cross-database
    compatibility (PostgreSQL and SQLite).
    """
    __tablename__ = "user_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    override_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique override action identifier (e.g. OVR-XXXXXXXXXXXX)",
    )
    event_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("threat_events.event_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Target threat event identifier being overridden",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        index=True,
        nullable=True,
        doc="User or investigator identifier submitting the override",
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        index=True,
        nullable=True,
        doc="Device identifier from which override originated",
    )
    override_reason: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Standardized override reason (FALSE_POSITIVE, USER_CONSENT, etc.)",
    )
    user_action: Mapped[str] = mapped_column(
        String(32),
        default="PROCEED_ANYWAY",
        nullable=False,
        doc="Decision taken: PROCEED_ANYWAY, ALLOW_ALWAYS, DISMISS_ALERT, REPORT_SAFE",
    )
    feedback_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User narrative or investigator notes explaining override rationale",
    )
    risk_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Flag confirming user explicitly confirmed risk warning dialog",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Contextual UI telemetry metadata (e.g. screen name, dwell time)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
        index=True,
        doc="UTC server override registration timestamp",
    )

    # SQLAlchemy 2.0 Relationships
    threat_event: Mapped[Optional[ThreatEvent]] = relationship(
        "ThreatEvent",
        back_populates="overrides",
        lazy="selectin",
    )

    if SQLALCHEMY_AVAILABLE:
        __table_args__ = (
            Index("ix_user_overrides_event_created", "event_id", "created_at"),
            Index("ix_user_overrides_reason_created", "override_reason", "created_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize model instance to a JSON-compatible dictionary."""
        created = self.created_at
        if isinstance(created, datetime):
            created_str = created.isoformat()
        else:
            created_str = str(created) if created else utcnow().isoformat()

        meta = self.metadata_json
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        elif not isinstance(meta, dict):
            meta = {}

        return {
            "override_id": self.override_id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "override_reason": self.override_reason,
            "user_action": self.user_action,
            "feedback_notes": self.feedback_notes,
            "risk_acknowledged": bool(self.risk_acknowledged),
            "metadata_json": meta,
            "created_at": created_str,
        }


# ── Pydantic Schemas & OpenAPI Documentation ──────────────────────────────────

class ThreatEventCreate(BaseModel):
    """Payload schema for ingesting an on-device threat telemetry event."""

    device_id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Unique client or hardware-derived device identifier",
    )
    user_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="User or account identifier associated with the device",
    )
    threat_type: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Classification of threat: SMS_PHISHING, MALICIOUS_APP, OVERLAY_ATTACK, ACCESSIBILITY_ABUSE, UPI_TAMPERING, CALL_FORWARDING, etc.",
    )
    severity: str = Field(
        default="MEDIUM",
        description="Threat severity rating: LOW, MEDIUM, HIGH, CRITICAL",
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Detection confidence score between 0.0 and 1.0",
    )
    status: str = Field(
        default="DETECTED",
        description="Initial event status: DETECTED, BLOCKED, WARNED, IGNORED, OVERRIDDEN, RESOLVED",
    )
    action_taken: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Automated mitigation applied on-device (e.g. NOTIFIED_USER, BLOCKED_APP)",
    )
    package_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Target package name or bundle identifier if threat is application-level",
    )
    platform: str = Field(
        default="android",
        max_length=32,
        description="Client OS platform (android, ios, web)",
    )
    app_version: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Client application release version",
    )
    os_version: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Operating system version string (e.g. Android 14)",
    )
    threat_source: str = Field(
        default="on_device_scanner",
        max_length=64,
        description="Detection engine or subsystem origin",
    )
    vpa: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Associated UPI Virtual Payment Address if extracted from threat context",
    )
    phone_number: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Associated phone number if extracted from threat context",
    )
    raw_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Arbitrary JSON telemetry details or diagnostic payload",
    )
    device_timestamp: Optional[datetime] = Field(
        default=None,
        description="ISO-8601 timestamp recorded by client device when threat was detected",
    )

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 3:
            raise ValueError("device_id must be at least 3 non-whitespace characters")
        return s

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        s = v.strip().lower()
        return s if s else "android"

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        s = v.strip().upper()
        allowed = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if s not in allowed:
            raise ValueError(f"Invalid severity '{v}'. Allowed values: {', '.join(sorted(allowed))}")
        return s

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        s = v.strip().upper()
        allowed = {"DETECTED", "BLOCKED", "WARNED", "IGNORED", "OVERRIDDEN", "RESOLVED"}
        if s not in allowed:
            raise ValueError(f"Invalid status '{v}'. Allowed values: {', '.join(sorted(allowed))}")
        return s

    @field_validator("threat_type")
    @classmethod
    def validate_threat_type(cls, v: str) -> str:
        s = v.strip().upper()
        if len(s) < 2:
            raise ValueError("threat_type must be at least 2 non-whitespace characters")
        return s

    @field_validator("device_timestamp", mode="before")
    @classmethod
    def parse_optional_device_timestamp(cls, v: Any) -> Optional[Any]:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            if not s or s.lower() == "none":
                return None
            return s
        return v

    @field_validator(
        "user_id",
        "action_taken",
        "package_name",
        "app_version",
        "os_version",
        "threat_source",
        "vpa",
        "phone_number",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "dev_9f8a7b6c5d4e",
                "user_id": "usr_78910",
                "threat_type": "SMS_PHISHING",
                "severity": "HIGH",
                "confidence": 0.94,
                "status": "DETECTED",
                "action_taken": "NOTIFIED_USER",
                "package_name": "com.fake.sbi.reward",
                "platform": "android",
                "app_version": "2.4.0",
                "os_version": "Android 14",
                "threat_source": "sms_heuristic_monitor",
                "vpa": "fraudster99@paytm",
                "phone_number": "+919876543210",
                "raw_payload": {
                    "matched_keywords": ["pan card", "blocked", "immediate"],
                    "sender_header": "VM-SBIINB",
                },
                "device_timestamp": "2026-09-05T12:00:00Z",
            }
        }
    )


class ThreatEventResponse(BaseModel):
    """Enriched response schema for an ingested threat event."""

    event_id: str = Field(
        ...,
        description="Unique immutable threat event identifier (EVT-XXXXXXXXXXXX)",
    )
    device_id: str = Field(
        ...,
        description="Unique client or hardware-derived device identifier",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User or account identifier associated with the device",
    )
    threat_type: str = Field(
        ...,
        description="Classification of threat",
    )
    severity: str = Field(
        ...,
        description="Assessed threat severity level",
    )
    confidence: float = Field(
        ...,
        description="Confidence score in [0.0, 1.0]",
    )
    status: str = Field(
        ...,
        description="Current event lifecycle state",
    )
    action_taken: Optional[str] = Field(
        default=None,
        description="Automated mitigation applied on-device",
    )
    package_name: Optional[str] = Field(
        default=None,
        description="Target package name or bundle identifier",
    )
    platform: str = Field(
        default="android",
        description="Client OS platform",
    )
    app_version: Optional[str] = Field(
        default=None,
        description="Client application release version",
    )
    os_version: Optional[str] = Field(
        default=None,
        description="Operating system version",
    )
    threat_source: str = Field(
        default="on_device_scanner",
        description="Detection subsystem or engine origin",
    )
    vpa: Optional[str] = Field(
        default=None,
        description="Associated UPI Virtual Payment Address",
    )
    phone_number: Optional[str] = Field(
        default=None,
        description="Associated phone number",
    )
    raw_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed JSON telemetry payload",
    )
    device_timestamp: Optional[str] = Field(
        default=None,
        description="ISO-8601 client device timestamp",
    )
    created_at: str = Field(
        ...,
        description="UTC ISO-8601 server registration timestamp",
    )
    override_count: int = Field(
        default=0,
        description="Count of user overrides recorded against this event",
    )

    @field_validator("device_id", mode="before")
    @classmethod
    def default_device_id(cls, v: Any) -> str:
        s = str(v).strip() if v else "unknown_device"
        return s if s else "unknown_device"

    @field_validator("threat_type", mode="before")
    @classmethod
    def default_threat_type(cls, v: Any) -> str:
        s = str(v).strip().upper() if v else "UNKNOWN"
        return s if s else "UNKNOWN"

    @field_validator("severity", mode="before")
    @classmethod
    def default_severity(cls, v: Any) -> str:
        s = str(v).strip().upper() if v else "MEDIUM"
        return s if s else "MEDIUM"

    @field_validator("confidence", mode="before")
    @classmethod
    def default_confidence(cls, v: Any) -> float:
        if v is None:
            return 0.85
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.85

    @field_validator("status", mode="before")
    @classmethod
    def default_status(cls, v: Any) -> str:
        s = str(v).strip().upper() if v else "DETECTED"
        return s if s else "DETECTED"

    @field_validator("raw_payload", mode="before")
    @classmethod
    def deserialize_raw_payload(cls, v: Any) -> Optional[Dict[str, Any]]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return v if isinstance(v, dict) else (v or {})

    @field_validator("platform", mode="before")
    @classmethod
    def default_platform(cls, v: Any) -> str:
        return str(v).strip().lower() if v else "android"

    @field_validator("threat_source", mode="before")
    @classmethod
    def default_threat_source(cls, v: Any) -> str:
        return str(v).strip() if v else "on_device_scanner"

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at(cls, v: Any) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        if v is not None:
            s = str(v).strip()
            if s and s.lower() != "none":
                return s
        return utcnow().isoformat()

    @field_validator("device_timestamp", mode="before")
    @classmethod
    def serialize_device_timestamp(cls, v: Any) -> Optional[str]:
        if isinstance(v, datetime):
            return v.isoformat()
        if v is None:
            return None
        s = str(v).strip()
        return s if s and s.lower() != "none" else None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "event_id": "EVT-9F8A7B6C5D4E",
                "device_id": "dev_9f8a7b6c5d4e",
                "user_id": "usr_78910",
                "threat_type": "SMS_PHISHING",
                "severity": "HIGH",
                "confidence": 0.94,
                "status": "DETECTED",
                "action_taken": "NOTIFIED_USER",
                "package_name": "com.fake.sbi.reward",
                "platform": "android",
                "app_version": "2.4.0",
                "os_version": "Android 14",
                "threat_source": "sms_heuristic_monitor",
                "vpa": "fraudster99@paytm",
                "phone_number": "+919876543210",
                "raw_payload": {
                    "matched_keywords": ["pan card", "blocked", "immediate"],
                    "sender_header": "VM-SBIINB",
                },
                "device_timestamp": "2026-09-05T12:00:00Z",
                "created_at": "2026-09-05T12:00:01.123456+00:00",
                "override_count": 0,
            }
        },
    )


class ThreatEventListResponse(BaseModel):
    """Paginated collection of threat telemetry events."""

    total: int = Field(
        ...,
        ge=0,
        description="Total number of threat events matching query criteria",
    )
    events: List[ThreatEventResponse] = Field(
        default_factory=list,
        description="List of threat telemetry event records",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "events": [
                    {
                        "event_id": "EVT-9F8A7B6C5D4E",
                        "device_id": "dev_9f8a7b6c5d4e",
                        "threat_type": "SMS_PHISHING",
                        "severity": "HIGH",
                        "confidence": 0.94,
                        "status": "DETECTED",
                        "platform": "android",
                        "created_at": "2026-09-05T12:00:01.123456+00:00",
                        "override_count": 0,
                    }
                ],
            }
        }
    )


class UserOverrideCreate(BaseModel):
    """Payload schema for submitting a user or analyst override on a threat event."""

    event_id: str = Field(
        ...,
        min_length=5,
        max_length=64,
        description="Target threat event identifier being overridden (e.g. EVT-XXXXXXXXXXXX)",
    )
    user_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Identifier of user or investigator submitting the override",
    )
    device_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Device identifier where the override was performed",
    )
    override_reason: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Standardized override reason: FALSE_POSITIVE, USER_CONSENT, LEGITIMATE_APP, SECURITY_EXEMPTION, TESTING, OTHER",
    )
    user_action: str = Field(
        default="PROCEED_ANYWAY",
        max_length=32,
        description="User decision: PROCEED_ANYWAY, ALLOW_ALWAYS, DISMISS_ALERT, REPORT_SAFE, WHITELIST",
    )
    feedback_notes: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Optional narrative context or explanation for why the warning was overridden",
    )
    risk_acknowledged: bool = Field(
        default=False,
        description="Whether user explicitly confirmed the risk acknowledgment warning dialog",
    )
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Auxiliary client UI telemetry context (e.g. dialog dwell time, screen name)",
    )

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        s = v.strip().upper()
        if len(s) < 5:
            raise ValueError("event_id must be at least 5 non-whitespace characters")
        return s

    @field_validator("override_reason")
    @classmethod
    def validate_override_reason(cls, v: str) -> str:
        s = v.strip().upper()
        if len(s) < 2:
            raise ValueError("override_reason must be at least 2 non-whitespace characters")
        return s

    @field_validator("user_id", "device_id", "feedback_notes", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("user_action")
    @classmethod
    def validate_user_action(cls, v: str) -> str:
        s = v.strip().upper()
        allowed = {"PROCEED_ANYWAY", "ALLOW_ALWAYS", "DISMISS_ALERT", "REPORT_SAFE", "WHITELIST", "IGNORE_WARNING"}
        if s not in allowed:
            raise ValueError(f"Invalid user_action '{v}'. Allowed values: {', '.join(sorted(allowed))}")
        return s

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "EVT-9F8A7B6C5D4E",
                "user_id": "usr_78910",
                "device_id": "dev_9f8a7b6c5d4e",
                "override_reason": "FALSE_POSITIVE",
                "user_action": "PROCEED_ANYWAY",
                "feedback_notes": "Official bank branch notification verified by customer care.",
                "risk_acknowledged": True,
                "metadata_json": {
                    "screen_name": "ThreatWarningDialog",
                    "interaction_dwell_seconds": 4.5,
                },
            }
        }
    )


class UserOverrideResponse(BaseModel):
    """Enriched response schema for a recorded user override."""

    override_id: str = Field(
        ...,
        description="Unique immutable override action identifier (OVR-XXXXXXXXXXXX)",
    )
    event_id: str = Field(
        ...,
        description="Target threat event identifier that was overridden",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User or investigator identifier submitting the override",
    )
    device_id: Optional[str] = Field(
        default=None,
        description="Device identifier where override was executed",
    )
    override_reason: str = Field(
        ...,
        description="Standardized override reason",
    )
    user_action: str = Field(
        ...,
        description="Action performed by user",
    )
    feedback_notes: Optional[str] = Field(
        default=None,
        description="Narrative context or investigator rationale",
    )
    risk_acknowledged: bool = Field(
        ...,
        description="Confirmation that risk warning was acknowledged",
    )
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contextual UI telemetry metadata",
    )
    created_at: str = Field(
        ...,
        description="UTC ISO-8601 server override registration timestamp",
    )

    @field_validator("override_reason", mode="before")
    @classmethod
    def default_override_reason(cls, v: Any) -> str:
        s = str(v).strip().upper() if v else "OTHER"
        return s if s else "OTHER"

    @field_validator("user_action", mode="before")
    @classmethod
    def default_user_action(cls, v: Any) -> str:
        s = str(v).strip().upper() if v else "PROCEED_ANYWAY"
        return s if s else "PROCEED_ANYWAY"

    @field_validator("risk_acknowledged", mode="before")
    @classmethod
    def default_risk_acknowledged(cls, v: Any) -> bool:
        if v is None:
            return False
        return bool(v)

    @field_validator("metadata_json", mode="before")
    @classmethod
    def deserialize_metadata_json(cls, v: Any) -> Optional[Dict[str, Any]]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return v if isinstance(v, dict) else (v or {})

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at(cls, v: Any) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        if v is not None:
            s = str(v).strip()
            if s and s.lower() != "none":
                return s
        return utcnow().isoformat()

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "override_id": "OVR-3A4B5C6D7E8F",
                "event_id": "EVT-9F8A7B6C5D4E",
                "user_id": "usr_78910",
                "device_id": "dev_9f8a7b6c5d4e",
                "override_reason": "FALSE_POSITIVE",
                "user_action": "PROCEED_ANYWAY",
                "feedback_notes": "Official bank branch notification verified by customer care.",
                "risk_acknowledged": True,
                "metadata_json": {
                    "screen_name": "ThreatWarningDialog",
                    "interaction_dwell_seconds": 4.5,
                },
                "created_at": "2026-09-05T12:05:00.654321+00:00",
            }
        },
    )


class UserOverrideListResponse(BaseModel):
    """Paginated collection of user override records."""

    total: int = Field(
        ...,
        ge=0,
        description="Total number of overrides matching query criteria",
    )
    overrides: List[UserOverrideResponse] = Field(
        default_factory=list,
        description="List of user override records",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "overrides": [
                    {
                        "override_id": "OVR-3A4B5C6D7E8F",
                        "event_id": "EVT-9F8A7B6C5D4E",
                        "user_id": "usr_78910",
                        "device_id": "dev_9f8a7b6c5d4e",
                        "override_reason": "FALSE_POSITIVE",
                        "user_action": "PROCEED_ANYWAY",
                        "risk_acknowledged": True,
                        "created_at": "2026-09-05T12:05:00.654321+00:00",
                    }
                ],
            }
        }
    )


class TelemetryStatsResponse(BaseModel):
    """Aggregated telemetry metrics and override breakdown."""

    total_events: int = Field(..., ge=0, description="Total ingested threat events")
    total_overrides: int = Field(..., ge=0, description="Total user overrides recorded")
    override_rate: float = Field(..., ge=0.0, le=1.0, description="Proportion of threat events overridden [0.0, 1.0]")
    severity_breakdown: Dict[str, int] = Field(default_factory=dict, description="Event count by severity rating")
    threat_type_breakdown: Dict[str, int] = Field(default_factory=dict, description="Event count by threat category")
    override_reason_breakdown: Dict[str, int] = Field(default_factory=dict, description="Override count by reason")
    active_devices_count: int = Field(..., ge=0, description="Count of distinct reporting device identifiers")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_events": 150,
                "total_overrides": 12,
                "override_rate": 0.08,
                "severity_breakdown": {"CRITICAL": 20, "HIGH": 45, "MEDIUM": 60, "LOW": 25},
                "threat_type_breakdown": {"SMS_PHISHING": 90, "MALICIOUS_APP": 40, "OVERLAY_ATTACK": 20},
                "override_reason_breakdown": {"FALSE_POSITIVE": 8, "USER_CONSENT": 4},
                "active_devices_count": 85,
            }
        }
    )

"""Simulated DPIP Smart Registry Institutional Adapter for SAMPATI V2.

Simulates querying and updating the Digital Payment Intelligence Platform (DPIP)
national fraud registry, supporting SHA-256 privacy-preserving hash lookups,
agency reporting histories, and analyst hotlist updates.
"""
from __future__ import annotations

import hashlib
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    from app.models.pydantic_models import BaseModel, Field  # type: ignore

from app.engine.honeypot import DEFAULT_HONEYPOTS, get_honeypot_registry

logger = logging.getLogger("sampati.adapters.dpip")

KNOWN_BAD_KEYWORDS = (
    "mule",
    "scam",
    "fraud",
    "phish",
    "botnet",
    "trap",
    "darkweb",
    "bad",
    "conduit",
    "cashout",
    "drain",
)


class DpipRegistryRecord(BaseModel):
    """Simulated record from DPIP National Smart Registry."""
    vpa_hash: str = Field(..., description="SHA-256 hash of normalized VPA")
    vpa: Optional[str] = Field(default=None, description="Plain VPA if resolved or known")
    threat_level: str = Field(default="CLEAN", description="Threat tier: CRITICAL, HIGH, MEDIUM, LOW, CLEAN")
    threat_score: float = Field(default=0.0, description="Registry risk score in [0.0, 1.0]")
    listed: bool = Field(default=False, description="Whether entity is actively listed on national fraud hotlist")
    record_id: Optional[str] = Field(default=None, description="Unique DPIP registry docket identifier")
    reporting_agencies: List[str] = Field(default_factory=list, description="Reporting agencies or intelligence sources")
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO-8601 timestamp")
    reason: Optional[str] = Field(default=None, description="Listing reason or intelligence narrative")


class DpipRegistryUpdateRequest(BaseModel):
    """Payload for submitting or updating a DPIP registry entry."""
    vpa_or_hash: str = Field(..., description="Plain VPA or 64-character SHA-256 hash")
    threat_level: str = Field(default="HIGH", description="Assessed threat level: CRITICAL, HIGH, MEDIUM, LOW, CLEAN")
    threat_score: float = Field(default=0.90, ge=0.0, le=1.0, description="Assessed threat score")
    reason: str = Field(default="Analyst-confirmed mule account", description="Reason for updating registry")
    agency: str = Field(default="SAMPATI_MESH", description="Reporting agency or PSP node")


class DpipSmartRegistryAdapter:
    """Mock adapter for DPIP Smart Registry queries and updates."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._honeypots = get_honeypot_registry()
        self._registry: Dict[str, DpipRegistryRecord] = {}
        self._seed_registry()

    @staticmethod
    def compute_hash(vpa: str) -> str:
        """Compute normalized SHA-256 hash of VPA."""
        clean = (vpa or "").strip().lower()
        return hashlib.sha256(clean.encode("utf-8")).hexdigest()

    def _seed_registry(self) -> None:
        """Pre-populate registry with default honeypots and synthetic mule nodes."""
        now_iso = datetime.now(timezone.utc).isoformat()
        for hp in DEFAULT_HONEYPOTS:
            h = self.compute_hash(hp)
            self._registry[h] = DpipRegistryRecord(
                vpa_hash=h,
                vpa=hp,
                threat_level="HIGH",
                threat_score=0.90,
                listed=True,
                record_id=f"DPIP-HP-{h[:8].upper()}",
                reporting_agencies=["NATIONAL_CYBER_CRIME_PORTAL", "DPIP_HOTLIST"],
                last_updated=now_iso,
                reason="Seeded synthetic honeypot trap node",
            )

    def query_hash(self, vpa_hash: str) -> DpipRegistryRecord:
        """Query registry directly by SHA-256 hash."""
        if not vpa_hash or not isinstance(vpa_hash, str):
            return DpipRegistryRecord(
                vpa_hash="",
                threat_level="CLEAN",
                threat_score=0.0,
                listed=False,
            )

        clean_hash = vpa_hash.strip().lower()
        with self._lock:
            if clean_hash in self._registry:
                return self._registry[clean_hash]

        return DpipRegistryRecord(
            vpa_hash=clean_hash,
            threat_level="CLEAN",
            threat_score=0.0,
            listed=False,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    def query_vpa(self, vpa: Optional[str]) -> DpipRegistryRecord:
        """Query registry by plain VPA or hash with automatic hash normalization."""
        if not vpa or not isinstance(vpa, str):
            return DpipRegistryRecord(
                vpa_hash="",
                vpa=vpa or "",
                threat_level="CLEAN",
                threat_score=0.0,
                listed=False,
            )

        clean_input = vpa.strip().lower()
        # Check if input is already a 64-character SHA-256 hex string
        if len(clean_input) == 64 and all(c in "0123456789abcdef" for c in clean_input):
            return self.query_hash(clean_input)

        vpa_hash = self.compute_hash(clean_input)
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            if vpa_hash in self._registry:
                record = self._registry[vpa_hash]
                if not record.vpa:
                    record.vpa = vpa
                return record

            # 1. Deterministic Honeypot Check
            if self._honeypots.is_honeypot(clean_input):
                rec = DpipRegistryRecord(
                    vpa_hash=vpa_hash,
                    vpa=vpa,
                    threat_level="HIGH",
                    threat_score=0.90,
                    listed=True,
                    record_id=f"DPIP-HP-{vpa_hash[:8].upper()}",
                    reporting_agencies=["NATIONAL_CYBER_CRIME_PORTAL", "DPIP_HOTLIST"],
                    last_updated=now_iso,
                    reason="Synthetic honeypot trap node detected",
                )
                self._registry[vpa_hash] = rec
                return rec

            # 2. Known-Bad Heuristic Check
            if any(kw in clean_input for kw in KNOWN_BAD_KEYWORDS):
                rec = DpipRegistryRecord(
                    vpa_hash=vpa_hash,
                    vpa=vpa,
                    threat_level="HIGH",
                    threat_score=0.85,
                    listed=True,
                    record_id=f"DPIP-HEUR-{vpa_hash[:8].upper()}",
                    reporting_agencies=["MULE_NETWORK_COORDINATION", "I4C"],
                    last_updated=now_iso,
                    reason="Heuristic mule identifier pattern match",
                )
                self._registry[vpa_hash] = rec
                return rec

            # 3. Check legacy DPIP feed if available
            try:
                from app.dpip.feed import get_dpip
                feed = get_dpip()
                ext_score = feed.external_score(clean_input)
                if ext_score and ext_score >= 0.5:
                    rec = DpipRegistryRecord(
                        vpa_hash=vpa_hash,
                        vpa=vpa,
                        threat_level="HIGH",
                        threat_score=round(float(ext_score), 2),
                        listed=True,
                        record_id=f"DPIP-FEED-{vpa_hash[:8].upper()}",
                        reporting_agencies=["DPIP_FEED_EXCHANGE"],
                        last_updated=now_iso,
                        reason="Flagged in DPIP external feed exchange",
                    )
                    self._registry[vpa_hash] = rec
                    return rec
            except Exception:
                pass

        # 4. Clean Entity
        return DpipRegistryRecord(
            vpa_hash=vpa_hash,
            vpa=vpa,
            threat_level="CLEAN",
            threat_score=0.0,
            listed=False,
            last_updated=now_iso,
        )

    def update_registry(self, req: DpipRegistryUpdateRequest) -> DpipRegistryRecord:
        """Update or register an entry in the DPIP registry."""
        target = req.vpa_or_hash.strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        if len(target) == 64 and all(c in "0123456789abcdef" for c in target):
            vpa_hash = target
            vpa_val = None
        else:
            vpa_hash = self.compute_hash(target)
            vpa_val = req.vpa_or_hash.strip()

        clean_level = req.threat_level.upper().strip()
        clean_score = max(0.0, min(1.0, float(req.threat_score)))
        is_listed = clean_score > 0.0 and clean_level != "CLEAN"

        rec = DpipRegistryRecord(
            vpa_hash=vpa_hash,
            vpa=vpa_val,
            threat_level=clean_level,
            threat_score=clean_score,
            listed=is_listed,
            record_id=f"DPIP-REG-{vpa_hash[:8].upper()}",
            reporting_agencies=[req.agency] if req.agency else ["SAMPATI_MESH"],
            last_updated=now_iso,
            reason=req.reason,
        )

        with self._lock:
            self._registry[vpa_hash] = rec

        # Propagate to legacy DPIP feed if VPA is provided
        if vpa_val:
            try:
                from app.dpip.feed import get_dpip
                feed = get_dpip()
                feed.ingest_external_signal(vpa_val, risk=clean_score, source=req.agency)
            except Exception as exc:
                logger.debug("Failed to propagate to legacy DPIP feed: %s", exc)

        return rec


_dpip_adapter: Optional[DpipSmartRegistryAdapter] = None


def get_dpip_adapter() -> DpipSmartRegistryAdapter:
    """Singleton getter for DpipSmartRegistryAdapter."""
    global _dpip_adapter
    if _dpip_adapter is None:
        _dpip_adapter = DpipSmartRegistryAdapter()
    return _dpip_adapter

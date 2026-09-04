"""Simulated NPCI MuleHunter Institutional Adapter for SAMPATI V2.

Simulates NPCI's central switch mule account intelligence engine, which assesses
account velocity, multi-bank link churn, and pass-through aggregation flags across
the national UPI payment switch.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    from app.models.pydantic_models import BaseModel, Field  # type: ignore

from app.engine.honeypot import get_honeypot_registry

logger = logging.getLogger("sampati.adapters.npci")

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

MODERATE_KEYWORDS = (
    "temp",
    "transfer",
    "fast",
    "quick",
)


class NpciMuleHunterResponse(BaseModel):
    """Simulated response payload from NPCI MuleHunter central switch."""
    vpa: str = Field(..., description="Target Virtual Payment Address evaluated")
    mule_probability: float = Field(..., description="Calculated mule account probability in [0.0, 1.0]")
    risk_rating: str = Field(..., description="Categorical risk tier: HIGH, MEDIUM, LOW, CLEAN")
    central_switch_flags: List[str] = Field(default_factory=list, description="Triggered switch-level risk indicators")
    switch_velocity_percentile: float = Field(default=0.0, description="Percentile ranking of 24h switch inflow/outflow velocity")
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO-8601 evaluation timestamp")


class NpciMuleHunterAdapter:
    """Mock adapter for NPCI Central Switch MuleHunter scoring service."""

    def __init__(self) -> None:
        self._honeypots = get_honeypot_registry()

    def score_account(self, vpa: Optional[str]) -> NpciMuleHunterResponse:
        """Evaluate a VPA against central switch telemetry rules and return mule probability."""
        if not vpa or not isinstance(vpa, str):
            return NpciMuleHunterResponse(
                vpa=vpa or "",
                mule_probability=0.0,
                risk_rating="CLEAN",
                central_switch_flags=["MISSING_IDENTIFIER"],
                switch_velocity_percentile=0.0,
            )

        clean_vpa = vpa.strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Deterministic Honeypot Detection
        if self._honeypots.is_honeypot(clean_vpa):
            return NpciMuleHunterResponse(
                vpa=vpa,
                mule_probability=0.96,
                risk_rating="HIGH",
                central_switch_flags=[
                    "CENTRAL_SWITCH_HONEYPOT_SINK",
                    "MULE_CLUSTER_CENTRAL_TRAP",
                    "RAPID_INFLOW_SURGE",
                ],
                switch_velocity_percentile=99.8,
                evaluated_at=now_iso,
            )

        # 2. Known-Bad Mule Signatures
        if any(kw in clean_vpa for kw in KNOWN_BAD_KEYWORDS):
            return NpciMuleHunterResponse(
                vpa=vpa,
                mule_probability=0.92,
                risk_rating="HIGH",
                central_switch_flags=[
                    "KNOWN_MULE_SIGNATURE",
                    "MULTI_BANK_BURST_OUTFLOW",
                ],
                switch_velocity_percentile=98.5,
                evaluated_at=now_iso,
            )

        # 3. Moderate Risk Velocity Conduit Indicators
        if any(kw in clean_vpa for kw in MODERATE_KEYWORDS):
            return NpciMuleHunterResponse(
                vpa=vpa,
                mule_probability=0.55,
                risk_rating="MEDIUM",
                central_switch_flags=["UNUSUAL_PSP_CONDUIT"],
                switch_velocity_percentile=72.0,
                evaluated_at=now_iso,
            )

        # 4. Clean / Normal Clearing
        # Deterministic low score based on SHA-256 hash
        seed = int(hashlib.sha256(clean_vpa.encode("utf-8")).hexdigest()[:8], 16)
        prob = round((seed % 10) / 100.0, 4)  # 0.00 to 0.09 (< 0.15)
        velocity_pct = round(15.0 + (seed % 30), 1)

        return NpciMuleHunterResponse(
            vpa=vpa,
            mule_probability=prob,
            risk_rating="LOW",
            central_switch_flags=["NORMAL_SWITCH_CLEARING"],
            switch_velocity_percentile=velocity_pct,
            evaluated_at=now_iso,
        )

    def evaluate_transaction(self, vpa: Optional[str]) -> NpciMuleHunterResponse:
        """Alias for score_account."""
        return self.score_account(vpa)


_npci_adapter: Optional[NpciMuleHunterAdapter] = None


def get_npci_adapter() -> NpciMuleHunterAdapter:
    """Singleton getter for NpciMuleHunterAdapter."""
    global _npci_adapter
    if _npci_adapter is None:
        _npci_adapter = NpciMuleHunterAdapter()
    return _npci_adapter

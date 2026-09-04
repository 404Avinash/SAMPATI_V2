"""Mock PSP Adapter for SAMPATI V2.

Simulates PSP-level client/server anomaly detection engines (e.g. PhonePe, Paytm,
Google Pay, BHIM) producing standardized fraud signals (`StandardFraudSignal`)
and broadcasting them into the central intelligence mesh.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from app.models.threat_intel import StandardFraudSignal, ThreatSignalResponse

logger = logging.getLogger("sampati.adapters.psp")

VALID_PSPS = ["PhonePe", "Paytm", "GooglePay", "BHIM"]


class MockPspAdapter:
    """Mock adapter producing standardized fraud signals from payment service providers."""

    def __init__(self) -> None:
        self.supported_psps = list(VALID_PSPS)

    def generate_signal(
        self,
        psp: str,
        vpa: str,
        anomaly_type: str = "velocity_anomaly",
        severity: str = "HIGH",
        confidence: float = 0.88,
        details: Optional[str] = None,
        phone: Optional[str] = None,
        url: Optional[str] = None,
    ) -> StandardFraudSignal:
        """Generate a standardized fraud signal for a specific PSP and target VPA."""
        clean_psp = psp.strip() if psp else "PhonePe"
        return StandardFraudSignal.from_psp(
            psp=clean_psp,
            vpa=vpa,
            anomaly_type=anomaly_type,
            severity=severity,
            confidence=confidence,
            details=details,
            phone=phone,
            url=url,
        )

    async def publish_to_mesh(
        self,
        signal: StandardFraudSignal,
        db: Optional[Any] = None,
    ) -> ThreatSignalResponse:
        """Publish a standard fraud signal directly into the central Threat Intelligence Mesh."""
        from app.services.threat_intel_service import get_threat_intel_service
        service = get_threat_intel_service()
        return await service.ingest_signal(signal, db=db)

    def simulate_psp_traffic(
        self,
        psp: str = "PhonePe",
        count: int = 3,
    ) -> List[StandardFraudSignal]:
        """Generate a batch of synthetic PSP fraud signals."""
        signals = []
        samples = [
            ("velocity_anomaly", "burst_user_01@okaxis", "Rapid multi-beneficiary outbound burst (8 txns in 60s)"),
            ("suspicious_beneficiary", "pooling_account@paytm", "Payment diverted to newly registered pooling beneficiary"),
            ("device_binding_churn", "churn_device@ybl", "SIM swap detected: 3 distinct accounts bound to device in 2 hours"),
        ]
        for i in range(min(count, len(samples))):
            anomaly, vpa, detail = samples[i]
            signals.append(
                self.generate_signal(
                    psp=psp,
                    vpa=vpa,
                    anomaly_type=anomaly,
                    severity="HIGH",
                    confidence=0.88,
                    details=detail,
                )
            )
        return signals


_psp_adapter: Optional[MockPspAdapter] = None


def get_psp_adapter() -> MockPspAdapter:
    """Singleton getter for MockPspAdapter."""
    global _psp_adapter
    if _psp_adapter is None:
        _psp_adapter = MockPspAdapter()
    return _psp_adapter

"""FastAPI Router for Simulated Institutional Signal Adapters (NPCI, DPIP, PSP).

Endpoints:
- GET /adapters/npci/mulehunter: Query NPCI MuleHunter central switch score
- GET /adapters/dpip/registry: Query DPIP Smart Registry by VPA or SHA-256 hash
- POST /adapters/dpip/registry: Update/list entry in DPIP Smart Registry
- POST /adapters/psp/simulate: Simulate and publish a standardized PSP fraud signal
- GET /adapters/signals/contributing: Aggregate institutional signals for a target VPA
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    from fastapi import APIRouter, Depends, HTTPException, Query, status
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # fallback stubs
    class APIRouter:  # type: ignore
        def __init__(self, *args, **kwargs): self.routes = []
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
    def Depends(f=None): return None  # type: ignore
    def Query(default=None, **kwargs): return default  # type: ignore
    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: Any = None):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")
    class status:  # type: ignore
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404
        HTTP_201_CREATED = 201

try:
    from pydantic import BaseModel, Field
except ImportError:
    from app.models.pydantic_models import BaseModel, Field  # type: ignore

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import get_db
except ImportError:
    AsyncSession = Any  # type: ignore
    async def get_db(): return None  # type: ignore

from app.adapters.dpip import (
    DpipRegistryRecord,
    DpipRegistryUpdateRequest,
    get_dpip_adapter,
)
from app.adapters.npci import (
    NpciMuleHunterResponse,
    get_npci_adapter,
)
from app.adapters.psp import (
    get_psp_adapter,
)
from app.adapters.service import (
    get_institutional_adapters,
)
from app.models.threat_intel import StandardFraudSignal
from app.models.upi_models import UpiTransaction

logger = logging.getLogger("sampati.api.adapters")
router = APIRouter()


class PspSimulateRequest(BaseModel):
    """Payload for simulating a PSP client/server fraud signal."""
    psp: str = Field(default="PhonePe", description="Originating PSP name (PhonePe, Paytm, GooglePay, BHIM)")
    vpa: str = Field(..., description="Target VPA to generate signal for")
    anomaly_type: str = Field(default="velocity_anomaly", description="Typology or anomaly code")
    severity: str = Field(default="HIGH", description="Assessed signal severity: LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(default=0.88, ge=0.0, le=1.0, description="Signal confidence score")
    details: Optional[str] = Field(default=None, description="Detailed explanation or incident note")
    phone: Optional[str] = Field(default=None, description="Associated phone number")
    url: Optional[str] = Field(default=None, description="Associated phishing URL")
    publish_to_mesh: bool = Field(default=True, description="Whether to ingest directly into central Threat Intel Mesh")


@router.get("/npci/mulehunter", response_model=NpciMuleHunterResponse, summary="Query NPCI MuleHunter Central Switch")
async def query_npci_mulehunter(
    vpa: str = Query(..., description="UPI Virtual Payment Address to evaluate"),
) -> NpciMuleHunterResponse:
    """Evaluate account against NPCI MuleHunter central switch heuristics."""
    if not vpa or not vpa.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VPA parameter is required")
    adapter = get_npci_adapter()
    return adapter.score_account(vpa.strip())


@router.get("/dpip/registry", response_model=DpipRegistryRecord, summary="Query DPIP Smart Registry")
async def query_dpip_registry(
    vpa: Optional[str] = Query(None, description="UPI Virtual Payment Address to evaluate"),
    vpa_hash: Optional[str] = Query(None, description="64-character SHA-256 hash of VPA"),
) -> DpipRegistryRecord:
    """Query DPIP National Fraud Registry by plain VPA or privacy-preserving SHA-256 hash."""
    if not vpa and not vpa_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'vpa' or 'vpa_hash' parameter must be provided",
        )
    adapter = get_dpip_adapter()
    if vpa_hash:
        return adapter.query_hash(vpa_hash.strip())
    return adapter.query_vpa(vpa.strip())  # type: ignore


@router.post("/dpip/registry", response_model=DpipRegistryRecord, summary="Update DPIP Smart Registry")
async def update_dpip_registry(
    body: DpipRegistryUpdateRequest,
) -> DpipRegistryRecord:
    """Submit confirmed mule account to DPIP Smart Registry."""
    if not body.vpa_or_hash or not body.vpa_or_hash.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vpa_or_hash must not be empty",
        )
    adapter = get_dpip_adapter()
    return adapter.update_registry(body)


@router.post("/psp/simulate", summary="Simulate Standardized PSP Fraud Signal")
async def simulate_psp_signal(
    body: PspSimulateRequest,
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Generate a StandardFraudSignal from a simulated PSP and optionally publish to central mesh."""
    if not body.vpa or not body.vpa.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vpa must not be empty")

    adapter = get_psp_adapter()
    signal: StandardFraudSignal = adapter.generate_signal(
        psp=body.psp,
        vpa=body.vpa.strip(),
        anomaly_type=body.anomaly_type,
        severity=body.severity,
        confidence=body.confidence,
        details=body.details,
        phone=body.phone,
        url=body.url,
    )

    published_response = None
    if body.publish_to_mesh:
        try:
            published_response = await adapter.publish_to_mesh(signal, db=db)
        except Exception as exc:
            logger.warning("Failed to publish PSP signal to central mesh: %s", exc)

    return {
        "status": "success",
        "signal": signal.model_dump() if hasattr(signal, "model_dump") else signal.dict(),
        "published": body.publish_to_mesh and published_response is not None,
        "mesh_signal_id": getattr(published_response, "signal_id", None) if published_response else None,
        "published_record": (
            published_response.model_dump() if hasattr(published_response, "model_dump") else (
                published_response.dict() if hasattr(published_response, "dict") else None
            )
        ) if published_response else None,
    }


@router.get("/signals/contributing", summary="Get Contributing Institutional Signals for VPA")
async def get_contributing_signals(
    vpa: str = Query(..., description="Target VPA to evaluate"),
    payer_vpa: Optional[str] = Query(None, description="Optional payer VPA"),
    amount: float = Query(100.0, ge=0.0, description="Optional transaction amount"),
) -> Dict[str, Any]:
    """Return aggregated institutional scores and contributing signal metadata for a target account."""
    if not vpa or not vpa.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vpa parameter is required")

    txn = UpiTransaction(
        txn_id=f"PROBE_{vpa[:8]}",
        payee_vpa=vpa.strip(),
        payer_vpa=payer_vpa.strip() if payer_vpa else "probe_payer@okaxis",
        amount=amount,
    )
    service = get_institutional_adapters()
    return service.evaluate_for_transaction(txn)

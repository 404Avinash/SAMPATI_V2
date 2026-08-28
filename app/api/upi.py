"""UPI Mule-Network Fraud Detection and Case Management API Router for SAMPATI V2.

Provides REST endpoints for inline transaction evaluation, cross-PSP federation rounds,
case investigation and feedback workflows, synthetic simulation, and real-time statistics
backed by AWS RDS PostgreSQL.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.websocket import broadcast_event
from app.db.session import get_db
from app.models.upi_models import (
    LabeledUpiTransaction,
    UpiEvaluationResponse,
    UpiTransaction,
)
from app.models.upi_persistence import MuleRingModel, UpiCaseModel
from app.services.upi_cases import UpiCaseService, get_upi_case_service
from app.synthetic.upi_generator import UpiWorld, generate_labeled_stream

logger = logging.getLogger("sampati.api.upi")
router = APIRouter()


class FeedbackRequest(BaseModel):
    confirmed_fraud: Optional[bool] = None
    confirmed: Optional[bool] = None

    @property
    def is_confirmed_fraud(self) -> bool:
        if self.confirmed_fraud is not None:
            return bool(self.confirmed_fraud)
        if self.confirmed is not None:
            return bool(self.confirmed)
        return False


class SimulateRequest(BaseModel):
    total_txns: int = 100
    fraud_ratio: float = 0.15
    seed: Optional[int] = 42
    run_federation: bool = True


@router.post("/check", summary="Inline UPI Pre-Transaction Gate")
async def check_upi_txn(
    txn: UpiTransaction,
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Inline pre-transaction gate for a single UPI payment."""
    service: UpiCaseService = get_upi_case_service()
    resp: UpiEvaluationResponse = service.evaluate(txn)

    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp.dict()
    await broadcast_event("UPI_EVALUATED", payload)

    if resp.case_id:
        case_data = service.get_case(resp.case_id)
        if case_data and db is not None:
            await service.save_case_to_db_session(case_data, db)

        if case_data:
            formatted_case = service.format_case_payload(case_data)
            await broadcast_event("new_case", formatted_case, stats=service.get_current_stats())

        await broadcast_event(
            "UPI_CASE_OPENED",
            {
                "case_id": resp.case_id,
                "txn_id": txn.txn_id,
                "payer_vpa": txn.payer_vpa,
                "payee_vpa": txn.payee_vpa,
                "amount": float(txn.amount),
                "verdict": resp.action,
                "risk_score": resp.risk_score,
                "reasons": resp.reasons,
                "timestamp": txn.timestamp.isoformat() if isinstance(txn.timestamp, datetime) else str(txn.timestamp),
            },
        )
    else:
        await broadcast_event("stats_update", service.get_current_stats())

    return payload


@router.post("/federation/run", summary="Trigger Federated Intelligence Round")
async def run_federation(
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Trigger a federation round and build SARs for any detected rings."""
    service: UpiCaseService = get_upi_case_service()
    result = service.run_federation()

    if db is not None:
        for ring in result.get("rings", []):
            await service.save_ring_to_db_session(ring, db)
        for case in service.list_cases():
            if case.get("status") == "INVESTIGATED":
                await service.save_case_to_db_session(case, db)

    suspicious_val = result.get("suspicious", result.get("suspicious_entities", []))
    suspicious_count = len(suspicious_val) if isinstance(suspicious_val, (list, set, dict)) else int(suspicious_val or 0)

    await broadcast_event(
        "FEDERATION_ROUND",
        {
            "rings_detected": len(result.get("rings", [])),
            "new_rings": len(result.get("new_rings", [])),
            "suspicious_entities": suspicious_count,
        },
    )
    await broadcast_event("stats_update", service.get_current_stats())
    return result


@router.get("/rings", summary="List Known Cross-PSP Mule Rings")
async def list_rings(
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Return all known cross-PSP mule rings."""
    service: UpiCaseService = get_upi_case_service()
    if db is not None:
        try:
            result = await db.execute(select(MuleRingModel).order_by(MuleRingModel.detected_at.desc()))
            db_rings = result.scalars().all()
            if db_rings:
                return {
                    "count": len(db_rings),
                    "rings": [r.to_dict() for r in db_rings],
                }
        except Exception as exc:
            logger.debug(f"DB rings query failed, falling back to coordinator memory: {exc}")

    rings = service.federation.current_rings()
    return {"count": len(rings), "rings": rings}


@router.get("/cases", summary="List Investigative UPI Cases")
async def list_upi_cases(
    status: Optional[str] = Query(None, description="Filter by case status (OPEN, INVESTIGATED, RESOLVED)"),
    verdict: Optional[str] = Query(None, description="Filter by verdict (ALLOW, HOLD, BLOCK)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """List investigative cases with pagination and optional filtering."""
    service: UpiCaseService = get_upi_case_service()

    if db is not None:
        try:
            stmt = select(UpiCaseModel).order_by(UpiCaseModel.created_at.desc())
            count_stmt = select(func.count(UpiCaseModel.case_id))

            if status:
                stmt = stmt.where(UpiCaseModel.status == status)
                count_stmt = count_stmt.where(UpiCaseModel.status == status)
            if verdict:
                stmt = stmt.where(UpiCaseModel.verdict == verdict)
                count_stmt = count_stmt.where(UpiCaseModel.verdict == verdict)

            total_count = await db.scalar(count_stmt) or 0
            items_result = await db.execute(stmt.offset(offset).limit(limit))
            db_cases = items_result.scalars().all()

            if total_count > 0 or not service.list_cases():
                return {
                    "count": total_count,
                    "items": [c.to_dict(include_sar=False) for c in db_cases],
                }
        except Exception as exc:
            logger.debug(f"DB cases query failed, falling back to memory: {exc}")

    cases = service.list_cases()
    if status:
        cases = [c for c in cases if c.get("status") == status]
    if verdict:
        cases = [c for c in cases if c.get("verdict") == verdict]

    total_count = len(cases)
    paginated = cases[offset : offset + limit]

    summaries = []
    for c in paginated:
        c_copy = dict(c)
        c_copy.pop("sar_markdown", None)
        summaries.append(c_copy)

    return {"count": total_count, "items": summaries}


@router.get("/cases/{case_id}", summary="Get Detailed UPI Case")
async def get_upi_case(
    case_id: str,
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Fetch complete case record including SAR report and token economy."""
    service: UpiCaseService = get_upi_case_service()

    if db is not None:
        try:
            result = await db.execute(select(UpiCaseModel).where(UpiCaseModel.case_id == case_id))
            db_case = result.scalar_one_or_none()
            if db_case:
                return db_case.to_dict(include_sar=True)
        except Exception as exc:
            logger.debug(f"DB case lookup failed for '{case_id}': {exc}")

    case = service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"UPI case '{case_id}' not found")
    return case


@router.get("/cases/{case_id}/graph.png", summary="Retrieve Case Ring Constellation Diagram")
async def get_case_graph(
    case_id: str,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Serve the rendered PNG topology artifact for a case."""
    service: UpiCaseService = get_upi_case_service()
    case = None
    if db is not None:
        try:
            res = await db.execute(select(UpiCaseModel).where(UpiCaseModel.case_id == case_id))
            db_c = res.scalar_one_or_none()
            if db_c:
                case = db_c.to_dict(include_sar=False)
        except Exception:
            pass

    if case is None:
        case = service.get_case(case_id)

    if not case:
        raise HTTPException(status_code=404, detail=f"UPI case '{case_id}' not found")

    path = case.get("visual_path")
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Visual summary not yet rendered")

    return FileResponse(path, media_type="image/png")


@router.post("/cases/{case_id}/feedback", summary="Submit Human Analyst Case Resolution")
async def submit_case_feedback(
    case_id: str,
    body: FeedbackRequest,
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Submit human investigator feedback (CONFIRMED_FRAUD vs FALSE_POSITIVE)."""
    service: UpiCaseService = get_upi_case_service()
    is_confirmed = body.is_confirmed_fraud
    try:
        result = service.submit_feedback(case_id, confirmed_fraud=is_confirmed)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"UPI case '{case_id}' not found")

    if db is not None:
        updated_case = service.get_case(case_id)
        if updated_case:
            await service.save_case_to_db_session(updated_case, db)
        feedback_record = {
            "case_id": case_id,
            "confirmed_fraud": is_confirmed,
            "resolution": result.get("resolution"),
            "vpas_flagged": updated_case.get("ring_members_vpas", []) if updated_case else [],
            "dpip_published": result.get("dpip_published"),
        }
        await service.save_feedback_to_db_session(feedback_record, db)

    await broadcast_event(
        "UPI_CASE_RESOLVED",
        {
            "case_id": case_id,
            "resolution": result.get("resolution"),
            "confirmed_fraud": is_confirmed,
            "dpip_published": result.get("dpip_published") is not None,
        },
    )
    await broadcast_event("stats_update", service.get_current_stats())
    return result


@router.post("/simulate", summary="Generate Labeled Synthetic UPI Traffic Stream")
async def simulate_traffic(
    body: SimulateRequest,
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Drive a labeled synthetic stream through the live gate for verification and demos."""
    service: UpiCaseService = get_upi_case_service()
    stream, ground_truth_rings = generate_labeled_stream(
        total_txns=body.total_txns,
        fraud_ratio=body.fraud_ratio,
        seed=body.seed,
    )

    verdicts: Dict[str, int] = {"ALLOW": 0, "HOLD": 0, "BLOCK": 0}
    opened_case_ids: List[str] = []

    for i, labeled in enumerate(stream):
        resp = service.evaluate(labeled.txn)
        verdicts[resp.action] = verdicts.get(resp.action, 0) + 1

        payload = resp.model_dump() if hasattr(resp, "model_dump") else resp.dict()
        await broadcast_event("UPI_EVALUATED", payload)

        if resp.case_id:
            opened_case_ids.append(resp.case_id)
            case_obj = service.get_case(resp.case_id)
            if case_obj:
                formatted = service.format_case_payload(case_obj)
                await broadcast_event("new_case", formatted, stats=service.get_current_stats())

            await broadcast_event(
                "UPI_CASE_OPENED",
                {
                    "case_id": resp.case_id,
                    "txn_id": labeled.txn.txn_id,
                    "payer_vpa": labeled.txn.payer_vpa,
                    "payee_vpa": labeled.txn.payee_vpa,
                    "amount": float(labeled.txn.amount),
                    "verdict": resp.action,
                    "risk_score": resp.risk_score,
                    "reasons": resp.reasons,
                    "timestamp": labeled.txn.timestamp.isoformat() if isinstance(labeled.txn.timestamp, datetime) else str(labeled.txn.timestamp),
                },
            )

    detected_rings = []
    if body.run_federation:
        fed_result = service.run_federation(now=stream[-1].txn.timestamp if stream else None)
        detected_rings = fed_result.get("rings", [])
    else:
        detected_rings = service.federation.current_rings()

    # Synchronize all simulated cases and rings to PostgreSQL if session is active
    if db is not None:
        for cid in opened_case_ids:
            c = service.get_case(cid)
            if c:
                await service.save_case_to_db_session(c, db)
        for ring in detected_rings:
            await service.save_ring_to_db_session(ring, db)

    summary = {
        "processed": len(stream),
        "verdicts": verdicts,
        "ground_truth_rings": len(ground_truth_rings),
        "detected_rings": len(detected_rings),
    }

    # Broadcast real-time stats update and simulation completion
    await broadcast_event("stats_update", service.get_current_stats())
    await broadcast_event("SIMULATION_COMPLETE", summary)
    return summary


@router.get("/stats", summary="Real-Time System and Persistence Telemetry")
async def upi_stats(
    db: Optional[AsyncSession] = Depends(get_db),
) -> Dict[str, Any]:
    """Return aggregated system counters and telemetry across sessions."""
    service: UpiCaseService = get_upi_case_service()

    total_cases = 0
    open_cases = 0
    investigated_cases = 0
    resolved_cases = 0
    rings_known = 0

    if db is not None:
        try:
            # Query case status distribution directly from DB
            status_stmt = select(UpiCaseModel.status, func.count(UpiCaseModel.case_id)).group_by(UpiCaseModel.status)
            status_rows = (await db.execute(status_stmt)).all()
            status_map = {row[0]: row[1] for row in status_rows}

            open_cases = status_map.get("OPEN", 0)
            investigated_cases = status_map.get("INVESTIGATED", 0)
            resolved_cases = status_map.get("RESOLVED", 0)
            total_cases = sum(status_map.values())

            # Query total rings known from DB
            rings_count = await db.scalar(select(func.count(MuleRingModel.ring_hash)))
            rings_known = rings_count or 0

            # If DB has data or memory is empty, return DB stats
            if total_cases > 0 or rings_known > 0 or not service.list_cases():
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "cases": {
                        "total": total_cases,
                        "open": open_cases,
                        "investigated": investigated_cases,
                        "resolved": resolved_cases,
                    },
                    "rings_known": rings_known,
                    "dpip": service.dpip.stats(),
                    "adaptive_sensitivity": round(service.adaptive.sensitivity, 3),
                }
        except Exception as exc:
            logger.debug(f"DB stats query failed, falling back to memory: {exc}")

    # In-memory fallback
    cases = service.list_cases()
    total_cases = len(cases)
    open_cases = sum(1 for c in cases if c.get("status") == "OPEN")
    investigated_cases = sum(1 for c in cases if c.get("status") == "INVESTIGATED")
    resolved_cases = sum(1 for c in cases if c.get("status") == "RESOLVED")
    rings_known = len(service.federation.current_rings())

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cases": {
            "total": total_cases,
            "open": open_cases,
            "investigated": investigated_cases,
            "resolved": resolved_cases,
        },
        "rings_known": rings_known,
        "dpip": service.dpip.stats(),
        "adaptive_sensitivity": round(service.adaptive.sensitivity, 3),
    }

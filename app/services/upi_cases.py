"""UPI Mule-Network Case Management Service for SAMPATI V2.

Coordinates scoring, federated intelligence, automated SAR generation,
token economy telemetry, visual graph rendering, and AWS RDS PostgreSQL persistence.
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dpip.feed import DpipFeed, get_dpip
from app.engine.adaptive import AdaptiveBehaviorModel, get_adaptive_model
from app.engine.upi_scorer import UpiRiskScorer
from app.engine.upi_state import UpiHotState, get_upi_state
from app.federation.coordinator import FederatedCoordinator, get_federation
from app.federation.psp_node import pseudonymize
from app.forensics.upi_sar import (
    build_upi_token_economy,
    generate_upi_sar,
    render_ring_png,
)
from app.models.upi_models import (
    LabeledUpiTransaction,
    MuleRingSummary,
    RuleHit,
    UpiEvaluationResponse,
    UpiTransaction,
    VerdictAction,
)
from app.models.upi_persistence import (
    CaseFeedbackModel,
    MuleRingModel,
    UpiCaseModel,
)

logger = logging.getLogger("sampati.services.upi_cases")


class UpiCaseService:
    """Singleton service managing UPI mule network detection and persistence."""

    def __init__(self, artifact_dir: str = "static/upi_cases") -> None:
        self.state: UpiHotState = get_upi_state()
        self.adaptive: AdaptiveBehaviorModel = get_adaptive_model()
        self.scorer: UpiRiskScorer = UpiRiskScorer(state=self.state, adaptive=self.adaptive)
        self.federation: FederatedCoordinator = get_federation()
        self.dpip: DpipFeed = get_dpip()
        self.artifact_dir: str = artifact_dir
        os.makedirs(self.artifact_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._txn_log: List[Dict[str, Any]] = []
        self._eval_count: int = 0
        self._allow_count: int = 0
        self._hold_count: int = 0
        self._block_count: int = 0

    def _infer_scenario(self, t: Dict[str, Any], member_set: set) -> str:
        """Infer whether a transaction represents fan-in, layering pass-through, or fan-out."""
        payer_in = pseudonymize(t.get("payer_vpa", ""), self.federation.salt) in member_set
        payee_in = pseudonymize(t.get("payee_vpa", ""), self.federation.salt) in member_set
        if payer_in and payee_in:
            return "pass_through"
        elif payee_in:
            return "fan_in"
        elif payer_in:
            return "fan_out"
        return "pass_through"

    def _resolve_members(self, ring_txns: List[Dict[str, Any]], member_set: set) -> List[str]:
        """Extract unmasked VPAs participating in the mule ring from transaction records."""
        vpas = set()
        for t in ring_txns:
            if pseudonymize(t.get("payer_vpa", ""), self.federation.salt) in member_set:
                vpas.add(t.get("payer_vpa", ""))
            if pseudonymize(t.get("payee_vpa", ""), self.federation.salt) in member_set:
                vpas.add(t.get("payee_vpa", ""))
        return sorted(vpas)

    def format_case_payload(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format case data dictionary to conform strictly with PROJECT.md contract."""
        trig = case_data.get("trigger_txn") or {}
        topology = case_data.get("topology")
        if not topology:
            topology = {
                "trigger_txn": trig,
                "fan_in": [case_data.get("payer_vpa")] if case_data.get("payer_vpa") else [],
                "hops": [],
                "fan_out": [case_data.get("payee_vpa")] if case_data.get("payee_vpa") else [],
            }
        return {
            "case_id": case_data.get("case_id"),
            "created_at": case_data.get("created_at"),
            "verdict": case_data.get("verdict"),
            "risk_score": case_data.get("risk_score"),
            "amount": float(case_data.get("amount") or 0.0),
            "reasons": case_data.get("reasons") or [],
            "trigger_txn": trig,
            "topology": topology,
            "ring_members_vpas": case_data.get("ring_members_vpas") or [],
            "token_economy": case_data.get("token_economy"),
            "sar_markdown": case_data.get("sar_markdown"),
            "status": case_data.get("status", "OPEN"),
        }

    def get_current_stats(self) -> Dict[str, Any]:
        """Calculate aggregated system telemetry counters for real-time streaming."""
        with self._lock:
            evaluated = self._eval_count
            allowed = self._allow_count
            held = self._hold_count
            blocked = self._block_count
            if evaluated == 0 and self._txn_log:
                evaluated = len(self._txn_log)
                allowed = sum(1 for t in self._txn_log if t.get("action") == "ALLOW")
                held = sum(1 for t in self._txn_log if t.get("action") == "HOLD")
                blocked = sum(1 for t in self._txn_log if t.get("action") == "BLOCK")

        dpip_stat = self.dpip.stats()
        if isinstance(dpip_stat, dict):
            dpip_count = dpip_stat.get("published_records", dpip_stat.get("published_count", dpip_stat.get("total", len(dpip_stat))))
        elif isinstance(dpip_stat, int):
            dpip_count = dpip_stat
        else:
            dpip_count = 0

        rings_count = len(self.federation.current_rings())
        return {
            "evaluated": evaluated,
            "allowed": allowed,
            "held": held,
            "blocked": blocked,
            "rings": rings_count,
            "dpip": dpip_count,
        }

    def emit_case_broadcast(self, case_data: Dict[str, Any]) -> None:
        """Emit real-time new_case payload over WebSocket."""
        try:
            from app.api.websocket import schedule_broadcast
            payload = {
                "event": "new_case",
                "data": self.format_case_payload(case_data),
                "stats": self.get_current_stats(),
            }
            schedule_broadcast(payload)
        except Exception as exc:
            logger.debug("Failed to emit case broadcast: %s", exc)

    def _open_case(self, txn: UpiTransaction, resp: UpiEvaluationResponse) -> str:
        """Create a new investigative case for flagged or held payments."""
        case_id = f"upi_case_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        if hasattr(txn, "model_dump"):
            trigger_txn_dict = txn.model_dump()
        elif hasattr(txn, "dict"):
            trigger_txn_dict = txn.dict()
        else:
            trigger_txn_dict = {
                "txn_id": getattr(txn, "txn_id", None),
                "payer_vpa": getattr(txn, "payer_vpa", None),
                "payee_vpa": getattr(txn, "payee_vpa", None),
                "amount": float(getattr(txn, "amount", 0.0)),
                "timestamp": str(getattr(txn, "timestamp", "")),
                "payer_psp": getattr(txn, "payer_psp", None),
                "payee_psp": getattr(txn, "payee_psp", None),
                "device_id": getattr(txn, "device_id", None),
                "txn_type": getattr(txn, "txn_type", "P2P"),
            }
        # Ensure timestamp is ISO string
        if isinstance(trigger_txn_dict.get("timestamp"), datetime):
            trigger_txn_dict["timestamp"] = trigger_txn_dict["timestamp"].isoformat()

        rule_hits_raw = getattr(resp, "rule_hits", None) or getattr(resp, "rule_breakdown", []) or []
        if isinstance(rule_hits_raw, list):
            rule_hits_list = [
                h.model_dump() if hasattr(h, "model_dump") else (h.dict() if hasattr(h, "dict") else (dict(h) if isinstance(h, dict) else str(h)))
                for h in rule_hits_raw
            ]
        elif isinstance(rule_hits_raw, dict):
            rule_hits_list = [rule_hits_raw]
        else:
            rule_hits_list = []

        default_topology = {
            "trigger_txn": trigger_txn_dict,
            "fan_in": [txn.payer_vpa] if txn.payer_vpa else [],
            "hops": [],
            "fan_out": [txn.payee_vpa] if txn.payee_vpa else [],
        }

        case_data: Dict[str, Any] = {
            "case_id": case_id,
            "trigger_txn_id": txn.txn_id,
            "trigger_txn": trigger_txn_dict,
            "payer_vpa": txn.payer_vpa,
            "payee_vpa": txn.payee_vpa,
            "amount": float(txn.amount),
            "verdict": resp.action,
            "risk_score": resp.risk_score,
            "reasons": resp.reasons,
            "rule_hits": rule_hits_list,
            "adaptive_score": float(resp.adaptive_score or 0.0),
            "network_score": float(resp.network_score or 0.0),
            "status": "OPEN",
            "ring_hash": None,
            "ring_members_vpas": [],
            "token_economy": None,
            "sar_markdown": None,
            "visual_path": None,
            "topology": default_topology,
            "created_at": now_iso,
            "resolution": None,
            "investigated_at": None,
            "resolution_notes": None,
        }

        with self._lock:
            self._cases[case_id] = case_data

        # Asynchronously persist to database if available
        self._schedule_db_save_case(case_data)
        # Broadcast real-time case notification to connected clients
        self.emit_case_broadcast(case_data)
        return case_id

    def create_case(
        self,
        txn: Union[UpiTransaction, Dict[str, Any]],
        resp: Optional[UpiEvaluationResponse] = None,
    ) -> str:
        """Create a new case from a transaction and broadcast event."""
        if isinstance(txn, dict):
            txn_dict = txn
            txn_obj = UpiTransaction(
                txn_id=txn_dict.get("txn_id", f"TXN_{uuid.uuid4().hex[:8]}"),
                payer_vpa=txn_dict.get("payer_vpa", ""),
                payee_vpa=txn_dict.get("payee_vpa", ""),
                amount=float(txn_dict.get("amount", 0.0)),
                timestamp=txn_dict.get("timestamp") or datetime.now(timezone.utc),
                payer_psp=txn_dict.get("payer_psp", "PSP_DEFAULT"),
                payee_psp=txn_dict.get("payee_psp", "PSP_DEFAULT"),
                device_id=txn_dict.get("device_id"),
                txn_type=txn_dict.get("txn_type", "P2P"),
            )
        else:
            txn_obj = txn

        if resp is None:
            resp = UpiEvaluationResponse(
                txn_id=txn_obj.txn_id,
                action="HOLD",
                risk_score=75,
                reasons=["INVESTIGATIVE_TRIGGER"],
                rule_breakdown=[],
            )

        return self._open_case(txn_obj, resp)

    def save_case(self, case_data: Dict[str, Any]) -> None:
        """Save or update case record and broadcast update."""
        cid = case_data.get("case_id")
        if not cid:
            return
        with self._lock:
            self._cases[cid] = dict(case_data)
        self._schedule_db_save_case(case_data)
        self.emit_case_broadcast(case_data)

    def evaluate(self, txn: UpiTransaction) -> UpiEvaluationResponse:
        """Inline pre-transaction evaluation gate."""
        network = self.federation.network_score_for_txn(txn)
        external = self.dpip.external_score_for_pair(txn.payer_vpa, txn.payee_vpa)
        combined_network = max(network, external)

        resp = self.scorer.evaluate(txn, network_score=combined_network)

        txn_entry = {
            "txn_id": txn.txn_id,
            "timestamp": txn.timestamp.isoformat() if isinstance(txn.timestamp, datetime) else str(txn.timestamp),
            "amount": float(txn.amount),
            "payer_vpa": txn.payer_vpa,
            "payee_vpa": txn.payee_vpa,
            "payer_psp": txn.payer_psp,
            "payee_psp": txn.payee_psp,
            "action": resp.action,
            "risk_score": resp.risk_score,
            "reasons": resp.reasons,
            "network_score": combined_network,
            "adaptive_score": resp.adaptive_score,
        }

        with self._lock:
            self._eval_count += 1
            if resp.action == "ALLOW":
                self._allow_count += 1
            elif resp.action == "HOLD":
                self._hold_count += 1
            elif resp.action == "BLOCK":
                self._block_count += 1

            self._txn_log.append(txn_entry)
            if len(self._txn_log) > 5000:
                self._txn_log = self._txn_log[-5000:]

        if resp.action in ("HOLD", "BLOCK"):
            case_id = self._open_case(txn, resp)
            resp.case_id = case_id

        return resp

    def _attach_ring_and_build_sar(self, ring: Dict[str, Any]) -> None:
        """Attach detected mule ring metadata and generate SAR for open cases."""
        member_set = set(ring.get("members", []))
        with self._lock:
            cases = [dict(c) for c in self._cases.values() if c.get("status") == "OPEN"]
            txn_log = list(self._txn_log)

        ring_txns: List[Dict[str, Any]] = []
        for t in txn_log:
            payer_in = pseudonymize(t.get("payer_vpa", ""), self.federation.salt) in member_set
            payee_in = pseudonymize(t.get("payee_vpa", ""), self.federation.salt) in member_set
            if payer_in or payee_in:
                t_copy = dict(t)
                t_copy.setdefault("scenario", self._infer_scenario(t, member_set))
                ring_txns.append(t_copy)

        updated_cases: List[Dict[str, Any]] = []

        for case in cases:
            trig = case.get("trigger_txn", {})
            trig_payer = pseudonymize(trig.get("payer_vpa", ""), self.federation.salt)
            trig_payee = pseudonymize(trig.get("payee_vpa", ""), self.federation.salt)
            if trig_payer in member_set or trig_payee in member_set:
                cid = case.get("case_id", "")
                economy = build_upi_token_economy(ring, ring_txns)
                sar = generate_upi_sar(cid, ring, ring_txns, trig, economy)
                visual = render_ring_png(cid, ring, ring_txns, artifact_dir=self.artifact_dir)

                scenarios = [t.get("scenario") for t in ring_txns]
                fan_in = sum(1 for s in scenarios if s == "fan_in")
                hops = sum(1 for s in scenarios if s == "pass_through")
                fan_out = sum(1 for s in scenarios if s == "fan_out")
                total_amount = sum(float(t.get("amount", 0.0)) for t in ring_txns)

                topology = {
                    "psps": ring.get("psps", []),
                    "member_count": ring.get("size", len(member_set)),
                    "total_amount": round(total_amount, 2),
                    "fan_in": fan_in,
                    "hops": hops,
                    "fan_out": fan_out,
                }

                with self._lock:
                    target_case = self._cases.get(cid)
                    if target_case:
                        target_case["ring_hash"] = ring.get("ring_hash")
                        target_case["ring_members_vpas"] = self._resolve_members(ring_txns, member_set)
                        target_case["token_economy"] = economy
                        target_case["sar_markdown"] = sar
                        target_case["visual_path"] = visual
                        target_case["topology"] = topology
                        target_case["status"] = "INVESTIGATED"
                        updated_cases.append(dict(target_case))

        # Persist ring and updated cases to PostgreSQL and broadcast updates
        self._schedule_db_save_ring(ring)
        for u_case in updated_cases:
            self._schedule_db_save_case(u_case)
            self.emit_case_broadcast(u_case)

    def run_federation(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Execute a cross-PSP federation consensus round."""
        result = self.federation.run_federation_round(now=now)
        for ring in result.get("rings", []):
            self._attach_ring_and_build_sar(ring)
            self._schedule_db_save_ring(ring)
        return result

    def submit_feedback(self, case_id: str, confirmed_fraud: bool) -> Dict[str, Any]:
        """Submit analyst feedback for a case and propagate updates."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                raise KeyError(f"UPI case '{case_id}' not found")
            member_vpas = case.get("ring_members_vpas", []) or [case.get("payer_vpa"), case.get("payee_vpa")]
            member_vpas = [v for v in member_vpas if v]

        if confirmed_fraud:
            psps_list = []
            if isinstance(case.get("topology"), dict):
                psps_list = case.get("topology", {}).get("psps", [])
            published = self.dpip.publish_confirmed_ring(
                ring_hash=case.get("ring_hash") or f"RING-CASE-{case_id}",
                vpas=member_vpas,
                psps=psps_list,
                total_amount=float(case.get("amount", 0.0)),
                case_id=case_id,
            )
            for v in member_vpas:
                self.dpip.ingest_external_signal(v, risk=1.0, source="ANALYST_CONFIRMED")
            self.adaptive.feedback(member_vpas, confirmed_fraud=True)
            resolution = "CONFIRMED_FRAUD"
        else:
            self.adaptive.feedback(member_vpas, confirmed_fraud=False)
            published = None
            resolution = "DISMISSED_FALSE_POSITIVE"

        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            case["status"] = "RESOLVED"
            case["resolution"] = resolution
            case["investigated_at"] = now_iso

        feedback_record = {
            "case_id": case_id,
            "confirmed_fraud": confirmed_fraud,
            "resolution": resolution,
            "notes": None,
            "vpas_flagged": member_vpas,
            "dpip_published": published,
        }

        # Persist feedback and updated case status to DB
        self._schedule_db_save_feedback(feedback_record)
        self._schedule_db_save_case(case)

        return {
            "case_id": case_id,
            "resolution": resolution,
            "dpip_published": published,
        }

    def list_cases(self) -> List[Dict[str, Any]]:
        """Return all in-memory cases sorted by created_at descending."""
        with self._lock:
            return sorted(self._cases.values(), key=lambda c: c.get("created_at", ""), reverse=True)

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Return full details for a given case_id."""
        with self._lock:
            case = self._cases.get(case_id)
            return dict(case) if case else None

    def clear(self) -> None:
        """Clear ephemeral state."""
        with self._lock:
            self._cases.clear()
            self._txn_log.clear()
            self._eval_count = 0
            self._allow_count = 0
            self._hold_count = 0
            self._block_count = 0

    # ── Database Sync and Persistence Helpers ─────────────────────────────────

    async def save_case_to_db_session(self, case_data: Dict[str, Any], session: AsyncSession) -> None:
        """Persist or upsert UpiCaseModel using an active AsyncSession."""
        cid = case_data["case_id"]
        existing = await session.get(UpiCaseModel, cid)

        created_at_val = case_data.get("created_at")
        if isinstance(created_at_val, str):
            try:
                created_at_dt = datetime.fromisoformat(created_at_val)
            except ValueError:
                created_at_dt = datetime.now(timezone.utc)
        else:
            created_at_dt = created_at_val or datetime.now(timezone.utc)

        investigated_at_val = case_data.get("investigated_at")
        if isinstance(investigated_at_val, str):
            try:
                investigated_at_dt = datetime.fromisoformat(investigated_at_val)
            except ValueError:
                investigated_at_dt = None
        else:
            investigated_at_dt = investigated_at_val

        if existing:
            existing.status = case_data.get("status", existing.status)
            existing.verdict = case_data.get("verdict", existing.verdict)
            existing.risk_score = case_data.get("risk_score", existing.risk_score)
            existing.ring_hash = case_data.get("ring_hash", existing.ring_hash)
            existing.ring_members_vpas = case_data.get("ring_members_vpas", existing.ring_members_vpas)
            existing.token_economy = case_data.get("token_economy", existing.token_economy)
            existing.sar_markdown = case_data.get("sar_markdown", existing.sar_markdown)
            existing.visual_path = case_data.get("visual_path", existing.visual_path)
            existing.topology = case_data.get("topology", existing.topology)
            existing.resolution = case_data.get("resolution", existing.resolution)
            existing.investigated_at = investigated_at_dt
            existing.resolution_notes = case_data.get("resolution_notes", existing.resolution_notes)
        else:
            new_case = UpiCaseModel(
                case_id=cid,
                created_at=created_at_dt,
                status=case_data.get("status", "OPEN"),
                verdict=case_data.get("verdict", "HOLD"),
                risk_score=case_data.get("risk_score", 0),
                payer_vpa=case_data.get("payer_vpa"),
                payee_vpa=case_data.get("payee_vpa"),
                amount=case_data.get("amount"),
                trigger_txn=case_data.get("trigger_txn", {}),
                rule_hits=case_data.get("rule_hits", []),
                adaptive_score=case_data.get("adaptive_score", 0.0),
                network_score=case_data.get("network_score", 0.0),
                ring_hash=case_data.get("ring_hash"),
                ring_members_vpas=case_data.get("ring_members_vpas", []),
                token_economy=case_data.get("token_economy"),
                sar_markdown=case_data.get("sar_markdown"),
                visual_path=case_data.get("visual_path"),
                topology=case_data.get("topology"),
                resolution=case_data.get("resolution"),
                investigated_at=investigated_at_dt,
                resolution_notes=case_data.get("resolution_notes"),
            )
            session.add(new_case)
        await session.flush()

    async def save_ring_to_db_session(self, ring_data: Dict[str, Any], session: AsyncSession) -> None:
        """Persist or upsert MuleRingModel using an active AsyncSession."""
        r_hash = ring_data.get("ring_hash")
        if not r_hash:
            return

        existing = await session.get(MuleRingModel, r_hash)

        detected_at_val = ring_data.get("detected_at")
        if isinstance(detected_at_val, str):
            try:
                detected_at_dt = datetime.fromisoformat(detected_at_val)
            except ValueError:
                detected_at_dt = datetime.now(timezone.utc)
        else:
            detected_at_dt = detected_at_val or datetime.now(timezone.utc)

        if existing:
            existing.size = ring_data.get("size", existing.size)
            existing.members = ring_data.get("members", existing.members)
            existing.psps = ring_data.get("psps", existing.psps)
            existing.total_amount = ring_data.get("total_amount", existing.total_amount)
            existing.status = ring_data.get("status", existing.status)
        else:
            new_ring = MuleRingModel(
                ring_hash=r_hash,
                detected_at=detected_at_dt,
                size=ring_data.get("size", len(ring_data.get("members", []))),
                members=ring_data.get("members", []),
                psps=ring_data.get("psps", []),
                total_amount=ring_data.get("total_amount", 0.0),
                status=ring_data.get("status", "ACTIVE"),
            )
            session.add(new_ring)
        await session.flush()

    async def save_feedback_to_db_session(self, feedback_data: Dict[str, Any], session: AsyncSession) -> None:
        """Persist CaseFeedbackModel using an active AsyncSession."""
        fb = CaseFeedbackModel(
            case_id=feedback_data["case_id"],
            confirmed_fraud=feedback_data["confirmed_fraud"],
            resolution=feedback_data["resolution"],
            notes=feedback_data.get("notes"),
            submitted_at=datetime.now(timezone.utc),
            vpas_flagged=feedback_data.get("vpas_flagged", []),
            dpip_published=feedback_data.get("dpip_published"),
        )
        session.add(fb)
        await session.flush()

    def _schedule_db_save_case(self, case_data: Dict[str, Any]) -> None:
        """Schedule asynchronous save of case to PostgreSQL."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._async_save_case(case_data))
        except RuntimeError:
            pass

    def _schedule_db_save_ring(self, ring_data: Dict[str, Any]) -> None:
        """Schedule asynchronous save of ring to PostgreSQL."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._async_save_ring(ring_data))
        except RuntimeError:
            pass

    def _schedule_db_save_feedback(self, feedback_data: Dict[str, Any]) -> None:
        """Schedule asynchronous save of feedback to PostgreSQL."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._async_save_feedback(feedback_data))
        except RuntimeError:
            pass

    async def _async_save_case(self, case_data: Dict[str, Any]) -> None:
        """Background save of case to DB."""
        from app.db.session import get_sessionmaker
        sm = get_sessionmaker()
        if sm is None:
            return
        try:
            async with sm() as session:
                await self.save_case_to_db_session(case_data, session)
                await session.commit()
        except Exception as exc:
            logger.debug(f"DB case background save failed (graceful): {exc}")

    async def _async_save_ring(self, ring_data: Dict[str, Any]) -> None:
        """Background save of ring to DB."""
        from app.db.session import get_sessionmaker
        sm = get_sessionmaker()
        if sm is None:
            return
        try:
            async with sm() as session:
                await self.save_ring_to_db_session(ring_data, session)
                await session.commit()
        except Exception as exc:
            logger.debug(f"DB ring background save failed (graceful): {exc}")

    async def _async_save_feedback(self, feedback_data: Dict[str, Any]) -> None:
        """Background save of feedback to DB."""
        from app.db.session import get_sessionmaker
        sm = get_sessionmaker()
        if sm is None:
            return
        try:
            async with sm() as session:
                await self.save_feedback_to_db_session(feedback_data, session)
                await session.commit()
        except Exception as exc:
            logger.debug(f"DB feedback background save failed (graceful): {exc}")

    async def sync_from_db(self) -> None:
        """Load persisted cases and rings from PostgreSQL on startup."""
        from app.db.session import get_sessionmaker
        sm = get_sessionmaker()
        if sm is None:
            return

        try:
            async with sm() as session:
                # Load cases
                result = await session.execute(select(UpiCaseModel).order_by(UpiCaseModel.created_at.desc()))
                cases = result.scalars().all()
                with self._lock:
                    for c in cases:
                        self._cases[c.case_id] = c.to_dict(include_sar=True)
                logger.info(f"Loaded {len(cases)} persistent cases from PostgreSQL into active service cache.")

                # Load rings
                r_result = await session.execute(select(MuleRingModel))
                rings = r_result.scalars().all()
                with self.federation._lock:
                    for r in rings:
                        self.federation._rings[r.ring_hash] = r.to_dict()
                logger.info(f"Loaded {len(rings)} persistent rings from PostgreSQL into federation coordinator.")
        except Exception as exc:
            logger.warning(f"Error synchronizing state from PostgreSQL: {exc}")


_service: Optional[UpiCaseService] = None


def get_upi_case_service() -> UpiCaseService:
    """Obtain or initialize the global UpiCaseService singleton."""
    global _service
    if _service is None:
        _service = UpiCaseService()
    return _service

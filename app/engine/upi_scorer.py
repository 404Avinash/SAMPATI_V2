"""3-Layer UPI Fraud Risk Scorer Engine for SAMPATI V2.

Layer 1: Deterministic rules (0 - 100 points, including R_HONEYPOT_HIT).
Layer 2: Adaptive EWMA anomaly detection (0 - 25 points).
Layer 3: Cross-PSP federated graph network score (0 - 40 points).
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Optional

from app.engine.adaptive import AdaptiveBehaviorModel, get_adaptive_model
from app.engine.upi_rules import evaluate_rules
from app.engine.upi_state import UpiHotState, get_upi_state
from app.models.upi_models import RuleHit, UpiEvaluationResponse, UpiTransaction

ALLOW_BELOW: int = 45
BLOCK_AT: int = 70
NETWORK_HOLD_FLOOR: float = 0.7
ADAPTIVE_MAX_POINTS: int = 25
NETWORK_MAX_POINTS: int = 40


class UpiRiskScorer:
    """Composite 3-layer risk scoring engine for real-time UPI payments."""

    def __init__(
        self,
        state: Optional[UpiHotState] = None,
        adaptive: Optional[AdaptiveBehaviorModel] = None,
    ) -> None:
        self.state: UpiHotState = state if state is not None else get_upi_state()
        self.adaptive: AdaptiveBehaviorModel = adaptive if adaptive is not None else get_adaptive_model()

    def evaluate(self, txn: UpiTransaction, network_score: float = 0.0) -> UpiEvaluationResponse:
        """Score an incoming UPI transaction through all 3 evaluation layers."""
        t0 = time.perf_counter()

        hits = evaluate_rules(txn, self.state)
        rule_score = min(100, sum(h.points for h in hits))

        adaptive_score = self.adaptive.score(txn)
        adaptive_pts = int(adaptive_score * ADAPTIVE_MAX_POINTS)

        network_pts = int(network_score * NETWORK_MAX_POINTS)

        combined = rule_score + adaptive_pts + network_pts
        risk_score = min(100, max(0, combined))

        if risk_score >= BLOCK_AT:
            action = "BLOCK"
        elif risk_score >= ALLOW_BELOW:
            action = "HOLD"
        elif network_score >= NETWORK_HOLD_FLOOR:
            action = "HOLD"
            risk_score = max(risk_score, ALLOW_BELOW)
        else:
            action = "ALLOW"

        reasons = [h.code for h in hits]
        if adaptive_score >= 0.6:
            reasons.append("BEHAVIORAL_ANOMALY")
        if network_score >= 0.5:
            reasons.append("FEDERATED_MULE_NETWORK")

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)

        self.state.record_txn(
            timestamp=txn.timestamp,
            payer_vpa=txn.payer_vpa,
            payee_vpa=txn.payee_vpa,
            amount=txn.amount,
            device_id=txn.device_id,
            sim_id=txn.sim_id,
        )

        self.adaptive.observe(txn)

        return UpiEvaluationResponse(
            txn_id=txn.txn_id,
            risk_score=risk_score,
            action=action,
            reasons=reasons,
            rule_breakdown=hits,
            rule_score=rule_score,
            adaptive_score=round(adaptive_score, 4),
            network_score=round(network_score, 4),
            execution_latency_ms=elapsed_ms,
            evaluated_at=datetime.now(timezone.utc),
        )


_scorer: Optional[UpiRiskScorer] = None


def get_upi_scorer() -> UpiRiskScorer:
    """Obtain or initialize the global singleton UpiRiskScorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = UpiRiskScorer()
    return _scorer

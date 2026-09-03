"""4-Layer UPI Fraud Risk Scorer Engine for SAMPATI V2.

Layer 1: Deterministic rules (0 - 100 points, including R_HONEYPOT_HIT, device telemetry, and campaign DNA).
Layer 2: Adaptive EWMA anomaly detection (0 - 25 points).
Layer 3: Cross-PSP federated graph network score (0 - 40 points).
Layer 4: Unsupervised Isolation Forest multivariate anomaly score (0 - 25 points).
Enriched with Dead Money Velocity (DMV) scoring and Campaign Signature clustering.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from app.engine.adaptive import AdaptiveBehaviorModel, get_adaptive_model
from app.engine.campaign import CampaignSignatureStore, get_campaign_store
from app.engine.dmv import DmvTracker, calculate_dmv_score, get_dmv_tracker
from app.engine.isolation_forest import UpiIsolationForest, get_isolation_forest
from app.engine.upi_rules import evaluate_rules, record_payer_telemetry
from app.engine.upi_state import UpiHotState, get_upi_state
from app.models.upi_models import UpiEvaluationResponse, UpiTransaction

ALLOW_BELOW: int = 45
BLOCK_AT: int = 70
NETWORK_HOLD_FLOOR: float = 0.7
ADAPTIVE_MAX_POINTS: int = 25
NETWORK_MAX_POINTS: int = 40
ML_MAX_POINTS: int = 25
ML_HOLD_FLOOR: float = 0.85
ML_ANOMALY_THRESHOLD: float = 0.70


class UpiRiskScorer:
    """Composite 4-layer risk scoring engine for real-time UPI payments."""

    def __init__(
        self,
        state: Optional[UpiHotState] = None,
        adaptive: Optional[AdaptiveBehaviorModel] = None,
        dmv_tracker: Optional[DmvTracker] = None,
        campaign_store: Optional[CampaignSignatureStore] = None,
        isolation_forest: Optional[UpiIsolationForest] = None,
    ) -> None:
        self.state: UpiHotState = state if state is not None else get_upi_state()
        self.adaptive: AdaptiveBehaviorModel = adaptive if adaptive is not None else get_adaptive_model()
        self.dmv_tracker: DmvTracker = dmv_tracker if dmv_tracker is not None else get_dmv_tracker()
        self.campaign_store: CampaignSignatureStore = campaign_store if campaign_store is not None else get_campaign_store()
        self.isolation_forest: UpiIsolationForest = (
            isolation_forest if isolation_forest is not None else get_isolation_forest()
        )
        self.ml_scorer: UpiIsolationForest = self.isolation_forest

    def evaluate(self, txn: UpiTransaction, network_score: float = 0.0) -> UpiEvaluationResponse:
        """Score an incoming UPI transaction through all 4 evaluation layers."""
        t0 = time.perf_counter()

        hits = evaluate_rules(txn, self.state, self.campaign_store)
        rule_score = min(100, sum(h.points for h in hits))

        adaptive_score = self.adaptive.score(txn)
        adaptive_pts = int(adaptive_score * ADAPTIVE_MAX_POINTS)

        network_pts = int(network_score * NETWORK_MAX_POINTS)

        # DMV Score calculation
        dmv_score = calculate_dmv_score(txn, self.dmv_tracker)

        # Layer 4: Unsupervised Isolation Forest Multivariate ML Anomaly Score
        ml_score = self.isolation_forest.score_txn(txn, self.state, dmv_score)
        if ml_score > 0.50:
            ml_pts = int(round((ml_score - 0.50) / 0.50 * ML_MAX_POINTS))
            ml_pts = min(ML_MAX_POINTS, max(0, ml_pts))
        else:
            ml_pts = 0

        combined = rule_score + adaptive_pts + network_pts + ml_pts
        risk_score = min(100, max(0, combined))

        if risk_score >= BLOCK_AT:
            action = "BLOCK"
        elif risk_score >= ALLOW_BELOW:
            action = "HOLD"
        elif network_score >= NETWORK_HOLD_FLOOR:
            action = "HOLD"
            risk_score = max(risk_score, ALLOW_BELOW)
        elif ml_score >= ML_HOLD_FLOOR:
            action = "HOLD"
            risk_score = max(risk_score, ALLOW_BELOW)
        else:
            action = "ALLOW"

        reasons = [h.code for h in hits]
        if adaptive_score >= 0.6:
            reasons.append("BEHAVIORAL_ANOMALY")
        if network_score >= 0.5:
            reasons.append("FEDERATED_MULE_NETWORK")
        if ml_score >= ML_ANOMALY_THRESHOLD:
            reasons.append("ML_MULTIVARIATE_ANOMALY")

        # Active Campaign Fingerprint matching
        matched_campaign = self.campaign_store.match_campaign(txn, threshold=0.82)
        campaign_id = matched_campaign[0] if matched_campaign is not None else None

        # On BLOCK verdict, ingest behavioral fingerprint into campaign signature store
        if action == "BLOCK":
            self.campaign_store.ingest_fingerprint(txn)

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)

        # Update historical state and telemetry
        self.state.record_txn(
            timestamp=txn.timestamp,
            payer_vpa=txn.payer_vpa,
            payee_vpa=txn.payee_vpa,
            amount=txn.amount,
            device_id=txn.device_id,
            sim_id=txn.sim_id,
        )

        self.dmv_tracker.record_txn(txn)

        record_payer_telemetry(
            payer_vpa=txn.payer_vpa,
            device_id=txn.device_id,
            sim_id=txn.sim_id,
            location=txn.location,
            timestamp=txn.timestamp,
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
            ml_anomaly_score=round(ml_score, 4),
            dmv_score=dmv_score,
            campaign_id=campaign_id,
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

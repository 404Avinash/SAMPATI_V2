"""Pydantic Models and Data Structures for SAMPATI V2 UPI Mule Detection."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

try:
    from pydantic import BaseModel, Field
except ImportError:
    from app.models.pydantic_models import BaseModel, Field  # type: ignore


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


SIMULATED_PSPS: List[str] = ["okaxis", "ybl", "paytm", "ibl"]
VerdictAction = Literal["ALLOW", "HOLD", "BLOCK"]
TxnType = Literal["P2P", "P2M", "COLLECT"]


class RuleHit(BaseModel):
    """A single explainable rule contribution to the risk score."""
    code: str = Field(..., description="Unique rule code identifier")
    points: int = Field(..., description="Risk points contributed by this rule")
    detail: str = Field(default="", description="Detailed human-readable reason")


class UpiTransaction(BaseModel):
    """Incoming UPI Transaction payload for inline evaluation."""
    txn_id: str = Field(..., description="Unique UPI transaction reference")
    timestamp: datetime = Field(default_factory=utcnow, description="Transaction timestamp in UTC")
    amount: float = Field(..., description="Transaction amount in INR")
    txn_type: str = Field(default="P2P", description="UPI transaction type: P2P, P2M, COLLECT")
    payer_vpa: str = Field(..., description="Payer Virtual Payment Address")
    payer_psp: str = Field(default="", description="Payer PSP handle")
    payer_account_age_days: int = Field(default=365, description="Age of payer bank account in days")
    payee_vpa: str = Field(..., description="Payee Virtual Payment Address")
    payee_psp: str = Field(default="", description="Payee PSP handle")
    payee_vpa_age_days: int = Field(default=365, description="Age of payee VPA in days")
    payee_is_new_for_payer: bool = Field(default=False, description="Whether this is first transfer between pair")
    device_id: str = Field(default="", description="Payer device hardware fingerprint")
    sim_id: str = Field(default="", description="Payer SIM card identifier")
    note: str = Field(default="", description="Optional UPI payment note/remark")
    ip: str = Field(default="", description="Payer IP address")
    location: str = Field(default="", description="Geo location")

    def __init__(self, **data: Any):
        if "payer_vpa" in data and not data.get("payer_psp"):
            vpa = data.get("payer_vpa", "")
            data["payer_psp"] = vpa.split("@")[-1] if "@" in vpa else "unknown"
        if "payee_vpa" in data and not data.get("payee_psp"):
            vpa = data.get("payee_vpa", "")
            data["payee_psp"] = vpa.split("@")[-1] if "@" in vpa else "unknown"
        super().__init__(**data)


class UpiEvaluationResponse(BaseModel):
    """Response returned by inline UPI scoring gate."""
    txn_id: str = Field(..., description="Transaction reference evaluated")
    risk_score: int = Field(..., description="Composite risk score from 0 to 100")
    action: str = Field(..., description="Decision verdict: ALLOW, HOLD, BLOCK")
    reasons: List[str] = Field(default_factory=list, description="List of triggered rule reason strings")
    rule_breakdown: List[RuleHit] = Field(default_factory=list, description="Detailed per-rule score contributions")
    rule_score: int = Field(default=0, description="Layer 1 deterministic rule score")
    adaptive_score: float = Field(default=0.0, description="Layer 2 adaptive anomaly score")
    network_score: float = Field(default=0.0, description="Layer 3 federated graph network score")
    execution_latency_ms: float = Field(default=0.0, description="Decision latency in milliseconds")
    evaluated_at: datetime = Field(default_factory=utcnow, description="Evaluation timestamp")
    case_id: Optional[str] = Field(default=None, description="Investigative case ID if HOLD or BLOCK")


class MuleRingSummary(BaseModel):
    """Discovered cross-PSP mule ring summary."""
    ring_id: str = Field(..., description="Unique ring identifier hash")
    scenario: str = Field(..., description="Mule pattern scenario descriptor")
    vpas: List[str] = Field(default_factory=list, description="Member VPAs involved in ring")
    psps: List[str] = Field(default_factory=list, description="PSP handles involved in ring")
    txn_ids: List[str] = Field(default_factory=list, description="Transaction references in ring")
    total_amount: float = Field(default=0.0, description="Total INR volume transferred in ring")


class LabeledUpiTransaction(BaseModel):
    """Synthetic labeled UPI transaction for simulation and benchmark testing."""
    txn: UpiTransaction = Field(..., description="Inner UPI transaction record")
    label: str = Field(default="legit", description="Ground truth label: legit or fraud")
    scenario: str = Field(default="p2p", description="Synthetic scenario pattern")
    ring_id: Optional[str] = Field(default=None, description="Associated ring ID if part of syndicate")


class FeedbackRequest(BaseModel):
    """Human investigator case feedback payload."""
    confirmed_fraud: Optional[bool] = Field(None, description="True if fraud confirmed, False if false positive")
    confirmed: Optional[bool] = Field(None, description="Alias for confirmed_fraud")

    @property
    def is_confirmed_fraud(self) -> bool:
        if self.confirmed_fraud is not None:
            return bool(self.confirmed_fraud)
        if self.confirmed is not None:
            return bool(self.confirmed)
        return False


class SimulateRequest(BaseModel):
    """Synthetic traffic simulation request."""
    total_txns: int = Field(default=100, description="Number of transactions to simulate")
    fraud_ratio: float = Field(default=0.15, description="Ratio of fraudulent transactions (0.0 to 1.0)")
    seed: Optional[int] = Field(default=42, description="Random generator seed for reproducibility")
    run_federation: bool = Field(default=True, description="Whether to trigger federation consensus after stream")


class CaseStatusUpdateRequest(BaseModel):
    """Request payload for updating investigative case status."""
    status: str = Field(..., description="Target status: reviewed, escalated, dismissed, open")
    notes: Optional[str] = Field(None, description="Analyst review commentary")
    resolution_notes: Optional[str] = Field(None, description="Detailed resolution justification")
    resolution: Optional[str] = Field(None, description="Custom resolution code")
    escalate_to_dpip: Optional[bool] = Field(None, description="Explicit flag to trigger DPIP publishing")


class AnalyticsSummary(BaseModel):
    """Summary statistics for analytics dashboard."""
    total_evaluated: int = Field(0, description="Total transactions evaluated")
    total_flagged: int = Field(0, description="Total transactions flagged (HOLD + BLOCK)")
    total_allowed: int = Field(0, description="Total transactions allowed")
    total_held: int = Field(0, description="Total transactions held")
    total_blocked: int = Field(0, description="Total transactions blocked")
    fraud_rate_pct: float = Field(0.0, description="Percentage of evaluated transactions flagged")
    avg_risk_score: float = Field(0.0, description="Average risk score across evaluations")
    total_amount_protected: float = Field(0.0, description="Total INR amount in flagged transactions")


class TimeSeriesBucket(BaseModel):
    """Time-series bucket item for verdict trends."""
    bucket: str = Field(..., description="Bucket identifier string")
    timestamp: str = Field(..., description="Bucket start timestamp in ISO format")
    allow: int = Field(0, description="Count of ALLOW verdicts")
    hold: int = Field(0, description="Count of HOLD verdicts")
    block: int = Field(0, description="Count of BLOCK verdicts")
    total: int = Field(0, description="Total transactions in bucket")
    fraud_rate_pct: float = Field(0.0, description="Fraud percentage in bucket")
    total_amount: float = Field(0.0, description="Total INR volume in bucket")


class RuleFrequencyItem(BaseModel):
    """Frequency and severity breakdown for a specific detection rule."""
    rule_id: str = Field(..., description="Detection rule identifier code")
    rule_name: str = Field(..., description="Human-readable rule name")
    trigger_count: int = Field(0, description="Number of times rule was triggered")
    percentage: float = Field(0.0, description="Trigger percentage relative to total rule hits")
    severity: str = Field("MEDIUM", description="Rule severity level: LOW, MEDIUM, HIGH, CRITICAL")


class TopFlaggedAccountItem(BaseModel):
    """Aggregated metrics for high-risk accounts."""
    account_id: str = Field(..., description="Unique account / VPA identifier")
    vpa: str = Field(..., description="Virtual Payment Address")
    bank: str = Field("UNKNOWN", description="Associated bank name")
    psp: str = Field("unknown", description="PSP handle identifier")
    flagged_count: int = Field(0, description="Total times account was flagged in cases")
    hold_count: int = Field(0, description="Times account was put on HOLD")
    block_count: int = Field(0, description="Times account was BLOCKED")
    total_flagged_amount: float = Field(0.0, description="Total INR volume flagged for this account")
    avg_risk_score: float = Field(0.0, description="Average risk score for cases involving this account")
    last_flagged_at: Optional[str] = Field(None, description="ISO timestamp of most recent flagged case")


class BankDistributionItem(BaseModel):
    """Bank and PSP breakdown of flagged payees."""
    bank: str = Field(..., description="Standardized bank name")
    psp: str = Field(..., description="Primary PSP handle")
    count: int = Field(0, description="Number of flagged cases for this bank")
    percentage: float = Field(0.0, description="Percentage of all flagged cases")
    flagged_amount: float = Field(0.0, description="Total INR volume flagged under this bank")


class AnalyticsResponse(BaseModel):
    """Full analytics payload for charts, trends, and risk distributions."""
    timestamp: str = Field(..., description="Report generation timestamp")
    interval: str = Field("hourly", description="Resolution interval: hourly or daily")
    summary: AnalyticsSummary = Field(default_factory=AnalyticsSummary, description="High-level metrics summary")
    time_series: List[Dict[str, Any]] = Field(default_factory=list, description="Time-bucketed verdict counts")
    rule_frequencies: List[Dict[str, Any]] = Field(default_factory=list, description="Rule trigger ranking")
    top_flagged_accounts: List[Dict[str, Any]] = Field(default_factory=list, description="Top high-risk accounts")
    bank_distribution: List[Dict[str, Any]] = Field(default_factory=list, description="Bank-wise fraud distribution")


class DetailedHealthResponse(BaseModel):
    """Real-time system health and telemetry report."""
    status: str = Field("ok", description="Overall health status")
    service: str = Field("sampati-upi", description="Service identifier name")
    version: str = Field("2.0.0", description="Service version string")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime: Dict[str, Any] = Field(default_factory=dict, description="Process uptime information")
    latency_ms: Dict[str, Any] = Field(default_factory=dict, description="Detection engine latency percentiles")
    database: Dict[str, Any] = Field(default_factory=dict, description="Database connection and pool status")
    redis: Dict[str, Any] = Field(default_factory=dict, description="Redis hot cache status and ping latency")
    websocket: Dict[str, Any] = Field(default_factory=dict, description="WebSocket active connection hub metrics")
    throughput: Dict[str, Any] = Field(default_factory=dict, description="Rolling throughput and evaluation counters")

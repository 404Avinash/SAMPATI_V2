"""Deterministic Rule Definitions for SAMPATI V2 UPI Mule Detection.

Implements explainable rule checks across velocity spikes, pass-through conduits,
device-farm clustering, structuring thresholds, and synthetic honeypot traps.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.engine.honeypot import get_honeypot_registry
from app.engine.upi_state import UpiHotState
from app.models.upi_models import RuleHit, UpiTransaction

FRESH_VPA_DAYS: int = 15
FLOW_RULE_MAX_ACCOUNT_AGE: int = 30
PASS_THROUGH_MIN_INFLOW: float = 5000.0
PASS_THROUGH_RATIO: float = 0.9
FAN_IN_DISTINCT_PAYERS: int = 5
FAN_OUT_DISTINCT_PAYEES: int = 5
DEVICE_FARM_VPAS: int = 3
NEW_ACCOUNT_HIGH_VALUE: float = 10000.0
CAUTION_THRESHOLDS: List[float] = [10000.0, 15000.0, 25000.0, 50000.0, 100000.0]


def rule_honeypot_hit(txn: UpiTransaction, state: Optional[UpiHotState] = None) -> Optional[RuleHit]:
    """R_HONEYPOT_HIT: Payee VPA matches seeded synthetic honeypot trap."""
    if not txn.payee_vpa:
        return None
    reg = get_honeypot_registry()
    if reg.is_honeypot(txn.payee_vpa):
        reg.record_hit(
            vpa=txn.payee_vpa,
            txn_id=getattr(txn, "txn_id", None),
            amount=float(getattr(txn, "amount", 0.0)),
            payer_vpa=getattr(txn, "payer_vpa", None),
        )
        return RuleHit(
            code="R_HONEYPOT_HIT",
            points=100,
            detail="Transaction directed to active synthetic honeypot VPA",
        )
    return None


def rule_new_payee_vpa(txn: UpiTransaction) -> Optional[RuleHit]:
    """NEW_PAYEE_VPA: Fresh payee VPA under caution threshold age."""
    if txn.payee_vpa_age_days < FRESH_VPA_DAYS:
        return RuleHit(
            code="NEW_PAYEE_VPA",
            points=25,
            detail=f"Payee VPA '{txn.payee_vpa}' registered {txn.payee_vpa_age_days}d ago (<{FRESH_VPA_DAYS}d)",
        )
    return None


def rule_pass_through_conduit(txn: UpiTransaction, state: UpiHotState) -> Optional[RuleHit]:
    """PASS_THROUGH_CONDUIT: Entity rapidly forwards nearly all incoming funds."""
    if txn.payer_account_age_days >= FLOW_RULE_MAX_ACCOUNT_AGE:
        return None
    now = txn.timestamp
    _, _, received = state.inbound_stats(txn.payer_vpa, now)
    if received < PASS_THROUGH_MIN_INFLOW:
        return None
    _, _, sent_before = state.outbound_stats(txn.payer_vpa, now)
    outflow = sent_before + txn.amount
    ratio = outflow / received
    if ratio >= PASS_THROUGH_RATIO and txn.amount >= 0.5 * received:
        return RuleHit(
            code="PASS_THROUGH_CONDUIT",
            points=30,
            detail=f"'{txn.payer_vpa}' forwarding {ratio:.0%} of Rs {received:,.0f} received in window",
        )
    return None


def rule_fan_in_burst(txn: UpiTransaction, state: UpiHotState) -> Optional[RuleHit]:
    """FAN_IN_BURST: Multiple distinct payers funneling into a fresh account."""
    if txn.payee_vpa_age_days >= FLOW_RULE_MAX_ACCOUNT_AGE:
        return None
    _, distinct_payers, _ = state.inbound_stats(txn.payee_vpa, txn.timestamp)
    if distinct_payers + 1 >= FAN_IN_DISTINCT_PAYERS:
        return RuleHit(
            code="FAN_IN_BURST",
            points=25,
            detail=f"Fresh payee '{txn.payee_vpa}' collecting from {distinct_payers + 1} distinct payers in window",
        )
    return None


def rule_fan_out_dispersal(txn: UpiTransaction, state: UpiHotState) -> Optional[RuleHit]:
    """FAN_OUT_DISPERSAL: Rapid dispersal to multiple distinct payee accounts."""
    if txn.payer_account_age_days >= FLOW_RULE_MAX_ACCOUNT_AGE:
        return None
    _, distinct_payees, _ = state.outbound_stats(txn.payer_vpa, txn.timestamp)
    if distinct_payees + 1 >= FAN_OUT_DISTINCT_PAYEES:
        return RuleHit(
            code="FAN_OUT_DISPERSAL",
            points=25,
            detail=f"Fresh payer '{txn.payer_vpa}' dispersing to {distinct_payees + 1} distinct payees in window",
        )
    return None


def rule_device_farm(txn: UpiTransaction, state: UpiHotState) -> Optional[RuleHit]:
    """DEVICE_FARM: Hardware device fingerprint or SIM shared across multiple VPAs."""
    for fp, kind in ((txn.device_id, "device"), (txn.sim_id, "SIM")):
        if not fp:
            continue
        count = state.device_vpa_count(fp)
        if count >= DEVICE_FARM_VPAS:
            return RuleHit(
                code="DEVICE_FARM",
                points=20,
                detail=f"Payer {kind} fingerprint bound to {count} distinct VPAs",
            )
    return None


def rule_new_account_high_value(txn: UpiTransaction) -> Optional[RuleHit]:
    """NEW_ACCOUNT_HIGH_VALUE: High-value payment on freshly created account."""
    if txn.payer_account_age_days < FRESH_VPA_DAYS and txn.amount >= NEW_ACCOUNT_HIGH_VALUE:
        return RuleHit(
            code="NEW_ACCOUNT_HIGH_VALUE",
            points=15,
            detail=f"Payer account {txn.payer_account_age_days}d old moving Rs {txn.amount:,.0f}",
        )
    return None


def rule_limit_skirting(txn: UpiTransaction) -> Optional[RuleHit]:
    """LIMIT_SKIRTING: Transaction amount suspiciously sits just under caution threshold."""
    for threshold in CAUTION_THRESHOLDS:
        if threshold * 0.98 <= txn.amount < threshold:
            return RuleHit(
                code="LIMIT_SKIRTING",
                points=10,
                detail=f"Amount Rs {txn.amount:,.2f} sits just under Rs {threshold:,.0f} threshold",
            )
    return None


def rule_known_fraud_entity(txn: UpiTransaction, state: UpiHotState) -> Optional[RuleHit]:
    """KNOWN_FRAUD_ENTITY: Payer or Payee VPA flagged in historical confirmed fraud cases."""
    for vpa, role in ((txn.payer_vpa, "Payer"), (txn.payee_vpa, "Payee")):
        if not vpa:
            continue
        hits = state.fraud_memory(vpa)
        if hits > 0:
            return RuleHit(
                code="KNOWN_FRAUD_ENTITY",
                points=35,
                detail=f"{role} '{vpa}' appeared in {hits} analyst-confirmed fraud case(s)",
            )
    return None


def evaluate_rules(txn: UpiTransaction, state: UpiHotState) -> List[RuleHit]:
    """Evaluate all deterministic rules against a single transaction in sequence."""
    hits: List[RuleHit] = []
    results = (
        rule_honeypot_hit(txn, state),
        rule_new_payee_vpa(txn),
        rule_pass_through_conduit(txn, state),
        rule_fan_in_burst(txn, state),
        rule_fan_out_dispersal(txn, state),
        rule_device_farm(txn, state),
        rule_new_account_high_value(txn),
        rule_limit_skirting(txn),
        rule_known_fraud_entity(txn, state),
    )
    for result in results:
        if result is not None:
            hits.append(result)
    return hits

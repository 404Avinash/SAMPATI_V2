"""Deterministic Rule Definitions for SAMPATI V2 UPI Mule Detection.

Implements explainable rule checks across velocity spikes, pass-through conduits,
device-farm clustering, structuring thresholds, synthetic honeypot traps,
SIM/device mismatch, impossible travel velocity, datacenter/VPN IP detection,
and fraud campaign DNA matching.
"""
from __future__ import annotations

import ipaddress
import math
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.engine.campaign import get_campaign_store, rule_campaign_match
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

# Standard Datacenter, Cloud Provider, VPN, and Tor Exit Node CIDR ranges
DATACENTER_CIDRS: List[str] = [
    # AWS Subnets
    "3.0.0.0/8", "13.0.0.0/8", "15.0.0.0/8", "18.0.0.0/8", "35.0.0.0/8",
    "52.0.0.0/8", "54.0.0.0/8", "65.0.0.0/8",
    # GCP Subnets
    "34.0.0.0/8", "35.184.0.0/13", "35.200.0.0/13",
    # Azure Subnets
    "20.0.0.0/8", "40.0.0.0/8", "51.0.0.0/8", "104.40.0.0/13",
    # DigitalOcean Subnets
    "104.131.0.0/16", "138.68.0.0/16", "159.203.0.0/16", "167.99.0.0/16", "188.166.0.0/16",
    # Tor Exit Nodes / Public VPN ranges
    "185.220.100.0/22", "198.51.100.0/24", "203.0.113.0/24", "194.26.29.0/24", "45.154.255.0/24",
]

COMPILED_DC_NETWORKS = [ipaddress.ip_network(cidr) for cidr in DATACENTER_CIDRS]

# Coordinates lookup for Indian & Global Tier-1 Tech / Metro hubs
CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025),
    "new delhi": (28.6139, 77.2090),
    "ncr": (28.6139, 77.2090),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "madras": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "calcutta": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "chandigarh": (30.7333, 76.7794),
    "kochi": (9.9312, 76.2673),
    "cochin": (9.9312, 76.2673),
    "patna": (25.5941, 85.1376),
    "london": (51.5074, -0.1278),
    "new york": (40.7128, -74.0060),
    "singapore": (1.3521, 103.8198),
    "dubai": (25.2048, 55.2708),
    "tokyo": (35.6762, 139.6503),
    "san francisco": (37.7749, -122.4194),
}

# In-memory telemetry cache for payer device and location history
_telemetry_lock = threading.Lock()
_payer_device_history: Dict[str, Tuple[str, str]] = {}
_payer_location_history: Dict[str, Tuple[str, datetime]] = {}


def record_payer_telemetry(
    payer_vpa: str,
    device_id: str = "",
    sim_id: str = "",
    location: str = "",
    timestamp: Optional[datetime] = None,
) -> None:
    """Record payer telemetry for SIM/device consistency and geographic travel tracking."""
    if not payer_vpa:
        return
    now = timestamp if isinstance(timestamp, datetime) else datetime.now(timezone.utc)
    with _telemetry_lock:
        if device_id or sim_id:
            curr_dev, curr_sim = _payer_device_history.get(payer_vpa, ("", ""))
            new_dev = device_id if device_id else curr_dev
            new_sim = sim_id if sim_id else curr_sim
            _payer_device_history[payer_vpa] = (new_dev, new_sim)

        if location:
            _payer_location_history[payer_vpa] = (location.strip(), now)


def clear_rule_telemetry() -> None:
    """Reset all in-memory telemetry tracking for testing."""
    with _telemetry_lock:
        _payer_device_history.clear()
        _payer_location_history.clear()


def resolve_coordinates(location_str: str) -> Optional[Tuple[float, float]]:
    """Parse 'lat,lon' coordinates or resolve known city names."""
    if not location_str or not isinstance(location_str, str):
        return None
    loc = location_str.strip()
    if "," in loc:
        parts = loc.split(",")
        if len(parts) >= 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return lat, lon
            except ValueError:
                pass

    loc_clean = loc.lower()
    for city, coords in CITY_COORDINATES.items():
        if city in loc_clean:
            return coords
    return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two points in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def rule_sim_device_mismatch(
    txn: UpiTransaction, state: Optional[UpiHotState] = None
) -> Optional[RuleHit]:
    """R_SIM_DEVICE_MISMATCH: Hardware device or SIM identity mismatch for a known payer."""
    if not txn.payer_vpa or not txn.device_id or not txn.sim_id:
        return None

    with _telemetry_lock:
        prev = _payer_device_history.get(txn.payer_vpa)

    if prev:
        last_dev, last_sim = prev
        if last_dev and last_sim:
            # Case 1: Same device, different SIM (SIM swap)
            if txn.device_id == last_dev and txn.sim_id != last_sim:
                return RuleHit(
                    code="R_SIM_DEVICE_MISMATCH",
                    points=30,
                    detail=f"SIM-device mismatch for '{txn.payer_vpa}': New SIM '{txn.sim_id[:8]}' inserted in known device '{txn.device_id[:8]}'",
                )
            # Case 2: Same SIM, different device (Device swap / account takeover)
            if txn.sim_id == last_sim and txn.device_id != last_dev:
                return RuleHit(
                    code="R_SIM_DEVICE_MISMATCH",
                    points=30,
                    detail=f"SIM-device mismatch for '{txn.payer_vpa}': Existing SIM '{txn.sim_id[:8]}' active on new device hardware '{txn.device_id[:8]}'",
                )
    return None


def rule_impossible_travel(
    txn: UpiTransaction, state: Optional[UpiHotState] = None
) -> Optional[RuleHit]:
    """R_IMPOSSIBLE_TRAVEL: Geographically impossible velocity between consecutive locations."""
    if not txn.payer_vpa or not txn.location:
        return None

    curr_coords = resolve_coordinates(txn.location)
    if curr_coords is None:
        return None

    with _telemetry_lock:
        prev = _payer_location_history.get(txn.payer_vpa)

    if prev:
        prev_loc, prev_time = prev
        prev_coords = resolve_coordinates(prev_loc)
        if prev_coords is None:
            return None

        now = txn.timestamp if isinstance(txn.timestamp, datetime) else datetime.now(timezone.utc)
        if prev_time.tzinfo is None:
            prev_time = prev_time.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        delta_sec = max(1.0, (now.timestamp() - prev_time.timestamp()))
        delta_hours = delta_sec / 3600.0
        delta_mins = delta_sec / 60.0

        dist_km = haversine_distance(prev_coords[0], prev_coords[1], curr_coords[0], curr_coords[1])
        speed_kmh = dist_km / delta_hours

        # Condition 1: >500 km in < 30 min (speed > 1000 km/h)
        # Condition 2: >100 km in < 3 min (speed > 2000 km/h)
        # Condition 3: speed > 1000 km/h and distance > 50 km
        if (dist_km > 500.0 and delta_mins < 30.0) or (dist_km > 100.0 and delta_mins < 3.0) or (speed_kmh > 1000.0 and dist_km > 50.0):
            return RuleHit(
                code="R_IMPOSSIBLE_TRAVEL",
                points=35,
                detail=f"Impossible travel velocity for '{txn.payer_vpa}': {dist_km:.0f}km in {delta_mins:.1f}min ({speed_kmh:.0f} km/h) between '{prev_loc}' and '{txn.location}'",
            )

    return None


def rule_datacenter_ip(txn: UpiTransaction) -> Optional[RuleHit]:
    """R_DATACENTER_IP: Transaction originates from a datacenter, cloud host, VPN, or Tor exit node."""
    if not txn.ip or not isinstance(txn.ip, str):
        return None

    ip_str = txn.ip.strip()
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return None

    for net in COMPILED_DC_NETWORKS:
        if ip_obj in net:
            return RuleHit(
                code="R_DATACENTER_IP",
                points=25,
                detail=f"Transaction originated from datacenter / cloud / VPN IP '{ip_str}' ({net})",
            )
    return None


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
        if txn.amount >= 1_000_000.0:
            pts = 50
        elif txn.amount >= 100_000.0:
            pts = 45
        elif txn.amount >= 50_000.0:
            pts = 25
        else:
            pts = 15
        return RuleHit(
            code="NEW_ACCOUNT_HIGH_VALUE",
            points=pts,
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


def evaluate_rules(
    txn: UpiTransaction,
    state: UpiHotState,
    campaign_store: Optional[Any] = None,
) -> List[RuleHit]:
    """Evaluate all deterministic rules against a single transaction in sequence."""
    hits: List[RuleHit] = []

    # 1. Honeypot check
    h_hit = rule_honeypot_hit(txn, state)
    if h_hit:
        hits.append(h_hit)

    # 2. Telemetry rules
    sim_hit = rule_sim_device_mismatch(txn, state)
    if sim_hit:
        hits.append(sim_hit)

    travel_hit = rule_impossible_travel(txn, state)
    if travel_hit:
        hits.append(travel_hit)

    dc_hit = rule_datacenter_ip(txn)
    if dc_hit:
        hits.append(dc_hit)

    # 3. Campaign fingerprint matching
    c_store = campaign_store if campaign_store is not None else get_campaign_store()
    camp_hit = rule_campaign_match(txn, c_store)
    if camp_hit:
        hits.append(camp_hit)

    # 4. Standard structural & flow rules
    flow_results = (
        rule_new_payee_vpa(txn),
        rule_pass_through_conduit(txn, state),
        rule_fan_in_burst(txn, state),
        rule_fan_out_dispersal(txn, state),
        rule_device_farm(txn, state),
        rule_new_account_high_value(txn),
        rule_limit_skirting(txn),
        rule_known_fraud_entity(txn, state),
    )
    for result in flow_results:
        if result is not None:
            hits.append(result)

    return hits

"""Dead Money Velocity (DMV) Engine for SAMPATI V2.

Quantifies the signature pattern of a mule account:
Extended dormancy (weeks/months) followed by a sudden spike of near-complete balance dissipation
in a narrow time window.
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional, Tuple

from app.models.upi_models import UpiTransaction

logger = logging.getLogger("sampati.engine.dmv")


class DmvTracker:
    """Thread-safe state tracker for Dead Money Velocity (DMV) across VPAs."""

    def __init__(self, window_hours: float = 720.0) -> None:
        self._lock = threading.Lock()
        self.window_seconds: float = window_hours * 3600.0
        # vpa -> deque of (timestamp, amount, is_outflow)
        self._flows: Dict[str, Deque[Tuple[datetime, float, bool]]] = defaultdict(deque)
        # vpa -> last seen timestamp
        self._last_outbound_time: Dict[str, datetime] = {}
        self._last_inbound_time: Dict[str, datetime] = {}
        # vpa -> latest computed DMV score
        self._dmv_scores: Dict[str, float] = {}

    def _ensure_utc(self, dt: Any) -> datetime:
        """Convert or ensure datetime is timezone-aware UTC."""
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return datetime.now(timezone.utc)

    def _evict(self, dq: Deque[Tuple[datetime, float, bool]], now: datetime) -> None:
        """Evict records older than window_seconds."""
        now_ts = now.timestamp()
        while dq and (now_ts - dq[0][0].timestamp()) > self.window_seconds:
            dq.popleft()

    def record_txn(self, txn: UpiTransaction) -> None:
        """Record an executed or evaluated transaction in DMV state."""
        now = self._ensure_utc(txn.timestamp)
        amt = float(txn.amount)

        with self._lock:
            if txn.payer_vpa:
                payer_dq = self._flows[txn.payer_vpa]
                self._evict(payer_dq, now)
                payer_dq.append((now, amt, True))
                self._last_outbound_time[txn.payer_vpa] = now

            if txn.payee_vpa:
                payee_dq = self._flows[txn.payee_vpa]
                self._evict(payee_dq, now)
                payee_dq.append((now, amt, False))
                self._last_inbound_time[txn.payee_vpa] = now

    def get_stats_window(self, vpa: str, now: datetime, window_sec: float) -> Tuple[int, float, float]:
        """Return (txn_count, outflow_sum, inflow_sum) in the given sliding window."""
        now_ts = now.timestamp()
        count = 0
        outflow = 0.0
        inflow = 0.0
        with self._lock:
            dq = self._flows.get(vpa, deque())
            for ts, amt, is_out in dq:
                if (now_ts - ts.timestamp()) <= window_sec:
                    count += 1
                    if is_out:
                        outflow += amt
                    else:
                        inflow += amt
        return count, outflow, inflow

    def get_previous_outbound_time(self, vpa: str) -> Optional[datetime]:
        """Return the previous outbound transaction timestamp for a VPA."""
        with self._lock:
            return self._last_outbound_time.get(vpa)

    def set_score(self, vpa: str, score: float) -> None:
        """Store the latest computed DMV score for a VPA."""
        with self._lock:
            self._dmv_scores[vpa] = round(float(score), 2)

    def get_score(self, vpa: str) -> float:
        """Retrieve the last known DMV score for a VPA."""
        with self._lock:
            return self._dmv_scores.get(vpa, 0.0)

    def get_top_vpas(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return top VPAs ranked descending by DMV score."""
        with self._lock:
            sorted_items = sorted(self._dmv_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
            now = datetime.now(timezone.utc)
            results = []
            for vpa, score in sorted_items:
                last_time = self._last_outbound_time.get(vpa) or self._last_inbound_time.get(vpa)
                last_iso = last_time.isoformat() if last_time else now.isoformat()
                
                tier = "GREEN" if score < 40.0 else ("AMBER" if score <= 70.0 else "RED")
                
                # compute 24h flows
                dq = self._flows.get(vpa, deque())
                out_24h = sum(amt for ts, amt, is_out in dq if is_out and (now.timestamp() - ts.timestamp()) <= 86400.0)
                in_24h = sum(amt for ts, amt, is_out in dq if not is_out and (now.timestamp() - ts.timestamp()) <= 86400.0)
                
                results.append({
                    "vpa": vpa,
                    "dmv_score": score,
                    "tier": tier,
                    "last_active": last_iso,
                    "outflow_24h": round(out_24h, 2),
                    "inflow_24h": round(in_24h, 2),
                })
            return results

    def clear(self) -> None:
        """Clear all tracking state."""
        with self._lock:
            self._flows.clear()
            self._last_outbound_time.clear()
            self._last_inbound_time.clear()
            self._dmv_scores.clear()


_dmv_tracker: Optional[DmvTracker] = None


def get_dmv_tracker() -> DmvTracker:
    """Obtain or initialize the global singleton DmvTracker."""
    global _dmv_tracker
    if _dmv_tracker is None:
        _dmv_tracker = DmvTracker()
    return _dmv_tracker


def calculate_dmv_score(txn: UpiTransaction, tracker: Optional[DmvTracker] = None) -> float:
    """Calculate Dead Money Velocity (DMV) score (0.0 to 100.0) for a transaction's payer.
    
    Quantifies dormancy index D and burst velocity index V.
    """
    trk = tracker if tracker is not None else get_dmv_tracker()
    now = txn.timestamp if isinstance(txn.timestamp, datetime) else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # 1. Dormancy Index D (0.0 - 1.0)
    prev_time = trk.get_previous_outbound_time(txn.payer_vpa)
    if prev_time is not None:
        if prev_time.tzinfo is None:
            prev_time = prev_time.replace(tzinfo=timezone.utc)
        elapsed_days = max(0.0, (now.timestamp() - prev_time.timestamp()) / 86400.0)
        dormancy_index = min(1.0, elapsed_days / 30.0)
    else:
        # First observed outbound transaction
        age_days = float(getattr(txn, "payer_account_age_days", 365))
        if age_days >= 30.0:
            effective_dormancy = min(90.0, age_days)
            dormancy_index = min(1.0, effective_dormancy / 30.0)
        else:
            dormancy_index = max(0.0, (age_days / 30.0) * 0.2)

    # 2. Burst Velocity Index V (0.0 - 1.0)
    # Stats in last 1 hour (3600s) and last 24 hours (86400s)
    count_1h, out_1h, in_1h = trk.get_stats_window(txn.payer_vpa, now, window_sec=3600.0)
    _, _, in_24h = trk.get_stats_window(txn.payer_vpa, now, window_sec=86400.0)

    current_outflow = out_1h + float(txn.amount)
    total_available_inflow = max(in_24h, float(txn.amount), 1.0)
    drain_ratio = min(1.0, current_outflow / total_available_inflow)

    rate_factor = min(1.0, (count_1h + 1) / 4.0)
    amt_factor = min(1.0, float(txn.amount) / 30000.0)

    burst_velocity_index = (0.50 * drain_ratio) + (0.30 * rate_factor) + (0.20 * amt_factor)
    burst_velocity_index = min(1.0, max(0.0, burst_velocity_index))

    # 3. Composite Score
    raw_dmv = 100.0 * (0.40 * dormancy_index + 0.60 * burst_velocity_index)

    # Synergistic escalation for high dormancy combined with high burst velocity
    if dormancy_index >= 0.5 and burst_velocity_index >= 0.4:
        multiplier = 1.0 + 0.5 * (dormancy_index * burst_velocity_index)
        final_score = raw_dmv * multiplier
    else:
        final_score = raw_dmv

    final_score = round(min(100.0, max(0.0, final_score)), 2)
    trk.set_score(txn.payer_vpa, final_score)
    return final_score

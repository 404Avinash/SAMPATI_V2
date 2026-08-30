"""VPA Synthetic Honeypot Network & Hit Tracking Engine for SAMPATI V2.

Maintains a registry of synthetic honeypot Virtual Payment Addresses (VPAs) designed
to attract and trap malicious fraud actors, automated botnet probes, and mule syndicates.
Tracks real-time hit counts, amounts deflected, and rolling 24-hour telemetry.
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("sampati.engine.honeypot")

# Seeded synthetic honeypot VPAs
DEFAULT_HONEYPOTS: List[str] = [
    "honeypot_trap_01@okaxis",
    "honeypot_mule_99@okhdfcbank",
    "phish_trap_node@okicici",
    "botnet_sink_04@oksbi",
    "mule_honeypot_prime@okaxis",
    "trap_collect_007@paytm",
    "phish_sink_alpha@ibl",
    "mule_decoy_99@ybl",
    "honeypot_mule_88@okhdfcbank",
    "decoy_phish_trap@oksbi",
    "honeypot.sink@upi",
    "trap_synthetic@upi",
    "darkweb_mule_sink@okaxis",
    "honeypot_phish_victim@ybl",
]

HONEYPOT_PREFIXES: tuple = (
    "honeypot_",
    "honeypot.",
    "phish_trap_",
    "botnet_sink_",
    "mule_honeypot_",
    "trap_sink_",
    "decoy_mule_",
    "trap_synthetic",
    "trap_collect",
    "decoy_phish",
)


class HoneypotRegistry:
    """Thread-safe registry for synthetic honeypot VPAs and real-time hit telemetry."""

    def __init__(self, seeds: Optional[List[str]] = None) -> None:
        self._lock = threading.Lock()
        self._seeds: List[str] = list(seeds or DEFAULT_HONEYPOTS)
        self._honeypots: Set[str] = set(h.strip().lower() for h in self._seeds)
        self._hit_counts: Dict[str, int] = defaultdict(int)
        self._amount_deflected: Dict[str, float] = defaultdict(float)
        self._last_hit_at: Dict[str, str] = {}
        self._hit_log: List[Dict[str, Any]] = []

    def is_honeypot(self, vpa: str) -> bool:
        """Check if a given VPA matches registered synthetic honeypot traps or prefixes."""
        if not vpa or not isinstance(vpa, str):
            return False
        clean = vpa.strip().lower()
        with self._lock:
            if clean in self._honeypots:
                return True
            return any(clean.startswith(prefix) for prefix in HONEYPOT_PREFIXES)

    def register_honeypot(self, vpa: str) -> None:
        """Register a new synthetic honeypot VPA into the active monitoring set."""
        if not vpa or not isinstance(vpa, str):
            return
        clean = vpa.strip().lower()
        with self._lock:
            self._honeypots.add(clean)

    def record_hit(
        self,
        vpa: str,
        txn_id: Optional[str] = None,
        amount: float = 0.0,
        payer_vpa: Optional[str] = None,
    ) -> None:
        """Record an attempted transaction against a synthetic honeypot VPA."""
        if not vpa or not isinstance(vpa, str):
            return
        clean = vpa.strip().lower()
        amt = max(0.0, float(amount or 0.0))
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        with self._lock:
            self._honeypots.add(clean)
            self._hit_counts[clean] += 1
            self._amount_deflected[clean] += amt
            self._last_hit_at[clean] = now_iso
            self._hit_log.append({
                "vpa": clean,
                "txn_id": str(txn_id) if txn_id else None,
                "payer_vpa": str(payer_vpa) if payer_vpa else None,
                "amount": amt,
                "timestamp": now_iso,
                "epoch": now.timestamp(),
            })
            # Bound log size to avoid unbounded memory growth
            if len(self._hit_log) > 10000:
                self._hit_log = self._hit_log[-10000:]

    def get_hits_24h(self, now: Optional[datetime] = None) -> int:
        """Calculate total honeypot hit count across the rolling 24-hour window."""
        ref_ts = (now or datetime.now(timezone.utc)).timestamp()
        cutoff = ref_ts - 86400.0
        with self._lock:
            return sum(1 for entry in self._hit_log if entry.get("epoch", 0.0) >= cutoff)

    def total_hits(self) -> int:
        """Return aggregate lifetime hit count across all registered honeypot VPAs."""
        with self._lock:
            return sum(self._hit_counts.values())

    def total_amount_deflected(self) -> float:
        """Return total cumulative INR volume deflected by honeypots."""
        with self._lock:
            return round(sum(self._amount_deflected.values()), 2)

    def list_honeypots(self) -> List[Dict[str, Any]]:
        """Return detailed status and metrics for all registered honeypot VPAs."""
        with self._lock:
            return [
                {
                    "vpa": h,
                    "hit_count": self._hit_counts.get(h, 0),
                    "amount_deflected": round(self._amount_deflected.get(h, 0.0), 2),
                    "last_hit_at": self._last_hit_at.get(h),
                    "status": "ACTIVE",
                }
                for h in sorted(self._honeypots)
            ]

    def get_stats(self) -> Dict[str, Any]:
        """Build full summary statistics payload for API responses and telemetry."""
        with self._lock:
            honeypots_list = [
                {
                    "vpa": h,
                    "hit_count": self._hit_counts.get(h, 0),
                    "amount_deflected": round(self._amount_deflected.get(h, 0.0), 2),
                    "last_hit_at": self._last_hit_at.get(h),
                    "status": "ACTIVE",
                }
                for h in sorted(self._honeypots)
            ]
            tot_hits = sum(self._hit_counts.values())
            tot_amt = round(sum(self._amount_deflected.values()), 2)
            cutoff = datetime.now(timezone.utc).timestamp() - 86400.0
            hits_24h = sum(1 for entry in self._hit_log if entry.get("epoch", 0.0) >= cutoff)

            return {
                "status": "ok",
                "total_registered": len(self._honeypots),
                "total_hits": tot_hits,
                "hits_24h": hits_24h,
                "total_amount_deflected": tot_amt,
                "honeypots": honeypots_list,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def clear(self) -> None:
        """Reset hit counts, amount deflected, and log while keeping default seeds."""
        with self._lock:
            self._honeypots = set(h.strip().lower() for h in self._seeds)
            self._hit_counts.clear()
            self._amount_deflected.clear()
            self._last_hit_at.clear()
            self._hit_log.clear()


_registry: Optional[HoneypotRegistry] = None


def get_honeypot_registry() -> HoneypotRegistry:
    """Obtain or initialize the global singleton HoneypotRegistry."""
    global _registry
    if _registry is None:
        _registry = HoneypotRegistry()
    return _registry


get_honeypot = get_honeypot_registry

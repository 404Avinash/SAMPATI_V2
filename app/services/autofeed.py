"""Live Synthetic Auto-Feed Engine for SAMPATI V2.

Runs an autonomous background generator loop producing real-time UPI traffic
streams (both legitimate payments and structured mule fraud patterns) routed
directly through the live inline evaluation pipeline and pushed to WebSocket hubs.
"""
from __future__ import annotations

import logging
import random
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.api.websocket import schedule_broadcast
from app.engine.honeypot import get_honeypot_registry
from app.models.upi_models import UpiTransaction
from app.synthetic.upi_generator import generate_legit_txn

logger = logging.getLogger("sampati.services.autofeed")

DATACENTER_IPS = [
    "3.220.100.45",
    "15.206.50.10",
    "34.93.100.22",
    "20.198.100.5",
    "138.68.44.12",
    "185.220.101.5",
]

FRAUD_NOTES = [
    "urgent kyc verification refund",
    "lottery prize winning fee",
    "crypto exchange p2p escrow cashout",
    "telegram task commission payout",
    "immediate account validation clearance",
]


class AutoFeedEngine:
    """Thread-safe background transaction generator and live evaluation driver."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: bool = False
        self._rate_tps: float = 10.0
        self._fraud_ratio: float = 0.2
        self._bursty: bool = False
        self._txns_generated: int = 0
        self._started_at: Optional[str] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def is_active(self) -> bool:
        """Check whether the background loop is actively running."""
        with self._lock:
            if not self._active:
                return False
            return bool(self._thread and self._thread.is_alive())

    def start(
        self,
        rate_tps: float = 10.0,
        fraud_ratio: float = 0.2,
        bursty: bool = False,
    ) -> Dict[str, Any]:
        """Start the background auto-feed loop. Idempotent if already running."""
        with self._lock:
            clamped_tps = min(50.0, max(0.1, float(rate_tps)))
            if self._active and self._thread and self._thread.is_alive():
                return {
                    "status": "already_running",
                    "active": True,
                    "rate_tps": self._rate_tps,
                }

            self._active = True
            self._rate_tps = clamped_tps
            self._fraud_ratio = min(1.0, max(0.0, float(fraud_ratio)))
            self._bursty = bool(bursty)
            self._started_at = datetime.now(timezone.utc).isoformat()
            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._run_loop,
                name="sampati-autofeed-worker",
                daemon=True,
            )
            self._thread.start()

            logger.info("AutoFeedEngine started at %.1f TPS (fraud ratio: %.2f, bursty: %s)", self._rate_tps, self._fraud_ratio, self._bursty)
            return {
                "status": "started",
                "active": True,
                "rate_tps": self._rate_tps,
            }

    def stop(self) -> Dict[str, Any]:
        """Stop the background auto-feed loop cleanly. Idempotent if already stopped."""
        with self._lock:
            if not self._active:
                return {
                    "status": "not_running",
                    "active": False,
                }

            self._active = False
            self._stop_event.set()
            thread = self._thread
            self._thread = None

        if thread and thread.is_alive():
            thread.join(timeout=1.0)

        logger.info("AutoFeedEngine stopped. Total transactions generated: %d", self._txns_generated)
        return {
            "status": "stopped",
            "active": False,
        }

    def get_status(self) -> Dict[str, Any]:
        """Return real-time telemetry and status of the auto-feed engine."""
        with self._lock:
            active = self._active and bool(self._thread and self._thread.is_alive())
            return {
                "active": active,
                "rate_tps": self._rate_tps,
                "tps": self._rate_tps,
                "fraud_ratio": self._fraud_ratio,
                "bursty": self._bursty,
                "txns_generated": self._txns_generated,
                "started_at": self._started_at,
            }

    def _generate_synthetic_txn(self) -> UpiTransaction:
        """Generate a realistic synthetic transaction based on configured fraud ratio."""
        is_fraud = random.random() < self._fraud_ratio

        if not is_fraud:
            try:
                labeled = generate_legit_txn(now=datetime.now(timezone.utc))
                return labeled.txn
            except Exception:
                pass

        # Fraudulent or suspicious transaction generation
        now = datetime.now(timezone.utc)
        hp_registry = get_honeypot_registry()
        honeypots = hp_registry.list_honeypots()

        fraud_pattern = random.choice(["honeypot", "structuring", "dormant_drain", "datacenter_probe"])

        if fraud_pattern == "honeypot" and honeypots:
            hp_vpa = random.choice(honeypots)["vpa"]
            return UpiTransaction(
                txn_id=f"TXN_FEED_HP_{uuid.uuid4().hex[:8]}",
                timestamp=now,
                amount=round(random.uniform(45000.0, 99000.0), 2),
                payer_vpa=f"mule_source_{uuid.uuid4().hex[:6]}@okaxis",
                payee_vpa=hp_vpa,
                payer_account_age_days=random.randint(1, 10),
                payee_vpa_age_days=random.randint(1, 10),
                note=random.choice(FRAUD_NOTES),
                ip=random.choice(DATACENTER_IPS),
            )
        elif fraud_pattern == "structuring":
            return UpiTransaction(
                txn_id=f"TXN_FEED_STR_{uuid.uuid4().hex[:8]}",
                timestamp=now,
                amount=random.choice([49990.0, 49999.0, 99990.0, 99995.0, 24990.0]),
                payer_vpa=f"smurf_node_{uuid.uuid4().hex[:6]}@okhdfcbank",
                payee_vpa=f"smurf_sink_{uuid.uuid4().hex[:6]}@ybl",
                payer_account_age_days=random.randint(2, 8),
                payee_vpa_age_days=random.randint(1, 5),
                note=random.choice(FRAUD_NOTES),
                ip=random.choice(DATACENTER_IPS),
            )
        elif fraud_pattern == "dormant_drain":
            return UpiTransaction(
                txn_id=f"TXN_FEED_DMV_{uuid.uuid4().hex[:8]}",
                timestamp=now,
                amount=round(random.uniform(75000.0, 98000.0), 2),
                payer_vpa=f"dormant_feed_{uuid.uuid4().hex[:6]}@okaxis",
                payee_vpa=f"exit_node_{uuid.uuid4().hex[:6]}@paytm",
                payer_account_age_days=random.randint(90, 300),
                payee_vpa_age_days=random.randint(1, 4),
                note="instant wallet sweep",
            )
        else:
            return UpiTransaction(
                txn_id=f"TXN_FEED_DC_{uuid.uuid4().hex[:8]}",
                timestamp=now,
                amount=round(random.uniform(15000.0, 48000.0), 2),
                payer_vpa=f"cloud_bot_{uuid.uuid4().hex[:6]}@okhdfcbank",
                payee_vpa=f"target_merchant_{uuid.uuid4().hex[:6]}@okaxis",
                ip=random.choice(DATACENTER_IPS),
                note=random.choice(FRAUD_NOTES),
            )

    def _run_loop(self) -> None:
        """Internal worker loop executing continuous synthetic stream evaluation."""
        from app.services.upi_cases import get_upi_case_service

        logger.debug("AutoFeedEngine background worker thread started.")
        while not self._stop_event.is_set():
            try:
                service = get_upi_case_service()
                txn = self._generate_synthetic_txn()
                resp = service.evaluate(txn)

                # Broadcast evaluation event
                eval_dict = resp.model_dump() if hasattr(resp, "model_dump") else resp.dict()
                schedule_broadcast({
                    "event": "UPI_EVALUATED",
                    "data": eval_dict,
                })

                # Broadcast case event if investigative case was opened
                if resp.case_id:
                    case_obj = service.get_case(resp.case_id)
                    if case_obj:
                        formatted = service.format_case_payload(case_obj)
                        schedule_broadcast({
                            "event": "new_case",
                            "data": formatted,
                            "stats": service.get_current_stats(),
                        })

                    schedule_broadcast({
                        "event": "UPI_CASE_OPENED",
                        "data": {
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
                    })

                with self._lock:
                    self._txns_generated += 1

                # Calculate sleep delay based on TPS and burstiness
                delay = 1.0 / max(0.1, self._rate_tps)
                if self._bursty and random.random() < 0.2:
                    delay = delay * 0.1

                self._stop_event.wait(delay)
            except Exception as exc:
                logger.debug("AutoFeedEngine iteration exception: %s", exc)
                self._stop_event.wait(0.05)

        logger.debug("AutoFeedEngine background worker thread terminated.")


# Global singleton instance
_autofeed_engine: Optional[AutoFeedEngine] = None
_autofeed_lock = threading.Lock()


def get_autofeed_engine() -> AutoFeedEngine:
    """Return the global singleton AutoFeedEngine instance."""
    global _autofeed_engine
    if _autofeed_engine is None:
        with _autofeed_lock:
            if _autofeed_engine is None:
                _autofeed_engine = AutoFeedEngine()
    return _autofeed_engine

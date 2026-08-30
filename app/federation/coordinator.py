"""Cross-PSP Federated Intelligence Coordinator for SAMPATI V2.

Coordinates privacy-preserving threat signal ingestion, hot-cache queries,
distributed feature share merging, multi-PSP mule ring detection, and
dynamic network risk scoring.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.federation.psp_node import PspNode, pseudonymize
from app.models.upi_models import SIMULATED_PSPS, UpiTransaction

logger = logging.getLogger("sampati.federation.coordinator")

SUSPICION_THRESHOLD: float = 0.5
GROW_THRESHOLD: float = 0.2
RING_MIN_MEMBERS: int = 3
RING_MIN_PSPS: int = 2


def _suspicion(feat: Dict[str, Any]) -> float:
    """Calculate suspicion score for an aggregated entity feature vector."""
    score = 0.0
    in_total = feat.get("in_total", 0.0) or 0.0
    out_total = feat.get("out_total", 0.0) or 0.0
    if in_total > 1000 and out_total > 0:
        ratio = out_total / in_total
        if 0.85 <= ratio <= 1.15:
            score += 0.45
    if feat.get("fresh"):
        score += 0.25
    if feat.get("in_distinct", 0) >= 4:
        score += 0.2
    if feat.get("out_distinct", 0) >= 4:
        score += 0.2
    if feat.get("device_shared"):
        score += 0.15
    return min(1.0, score)


class FederatedCoordinator:
    """Thread-safe multi-PSP federation coordinator with hot threat signal caching."""

    def __init__(self, federation_salt: str = "sampati-demo-salt") -> None:
        self.salt: str = federation_salt
        self.nodes: Dict[str, PspNode] = {
            psp: PspNode(psp, federation_salt) for psp in SIMULATED_PSPS
        }
        self._lock = threading.Lock()
        self._scores: Dict[str, float] = {}
        self._signals: Dict[str, Dict[str, Any]] = {}
        self._ring_members: Dict[str, Set[str]] = defaultdict(set)
        self._rings: Dict[str, Dict[str, Any]] = {}
        self._merged_features: Dict[str, Dict[str, Any]] = {}
        self._redis_client: Optional[Any] = None

    def _normalize_risk_level(self, risk_level: Any) -> float:
        """Map categorical risk level string or numeric score to [0.0, 1.0]."""
        if isinstance(risk_level, (int, float)):
            return max(0.0, min(1.0, float(risk_level)))
        if isinstance(risk_level, str):
            val = risk_level.strip().upper()
            mapping = {
                "CRITICAL": 1.0,
                "CRIT": 1.0,
                "HIGH": 0.85,
                "MEDIUM": 0.5,
                "MED": 0.5,
                "LOW": 0.2,
                "INFO": 0.05,
                "ALLOW": 0.0,
                "NONE": 0.0,
            }
            if val in mapping:
                return mapping[val]
            try:
                num = float(val)
                return max(0.0, min(1.0, num))
            except ValueError:
                return 0.5
        return 0.5

    def _score_to_risk_level(self, score: float) -> str:
        """Convert normalized numerical score to human-readable risk level label."""
        if score >= 0.90:
            return "CRITICAL"
        if score >= 0.70:
            return "HIGH"
        if score >= 0.35:
            return "MEDIUM"
        if score > 0.0:
            return "LOW"
        return "NONE"

    def record_signal(
        self,
        vpa_hash: str,
        risk_level: Union[str, float],
        ring_hash: Optional[str] = None,
        node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record privacy-preserving federated signal with sub-5ms lookup readiness."""
        clean_hash = str(vpa_hash).strip().lower()
        norm_score = self._normalize_risk_level(risk_level)
        reporting_node = str(node_id or "peer_node").strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            if clean_hash not in self._signals:
                self._signals[clean_hash] = {
                    "vpa_hash": clean_hash,
                    "risk_level": risk_level if isinstance(risk_level, str) else self._score_to_risk_level(norm_score),
                    "score": norm_score,
                    "ring_hash": ring_hash,
                    "reported_by_nodes": set(),
                    "recorded_at": now_iso,
                    "last_updated": now_iso,
                }
            sig = self._signals[clean_hash]
            sig["score"] = max(sig["score"], norm_score)
            if isinstance(risk_level, str):
                sig["risk_level"] = risk_level.upper()
            else:
                sig["risk_level"] = self._score_to_risk_level(sig["score"])
            sig["reported_by_nodes"].add(reporting_node)
            sig["last_updated"] = now_iso

            if ring_hash:
                sig["ring_hash"] = ring_hash
                self._ring_members[ring_hash].add(clean_hash)

            # Update direct lookup score cache
            self._scores[clean_hash] = max(self._scores.get(clean_hash, 0.0), norm_score)

        return {
            "status": "accepted",
            "vpa_hash": clean_hash,
            "risk_level": risk_level if isinstance(risk_level, str) else self._score_to_risk_level(norm_score),
            "federated_risk_score": norm_score,
            "ring_hash": ring_hash,
            "timestamp": now_iso,
            "recorded_at": now_iso,
        }

    def query_signal(self, vpa_hash: str) -> Dict[str, Any]:
        """Sub-5ms hot cache query for federated threat signals."""
        if not vpa_hash:
            return {
                "vpa_hash": "",
                "federated_risk_score": 0.0,
                "risk_level": "NONE",
                "ring_members": [],
                "reported_by_nodes": [],
                "cached": True,
                "last_updated": None,
            }

        clean_hash = str(vpa_hash).strip().lower()

        with self._lock:
            sig = self._signals.get(clean_hash)
            if sig:
                ring_h = sig.get("ring_hash")
                if ring_h and ring_h in self._ring_members:
                    members = sorted(list(self._ring_members[ring_h]))
                else:
                    members = [clean_hash]
                return {
                    "vpa_hash": clean_hash,
                    "federated_risk_score": round(float(sig["score"]), 4),
                    "risk_level": sig.get("risk_level", self._score_to_risk_level(sig["score"])),
                    "ring_members": members,
                    "reported_by_nodes": sorted(list(sig.get("reported_by_nodes", []))),
                    "cached": True,
                    "last_updated": sig.get("last_updated"),
                }

            # Secondary check on direct scores map
            if clean_hash in self._scores:
                score = self._scores[clean_hash]
                return {
                    "vpa_hash": clean_hash,
                    "federated_risk_score": round(float(score), 4),
                    "risk_level": self._score_to_risk_level(score),
                    "ring_members": [clean_hash],
                    "reported_by_nodes": ["federated_mesh"],
                    "cached": True,
                    "last_updated": None,
                }

        return {
            "vpa_hash": clean_hash,
            "federated_risk_score": 0.0,
            "risk_level": "NONE",
            "ring_members": [],
            "reported_by_nodes": [],
            "cached": True,
            "last_updated": None,
        }

    def list_signals(self) -> List[Dict[str, Any]]:
        """Return all active recorded signals for telemetry and debugging."""
        with self._lock:
            res = []
            for h, sig in self._signals.items():
                ring_h = sig.get("ring_hash")
                members = sorted(list(self._ring_members[ring_h])) if ring_h else [h]
                res.append({
                    "vpa_hash": h,
                    "federated_risk_score": sig["score"],
                    "risk_level": sig.get("risk_level", self._score_to_risk_level(sig["score"])),
                    "ring_members": members,
                    "reported_by_nodes": sorted(list(sig.get("reported_by_nodes", []))),
                    "ring_hash": ring_h,
                    "recorded_at": sig.get("recorded_at"),
                    "last_updated": sig.get("last_updated"),
                })
            return res

    def network_score(self, vpa: str) -> float:
        """Lookup federated score across raw VPA, SHA-256 hash, and salted pseudonym."""
        if not vpa:
            return 0.0

        clean_vpa = str(vpa).strip().lower()
        sha256_hash = hashlib.sha256(clean_vpa.encode("utf-8")).hexdigest()
        pseudo = pseudonymize(clean_vpa, self.salt)

        with self._lock:
            # Score lookups across all 3 key representations
            s_raw = self._scores.get(clean_vpa, 0.0)
            s_sha = self._scores.get(sha256_hash, 0.0)
            s_pseudo = self._scores.get(pseudo, 0.0)

            # Signal score lookups
            sig_raw = self._signals.get(clean_vpa, {}).get("score", 0.0)
            sig_sha = self._signals.get(sha256_hash, {}).get("score", 0.0)
            sig_pseudo = self._signals.get(pseudo, {}).get("score", 0.0)

            return max(s_raw, s_sha, s_pseudo, sig_raw, sig_sha, sig_pseudo, 0.0)

    def network_score_for_txn(self, txn: Any) -> float:
        """Calculate maximum federated risk score for payer and payee in a transaction."""
        payer_vpa = ""
        payee_vpa = ""
        if isinstance(txn, dict):
            payer_vpa = str(txn.get("payer_vpa") or "")
            payee_vpa = str(txn.get("payee_vpa") or "")
        elif hasattr(txn, "payer_vpa") and hasattr(txn, "payee_vpa"):
            payer_vpa = str(getattr(txn, "payer_vpa", "") or "")
            payee_vpa = str(getattr(txn, "payee_vpa", "") or "")

        return max(self.network_score(payer_vpa), self.network_score(payee_vpa))

    def route(self, txn: UpiTransaction) -> None:
        """Route transaction to participating PSP nodes that observe either party."""
        for node in self.nodes.values():
            if node.observes(txn):
                node.ingest(txn)

    def run_federation_round(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Collect shares, merge, detect rings, refresh network scores."""
        now = now or datetime.now(timezone.utc)
        shares = {psp: node.build_share(now) for psp, node in self.nodes.items()}

        merged: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "in_count": 0,
                "in_distinct": 0,
                "in_total": 0.0,
                "out_count": 0,
                "out_distinct": 0,
                "out_total": 0.0,
                "min_age_days": 999.0,
                "fresh": False,
                "device_shared": False,
                "psps": set(),
            }
        )
        reporter: Dict[str, str] = {}
        edges: Set[Tuple[str, str]] = set()

        for psp, share in shares.items():
            for pseudo, feat in share.get("features", {}).items():
                m = merged[pseudo]
                m["in_count"] += feat.get("in_count", 0)
                m["in_distinct"] += feat.get("in_distinct", 0)
                m["in_total"] += feat.get("in_total", 0.0)
                m["out_count"] += feat.get("out_count", 0)
                m["out_distinct"] += feat.get("out_distinct", 0)
                m["out_total"] += feat.get("out_total", 0.0)
                m["min_age_days"] = min(m["min_age_days"], feat.get("min_age_days", 999.0))
                m["fresh"] = m["fresh"] or feat.get("fresh", False)
                m["device_shared"] = m["device_shared"] or feat.get("device_shared", False)
                m["psps"].add(psp)
                reporter[pseudo] = share.get("psp", psp)

            for src, dst, _amt in share.get("edges", []):
                edges.add((src, dst))

        suspicion_by_node = {p: _suspicion(f) for p, f in merged.items()}
        seeds = {p for p, s in suspicion_by_node.items() if s >= SUSPICION_THRESHOLD}
        growable = {p for p, s in suspicion_by_node.items() if s >= GROW_THRESHOLD}

        adjacency: Dict[str, Set[str]] = defaultdict(set)
        for u, v in edges:
            if u in growable and v in growable:
                adjacency[u].add(v)
                adjacency[v].add(u)

        new_rings: List[Dict[str, Any]] = []
        visited: Set[str] = set()

        for start in sorted(seeds):
            if start in visited:
                continue
            component: Set[str] = set()
            stack = [start]
            while stack:
                curr = stack.pop()
                if curr in visited:
                    continue
                visited.add(curr)
                component.add(curr)
                for neighbor in adjacency[curr]:
                    if neighbor not in visited:
                        stack.append(neighbor)

            psps: Set[str] = set()
            for member in component:
                psps.update(merged[member]["psps"])

            if len(component) >= RING_MIN_MEMBERS and len(psps) >= RING_MIN_PSPS:
                sorted_members = sorted(component)
                ring_hash = hashlib.sha256(":".join(sorted_members).encode("utf-8")).hexdigest()[:16]
                new_rings.append({
                    "ring_hash": ring_hash,
                    "members": sorted_members,
                    "size": len(component),
                    "psps": sorted(psps),
                    "detected_at": now.isoformat(),
                })

        scores = {p: suspicion_by_node[p] * 0.6 for p in seeds}

        with self._lock:
            for ring in new_rings:
                self._rings[ring["ring_hash"]] = ring
                for member in ring["members"]:
                    self._ring_members[ring["ring_hash"]].add(member)

            for ring in self._rings.values():
                boost = min(1.0, 0.7 + 0.05 * ring["size"])
                for member in ring["members"]:
                    scores[member] = max(scores.get(member, 0.0), boost)

            self._scores.update(scores)
            self._merged_features = dict(merged)
            all_rings = list(self._rings.values())

        return {
            "shares": len(shares),
            "entities": len(merged),
            "suspicious": len(seeds),
            "rings": all_rings,
            "new_rings": new_rings,
        }

    def current_rings(self) -> List[Dict[str, Any]]:
        """Return all currently identified mule rings in the federation."""
        with self._lock:
            return list(self._rings.values())

    def clear(self) -> None:
        """Reset all internal caches and member node histories."""
        with self._lock:
            self._scores.clear()
            self._signals.clear()
            self._ring_members.clear()
            self._rings.clear()
            self._merged_features.clear()
        for node in self.nodes.values():
            node.clear()


_federation: Optional[FederatedCoordinator] = None


def get_federation() -> FederatedCoordinator:
    """Singleton factory accessor for the global FederatedCoordinator instance."""
    global _federation
    if _federation is None:
        _federation = FederatedCoordinator()
    return _federation

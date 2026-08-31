"""Fraud Campaign DNA Fingerprinting & Signature Store for SAMPATI V2.

Extracts behavioral DNA fingerprints from transactions resulting in BLOCK or CONFIRMED_FRAUD,
clusters them into active fraud syndicates, and matches incoming transactions against
known campaign signatures (R_CAMPAIGN_MATCH).
"""
from __future__ import annotations

import logging
import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.upi_models import RuleHit, UpiTransaction

logger = logging.getLogger("sampati.engine.campaign")

# Keyword clusters indicative of recurring fraud campaigns
FRAUD_KEYWORD_CLUSTERS: Dict[str, Set[str]] = {
    "CAMP-KYC-PHISH-01": {
        "kyc", "verify", "pan", "aadhar", "aadhaar", "update", "unblock",
        "bank", "otp", "debit", "card", "expire", "suspended", "service"
    },
    "CAMP-SMURF-BURST-02": {
        "transfer", "split", "cashout", "settle", "settlement", "instant",
        "p2p", "conduit", "fund", "float", "liquidity"
    },
    "CAMP-INVESTMENT-03": {
        "task", "invest", "bonus", "telegram", "crypto", "profit", "earn",
        "commission", "parttime", "job", "vip", "reward", "lottery", "prize", "refund"
    },
}


class CampaignSignature:
    """Represents a behavioral fingerprint profile for an active fraud campaign."""

    def __init__(
        self,
        campaign_id: str,
        name: str,
        scenario: str,
        keywords: Set[str],
        typical_amount_range: Tuple[float, float],
        typical_hour_buckets: List[int],
        seed_vpas: Optional[List[str]] = None,
    ) -> None:
        self.campaign_id: str = campaign_id
        self.name: str = name
        self.scenario: str = scenario
        self.keywords: Set[str] = set(k.lower() for k in keywords)
        self.min_amount: float = typical_amount_range[0]
        self.max_amount: float = typical_amount_range[1]
        self.typical_hours: Set[int] = set(typical_hour_buckets)
        self.member_vpas: Set[str] = set(v.lower().strip() for v in (seed_vpas or []))
        self.hit_count: int = 1
        self.last_seen_at: datetime = datetime.now(timezone.utc)

    def compute_similarity(self, txn: UpiTransaction) -> float:
        """Calculate weighted cosine-like similarity [0.0, 1.0] for an incoming transaction."""
        # 1. Payment Note / Keyword Similarity (weight: 0.35)
        note = (txn.note or "").lower()
        note_words = set(re.findall(r"\b[a-z0-9_]+\b", note))
        kw_match_count = len(note_words.intersection(self.keywords))
        kw_sim = min(1.0, kw_match_count / 1.0) if kw_match_count > 0 else 0.0

        # Also check payee VPA handle for keywords
        payee_clean = (txn.payee_vpa or "").lower()
        if any(kw in payee_clean for kw in self.keywords):
            kw_sim = max(kw_sim, 0.85)

        # 2. Amount Distribution Similarity (weight: 0.30)
        amt = float(txn.amount)
        if self.min_amount <= amt <= self.max_amount:
            # High match if within expected range
            amt_sim = 1.0
        elif amt < self.min_amount:
            amt_sim = max(0.0, 1.0 - (self.min_amount - amt) / max(1.0, self.min_amount))
        else:
            amt_sim = max(0.0, 1.0 - (amt - self.max_amount) / max(1.0, self.max_amount))

        # Check for structuring / rounding patterns (e.g., 9999, 4999, 49999)
        if any(abs(amt - thresh) <= 50.0 for thresh in (10000.0, 15000.0, 25000.0, 50000.0, 100000.0)):
            amt_sim = max(amt_sim, 0.90)

        # 3. Temporal Bucket Similarity (weight: 0.15)
        txn_time = txn.timestamp if isinstance(txn.timestamp, datetime) else datetime.now(timezone.utc)
        hour = txn_time.hour
        hour_sim = 1.0 if (not self.typical_hours or hour in self.typical_hours) else 0.40

        # 4. Entity VPA Membership / PSP overlap (weight: 0.20)
        vpa_sim = 0.0
        if txn.payer_vpa and txn.payer_vpa.lower().strip() in self.member_vpas:
            vpa_sim = 1.0
        elif txn.payee_vpa and txn.payee_vpa.lower().strip() in self.member_vpas:
            vpa_sim = 1.0

        # Composite weighted similarity
        # If keyword or VPA strongly matches, boost composite
        score = (0.35 * kw_sim) + (0.30 * amt_sim) + (0.15 * hour_sim) + (0.20 * vpa_sim)

        if kw_sim >= 0.85 and amt_sim >= 0.70:
            score = max(score, 0.85)

        if vpa_sim >= 0.9:
            score = max(score, 0.90)

        return min(1.0, max(0.0, score))


class CampaignSignatureStore:
    """Thread-safe catalog of known active fraud syndicate campaign signatures."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._signatures: Dict[str, CampaignSignature] = {}
        self._seed_default_campaigns()

    def _seed_default_campaigns(self) -> None:
        """Seed reference campaigns for KYC phishing, smurfing dispersal, and task scam."""
        self._signatures["CAMP-KYC-PHISH-01"] = CampaignSignature(
            campaign_id="CAMP-KYC-PHISH-01",
            name="KYC Phishing Syndicate",
            scenario="phishing_conduit",
            keywords=FRAUD_KEYWORD_CLUSTERS["CAMP-KYC-PHISH-01"],
            typical_amount_range=(5000.0, 95000.0),
            typical_hour_buckets=list(range(24)),
            seed_vpas=["phish_trap_node@okicici", "kyc_verify_alert@ybl", "unblock_sbi_help@oksbi"],
        )
        self._signatures["CAMP-SMURF-BURST-02"] = CampaignSignature(
            campaign_id="CAMP-SMURF-BURST-02",
            name="Micro-Smurfing Dispersal Ring",
            scenario="fan_out_smurfing",
            keywords=FRAUD_KEYWORD_CLUSTERS["CAMP-SMURF-BURST-02"],
            typical_amount_range=(2000.0, 24999.0),
            typical_hour_buckets=list(range(24)),
            seed_vpas=["mule_honeypot_prime@okaxis", "smurf_collector_01@okaxis"],
        )
        self._signatures["CAMP-INVESTMENT-03"] = CampaignSignature(
            campaign_id="CAMP-INVESTMENT-03",
            name="Task Scam / Investment Fraud Ring",
            scenario="investment_ponzi",
            keywords=FRAUD_KEYWORD_CLUSTERS["CAMP-INVESTMENT-03"],
            typical_amount_range=(1000.0, 50000.0),
            typical_hour_buckets=list(range(24)),
            seed_vpas=["bonus_task_pay@okaxis", "crypto_earn_vip@paytm"],
        )

    def match_campaign(
        self, txn: UpiTransaction, threshold: float = 0.82
    ) -> Optional[Tuple[str, float, str]]:
        """Evaluate transaction against stored signatures.
        
        Returns (campaign_id, similarity_score, campaign_name) if top similarity >= threshold.
        """
        with self._lock:
            best_camp: Optional[str] = None
            best_name: str = ""
            best_sim: float = 0.0

            for camp_id, sig in self._signatures.items():
                sim = sig.compute_similarity(txn)
                if sim > best_sim:
                    best_sim = sim
                    best_camp = camp_id
                    best_name = sig.name

            if best_camp and best_sim >= threshold:
                return best_camp, round(best_sim, 4), best_name
            return None

    def ingest_fingerprint(
        self,
        txn: UpiTransaction,
        label: str = "CONFIRMED_FRAUD",
    ) -> str:
        """Ingest a confirmed fraud or blocked transaction behavioral fingerprint."""
        with self._lock:
            # Check if it clusters into an existing campaign (similarity >= 0.70)
            best_camp: Optional[CampaignSignature] = None
            best_sim: float = 0.0

            for sig in self._signatures.values():
                sim = sig.compute_similarity(txn)
                if sim > best_sim:
                    best_sim = sim
                    best_camp = sig

            now = datetime.now(timezone.utc)
            if best_camp and best_sim >= 0.70:
                best_camp.hit_count += 1
                best_camp.last_seen_at = now
                if txn.payer_vpa:
                    best_camp.member_vpas.add(txn.payer_vpa.lower().strip())
                if txn.payee_vpa:
                    best_camp.member_vpas.add(txn.payee_vpa.lower().strip())
                return best_camp.campaign_id

            # Create dynamic new campaign signature
            raw_id = abs(hash(f"{txn.txn_id}-{txn.payer_vpa}-{txn.amount}")) % 10000
            new_id = f"CAMP-AUTO-{raw_id:04d}"
            
            note_words = set(re.findall(r"\b[a-z0-9_]+\b", (txn.note or "").lower()))
            amt = float(txn.amount)
            
            new_sig = CampaignSignature(
                campaign_id=new_id,
                name=f"Syndicate Cluster {new_id}",
                scenario="dynamic_cluster",
                keywords=note_words if note_words else {"transfer", "settle"},
                typical_amount_range=(max(500.0, amt * 0.5), amt * 1.5),
                typical_hour_buckets=[(txn.timestamp if isinstance(txn.timestamp, datetime) else now).hour],
                seed_vpas=[txn.payer_vpa, txn.payee_vpa],
            )
            new_sig.last_seen_at = now
            self._signatures[new_id] = new_sig
            return new_id

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """Return list of active campaigns and their metrics."""
        with self._lock:
            results = []
            for cid, sig in sorted(self._signatures.items()):
                results.append({
                    "campaign_id": cid,
                    "name": sig.name,
                    "scenario": sig.scenario,
                    "hit_count": sig.hit_count,
                    "member_count": len(sig.member_vpas),
                    "last_seen_at": sig.last_seen_at.isoformat(),
                })
            return results

    def clear(self) -> None:
        """Reset signatures back to default seeds."""
        with self._lock:
            self._signatures.clear()
            self._seed_default_campaigns()


_campaign_store: Optional[CampaignSignatureStore] = None


def get_campaign_store() -> CampaignSignatureStore:
    """Obtain or initialize the global singleton CampaignSignatureStore."""
    global _campaign_store
    if _campaign_store is None:
        _campaign_store = CampaignSignatureStore()
    return _campaign_store


def rule_campaign_match(
    txn: UpiTransaction,
    store: Optional[CampaignSignatureStore] = None,
) -> Optional[RuleHit]:
    """R_CAMPAIGN_MATCH: Behavioral DNA similarity matching active fraud campaigns."""
    st = store if store is not None else get_campaign_store()
    match = st.match_campaign(txn, threshold=0.82)
    if match is not None:
        camp_id, sim, name = match
        return RuleHit(
            code="R_CAMPAIGN_MATCH",
            points=30,
            detail=f"Behavioral DNA matches active syndicate campaign '{camp_id}' ({name}, similarity: {sim:.0%})",
        )
    return None


def check_campaign_match(
    txn: UpiTransaction,
    store: Optional[CampaignSignatureStore] = None,
) -> Tuple[Optional[RuleHit], Optional[str]]:
    """Return both RuleHit and campaign_id if similarity threshold >= 0.82."""
    st = store if store is not None else get_campaign_store()
    match = st.match_campaign(txn, threshold=0.82)
    if match is not None:
        camp_id, sim, name = match
        return (
            RuleHit(
                code="R_CAMPAIGN_MATCH",
                points=30,
                detail=f"Behavioral DNA matches active syndicate campaign '{camp_id}' ({name}, similarity: {sim:.0%})",
            ),
            camp_id,
        )
    return None, None

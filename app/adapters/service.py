"""Institutional Adapter Coordination Service for SAMPATI V2.

Aggregates simulated institutional intelligence sources (NPCI MuleHunter,
DPIP Smart Registry, and Mock PSPs) to enrich inline transaction evaluation
with federated institutional signals.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.adapters.dpip import DpipSmartRegistryAdapter, get_dpip_adapter
from app.adapters.npci import NpciMuleHunterAdapter, get_npci_adapter
from app.adapters.psp import MockPspAdapter, get_psp_adapter
from app.models.upi_models import UpiTransaction

logger = logging.getLogger("sampati.adapters.service")


class InstitutionalAdapterService:
    """Coordinating service evaluating transactions against simulated institutional adapters."""

    def __init__(
        self,
        npci_adapter: Optional[NpciMuleHunterAdapter] = None,
        dpip_adapter: Optional[DpipSmartRegistryAdapter] = None,
        psp_adapter: Optional[MockPspAdapter] = None,
    ) -> None:
        self.npci = npci_adapter or get_npci_adapter()
        self.dpip = dpip_adapter or get_dpip_adapter()
        self.psp = psp_adapter or get_psp_adapter()

    def evaluate_for_transaction(self, txn: UpiTransaction) -> Dict[str, Any]:
        """Evaluate incoming UPI transaction against NPCI, DPIP, and PSP institutional adapters."""
        payee_vpa = getattr(txn, "payee_vpa", "") or ""
        payer_vpa = getattr(txn, "payer_vpa", "") or ""

        # 1. Query NPCI MuleHunter for payee and payer
        npci_payee = self.npci.score_account(payee_vpa)
        npci_payer = self.npci.score_account(payer_vpa) if payer_vpa else None

        if npci_payer and npci_payer.mule_probability > npci_payee.mule_probability:
            active_npci = npci_payer
        else:
            active_npci = npci_payee

        mock_npci_score = active_npci.mule_probability

        # 2. Query DPIP Smart Registry for payee and payer
        dpip_payee = self.dpip.query_vpa(payee_vpa)
        dpip_payer = self.dpip.query_vpa(payer_vpa) if payer_vpa else None

        if dpip_payer and dpip_payer.threat_score > dpip_payee.threat_score:
            active_dpip = dpip_payer
        else:
            active_dpip = dpip_payee

        mock_dpip_threat_level = active_dpip.threat_score

        # 3. Build contributing signal sources list with explicit institution labels
        contributing_signals: List[Dict[str, Any]] = [
            {
                "institution": "NPCI",
                "adapter": "NPCI MuleHunter",
                "score": round(float(mock_npci_score), 4),
                "risk_rating": active_npci.risk_rating,
                "flags": active_npci.central_switch_flags,
                "switch_velocity_percentile": active_npci.switch_velocity_percentile,
                "summary": f"NPCI MuleHunter central switch risk rating: {active_npci.risk_rating} ({round(mock_npci_score * 100, 1)}% mule probability)",
            },
            {
                "institution": "DPIP",
                "adapter": "DPIP Smart Registry",
                "score": round(float(mock_dpip_threat_level), 4),
                "risk_rating": active_dpip.threat_level,
                "threat_level": active_dpip.threat_level,
                "listed": active_dpip.listed,
                "vpa_hash": active_dpip.vpa_hash,
                "reporting_agencies": active_dpip.reporting_agencies,
                "summary": f"DPIP Smart Registry status: {active_dpip.threat_level} (Score {mock_dpip_threat_level}) - {'LISTED' if active_dpip.listed else 'CLEAN'}",
            },
        ]

        # 4. Attach PSP contributing signal if risk is elevated or specific PSP matched
        if mock_npci_score >= 0.50 or mock_dpip_threat_level >= 0.50:
            psp_name = "PhonePe"
            payee_psp_str = getattr(txn, "payee_psp", "") or ""
            if "paytm" in payee_psp_str.lower() or "paytm" in payee_vpa.lower():
                psp_name = "Paytm"
            elif "sbi" in payee_psp_str.lower() or "google" in payee_psp_str.lower():
                psp_name = "GooglePay"
            elif "bhim" in payee_psp_str.lower() or "upi" in payee_psp_str.lower():
                psp_name = "BHIM"

            anomaly_type = "suspicious_beneficiary" if mock_npci_score >= 0.85 else "velocity_anomaly"
            contributing_signals.append({
                "institution": psp_name,
                "adapter": f"{psp_name} Risk Engine",
                "score": round(float(mock_npci_score), 4),
                "risk_rating": "HIGH" if mock_npci_score >= 0.85 else "MEDIUM",
                "anomaly_type": anomaly_type,
                "summary": f"{psp_name} Fraud Guard flagged {anomaly_type.replace('_', ' ')} on beneficiary account",
            })

        return {
            "mock_npci_score": round(float(mock_npci_score), 4),
            "mock_dpip_threat_level": round(float(mock_dpip_threat_level), 4),
            "contributing_signals": contributing_signals,
        }


_institutional_service: Optional[InstitutionalAdapterService] = None


def get_institutional_adapters() -> InstitutionalAdapterService:
    """Singleton getter for InstitutionalAdapterService."""
    global _institutional_service
    if _institutional_service is None:
        _institutional_service = InstitutionalAdapterService()
    return _institutional_service

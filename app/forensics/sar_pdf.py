"""SAR PDF Generator for SAMPATI V2 UPI Mule Detection.

Renders high-fidelity Suspicious Activity Report (SAR) documents into valid PDF
binary streams compliant with FIU-IND and RBI DPIP reporting standards.
"""
from __future__ import annotations

import io
import logging
import os
import textwrap
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Ensure writable matplotlib config directory in restricted sandbox environments
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

from app.forensics.upi_sar import build_upi_token_economy, generate_upi_sar

logger = logging.getLogger("sampati.forensics.sar_pdf")


def build_sar_pdf(case_data: Dict[str, Any]) -> bytes:
    """Generate a formal Suspicious Activity Report (SAR) PDF binary stream for a UPI case."""
    case_id = str(case_data.get("case_id", "UNKNOWN_CASE"))
    verdict = str(case_data.get("verdict", "HOLD")).upper()
    risk_score = int(case_data.get("risk_score", 0))
    status = str(case_data.get("status", "OPEN")).upper()
    created_at = str(case_data.get("created_at", datetime.now(timezone.utc).isoformat()))

    payer_vpa = str(case_data.get("payer_vpa") or "N/A")
    payee_vpa = str(case_data.get("payee_vpa") or "N/A")
    amount = float(case_data.get("amount") or 0.0)
    trigger_txn_id = str(case_data.get("trigger_txn_id") or "N/A")

    reasons: List[str] = case_data.get("reasons") or []
    rule_hits: List[Any] = case_data.get("rule_hits") or []
    ring_members: List[str] = case_data.get("ring_members_vpas") or []
    ring_hash = case_data.get("ring_hash") or "N/A"
    dmv_score = float(case_data.get("dmv_score") or 0.0)
    campaign_id = case_data.get("campaign_id") or "None"
    sar_markdown = case_data.get("sar_markdown")

    # If sar_markdown is not already generated on the case, build it dynamically
    if not sar_markdown:
        ring = {
            "ring_hash": ring_hash,
            "psps": list(set([v.split("@")[-1] for v in ring_members if "@" in v] or ["okaxis", "okhdfcbank"])),
            "size": len(ring_members) or 2,
            "layering_hops": 2,
            "mule_members": ring_members or [payer_vpa, payee_vpa],
        }
        trigger_dict = case_data.get("trigger_txn") or {
            "txn_id": trigger_txn_id,
            "payer_vpa": payer_vpa,
            "payee_vpa": payee_vpa,
            "amount": amount,
            "timestamp": created_at,
        }
        economy = case_data.get("token_economy") or build_upi_token_economy(ring, [trigger_dict])
        try:
            sar_markdown = generate_upi_sar(case_id, ring, [trigger_dict], trigger_dict, economy)
        except Exception as exc:
            logger.debug("Dynamic SAR markdown generation fallback: %s", exc)
            sar_markdown = (
                f"# Suspicious Activity Report (SAR) — {case_id}\n\n"
                f"**Generated:** {created_at}\n"
                f"**Fraud typology:** UPI_MULE_NETWORK_LAYERING\n\n"
                f"## 1. Executive Summary\n"
                f"Flagged transaction of Rs {amount:,.2f} from {payer_vpa} to {payee_vpa}.\n"
                f"Risk Score: {risk_score}/100. Verdict: {verdict}.\n"
            )

    buf = io.BytesIO()

    with PdfPages(buf) as pdf:
        # ── PAGE 1: Executive Dossier & Forensic Metadata ─────────────────────
        fig = plt.figure(figsize=(8.5, 11), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")

        # Header background banner
        header_color = "#991b1b" if verdict == "BLOCK" else ("#b45309" if verdict == "HOLD" else "#1e3a8a")
        rect_hdr = plt.Rectangle((0, 0.90), 1.0, 0.10, facecolor=header_color, edgecolor="none", transform=ax.transAxes)
        ax.add_patch(rect_hdr)

        ax.text(
            0.05, 0.955,
            "SUSPICIOUS ACTIVITY REPORT (SAR) — FIU-IND / RBI DPIP",
            color="white", fontsize=15, weight="bold", transform=ax.transAxes, va="center",
        )
        ax.text(
            0.05, 0.925,
            f"Case Identifier: {case_id}  |  Typology: UPI_MULE_NETWORK_LAYERING  |  Status: {status}",
            color="#fef08a", fontsize=10, weight="medium", transform=ax.transAxes, va="center",
        )

        # Overview Table / Metric Badges
        y = 0.86
        # Summary Box
        box_summary = plt.Rectangle((0.05, y - 0.13), 0.90, 0.13, facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=1, transform=ax.transAxes)
        ax.add_patch(box_summary)

        ax.text(0.07, y - 0.03, "CASE ASSESSMENT SUMMARY", color="#0f172a", fontsize=11, weight="bold", transform=ax.transAxes)
        ax.text(0.07, y - 0.065, f"Final Verdict: {verdict}    |    Risk Score: {risk_score} / 100    |    DMV Score: {dmv_score:.1f}", color="#1e293b", fontsize=10, weight="semibold", transform=ax.transAxes)
        ax.text(0.07, y - 0.095, f"Report Generated: {created_at}    |    Active Campaign: {campaign_id}", color="#475569", fontsize=9, transform=ax.transAxes)
        ax.text(0.07, y - 0.12, f"Mule Ring Identifier: {ring_hash}", color="#475569", fontsize=9, transform=ax.transAxes)

        # Trigger Transaction Box
        y = 0.70
        box_txn = plt.Rectangle((0.05, y - 0.13), 0.90, 0.13, facecolor="#f1f5f9", edgecolor="#cbd5e1", linewidth=1, transform=ax.transAxes)
        ax.add_patch(box_txn)

        ax.text(0.07, y - 0.03, "TRIGGER TRANSACTION DNA", color="#0f172a", fontsize=11, weight="bold", transform=ax.transAxes)
        ax.text(0.07, y - 0.065, f"Transaction ID: {trigger_txn_id}    |    Amount: Rs {amount:,.2f}", color="#0f172a", fontsize=10, weight="semibold", transform=ax.transAxes)
        ax.text(0.07, y - 0.095, f"Origin Payer VPA: {payer_vpa}", color="#1e293b", fontsize=9, transform=ax.transAxes)
        ax.text(0.07, y - 0.12, f"Destination Payee VPA: {payee_vpa}", color="#1e293b", fontsize=9, transform=ax.transAxes)

        # Detection Reasons & Rules Box
        y = 0.54
        box_rules = plt.Rectangle((0.05, y - 0.14), 0.90, 0.14, facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=1, transform=ax.transAxes)
        ax.add_patch(box_rules)

        ax.text(0.07, y - 0.03, "EXPLAINABLE DETECTION TRIGGERS & RULE BREAKDOWN", color="#0f172a", fontsize=11, weight="bold", transform=ax.transAxes)
        reasons_str = ", ".join(reasons) if reasons else "None"
        ax.text(0.07, y - 0.065, f"Triggered Reasons: {reasons_str}", color="#b91c1c", fontsize=9.5, weight="bold", transform=ax.transAxes)

        # Rule Hits List
        hits_lines = []
        for h in rule_hits[:3]:
            if isinstance(h, dict):
                code = h.get("code", "")
                pts = h.get("points", "")
                det = h.get("detail", "")
                hits_lines.append(f"• [{code}] (+{pts} pts): {det}")
            else:
                hits_lines.append(f"• {h}")
        if not hits_lines:
            hits_lines = ["• Standard threshold evaluation and federated signal fusion."]

        ry = y - 0.095
        for line in hits_lines[:2]:
            ax.text(0.07, ry, textwrap.shorten(line, width=105, placeholder="..."), color="#334155", fontsize=8.5, transform=ax.transAxes)
            ry -= 0.025

        # Ring Members & Topology Section
        y = 0.37
        box_ring = plt.Rectangle((0.05, y - 0.12), 0.90, 0.12, facecolor="#f1f5f9", edgecolor="#cbd5e1", linewidth=1, transform=ax.transAxes)
        ax.add_patch(box_ring)

        ax.text(0.07, y - 0.03, "MULE RING TOPOLOGY & PARTICIPATING ACCOUNTS", color="#0f172a", fontsize=11, weight="bold", transform=ax.transAxes)
        members_str = ", ".join(ring_members) if ring_members else f"{payer_vpa}, {payee_vpa}"
        ax.text(0.07, y - 0.065, f"Participating Ring Members ({len(ring_members) or 2} accounts):", color="#1e293b", fontsize=9.5, weight="semibold", transform=ax.transAxes)
        ax.text(0.07, y - 0.095, textwrap.shorten(members_str, width=110, placeholder="..."), color="#334155", fontsize=9, transform=ax.transAxes)

        # Narrative Preview Section
        y = 0.22
        box_narr = plt.Rectangle((0.05, 0.04), 0.90, y - 0.04, facecolor="#ffffff", edgecolor="#cbd5e1", linewidth=1, transform=ax.transAxes)
        ax.add_patch(box_narr)

        ax.text(0.07, y - 0.025, "SAR EXECUTIVE NARRATIVE", color="#0f172a", fontsize=11, weight="bold", transform=ax.transAxes)

        clean_narrative = sar_markdown.replace("#", "").replace("**", "").replace("`", "")
        narr_lines = [l.strip() for l in clean_narrative.split("\n") if l.strip()]
        ny = y - 0.055
        for line in narr_lines[:6]:
            wrapped = textwrap.wrap(line, width=105)
            for w in wrapped[:2]:
                if ny >= 0.055:
                    ax.text(0.07, ny, w, color="#334155", fontsize=8.5, transform=ax.transAxes)
                    ny -= 0.022
                else:
                    break

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # ── PAGE 2: Full Narrative, Forensics Graph & Action Plan ─────────────
        fig2 = plt.figure(figsize=(8.5, 11), dpi=150)
        ax2 = fig2.add_axes([0, 0, 1, 1])
        ax2.axis("off")

        # Header banner
        rect_hdr2 = plt.Rectangle((0, 0.92), 1.0, 0.08, facecolor="#1e293b", edgecolor="none", transform=ax2.transAxes)
        ax2.add_patch(rect_hdr2)
        ax2.text(0.05, 0.955, f"SAR DETAILED NARRATIVE & TOPOLOGY — {case_id}", color="white", fontsize=13, weight="bold", transform=ax2.transAxes, va="center")

        # Embedded Visual Graph if exists
        visual_path = case_data.get("visual_path")
        y_text_start = 0.88
        if visual_path and os.path.exists(visual_path):
            try:
                img = Image.open(visual_path)
                # Display image in upper section
                ax_img = fig2.add_axes([0.15, 0.58, 0.70, 0.30])
                ax_img.imshow(img)
                ax_img.axis("off")
                y_text_start = 0.54
            except Exception as exc:
                logger.debug("Failed to embed visual graph PNG: %s", exc)

        # Complete Narrative Paragraphs
        ny = y_text_start
        ax2.text(0.05, ny, "FULL INVESTIGATIVE NARRATIVE & TOKEN COMPRESSION:", color="#0f172a", fontsize=11, weight="bold", transform=ax2.transAxes)
        ny -= 0.03

        for line in narr_lines:
            if ny < 0.12:
                break
            wrapped = textwrap.wrap(line, width=105)
            for w in wrapped:
                if ny < 0.12:
                    break
                ax2.text(0.05, ny, w, color="#334155", fontsize=8.5, transform=ax2.transAxes)
                ny -= 0.020
            ny -= 0.008

        # Footer Action Plan
        box_action = plt.Rectangle((0.05, 0.03), 0.90, 0.07, facecolor="#fef2f2" if verdict == "BLOCK" else "#fffbeb", edgecolor="#fca5a5" if verdict == "BLOCK" else "#fde68a", linewidth=1, transform=ax2.transAxes)
        ax2.add_patch(box_action)
        action_title = "RECOMMENDED ENFORCEMENT ACTION: FIU-IND SEC 12 PRESCRIBED FILING" if verdict == "BLOCK" else "RECOMMENDED ACTION: ENHANCED DUE DILIGENCE & TEMPORARY HOLD"
        ax2.text(0.07, 0.075, action_title, color="#991b1b" if verdict == "BLOCK" else "#92400e", fontsize=9.5, weight="bold", transform=ax2.transAxes)
        ax2.text(0.07, 0.045, "Freeze beneficiary accounts, broadcast cross-PSP federated revocation signals, and submit STR to RBI DPIP portal.", color="#475569", fontsize=8.5, transform=ax2.transAxes)

        pdf.savefig(fig2, bbox_inches="tight")
        plt.close(fig2)

    return buf.getvalue()


# Alias for backward compatibility
generate_sar_pdf = build_sar_pdf

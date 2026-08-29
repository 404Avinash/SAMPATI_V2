import React from "react";
import Modal from "../common/Modal";
import { VerdictBadge, StatusBadge, RiskScoreBadge } from "../common/StatusBadge";
import ForensicImageViewer from "./ForensicImageViewer";
import SarNarrativeView from "./SarNarrativeView";
import PayeeBreakdownTable from "./PayeeBreakdownTable";
import StatusTransitionActions from "./StatusTransitionActions";
import { formatINR, formatDateTime } from "../../services/api";

export default function CaseDetailModal({ caseData, isOpen, onClose }) {
  if (!caseData) return null;

  const trigger = caseData.trigger_txn || {};
  const reasons = Array.isArray(caseData.reasons) ? caseData.reasons : [];
  const ruleHits = Array.isArray(caseData.rule_hits) ? caseData.rule_hits : [];

  const copyCaseId = () => {
    navigator.clipboard?.writeText(caseData.case_id);
    alert(`Copied Case ID: ${caseData.case_id}`);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="max-w-5xl"
      title={
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono">{caseData.case_id}</span>
          <button
            onClick={copyCaseId}
            className="text-xs text-muted hover:text-ink-900 px-1.5 py-0.5 rounded bg-white border border-hairline font-mono"
            title="Copy Case ID"
          >
            Copy
          </button>
        </div>
      }
      subtitle="Comprehensive Fraud Investigation Dossier"
    >
      <div className="space-y-6">
        {/* Top Summary Banner */}
        <div className="bg-surface-muted/60 p-4 rounded-xl border border-hairline flex flex-wrap items-center justify-between gap-4">
          {/* Status & Verdict Group */}
          <div className="flex flex-wrap items-center gap-3">
            <VerdictBadge verdict={caseData.verdict} />
            <StatusBadge status={caseData.status} />
            <RiskScoreBadge score={caseData.risk_score} />
          </div>

          {/* Timestamp & Amount */}
          <div className="flex items-center gap-6 font-mono text-xs text-muted">
            <div>
              <span className="text-[10px] uppercase block text-muted/80">Trigger Amount</span>
              <span className="text-sm font-bold text-ink-900">
                {formatINR(trigger.amount ?? caseData.amount)}
              </span>
            </div>
            <div>
              <span className="text-[10px] uppercase block text-muted/80">Detected At</span>
              <span className="text-ink-900 font-semibold">
                {formatDateTime(caseData.created_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Trigger Flow Card */}
        <div className="panel p-4 bg-white space-y-2">
          <div className="text-[10px] font-mono uppercase text-muted">Trigger Flow &amp; Entities</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-2.5 rounded bg-surface-muted border border-hairline">
              <span className="text-[10px] uppercase text-muted block">Payer VPA (Victim / Sender)</span>
              <span className="text-body font-bold break-all">
                {trigger.payer_vpa || caseData.payer_vpa || "—"}
              </span>
            </div>
            <div className="p-2.5 rounded bg-surface-muted border border-hairline">
              <span className="text-[10px] uppercase text-muted block">Payee VPA (Collector / Target)</span>
              <span className="text-body font-bold break-all">
                {trigger.payee_vpa || caseData.payee_vpa || "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Rule Hits / Primary Signals */}
        {(reasons.length > 0 || ruleHits.length > 0) && (
          <div className="panel p-4 bg-white space-y-2">
            <div className="text-[10px] font-mono uppercase text-muted">Primary Signals &amp; Rule Hits</div>
            <div className="flex flex-wrap gap-2">
              {(ruleHits.length > 0 ? ruleHits : reasons).map((r, i) => {
                const label = typeof r === "object" ? r.rule_name || r.rule_id || JSON.stringify(r) : r;
                return (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200 text-xs font-mono"
                  >
                    <span>⚡</span>
                    <span>{label}</span>
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* 4-Panel Visual Forensics PNG Viewer */}
        <ForensicImageViewer caseId={caseData.case_id} />

        {/* AI SAR Narrative */}
        <SarNarrativeView
          markdown={caseData.sar_markdown}
          tokenEconomy={caseData.token_economy}
        />

        {/* Payee Breakdown Table */}
        <PayeeBreakdownTable caseData={caseData} />

        {/* Status Transition Workflow Action Buttons */}
        <StatusTransitionActions caseData={caseData} />
      </div>
    </Modal>
  );
}

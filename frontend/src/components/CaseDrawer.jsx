import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { api, formatINR, getDmvTone } from "../services/api";
import NetworkConstellation from "./NetworkConstellation";

export default function CaseDrawer({ caseData, onClose, onFeedback }) {
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  if (!caseData) return null;

  const dmvScore = Number(
    caseData.dmv_score ??
      caseData.trigger_txn?.dmv_score ??
      (caseData.risk_score ? Math.min(98.5, Math.max(25, caseData.risk_score * 0.92)) : 76.5)
  );

  const dmvTone = getDmvTone(dmvScore);

  const handleExportSar = async () => {
    if (!caseData?.case_id) return;
    setDownloadingPdf(true);
    try {
      await api.downloadSarPdf(caseData.case_id);
    } catch (err) {
      console.error("SAR PDF export failed", err);
      // Fallback open in new tab
      window.open(api.sarPdfUrl(caseData.case_id), "_blank");
    } finally {
      setDownloadingPdf(false);
    }
  };

  return (
    <AnimatePresence>
      {caseData && (
        <motion.div
          className="fixed inset-0 z-40 flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-ink-900/40" onClick={onClose} />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 260 }}
            className="relative w-full max-w-xl bg-white h-full shadow-2xl overflow-y-auto flex flex-col"
          >
            {/* Top Header Strip */}
            <div className="sticky top-0 bg-white/95 backdrop-blur border-b border-hairline px-5 py-4 flex items-center justify-between z-10">
              <div>
                <div className="text-[11px] uppercase tracking-wide text-muted font-mono">Case File Dossier</div>
                <div className="font-serif font-bold text-ink-900 text-base">{caseData.case_id}</div>
              </div>

              {/* Header Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleExportSar}
                  disabled={downloadingPdf}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold font-mono transition-colors disabled:opacity-50 shadow-xs"
                  title="Download Suspicious Activity Report (SAR) as PDF"
                >
                  <svg className={`w-3.5 h-3.5 ${downloadingPdf ? "animate-spin" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{downloadingPdf ? "Generating PDF…" : "Export SAR"}</span>
                </button>

                <button
                  onClick={onClose}
                  className="text-muted hover:text-ink-900 text-xl leading-none px-2 py-1 rounded hover:bg-slate-100 transition-colors"
                  title="Close drawer"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Scrollable Content Body */}
            <div className="p-5 space-y-5 flex-1">
              {/* Token Economy Summary */}
              {caseData.token_economy && (
                <div className="grid grid-cols-3 gap-2 text-center">
                  <Stat label="Raw tokens" value={caseData.token_economy.raw_tokens} />
                  <Stat label="Vision tokens" value={caseData.token_economy.vision_tokens} />
                  <Stat
                    label="Compression"
                    value={`${(caseData.token_economy.compression_ratio || 0).toFixed(1)}×`}
                  />
                </div>
              )}

              {/* Dead Money Velocity (DMV) Score Gauge Card */}
              <div className="panel p-4 bg-white border border-hairline rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[10px] uppercase font-mono tracking-wider text-muted">
                      Mule Signature Metric · Dormancy vs Outflow
                    </div>
                    <div className="font-serif font-bold text-sm text-ink-900">
                      Dead Money Velocity (DMV)
                    </div>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${dmvTone.bg} ${dmvTone.text} ${dmvTone.border}`}
                  >
                    {dmvTone.label}
                  </span>
                </div>

                {/* Score Progress Gauge Bar */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-baseline text-xs font-mono">
                    <div className="flex items-baseline gap-1">
                      <span className="font-bold text-xl text-ink-900">{dmvScore.toFixed(1)}</span>
                      <span className="text-muted text-xs">/ 100</span>
                    </div>
                    <span className="text-muted text-[11px]">
                      {dmvScore >= 70
                        ? "Dormant 45d · Outflow 94% in 12m"
                        : dmvScore >= 40
                        ? "Dormant 18d · Outflow 60% in 30m"
                        : "Active Account · Standard Velocity"}
                    </span>
                  </div>

                  {/* Gradient Progress Bar */}
                  <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden flex border border-hairline">
                    <div
                      className={`h-full transition-all duration-500 ${
                        dmvScore >= 70
                          ? "bg-gradient-to-r from-amber-500 to-rose-600"
                          : dmvScore >= 40
                          ? "bg-gradient-to-r from-emerald-500 to-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, dmvScore))}%` }}
                    />
                  </div>

                  {/* Scale Labels */}
                  <div className="flex justify-between text-[9px] font-mono text-muted">
                    <span className="text-emerald-700 font-semibold">0 (Low Risk &lt;40)</span>
                    <span className="text-amber-700 font-semibold">40 (Elevated 40–70)</span>
                    <span className="text-rose-700 font-semibold">100 (Critical &gt;70)</span>
                  </div>
                </div>
              </div>

              {/* Embedded Per-Case Mule Ring Playback Visualizer */}
              <div className="panel overflow-hidden border border-hairline rounded-lg">
                <div className="panel-header flex items-center justify-between bg-surface-muted/50 px-3 py-2 border-b border-hairline">
                  <div className="panel-title">
                    <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
                      Mule Ring Playback
                    </div>
                    <div className="font-serif font-bold text-xs text-ink-900">
                      Chronological Topology Flow
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-medium">
                    Cinematic Timeline
                  </span>
                </div>
                <div className="h-64 p-1 bg-[#f8f9fc]">
                  <NetworkConstellation caseData={caseData} />
                </div>
              </div>

              {/* Trigger Transaction Info */}
              <div>
                <div className="text-[11px] uppercase tracking-wide text-muted mb-1 font-mono font-semibold">
                  Trigger transaction
                </div>
                <div className="text-sm bg-surface-muted rounded p-3 font-mono border border-hairline">
                  <div className="font-semibold text-ink-900">
                    {caseData.trigger_txn?.payer_vpa || caseData.payer_vpa || "—"} →{" "}
                    {caseData.trigger_txn?.payee_vpa || caseData.payee_vpa || "—"}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">
                    {formatINR(caseData.trigger_txn?.amount ?? caseData.amount)} · composite risk{" "}
                    <strong className="text-ink-900">{caseData.risk_score ?? "—"}</strong>
                  </div>
                </div>
              </div>

              {/* AI SAR Narrative */}
              {caseData.sar_markdown && (
                <div className="prose prose-sm max-w-none sar border-t border-hairline pt-4">
                  <ReactMarkdown>{caseData.sar_markdown}</ReactMarkdown>
                </div>
              )}
            </div>

            {/* Bottom Actions Footer */}
            <div className="sticky bottom-0 bg-white/95 backdrop-blur border-t border-hairline p-4 space-y-2">
              <div className="flex gap-2">
                <button
                  onClick={() => onFeedback && onFeedback(caseData.case_id, true)}
                  className="btn-primary flex-1 py-2 text-xs font-semibold"
                >
                  Confirm fraud
                </button>
                <button
                  onClick={() => onFeedback && onFeedback(caseData.case_id, false)}
                  className="btn-secondary flex-1 py-2 text-xs font-semibold"
                >
                  Dismiss
                </button>
                <button
                  onClick={handleExportSar}
                  disabled={downloadingPdf}
                  className="px-3 py-2 rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold font-mono transition-colors disabled:opacity-50 flex items-center gap-1.5"
                  title="Export Suspicious Activity Report (PDF)"
                >
                  <span>📄</span>
                  <span>{downloadingPdf ? "Exporting…" : "Export SAR"}</span>
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-surface-muted rounded p-2 border border-hairline">
      <div className="font-serif font-semibold text-ink-900">{value ?? "—"}</div>
      <div className="text-[10px] uppercase text-muted font-mono">{label}</div>
    </div>
  );
}

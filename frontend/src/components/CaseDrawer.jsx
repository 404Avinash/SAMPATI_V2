import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { api, formatINR, formatDateTime, getDmvTone } from "../services/api";
import { VerdictBadge, StatusBadge, RiskScoreBadge } from "./common/StatusBadge";
import ForensicImageViewer from "./investigations/ForensicImageViewer";
import PayeeBreakdownTable from "./investigations/PayeeBreakdownTable";
import StatusTransitionActions from "./investigations/StatusTransitionActions";
import NetworkConstellation from "./NetworkConstellation";
import CaseAiCopilotView from "./investigations/CaseAiCopilotView";

export function DmvArcGauge({ score }) {
  const numScore = typeof score === "number" ? score : parseFloat(score) || 0;
  const clamped = Math.max(0, Math.min(100, numScore));
  // Needle angle: map [0, 100] -> [-90, +90] degrees (left to right semicircle)
  const needleAngle = -90 + (clamped / 100) * 180;

  return (
    <div className="flex flex-col items-center justify-center p-3 bg-slate-50/70 rounded-xl border border-hairline relative">
      <svg viewBox="0 0 220 125" className="w-56 overflow-visible">
        <defs>
          <linearGradient id="dmv-green" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
          <linearGradient id="dmv-amber" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#fbbf24" />
          </linearGradient>
          <linearGradient id="dmv-red" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f43f5e" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>

        {/* Outer Background Track */}
        <path
          d="M 25 110 A 85 85 0 0 1 195 110"
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="14"
          strokeLinecap="round"
        />

        {/* Green Arc (0 - 40%) -> 180deg to 108deg */}
        <path
          d="M 25 110 A 85 85 0 0 1 60 41.2"
          fill="none"
          stroke="url(#dmv-green)"
          strokeWidth="14"
          strokeLinecap="round"
        />

        {/* Amber Arc (40 - 70%) -> 108deg to 54deg */}
        <path
          d="M 64 37 A 85 85 0 0 1 156 37"
          fill="none"
          stroke="url(#dmv-amber)"
          strokeWidth="14"
        />

        {/* Red Arc (70 - 100%) -> 54deg to 0deg */}
        <path
          d="M 160 41.2 A 85 85 0 0 1 195 110"
          fill="none"
          stroke="url(#dmv-red)"
          strokeWidth="14"
          strokeLinecap="round"
        />

        {/* Scale Tick Labels */}
        <text x="22" y="122" fontSize="9" fill="#059669" fontFamily="monospace" fontWeight="bold">0</text>
        <text x="50" y="24" fontSize="9" fill="#d97706" fontFamily="monospace" fontWeight="bold">40</text>
        <text x="160" y="24" fontSize="9" fill="#dc2626" fontFamily="monospace" fontWeight="bold">70</text>
        <text x="194" y="122" fontSize="9" fill="#991b1b" fontFamily="monospace" fontWeight="bold">100</text>

        {/* Animated Needle */}
        <g
          style={{
            transform: `rotate(${needleAngle}deg)`,
            transformOrigin: "110px 110px",
            transition: "transform 1s cubic-bezier(0.34, 1.56, 0.64, 1)",
          }}
        >
          {/* Needle shape */}
          <polygon
            points="107,110 113,110 111,35 109,35"
            fill="#0f172a"
          />
          <circle cx="110" cy="35" r="2.5" fill="#ef4444" />
        </g>

        {/* Pivot Center Hub */}
        <circle cx="110" cy="110" r="7" fill="#0f172a" stroke="#ffffff" strokeWidth="2" />
      </svg>

      {/* Numerical Value Readout */}
      <div className="text-center -mt-2">
        <div className="flex items-baseline justify-center gap-1">
          <span className="font-mono text-2xl font-bold text-ink-900">{clamped.toFixed(1)}</span>
          <span className="text-xs text-muted font-mono font-semibold">/ 100</span>
        </div>
      </div>
    </div>
  );
}

export function RuleBreakdownChart({ ruleHits = [], reasons = [], riskScore = 0 }) {
  let data = [];
  if (Array.isArray(ruleHits) && ruleHits.length > 0) {
    data = ruleHits.map((h) => ({
      name: h.detail || h.rule_name || h.code || "Rule Signal",
      points: Number(h.points) || 20,
      code: h.code || h.rule_id || "",
    }));
  } else if (Array.isArray(reasons) && reasons.length > 0) {
    const defaultPts = Math.max(15, Math.round((riskScore || 65) / Math.max(1, reasons.length)));
    data = reasons.map((r, idx) => ({
      name: typeof r === "string" ? r : r.detail || r.rule_name || `Signal ${idx + 1}`,
      points: typeof r === "object" && r.points ? Number(r.points) : defaultPts,
      code: typeof r === "object" ? r.code || "" : "",
    }));
  } else {
    data = [
      { name: "Dead Money Outflow Velocity", points: 40, code: "DMV_VELOCITY" },
      { name: "Rapid Fan-In Aggregation", points: 30, code: "FAN_IN_BURST" },
      { name: "New Account High Value Transfer", points: 20, code: "NEW_ACC_HV" },
    ];
  }

  // Sort descending by points
  data.sort((a, b) => b.points - a.points);

  const chartHeight = Math.max(140, Math.min(280, data.length * 34 + 20));

  return (
    <div className="panel p-4 bg-white border border-hairline rounded-xl space-y-2">
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-mono uppercase text-muted tracking-wider">
          Explainable Rule Breakdown (Sorted by Points)
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-muted text-muted border border-hairline">
          {data.length} Signals
        </span>
      </div>

      <div style={{ width: "100%", height: chartHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 4, right: 24, left: 10, bottom: 4 }}
          >
            <XAxis
              type="number"
              domain={[0, "dataMax + 10"]}
              tick={{ fontSize: 10, fontFamily: "monospace", fill: "#64748b" }}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={140}
              tick={{ fontSize: 10, fill: "#334155" }}
              tickFormatter={(val) => (val.length > 20 ? `${val.slice(0, 18)}…` : val)}
            />
            <Tooltip
              formatter={(val) => [`${val} Risk Points`, "Contribution"]}
              contentStyle={{
                fontSize: "11px",
                fontFamily: "monospace",
                borderRadius: "6px",
                borderColor: "#e2e8f0",
                backgroundColor: "#ffffff",
              }}
            />
            <Bar
              dataKey="points"
              radius={[0, 4, 4, 0]}
              isAnimationActive={true}
              animationDuration={800}
            >
              {data.map((entry, idx) => (
                <Cell
                  key={`cell-${idx}`}
                  fill={
                    entry.points >= 35
                      ? "#ef4444"
                      : entry.points >= 20
                      ? "#f59e0b"
                      : "#10b981"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const copyToClipboard = async (text) => {
  if (!text) return false;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (err) {
    console.warn("Clipboard API writeText failed, falling back to execCommand", err);
  }
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    textArea.style.top = "-9999px";
    textArea.setAttribute("readonly", "");
    document.body.appendChild(textArea);
    textArea.select();
    const successful = document.execCommand("copy");
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    console.error("Fallback clipboard copy failed", err);
    return false;
  }
};

export default function CaseDrawer({ caseData, onClose, onFeedback }) {
  const [activeTab, setActiveTab] = useState("forensics");
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [sarError, setSarError] = useState(null);
  const [copied, setCopied] = useState(false);

  if (!caseData) return null;

  const trigger = caseData.trigger_txn || {};
  const dmvScore = Number(
    caseData.dmv_score ??
      caseData.trigger_txn?.dmv_score ??
      (caseData.risk_score ? Math.min(98.5, Math.max(25, caseData.risk_score * 0.92)) : 76.5)
  );

  const dmvTone = getDmvTone(dmvScore);

  const handleCopyCaseId = async () => {
    if (caseData.case_id) {
      const ok = await copyToClipboard(caseData.case_id);
      if (ok) {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    }
  };

  const handleExportSar = async () => {
    if (!caseData?.case_id) return;
    setDownloadingPdf(true);
    setSarError(null);
    try {
      await api.downloadSarPdf(caseData.case_id);
    } catch (err) {
      console.error("SAR PDF export failed", err);
      setSarError(err.message || "Failed to generate SAR PDF. Server returned an invalid response.");
      setTimeout(() => setSarError(null), 6000);
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
          <div className="absolute inset-0 bg-ink-900/40 backdrop-blur-xs" onClick={onClose} />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 260 }}
            className="relative w-full max-w-2xl bg-white h-full shadow-2xl overflow-y-auto flex flex-col"
          >
            {/* Top Header Strip */}
            <div className="sticky top-0 bg-white/95 backdrop-blur border-b border-hairline px-5 py-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-muted font-mono">Case File Dossier</div>
                  <div className="font-serif font-bold text-ink-900 text-base flex items-center gap-2">
                    <span>{caseData.case_id}</span>
                    <button
                      onClick={handleCopyCaseId}
                      className="text-[10px] text-muted hover:text-ink-900 px-1.5 py-0.5 rounded bg-surface-muted border border-hairline font-mono transition-colors"
                      title="Copy Case ID"
                    >
                      {copied ? "Copied ✓" : "Copy"}
                    </button>
                  </div>
                </div>
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
                  ✕
                </button>
              </div>
            </div>

            {/* Navigation Tabs Bar */}
            <div className="bg-surface-muted/90 border-b border-hairline px-5 py-2 flex items-center gap-2 z-10 sticky top-[65px] backdrop-blur-xs">
              <button
                onClick={() => setActiveTab("forensics")}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
                  activeTab === "forensics"
                    ? "bg-white text-ink-900 shadow-xs border border-hairline"
                    : "text-muted hover:text-ink-900 hover:bg-white/60"
                }`}
              >
                <span>📋</span>
                <span>Forensic Dossier</span>
              </button>

              <button
                onClick={() => setActiveTab("copilot")}
                title="Interactive Gemini Assistant & Platform Agent"
                className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
                  activeTab === "copilot"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-indigo-900 bg-indigo-50/80 hover:bg-indigo-100 border border-indigo-200/80"
                }`}
              >
                <span>✨</span>
                <span>Gemini Assistant</span>
                <span
                  className={`text-[9px] px-1.5 py-0.2 rounded-full uppercase font-bold tracking-wider ${
                    activeTab === "copilot" ? "bg-white/20 text-white" : "bg-indigo-200 text-indigo-900"
                  }`}
                >
                  Autonomous
                </span>
              </button>
            </div>

            {/* Inline SAR Export Error Toast Message */}
            {sarError && (
              <div className="mx-5 mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start justify-between gap-2 text-xs font-mono text-rose-800 shadow-sm animate-fadeIn">
                <div className="flex items-start gap-2">
                  <span className="text-base leading-none">⚠️</span>
                  <div>
                    <strong className="block font-bold">SAR PDF Generation Failed</strong>
                    <span className="text-[11px] text-rose-700">{sarError}</span>
                  </div>
                </div>
                <button
                  onClick={() => setSarError(null)}
                  className="text-rose-500 hover:text-rose-800 font-bold text-sm leading-none p-1"
                  title="Dismiss notification"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Scrollable Content Body */}
            <div className="p-5 space-y-5 flex-1">
              {activeTab === "copilot" ? (
                <CaseAiCopilotView
                  caseData={caseData}
                  onExportSar={handleExportSar}
                  downloadingPdf={downloadingPdf}
                />
              ) : (
                <>
                  {/* Top Status & Amount Summary Banner */}
                  <div className="bg-surface-muted/60 p-4 rounded-xl border border-hairline flex flex-wrap items-center justify-between gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <VerdictBadge verdict={caseData.verdict} />
                      <StatusBadge status={caseData.status} />
                      <RiskScoreBadge score={caseData.risk_score} />
                    </div>
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

              {/* Dead Money Velocity (DMV) Score Arc Dial Gauge Card */}
              <div className="panel p-4 bg-white border border-hairline rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[10px] uppercase font-mono tracking-wider text-muted">
                      Mule Signature Metric · Dormancy vs Outflow
                    </div>
                    <div className="font-serif font-bold text-sm text-ink-900">
                      Dead Money Velocity (DMV) Dial Gauge
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${dmvTone.bg} ${dmvTone.text} ${dmvTone.border}`}
                  >
                    {dmvTone.label}
                  </span>
                </div>

                {/* Animated Semicircular Arc Gauge */}
                <DmvArcGauge score={dmvScore} />

                {/* Interpretation notes */}
                <div className="text-center text-xs font-mono text-slate-600">
                  <span className="font-semibold text-ink-900">{dmvTone.category}</span> —{" "}
                  <span className="text-muted">
                    {dmvScore >= 70
                      ? "High mule drain risk: rapid account depletion post dormancy."
                      : dmvScore >= 40
                      ? "Elevated velocity signature: moderate velocity surge detected."
                      : "Standard legitimate transaction flow velocity."}
                  </span>
                </div>
              </div>

              {/* Explainable Rule Breakdown Recharts Horizontal Bar Chart */}
              <RuleBreakdownChart
                ruleHits={caseData.rule_hits}
                reasons={caseData.reasons}
                riskScore={caseData.risk_score}
              />

              {/* Trigger Transaction Info Card */}
              <div className="panel p-4 bg-white border border-hairline rounded-xl space-y-2">
                <div className="text-[10px] uppercase tracking-wide text-muted font-mono font-semibold">
                  Trigger Transaction Flow
                </div>
                <div className="text-xs bg-surface-muted rounded-lg p-3 font-mono border border-hairline space-y-1.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="font-semibold text-ink-900">
                      <span className="text-body font-medium">{trigger.payer_vpa || caseData.payer_vpa || "—"}</span>
                      <span className="text-muted mx-2">→</span>
                      <span className="text-ink-900 font-bold">{trigger.payee_vpa || caseData.payee_vpa || "—"}</span>
                    </div>
                    <span className="font-bold text-sm text-ink-900">
                      {formatINR(trigger.amount ?? caseData.amount)}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-600 flex items-center gap-3">
                    <span>Composite Risk: <strong className="text-ink-900">{caseData.risk_score ?? "—"}</strong></span>
                    <span>·</span>
                    <span>Verdict: <strong className="text-ink-900">{caseData.verdict || "HOLD"}</strong></span>
                  </div>
                </div>
              </div>

              {/* 4-Panel Visual Forensics Viewer with Multi-Tier Fallback */}
              <ForensicImageViewer caseId={caseData.case_id} caseData={caseData} />

              {/* Embedded Per-Case Mule Ring Playback Visualizer */}
              <div className="panel overflow-hidden border border-hairline rounded-xl">
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

              {/* Payee & Account Breakdown Table */}
              <PayeeBreakdownTable caseData={caseData} />

              {/* AI SAR Narrative */}
              {caseData.sar_markdown && (
                <div className="panel p-4 bg-white border border-hairline rounded-xl space-y-2">
                  <div className="text-[10px] uppercase tracking-wide text-muted font-mono font-semibold">
                    AI Suspicious Activity Report (SAR) Narrative
                  </div>
                  <div className="prose prose-sm max-w-none sar pt-1 font-sans text-xs">
                    <ReactMarkdown>{caseData.sar_markdown}</ReactMarkdown>
                  </div>
                </div>
              )}

              {/* Status Transition Actions */}
              <StatusTransitionActions caseData={caseData} />
            </>
          )}
        </div>

            {/* Bottom Actions Footer */}
            <div className="sticky bottom-0 bg-white/95 backdrop-blur border-t border-hairline p-4 space-y-2">
              <div className="flex gap-2">
                <button
                  onClick={() => onFeedback && onFeedback(caseData.case_id, true)}
                  className="btn-primary flex-1 py-2 text-xs font-semibold"
                >
                  Confirm Fraud
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
    <div className="bg-surface-muted rounded-lg p-2.5 border border-hairline">
      <div className="font-serif font-bold text-ink-900 text-sm">{value ?? "—"}</div>
      <div className="text-[10px] uppercase text-muted font-mono tracking-wider">{label}</div>
    </div>
  );
}

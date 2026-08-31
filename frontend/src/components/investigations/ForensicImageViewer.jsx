import React, { useState, useEffect } from "react";
import { api, formatINR, shortVpa } from "../../services/api";

export function SvgRingTopology({ caseId, caseData, isExpanded = false }) {
  const topo = (typeof caseData?.topology === "object" && caseData?.topology) || {};
  const trigger = (typeof topo.trigger_txn === "object" && topo.trigger_txn) || caseData?.trigger_txn || {};
  const collector = trigger.payee_vpa || caseData?.payee_vpa || "mule.collector@upi";
  const victim = trigger.payer_vpa || caseData?.payer_vpa || "victim.payer@upi";
  const members = Array.isArray(caseData?.ring_members_vpas) ? caseData.ring_members_vpas : [];

  // Extract or synthesize nodes
  const fanIn = Array.isArray(topo.fan_in) && topo.fan_in.length > 0
    ? topo.fan_in
    : members.length > 2
    ? members.slice(0, 2)
    : [victim];

  const hops = Array.isArray(topo.hops) && topo.hops.length > 0
    ? topo.hops
    : members.length > 3
    ? members.slice(2, 4)
    : ["layer.hop01@axis", "layer.hop02@icici"];

  const fanOut = Array.isArray(topo.fan_out) && topo.fan_out.length > 0
    ? topo.fan_out
    : members.length > 4
    ? members.slice(4)
    : ["cashout.atm@sbi"];

  const ringHash = caseData?.ring_hash || caseData?.campaign_id || (caseId ? `RING-${caseId.slice(0, 8)}` : "RING-SYN-7492");
  const amount = trigger.amount ?? caseData?.amount ?? 85000;

  const width = isExpanded ? 760 : 480;
  const height = isExpanded ? 340 : 220;
  const hubX = width / 2;
  const hubY = height / 2;

  // Compute positions
  const victimNodes = fanIn.map((item, idx) => {
    const vpa = typeof item === "string" ? item : item?.payer_vpa || item?.vpa || `victim-${idx + 1}@upi`;
    const ySpacing = height / (fanIn.length + 1);
    return {
      id: `victim-${idx}`,
      vpa,
      x: isExpanded ? 100 : 70,
      y: ySpacing * (idx + 1),
      label: "VICTIM",
      color: "#059669",
    };
  });

  const hopNodes = hops.map((item, idx) => {
    const vpa = typeof item === "string" ? item : item?.payee_vpa || item?.vpa || `hop-${idx + 1}@upi`;
    const xOffset = isExpanded ? 90 : 60;
    const yPos = idx % 2 === 0 ? (isExpanded ? 50 : 35) : (height - (isExpanded ? 50 : 35));
    return {
      id: `hop-${idx}`,
      vpa,
      x: hubX + (idx % 2 === 0 ? -xOffset : xOffset),
      y: yPos,
      label: "LAYER HOP",
      color: "#d97706",
    };
  });

  const cashoutNodes = fanOut.map((item, idx) => {
    const vpa = typeof item === "string" ? item : item?.payee_vpa || item?.vpa || `cashout-${idx + 1}@upi`;
    const ySpacing = height / (fanOut.length + 1);
    return {
      id: `cashout-${idx}`,
      vpa,
      x: width - (isExpanded ? 100 : 70),
      y: ySpacing * (idx + 1),
      label: "CASHOUT",
      color: "#dc2626",
    };
  });

  return (
    <div className={`relative w-full ${isExpanded ? "h-[360px]" : "h-[240px]"} bg-[#0b0f19] rounded-lg overflow-hidden flex flex-col p-3 select-none transition-all`}>
      {/* Top Meta Bar */}
      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 border-b border-slate-800 pb-1.5 mb-1 z-10">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
          <span className="font-semibold text-slate-200">IN-BROWSER VECTOR TOPOLOGY</span>
          <span className="text-slate-500">· Layer 4 Vector Fallback</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-amber-300 border border-slate-700">
            Hash: {ringHash.slice(0, 14)}
          </span>
          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            {formatINR(amount)}
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="flex-1 w-full h-full"
        style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.5))" }}
      >
        <defs>
          {/* Arrow Markers */}
          <marker id="arrow-teal" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#14b8a6" />
          </marker>
          <marker id="arrow-amber" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#f59e0b" />
          </marker>
          <marker id="arrow-rose" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#f43f5e" />
          </marker>

          {/* Radial Gradient for Hub */}
          <radialGradient id="hub-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#dc2626" stopOpacity="0.8" />
            <stop offset="60%" stopColor="#991b1b" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#7f1d1d" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Grid Background Lines */}
        <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />
        <line x1={hubX} y1="0" x2={hubX} y2={height} stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />

        {/* Edges from Victims to Hub */}
        {victimNodes.map((v) => (
          <g key={`edge-${v.id}`}>
            <path
              d={`M ${v.x} ${v.y} Q ${(v.x + hubX) / 2} ${v.y} ${hubX} ${hubY}`}
              fill="none"
              stroke="#14b8a6"
              strokeWidth="1.75"
              strokeDasharray="4 3"
              markerEnd="url(#arrow-teal)"
              opacity="0.8"
            />
          </g>
        ))}

        {/* Edges from Hub to Hops */}
        {hopNodes.map((h) => (
          <g key={`edge-${h.id}`}>
            <path
              d={`M ${hubX} ${hubY} Q ${(hubX + h.x) / 2} ${h.y} ${h.x} ${h.y}`}
              fill="none"
              stroke="#f59e0b"
              strokeWidth="1.75"
              strokeDasharray="4 3"
              markerEnd="url(#arrow-amber)"
              opacity="0.8"
            />
          </g>
        ))}

        {/* Edges from Hops / Hub to Cashout */}
        {cashoutNodes.map((c, idx) => {
          const source = hopNodes[idx % hopNodes.length] || { x: hubX, y: hubY };
          return (
            <g key={`edge-${c.id}`}>
              <path
                d={`M ${source.x} ${source.y} Q ${(source.x + c.x) / 2} ${c.y} ${c.x} ${c.y}`}
                fill="none"
                stroke="#f43f5e"
                strokeWidth="1.75"
                strokeDasharray="4 3"
                markerEnd="url(#arrow-rose)"
                opacity="0.85"
              />
            </g>
          );
        })}

        {/* Center Mule Collector Hub */}
        <circle cx={hubX} cy={hubY} r={isExpanded ? 34 : 26} fill="url(#hub-glow)" />
        <circle cx={hubX} cy={hubY} r={isExpanded ? 18 : 14} fill="#b91c1c" stroke="#fca5a5" strokeWidth="2" />
        <text
          x={hubX}
          y={hubY + 4}
          textAnchor="middle"
          fill="#ffffff"
          fontSize={isExpanded ? "9" : "8"}
          fontWeight="bold"
          fontFamily="monospace"
        >
          HUB
        </text>
        <text
          x={hubX}
          y={hubY + (isExpanded ? 28 : 22)}
          textAnchor="middle"
          fill="#fca5a5"
          fontSize={isExpanded ? "10" : "8"}
          fontFamily="monospace"
          fontWeight="600"
        >
          {shortVpa(collector)}
        </text>

        {/* Victim Nodes */}
        {victimNodes.map((v) => (
          <g key={v.id}>
            <circle cx={v.x} cy={v.y} r={isExpanded ? 12 : 9} fill="#065f46" stroke="#6ee7b7" strokeWidth="1.5" />
            <text
              x={v.x}
              y={v.y + 3}
              textAnchor="middle"
              fill="#ffffff"
              fontSize={isExpanded ? "8" : "7"}
              fontWeight="bold"
              fontFamily="monospace"
            >
              IN
            </text>
            <text
              x={v.x}
              y={v.y - (isExpanded ? 15 : 12)}
              textAnchor="middle"
              fill="#6ee7b7"
              fontSize={isExpanded ? "9" : "7.5"}
              fontFamily="monospace"
            >
              {shortVpa(v.vpa)}
            </text>
          </g>
        ))}

        {/* Hop Nodes */}
        {hopNodes.map((h) => (
          <g key={h.id}>
            <circle cx={h.x} cy={h.y} r={isExpanded ? 12 : 9} fill="#92400e" stroke="#fcd34d" strokeWidth="1.5" />
            <text
              x={h.x}
              y={h.y + 3}
              textAnchor="middle"
              fill="#ffffff"
              fontSize={isExpanded ? "8" : "7"}
              fontWeight="bold"
              fontFamily="monospace"
            >
              HOP
            </text>
            <text
              x={h.x}
              y={h.y > hubY ? h.y + (isExpanded ? 18 : 14) : h.y - (isExpanded ? 15 : 11)}
              textAnchor="middle"
              fill="#fcd34d"
              fontSize={isExpanded ? "9" : "7.5"}
              fontFamily="monospace"
            >
              {shortVpa(h.vpa)}
            </text>
          </g>
        ))}

        {/* Cashout Nodes */}
        {cashoutNodes.map((c) => (
          <g key={c.id}>
            <circle cx={c.x} cy={c.y} r={isExpanded ? 12 : 9} fill="#9f1239" stroke="#fda4af" strokeWidth="1.5" />
            <text
              x={c.x}
              y={c.y + 3}
              textAnchor="middle"
              fill="#ffffff"
              fontSize={isExpanded ? "8" : "7"}
              fontWeight="bold"
              fontFamily="monospace"
            >
              OUT
            </text>
            <text
              x={c.x}
              y={c.y - (isExpanded ? 15 : 12)}
              textAnchor="middle"
              fill="#fda4af"
              fontSize={isExpanded ? "9" : "7.5"}
              fontFamily="monospace"
            >
              {shortVpa(c.vpa)}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend Footer */}
      <div className="flex items-center justify-center gap-4 text-[9px] font-mono text-slate-400 border-t border-slate-800/80 pt-1.5 mt-auto">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Victim (Fan-In)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-rose-500 inline-block" /> Collector Hub
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Layering Hop
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-rose-400 inline-block" /> Cash-Out Exit
        </span>
      </div>
    </div>
  );
}

export default function ForensicImageViewer({ caseId, caseData }) {
  const [zoomed, setZoomed] = useState(false);
  // Tier: 1 = /upi/cases/${caseId}/graph.png, 2 = /static/upi_cases/${caseId}_ring.png, 3 = SVG vector topology
  const [tier, setTier] = useState(1);
  const [loading, setLoading] = useState(true);
  const [imgLoaded, setImgLoaded] = useState(false);

  useEffect(() => {
    setTier(1);
    setLoading(true);
    setImgLoaded(false);
  }, [caseId]);

  if (!caseId) return null;

  const currentSrc =
    tier === 1
      ? api.caseGraphUrl(caseId)
      : tier === 2
      ? api.caseStaticRingUrl(caseId)
      : null;

  const handleImageError = () => {
    if (tier === 1) {
      // Fallback to Tier 2 (static png)
      setTier(2);
      setLoading(true);
      setImgLoaded(false);
    } else if (tier === 2) {
      // Fallback to Tier 3 (in-browser SVG vector topology)
      setTier(3);
      setLoading(false);
      setImgLoaded(false);
    }
  };

  const handleImageLoad = () => {
    setLoading(false);
    setImgLoaded(true);
  };

  return (
    <div className="panel overflow-hidden border border-hairline bg-surface-muted/30">
      <div className="panel-header flex items-center justify-between bg-white">
        <div className="panel-title">
          <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
            Layer 4 · Visual Forensics
          </div>
          <div className="font-serif font-bold text-sm text-ink-900 flex items-center gap-2">
            <span>4-Panel Forensic Graph Summary</span>
            {tier === 3 && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                SVG Vector Mode
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoomed(true)}
            className="text-xs font-mono text-muted hover:text-ink-900 flex items-center gap-1 px-2.5 py-1 rounded bg-surface-muted hover:bg-white border border-hairline transition-colors"
            title="Expand in full-screen lightbox"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
              />
            </svg>
            <span>Lightbox Zoom</span>
          </button>
        </div>
      </div>

      <div className="p-3 flex items-center justify-center min-h-[240px] bg-white relative">
        {loading && tier !== 3 && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <div className="flex items-center gap-2 text-xs font-mono text-muted">
              <span className="w-3 h-3 rounded-full border-2 border-ink-900 border-t-transparent animate-spin" />
              <span>
                {tier === 1 ? "Rendering visual graph…" : "Loading forensic ring image…"}
              </span>
            </div>
          </div>
        )}

        {tier === 3 ? (
          <SvgRingTopology caseId={caseId} caseData={caseData} isExpanded={false} />
        ) : (
          <img
            key={`${caseId}-${tier}`}
            src={currentSrc}
            alt={`Forensic summary for case ${caseId}`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            onClick={() => setZoomed(true)}
            className={`w-full max-h-[420px] object-contain rounded cursor-zoom-in hover:opacity-95 transition-opacity duration-500 ${
              imgLoaded ? "opacity-100" : "opacity-0"
            }`}
          />
        )}
      </div>

      {/* Lightbox Zoom Modal */}
      {zoomed && (
        <div
          className="fixed inset-0 z-50 bg-ink-900/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-8"
          onClick={() => setZoomed(false)}
        >
          <div
            className="relative max-w-5xl w-full max-h-[92vh] bg-white rounded-xl shadow-2xl p-4 overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-hairline">
              <div className="font-serif font-bold text-ink-900 flex items-center gap-2">
                <span>4-Panel Forensic Evidence Dossier · {caseId}</span>
                {tier === 3 && (
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                    Vector Topology Mode
                  </span>
                )}
              </div>
              <button
                onClick={() => setZoomed(false)}
                className="w-8 h-8 rounded-md flex items-center justify-center text-muted hover:text-ink-900 text-xl font-bold leading-none hover:bg-slate-100"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto p-2 flex items-center justify-center bg-slate-50 rounded-lg mt-2">
              {tier === 3 ? (
                <div className="w-full max-w-4xl">
                  <SvgRingTopology caseId={caseId} caseData={caseData} isExpanded={true} />
                </div>
              ) : (
                <img
                  src={currentSrc}
                  alt="Forensic Evidence High Res"
                  className="max-w-full max-h-[80vh] object-contain rounded shadow-md"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

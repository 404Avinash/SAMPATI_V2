import React from "react";
import ReactMarkdown from "react-markdown";

export default function SarNarrativeView({ markdown, tokenEconomy }) {
  if (!markdown && !tokenEconomy) return null;

  return (
    <div className="space-y-4">
      {/* Token Economy Header */}
      {tokenEconomy && (
        <div className="grid grid-cols-3 gap-3 bg-surface-muted/60 p-3 rounded-lg border border-hairline text-center font-mono">
          <div>
            <div className="text-[10px] uppercase text-muted">Raw Text Tokens</div>
            <div className="text-sm font-bold text-ink-900 mt-0.5">
              {tokenEconomy.raw_tokens ?? "—"}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-muted">Vision Tokens</div>
            <div className="text-sm font-bold text-ink-900 mt-0.5">
              {tokenEconomy.vision_tokens ?? "—"}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-muted">Token Compression</div>
            <div className="text-sm font-bold text-emerald-700 mt-0.5">
              {tokenEconomy.compression_ratio
                ? `${Number(tokenEconomy.compression_ratio).toFixed(1)}× savings`
                : "—"}
            </div>
          </div>
        </div>
      )}

      {/* AI SAR Narrative Content */}
      {markdown ? (
        <div className="panel p-5 bg-white">
          <div className="text-[11px] uppercase tracking-wide text-muted font-mono mb-3 flex items-center justify-between pb-2 border-b border-hairline">
            <span className="flex items-center gap-1.5 text-ink-900 font-bold font-serif">
              <span>✦</span> AI Suspicious Activity Report (SAR) Narrative
            </span>
            <span className="text-[10px] text-muted">Gemini 2.5 Vision + Heuristic Attribution</span>
          </div>
          <div className="prose prose-sm max-w-none sar leading-relaxed font-sans text-body">
            <ReactMarkdown>{markdown}</ReactMarkdown>
          </div>
        </div>
      ) : (
        <div className="panel p-6 text-center text-xs font-mono text-muted">
          AI narrative generation pending for this case.
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "../../services/api";

const SUGGESTED_QUESTIONS = [
  "Why was this transaction flagged?",
  "Explain the mule ring structure and linked entities",
  "Interpret the Dead Money Velocity (DMV) score",
  "What regulatory actions are recommended for FIU-IND?",
  "Draft a formal SAR executive summary",
];

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

const MARKDOWN_COMPONENTS = {
  code({ inline, className, children, ...props }) {
    return inline ? (
      <code className="bg-slate-100 text-indigo-700 font-mono text-[11px] px-1 py-0.5 rounded border border-slate-200 break-all" {...props}>
        {children}
      </code>
    ) : (
      <div className="my-2 rounded-lg bg-slate-900 text-slate-100 p-2.5 overflow-x-auto text-[11px] font-mono border border-slate-700">
        <code {...props}>{children}</code>
      </div>
    );
  },
  table({ children }) {
    return (
      <div className="overflow-x-auto my-2 border border-slate-200 rounded-lg shadow-2xs">
        <table className="min-w-full divide-y divide-slate-200 text-xs text-left">{children}</table>
      </div>
    );
  },
  th({ children }) {
    return <th className="bg-slate-100 px-2 py-1 text-slate-700 font-semibold font-mono text-[10px] uppercase">{children}</th>;
  },
  td({ children }) {
    return <td className="px-2 py-1 border-t border-slate-100 text-slate-700 font-mono text-[11px] break-words">{children}</td>;
  },
  ul({ children }) {
    return <ul className="list-disc list-inside space-y-0.5 my-1 text-xs">{children}</ul>;
  },
  ol({ children }) {
    return <ol className="list-decimal list-inside space-y-0.5 my-1 text-xs">{children}</ol>;
  },
  li({ children }) {
    return <li className="leading-relaxed break-words">{children}</li>;
  },
  p({ children }) {
    return <p className="mb-1.5 last:mb-0 leading-relaxed break-words">{children}</p>;
  },
  strong({ children }) {
    return <strong className="font-bold text-slate-900">{children}</strong>;
  },
  blockquote({ children }) {
    return <blockquote className="border-l-2 border-indigo-400 pl-2.5 my-1 text-slate-600 italic bg-indigo-50/40 py-0.5 rounded-r break-words">{children}</blockquote>;
  },
};

export default function CaseAiCopilotView({ caseData, onExportSar, downloadingPdf }) {
  const [briefing, setBriefing] = useState(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [briefingError, setBriefingError] = useState(null);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const [chatError, setChatError] = useState(null);

  const [sarNarrative, setSarNarrative] = useState(null);
  const [loadingSar, setLoadingSar] = useState(false);
  const [sarError, setSarError] = useState(null);

  const [copiedBriefing, setCopiedBriefing] = useState(false);
  const [copiedSar, setCopiedSar] = useState(false);

  const chatBottomRef = useRef(null);
  const messagesBoxRef = useRef(null);

  const caseId = caseData?.case_id;

  // Load briefing and initialize chat on caseId change
  useEffect(() => {
    if (!caseId) return;

    let isMounted = true;
    setLoadingBriefing(true);
    setBriefingError(null);
    setSarNarrative(null);
    setSarError(null);

    // Initial greeting in chat
    setMessages([
      {
        id: "init",
        role: "assistant",
        text: `Hello Investigator. I am your **SAMPATI AI Fraud Analyst Copilot** powered by Google Gemini. I have loaded case records for **\`${caseId}\`**. You can review the automated briefing below or ask me any question regarding money routing, DMV velocity, or regulatory compliance protocols.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        source: "system",
      },
    ]);

    api
      .getAiBriefing(caseId)
      .then((data) => {
        if (isMounted) {
          setBriefing(data);
          setLoadingBriefing(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Failed to load AI briefing", err);
          setBriefingError(err.message || "Failed to load AI briefing");
          setLoadingBriefing(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [caseId]);

  // Scroll to bottom of chat box smoothly without scrolling parent drawer
  useEffect(() => {
    if (messagesBoxRef.current) {
      messagesBoxRef.current.scrollTo({
        top: messagesBoxRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, loadingChat]);

  const handleRefreshBriefing = async () => {
    if (!caseId) return;
    setLoadingBriefing(true);
    setBriefingError(null);
    try {
      const data = await api.getAiBriefing(caseId, true);
      setBriefing(data);
    } catch (err) {
      console.error("Refresh AI briefing failed", err);
      setBriefingError(err.message || "Failed to refresh briefing");
    } finally {
      setLoadingBriefing(false);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const q = (textToSend || input).trim();
    if (!q || !caseId || loadingChat) return;

    setInput("");
    setChatError(null);

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoadingChat(true);

    try {
      // Build clean conversation history turns for API
      const historyTurns = messages
        .filter((m) => m.id !== "init" && !m.isError)
        .slice(-6)
        .map((m) => ({
          role: m.role,
          content: m.text,
        }));

      const res = await api.chatAiCopilot(caseId, q, historyTurns);
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: res.answer || "No response received from Copilot.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        source: res.source,
        model: res.model,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error("Chat error", err);
      setChatError(err.message || "Failed to send message to Copilot");
      const errorMsg = {
        id: `assistant-err-${Date.now()}`,
        role: "assistant",
        text: `⚠️ **Copilot Error:** Unable to reach AI service (${err.message || "network error"}). Please try again.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoadingChat(false);
    }
  };

  const handleGenerateSarDraft = async () => {
    if (!caseId || loadingSar) return;
    setLoadingSar(true);
    setSarError(null);
    try {
      const res = await api.getAiSarNarrative(caseId);
      setSarNarrative(res.sar_narrative || "No narrative generated.");
    } catch (err) {
      console.error("SAR generation failed", err);
      setSarError(err.message || "Failed to draft SAR narrative.");
    } finally {
      setLoadingSar(false);
    }
  };

  const handleCopyBriefing = async () => {
    if (!briefing) return;
    const text = `SAMPATI AI CASE BRIEFING - ${briefing.case_id}\n\n` +
      `Scam Typology: ${briefing.scam_classification}\n` +
      `Threat Level: ${briefing.threat_level} (Confidence: ${Math.round((briefing.confidence_score || 0.85) * 100)}%)\n\n` +
      `Executive Summary:\n${briefing.executive_summary}\n\n` +
      `Ring Analysis:\n${briefing.ring_analysis}\n\n` +
      `Key Indicators:\n${(briefing.key_indicators || []).map((k) => `• ${k}`).join("\n")}\n\n` +
      `Recommended Actions:\n${(briefing.recommended_actions || []).map((a, i) => `${i + 1}. ${a}`).join("\n")}`;
    const ok = await copyToClipboard(text);
    if (ok) {
      setCopiedBriefing(true);
      setTimeout(() => setCopiedBriefing(false), 2000);
    }
  };

  const handleCopySar = async () => {
    if (!sarNarrative) return;
    const ok = await copyToClipboard(sarNarrative);
    if (ok) {
      setCopiedSar(true);
      setTimeout(() => setCopiedSar(false), 2000);
    }
  };

  const isGemini = briefing?.source === "gemini-ai";

  return (
    <div className="space-y-6">
      {/* Copilot Status Banner */}
      <div className="p-3.5 bg-gradient-to-r from-indigo-900 via-slate-900 to-ink-900 rounded-xl text-white shadow-md border border-indigo-700/40 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-400/40 flex items-center justify-center text-base">
            ✨
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-serif font-bold text-sm tracking-wide">Google Gemini AI Copilot</span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-400/20 text-emerald-300 border border-emerald-400/30">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Active
              </span>
            </div>
            <p className="text-[11px] text-slate-300 font-sans">
              Real-time forensic synthesis, pattern typology classification &amp; regulatory Q&amp;A
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefreshBriefing}
            disabled={loadingBriefing}
            className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-xs font-mono border border-white/20 transition-colors flex items-center gap-1.5 disabled:opacity-50"
            title="Refresh AI briefing from Gemini API"
          >
            <span className={loadingBriefing ? "animate-spin" : ""}>🔄</span>
            <span>{loadingBriefing ? "Synthesizing…" : "Refresh"}</span>
          </button>
        </div>
      </div>

      {/* Briefing Error Banner */}
      {briefingError && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs font-mono text-amber-900 flex items-start justify-between gap-2">
          <div className="flex items-start gap-2">
            <span>⚠️</span>
            <div>
              <strong className="block font-bold">AI Briefing Warning</strong>
              <span className="text-[11px] text-amber-800">{briefingError}</span>
            </div>
          </div>
          <button
            onClick={handleRefreshBriefing}
            className="px-2 py-0.5 rounded bg-amber-200 hover:bg-amber-300 text-amber-900 text-[11px] font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Automated Case Executive Briefing Panel */}
      <div className="panel p-5 bg-white border border-hairline rounded-xl space-y-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-hairline">
          <div>
            <div className="text-[10px] uppercase font-mono tracking-wider text-muted">
              Executive AI Briefing
            </div>
            <div className="font-serif font-bold text-base text-ink-900 flex items-center gap-2">
              <span>Forensic Synthesis</span>
              {briefing && (
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold border ${
                    isGemini
                      ? "bg-purple-50 text-purple-700 border-purple-200"
                      : "bg-slate-100 text-slate-700 border-slate-300"
                  }`}
                >
                  {isGemini ? `✨ ${briefing.model || "Gemini 1.5 Flash"}` : "🛡️ Deterministic Rule Engine"}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {briefing && (
              <>
                <span
                  className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded border ${
                    briefing.threat_level === "CRITICAL"
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : briefing.threat_level === "HIGH"
                      ? "bg-amber-50 text-amber-700 border-amber-200"
                      : "bg-emerald-50 text-emerald-700 border-emerald-200"
                  }`}
                >
                  {briefing.threat_level} THREAT
                </span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-muted text-muted border border-hairline">
                  {Math.round((briefing.confidence_score || 0.85) * 100)}% Confidence
                </span>
                <button
                  onClick={handleCopyBriefing}
                  className="px-2 py-1 rounded bg-surface-muted hover:bg-slate-200 text-ink-900 text-xs font-mono border border-hairline transition-colors"
                  title="Copy briefing to clipboard"
                >
                  {copiedBriefing ? "Copied ✓" : "Copy Briefing"}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Loading Skeleton */}
        {loadingBriefing && !briefing && (
          <div className="py-8 text-center space-y-3">
            <div className="inline-block w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-xs font-mono text-muted">
              Consulting Google Gemini Fraud Intelligence Mesh…
            </p>
          </div>
        )}

        {/* Briefing Content */}
        {briefing && (
          <div className="space-y-4 text-xs font-sans">
            {/* Scam Pattern Badges */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] uppercase font-mono text-muted font-bold">
                Pattern Typology:
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-50 text-indigo-900 border border-indigo-200 font-mono font-bold text-xs shadow-2xs">
                <span>🎯</span>
                <span>{briefing.scam_classification}</span>
              </span>
            </div>

            {/* Executive Summary Narrative */}
            <div className="p-3.5 rounded-lg bg-surface-muted/60 border border-hairline space-y-1">
              <div className="text-[10px] uppercase font-mono font-bold text-muted tracking-wide">
                Executive Overview
              </div>
              <p className="text-body leading-relaxed font-sans text-xs break-words">
                {briefing.executive_summary}
              </p>
            </div>

            {/* Ring Analysis Breakdown */}
            <div className="p-3.5 rounded-lg bg-slate-50 border border-hairline space-y-1">
              <div className="text-[10px] uppercase font-mono font-bold text-slate-500 tracking-wide">
                Ring Network &amp; Topology Flow
              </div>
              <p className="text-slate-700 leading-relaxed font-sans text-xs break-words">
                {briefing.ring_analysis}
              </p>
            </div>

            {/* Two Column: Key Indicators & Recommended Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Key Indicators */}
              <div className="p-3 rounded-lg bg-rose-50/50 border border-rose-100 space-y-2">
                <div className="text-[10px] uppercase font-mono font-bold text-rose-800 flex items-center gap-1">
                  <span>⚡</span>
                  <span>Key Red Flags Observed</span>
                </div>
                <ul className="space-y-1.5 text-[11px] text-rose-950 font-mono">
                  {(briefing.key_indicators || []).map((item, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-rose-500 font-bold">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recommended Actions */}
              <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100 space-y-2">
                <div className="text-[10px] uppercase font-mono font-bold text-emerald-800 flex items-center gap-1">
                  <span>🛡️</span>
                  <span>Prescribed Remediation</span>
                </div>
                <ul className="space-y-1.5 text-[11px] text-emerald-950 font-sans">
                  {(briefing.recommended_actions || []).map((item, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="font-mono font-bold text-emerald-700">{idx + 1}.</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Interactive Case Copilot Chat Interface */}
      <div className="panel bg-white border border-hairline rounded-xl overflow-hidden shadow-xs flex flex-col">
        <div className="panel-header bg-surface-muted/50 px-4 py-3 border-b border-hairline flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-base">💬</span>
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-muted">
                Interactive Analyst Q&amp;A
              </div>
              <div className="font-serif font-bold text-sm text-ink-900">
                Case Copilot Chat Assistant
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium">
            Context-Aware
          </span>
        </div>

        {/* Message History Thread */}
        <div ref={messagesBoxRef} className="p-4 space-y-3 max-h-80 overflow-y-auto bg-slate-50/50">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
            >
              <div className="flex items-center gap-1.5 mb-1 px-1">
                <span className="text-[10px] font-mono text-muted">
                  {m.role === "user" ? "🧑‍💻 You (Analyst)" : "✨ Gemini Copilot"}
                </span>
                <span className="text-[9px] font-mono text-slate-400">· {m.timestamp}</span>
              </div>

              <div
                className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-xs break-words overflow-hidden ${
                  m.role === "user"
                    ? "bg-ink-900 text-white shadow-xs"
                    : m.isError
                    ? "bg-rose-50 text-rose-900 border border-rose-200"
                    : "bg-white text-ink-900 border border-hairline shadow-2xs"
                }`}
              >
                {m.role === "assistant" ? (
                  <div className="prose prose-xs max-w-none font-sans space-y-1 break-words">
                    <ReactMarkdown components={MARKDOWN_COMPONENTS}>{m.text}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="font-sans leading-relaxed whitespace-pre-wrap break-words">{m.text}</p>
                )}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {loadingChat && (
            <div className="flex items-center gap-2 text-xs font-mono text-muted p-2 bg-white rounded-lg border border-hairline max-w-[200px] animate-pulse">
              <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
              <span>Copilot is analyzing…</span>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Suggested Quick Prompt Chips */}
        <div className="px-4 py-2.5 bg-white border-t border-hairline flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] font-mono uppercase text-muted font-bold mr-1">
            Suggested:
          </span>
          {SUGGESTED_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              disabled={loadingChat}
              onClick={() => handleSendMessage(q)}
              className="text-[11px] font-sans px-2.5 py-1 rounded-full bg-surface-muted hover:bg-indigo-50 hover:text-indigo-700 border border-hairline hover:border-indigo-200 transition-colors disabled:opacity-40 text-slate-700"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Chat Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(input);
          }}
          className="p-3 bg-white border-t border-hairline flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                if (input.trim() && !loadingChat) {
                  handleSendMessage(input);
                }
              }
            }}
            disabled={loadingChat}
            placeholder={`Ask Copilot about Case ${caseId || ""} (e.g., 'What is the mule topology?')...`}
            className="flex-1 text-xs border border-hairline rounded-lg px-3 py-2 bg-surface-muted/40 focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-indigo-500 font-sans"
          />
          <button
            type="submit"
            disabled={!input.trim() || loadingChat}
            className="btn-primary py-2 px-4 text-xs font-semibold disabled:opacity-40 flex items-center gap-1.5"
          >
            <span>Ask</span>
            <span>➔</span>
          </button>
        </form>

        {chatError && (
          <div className="px-4 py-2 bg-rose-50 text-[11px] font-mono text-rose-700 border-t border-rose-200">
            {chatError}
          </div>
        )}
      </div>

      {/* Regulatory SAR Narrative Drafting Section */}
      <div className="panel p-5 bg-white border border-hairline rounded-xl space-y-3 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-[10px] uppercase font-mono tracking-wider text-muted">
              Regulatory Compliance Tool
            </div>
            <div className="font-serif font-bold text-sm text-ink-900">
              FIU-IND Suspicious Activity Report (SAR) Narrative
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!sarNarrative ? (
              <button
                onClick={handleGenerateSarDraft}
                disabled={loadingSar}
                className="px-3 py-1.5 rounded-md bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold font-mono transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                <span>📝</span>
                <span>{loadingSar ? "Drafting SAR…" : "Draft SAR Narrative"}</span>
              </button>
            ) : (
              <>
                <button
                  onClick={handleCopySar}
                  className="px-2.5 py-1 rounded bg-surface-muted hover:bg-slate-200 text-ink-900 text-xs font-mono border border-hairline transition-colors"
                >
                  {copiedSar ? "Copied ✓" : "Copy SAR"}
                </button>
                <button
                  onClick={onExportSar}
                  disabled={downloadingPdf}
                  className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-mono font-semibold transition-colors disabled:opacity-50"
                >
                  {downloadingPdf ? "Exporting…" : "Export PDF"}
                </button>
              </>
            )}
          </div>
        </div>

        {sarError && (
          <div className="p-2.5 bg-rose-50 border border-rose-200 rounded text-xs font-mono text-rose-800">
            {sarError}
          </div>
        )}

        {sarNarrative && (
          <div className="p-4 rounded-lg bg-slate-50 border border-hairline text-xs font-sans leading-relaxed space-y-2">
            <div className="prose prose-xs max-w-none text-slate-800 font-sans">
              <ReactMarkdown components={MARKDOWN_COMPONENTS}>{sarNarrative}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

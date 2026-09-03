const BASE = "";

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${options.method || "GET"} ${path} -> ${res.status}: ${text}`);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

export const api = {
  // Existing Core Endpoints
  simulate: (count, fraudRatio) =>
    req("/upi/simulate", {
      method: "POST",
      body: JSON.stringify({ total_txns: count, fraud_ratio: fraudRatio }),
    }),

  runFederation: () => req("/upi/federation/run", { method: "POST" }),

  cases: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req(`/upi/cases${qs ? `?${qs}` : ""}`).catch(() => req(`/cases${qs ? `?${qs}` : ""}`));
  },

  case: (id) =>
    req(`/upi/cases/${id}`).catch(() => req(`/cases/${id}`)),

  feedback: (id, confirmed) =>
    req(`/upi/cases/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ confirmed }),
    }),

  stats: () =>
    req("/upi/stats").catch(() => req("/stats")),

  checkTxn: (txn) => req("/upi/check", { method: "POST", body: JSON.stringify(txn) }),

  // R2 / M3 Backend Additions
  getAnalytics: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req(`/stats/analytics${qs ? `?${qs}` : ""}`)
      .catch(() => req(`/upi/stats/analytics${qs ? `?${qs}` : ""}`))
      .catch(() => null);
  },

  getDetailedHealth: () =>
    req("/health/detailed")
      .catch(() => req("/upi/health/detailed"))
      .catch(() => req("/api/health/detailed"))
      .catch(() => null),

  updateCaseStatus: (caseId, payload) => {
    const body =
      typeof payload === "string"
        ? JSON.stringify({ status: payload })
        : JSON.stringify({
            status: payload.status,
            notes: payload.notes || payload.resolution_notes || "",
            resolution_notes: payload.resolution_notes || payload.notes || "",
            resolution: payload.resolution || "",
            escalate_to_dpip: Boolean(payload.escalate_to_dpip || payload.publish_to_dpip),
          });

    return req(`/cases/${caseId}/status`, {
      method: "PATCH",
      body,
    }).catch(() =>
      req(`/upi/cases/${caseId}/status`, {
        method: "PATCH",
        body,
      })
    );
  },

  updateSensitivity: (sensitivity) =>
    req("/upi/settings/sensitivity", {
      method: "POST",
      body: JSON.stringify({ sensitivity }),
    }).catch(() =>
      req("/engine/sensitivity", {
        method: "POST",
        body: JSON.stringify({ sensitivity }),
      })
    ),

  getDeployStatus: () =>
    req("/api/deployment/status").catch(() => ({
      commit_sha: "404avinash/sampati_v2@main",
      image_tag: "ghcr.io/404avinash/sampati_v2:latest",
      status: "PASSING",
      deployed_at: new Date().toISOString(),
      environment: "AWS EC2 Mumbai (ap-south-1)",
      health_status: "HEALTHY",
      rollback_target: "ghcr.io/404avinash/sampati_v2:prev",
    })),

  caseGraphUrl: (caseId) => `/upi/cases/${caseId}/graph.png`,
  caseStaticRingUrl: (caseId) => `/static/upi_cases/${caseId}_ring.png`,

  // Auto-Feed Lifecycle Endpoints (R3 / R6)
  startAutoFeed: (options = {}) =>
    req("/upi/autofeed/start", {
      method: "POST",
      body: JSON.stringify({
        rate_tps: options.rate_tps || 10.0,
        fraud_ratio: options.fraud_ratio !== undefined ? options.fraud_ratio : 0.15,
        bursty: options.bursty !== false,
      }),
    }),

  stopAutoFeed: () => req("/upi/autofeed/stop", { method: "POST" }),

  getAutoFeedStatus: () =>
    req("/upi/autofeed/status").catch(() => ({
      active: false,
      rate_tps: 10.0,
      total_generated: 0,
      total_flagged: 0,
    })),

  // SAR PDF Export Endpoints (R1 / R4)
  sarPdfUrl: (caseId) => `/cases/${caseId}/sar/pdf`,

  downloadSarPdf: async (caseId) => {
    let res = await fetch(`/cases/${caseId}/sar/pdf`);
    if (!res.ok) {
      res = await fetch(`/upi/cases/${caseId}/sar/pdf`);
    }
    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`PDF download failed with HTTP ${res.status}: ${errText || res.statusText}`);
    }
    const contentType = (res.headers.get("content-type") || "").toLowerCase();
    if (!contentType.includes("pdf")) {
      const errText = await res.text().catch(() => "");
      throw new Error(
        `Invalid content-type '${contentType}' received for PDF (expected application/pdf)`
      );
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SAR_${caseId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  // Gemini Assistant & AI Forensic Endpoints
  getAiBriefing: (caseId, refresh = false) => {
    const qs = refresh ? "?refresh=true" : "";
    return req(`/cases/${caseId}/ai-briefing${qs}`).catch(() =>
      req(`/upi/cases/${caseId}/ai-briefing${qs}`)
    );
  },

  chatGeminiAssistant: (caseId, question, history = []) =>
    req(`/cases/${caseId}/ai-chat`, {
      method: "POST",
      body: JSON.stringify({ question, history }),
    }).catch(() =>
      req(`/upi/cases/${caseId}/ai-chat`, {
        method: "POST",
        body: JSON.stringify({ question, history }),
      })
    ),

  chatAiCopilot: (caseId, question, history = []) =>
    api.chatGeminiAssistant(caseId, question, history),

  getAiSarNarrative: (caseId) =>
    req(`/cases/${caseId}/ai-sar`).catch(() => req(`/upi/cases/${caseId}/ai-sar`)),

  // Threat Intelligence & Pre-Transaction Early Warning (R1 / R2)
  getThreatSignals: (params = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    if (params.severity) query.set("severity", params.severity);
    if (params.source) query.set("source", params.source);
    if (params.campaign_id) query.set("campaign_id", params.campaign_id);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return req(`/intel/signals${qs}`).catch(() =>
      req(`/threat-intel/signals${qs}`).catch(() => req(`/upi/intel/signals${qs}`))
    );
  },

  getThreatSignal: (signalId) =>
    req(`/intel/signals/${signalId}`).catch(() =>
      req(`/threat-intel/signals/${signalId}`).catch(() => req(`/upi/intel/signals/${signalId}`))
    ),

  ingestThreatSignal: (signalData) =>
    req("/intel/signals", {
      method: "POST",
      body: JSON.stringify(signalData),
    }).catch(() =>
      req("/threat-intel/signals", {
        method: "POST",
        body: JSON.stringify(signalData),
      })
    ),

  getThreatGraph: (params = {}) => {
    const query = new URLSearchParams();
    if (params.subgraph_node) query.set("subgraph_node", params.subgraph_node);
    if (params.depth) query.set("depth", params.depth);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return req(`/intel/graph${qs}`).catch(() =>
      req(`/threat-intel/graph${qs}`).catch(() => req(`/upi/intel/graph${qs}`))
    );
  },

  getThreatCampaigns: () =>
    req("/intel/campaigns").catch(() =>
      req("/threat-intel/campaigns").catch(() => req(`/upi/intel/campaigns`))
    ),

  simulateThreatSignals: (count = 3) =>
    req(`/intel/simulate?count=${count}`, { method: "POST" }).catch(() =>
      req(`/threat-intel/simulate?count=${count}`, { method: "POST" })
    ),
};

export function formatINR(amount) {
  if (amount == null || isNaN(amount)) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function relativeTime(iso) {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (isNaN(then)) return "—";
  const diffSec = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const m = Math.floor(diffSec / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

export function formatTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleTimeString("en-IN", { hour12: false });
  } catch {
    return iso;
  }
}

export function formatDateTime(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return `${d.toLocaleDateString("en-IN")} ${d.toLocaleTimeString("en-IN", { hour12: false })}`;
  } catch {
    return iso;
  }
}

export function shortVpa(vpa) {
  if (!vpa || typeof vpa !== "string") return vpa == null ? "—" : String(vpa);
  return vpa.length > 24 ? `${vpa.slice(0, 11)}…${vpa.slice(-9)}` : vpa;
}

export function getRiskTone(score) {
  const num = typeof score === "number" ? score : parseFloat(score) || 0;
  if (num >= 75) return { text: "text-rose-600", bg: "bg-rose-50", border: "border-rose-200", bar: "bg-rose-500" };
  if (num >= 40) return { text: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", bar: "bg-amber-500" };
  return { text: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", bar: "bg-emerald-500" };
}

export function getVerdictTone(verdict) {
  switch (verdict?.toUpperCase()) {
    case "BLOCK":
      return {
        badge: "bg-verdict-blockBg text-verdict-block border-verdict-block/30",
        color: "#b3261e",
        label: "BLOCK",
      };
    case "HOLD":
      return {
        badge: "bg-verdict-holdBg text-verdict-hold border-verdict-hold/30",
        color: "#a8660a",
        label: "HOLD",
      };
    case "ALLOW":
    default:
      return {
        badge: "bg-verdict-allowBg text-verdict-allow border-verdict-allow/30",
        color: "#0f7a3d",
        label: "ALLOW",
      };
  }
}

export function getDmvTone(score) {
  const num = typeof score === "number" ? score : parseFloat(score) || 0;
  if (num >= 70) {
    return {
      text: "text-rose-700",
      bg: "bg-rose-50",
      border: "border-rose-200",
      bar: "bg-rose-600",
      label: "CRITICAL DRAIN",
      category: "Critical Mule Signature (>70)",
    };
  }
  if (num >= 40) {
    return {
      text: "text-amber-700",
      bg: "bg-amber-50",
      border: "border-amber-200",
      bar: "bg-amber-500",
      label: "ELEVATED VELOCITY",
      category: "Elevated Velocity (40-70)",
    };
  }
  return {
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    bar: "bg-emerald-500",
    label: "LOW VELOCITY",
    category: "Normal Flow (<40)",
  };
}


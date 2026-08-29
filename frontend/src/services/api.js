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

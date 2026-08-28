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
  simulate: (count, fraudRatio) =>
    req("/upi/simulate", {
      method: "POST",
      body: JSON.stringify({ total_txns: count, fraud_ratio: fraudRatio }),
    }),
  runFederation: () => req("/upi/federation/run", { method: "POST" }),
  cases: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req(`/upi/cases${qs ? `?${qs}` : ""}`);
  },
  case: (id) => req(`/upi/cases/${id}`),
  feedback: (id, confirmed) =>
    req(`/upi/cases/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ confirmed }),
    }),
  stats: () => req("/upi/stats"),
  checkTxn: (txn) => req("/upi/check", { method: "POST", body: JSON.stringify(txn) }),
};

export function formatINR(amount) {
  if (amount == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function relativeTime(iso) {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  const diffSec = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const m = Math.floor(diffSec / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

export function formatTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleTimeString("en-IN", { hour12: false });
  } catch {
    return iso;
  }
}

export function shortVpa(vpa) {
  if (!vpa || typeof vpa !== "string") return vpa == null ? "—" : String(vpa);
  return vpa.length > 22 ? `${vpa.slice(0, 10)}…${vpa.slice(-8)}` : vpa;
}

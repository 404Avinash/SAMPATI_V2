import React, { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, relativeTime } from "../services/api";
import { useToast } from "../context/ToastContext";

const SAMPLE_SIMULATION_PAYLOADS = [
  {
    title: "SBI KYC Phishing SMS",
    source: "sms_gateway",
    raw_content:
      "Dear SBI customer, your UPI account +919876543210 is suspended due to pending PAN KYC. Update immediately at https://sbi-kyc-auth-portal.in/login or verify at sbi.kyc.verification@oksbi within 2 hrs to prevent total asset freeze.",
    extracted: {
      phone: "+919876543210",
      upi_id: "sbi.kyc.verification@oksbi",
      url: "https://sbi-kyc-auth-portal.in/login",
      tags: ["Bank impersonation", "Urgency", "KYC suspension"],
    },
    campaign: "CAMP-KYC-PHISH-01",
    campaignName: "KYC Phishing Campaign",
    similarity: 94,
    nodes: ["VPA:sbi.kyc.verification@oksbi", "PHONE:+919876543210", "URL:sbi-kyc-auth-portal.in", "RULE:PRE_ARM_HONEYPOT"],
  },
  {
    title: "Part-Time Task Scam SMS",
    source: "mobile_app",
    raw_content:
      "Earn Rs 3,000-8,000 daily with Amazon product rating! Simple online job. Send deposit Rs 500 to amazon.merchant.pay@ybl or join https://t.me/vip_amazon_tasks_in to start today. Call 9823456789.",
    extracted: {
      phone: "+919823456789",
      upi_id: "amazon.merchant.pay@ybl",
      url: "https://t.me/vip_amazon_tasks_in",
      tags: ["Part-time job", "Guaranteed returns", "Deposit pooling"],
    },
    campaign: "CAMP-TASK-INVEST-02",
    campaignName: "Telegram Task Investment Scam",
    similarity: 88,
    nodes: ["VPA:amazon.merchant.pay@ybl", "PHONE:+919823456789", "URL:t.me/vip_amazon_tasks_in", "RULE:TASK_SCAM_MONITOR"],
  },
  {
    title: "Electricity Bill Disconnection Alert",
    source: "mule_sensor",
    raw_content:
      "Electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Contact electricity officer immediately at +919711223344 or pay at bescom.billdesk@paytm.",
    extracted: {
      phone: "+919711223344",
      upi_id: "bescom.billdesk@paytm",
      url: "https://bescom-bill-update.online",
      tags: ["Utility scam", "Urgency", "Threat of disconnection"],
    },
    campaign: "CAMP-KYC-PHISH-01",
    campaignName: "KYC & Utility Phishing Campaign",
    similarity: 91,
    nodes: ["VPA:bescom.billdesk@paytm", "PHONE:+919711223344", "URL:bescom-bill-update.online", "RULE:PRE_ARM_BLOCK"],
  },
  {
    title: "[NPCI] MuleHunter Switch Alert",
    source: "npci_mulehunter",
    institution: "NPCI",
    raw_content:
      "[NPCI Central Switch] Flagged account darkweb_mule_sink@okaxis with 96% mule probability. Rapid inflow surge from multiple banks across 5 states.",
    extracted: {
      phone: "+919811223344",
      upi_id: "darkweb_mule_sink@okaxis",
      url: "",
      tags: ["NPCI:MuleHunter", "Central Switch Flag", "High Mule Probability"],
    },
    campaign: "CAMP-KYC-PHISH-01",
    campaignName: "Campaign Central Switch Aggregation",
    similarity: 95,
    nodes: ["VPA:darkweb_mule_sink@okaxis", "INST:NPCI", "RULE:CENTRAL_SWITCH_HONEYPOT_SINK"],
  },
  {
    title: "[DPIP] National Fraud Registry Match",
    source: "dpip_registry",
    institution: "DPIP",
    raw_content:
      "[DPIP Smart Registry] Entity honeypot_trap_01@okaxis actively listed on National Cyber Crime Reporting Portal (I4C). Threat score: 0.90.",
    extracted: {
      phone: "+919877665544",
      upi_id: "honeypot_trap_01@okaxis",
      url: "",
      tags: ["DPIP:Registry", "I4C Portal", "Listed Fraud Entity"],
    },
    campaign: "CAMP-KYC-PHISH-01",
    campaignName: "National Registry Match",
    similarity: 92,
    nodes: ["VPA:honeypot_trap_01@okaxis", "INST:DPIP", "RULE:PRE_ARM_BLOCK"],
  },
  {
    title: "[PhonePe] Cross-PSP Velocity Burst",
    source: "psp_phonepe",
    institution: "PhonePe",
    raw_content:
      "[PhonePe Fraud Engine] Flagged velocity anomaly on beneficiary burst_fraud_node@ybl: 14 outbound transfers within 90 seconds.",
    extracted: {
      phone: "+919655443322",
      upi_id: "burst_fraud_node@ybl",
      url: "",
      tags: ["PSP:PhonePe", "Velocity Anomaly", "Pre-transaction alert"],
    },
    campaign: "CAMP-TASK-INVEST-02",
    campaignName: "Telegram Task Investment Scam",
    similarity: 89,
    nodes: ["VPA:burst_fraud_node@ybl", "INST:PhonePe", "RULE:VELOCITY_ANOMALY"],
  },
  {
    title: "[Paytm] Suspicious Beneficiary Pooling",
    source: "psp_paytm",
    institution: "Paytm",
    raw_content:
      "[Paytm Risk Guard] Suspicious beneficiary pooling detected on trap_collect_007@paytm: high-velocity inflow aggregation.",
    extracted: {
      phone: "+919733221100",
      upi_id: "trap_collect_007@paytm",
      url: "",
      tags: ["PSP:Paytm", "Suspicious Beneficiary", "Pre-transaction alert"],
    },
    campaign: "CAMP-KYC-PHISH-01",
    campaignName: "Campaign Central Switch Aggregation",
    similarity: 90,
    nodes: ["VPA:trap_collect_007@paytm", "INST:Paytm", "RULE:SUSPICIOUS_BENEFICIARY"],
  },
];

const INITIAL_FALLBACK_SIGNALS = [
  {
    signal_id: "SIG-2026-KYC-9421",
    source: "sms_gateway",
    severity: "CRITICAL",
    confidence: 0.96,
    extracted_entities: {
      phone: "+919876543210",
      upi_id: "sbi.kyc.verification@oksbi",
      url: "https://sbi-kyc-auth-portal.in/login",
      tags: ["Bank impersonation", "Urgency", "KYC suspension"],
    },
    matched_campaign: "CAMP-KYC-PHISH-01",
    linked_graph_nodes: ["VPA:sbi.kyc.verification@oksbi", "PHONE:+919876543210", "CAMPAIGN:CAMP-KYC-PHISH-01"],
    raw_content:
      "Dear SBI customer, your UPI account +919876543210 is suspended due to pending PAN KYC. Update immediately at https://sbi-kyc-auth-portal.in/login or verify at sbi.kyc.verification@oksbi within 2 hrs to prevent total asset freeze.",
    created_at: new Date(Date.now() - 120000).toISOString(),
  },
  {
    signal_id: "SIG-2026-TASK-8812",
    source: "mobile_app",
    severity: "HIGH",
    confidence: 0.92,
    extracted_entities: {
      phone: "+919823456789",
      upi_id: "amazon.merchant.pay@ybl",
      url: "https://t.me/vip_amazon_tasks_in",
      tags: ["Part-time job", "Guaranteed returns", "Deposit pooling"],
    },
    matched_campaign: "CAMP-TASK-INVEST-02",
    linked_graph_nodes: ["VPA:amazon.merchant.pay@ybl", "PHONE:+919823456789", "CAMPAIGN:CAMP-TASK-INVEST-02"],
    raw_content:
      "Earn Rs 3,000-8,000 daily with Amazon product rating! Simple online job. Send deposit Rs 500 to amazon.merchant.pay@ybl or join https://t.me/vip_amazon_tasks_in to start today. Call 9823456789.",
    created_at: new Date(Date.now() - 480000).toISOString(),
  },
  {
    signal_id: "SIG-2026-ELEC-4103",
    source: "mule_sensor",
    severity: "MEDIUM",
    confidence: 0.89,
    extracted_entities: {
      phone: "+919711223344",
      upi_id: "bescom.billdesk@paytm",
      url: "https://bescom-bill-update.online",
      tags: ["Utility scam", "Urgency", "Threat of disconnection"],
    },
    matched_campaign: "CAMP-KYC-PHISH-01",
    linked_graph_nodes: ["VPA:bescom.billdesk@paytm", "PHONE:+919711223344"],
    raw_content:
      "Electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Contact electricity officer immediately at +919711223344 or pay at bescom.billdesk@paytm.",
    created_at: new Date(Date.now() - 950000).toISOString(),
  },
];

export function renderInstitutionBadge(source, institution) {
  const src = (source || "").toLowerCase();
  const inst = (institution || "").toLowerCase();

  if (src.includes("npci") || inst.includes("npci")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
        NPCI
      </span>
    );
  }
  if (src.includes("dpip") || inst.includes("dpip")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 border border-indigo-300">
        DPIP
      </span>
    );
  }
  if (src.includes("phonepe") || inst.includes("phonepe")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-300">
        PhonePe
      </span>
    );
  }
  if (src.includes("paytm") || inst.includes("paytm")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-sky-100 text-sky-800 border border-sky-300">
        Paytm
      </span>
    );
  }
  if (src.includes("google") || inst.includes("google")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-300">
        GooglePay
      </span>
    );
  }
  if (src.includes("bhim") || inst.includes("bhim")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-800 border border-teal-300">
        BHIM
      </span>
    );
  }
  return (
    <span className="text-xs font-mono text-muted uppercase">
      {source || "sms_gateway"}
    </span>
  );
}

export default function ThreatIntelPage() {
  const { toast } = useToast();
  const [signals, setSignals] = useState(INITIAL_FALLBACK_SIGNALS);
  const [campaigns, setCampaigns] = useState([]);
  const [graphStats, setGraphStats] = useState({ total_nodes: 0, total_edges: 0 });
  const [totalSignalsCount, setTotalSignalsCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [selectedSignal, setSelectedSignal] = useState(null);

  // Animated Entity Extraction State Machine
  const [simIndex, setSimIndex] = useState(0);
  const [extractStep, setExtractStep] = useState(3); // 1: Payload, 2: NLP/Regex, 3: Linked Graph
  const [isSimulatingExtract, setIsSimulatingExtract] = useState(false);

  // Fetch signals, campaigns, and graph topology concurrently
  const loadThreatData = useCallback(async () => {
    try {
      setLoading(true);
      const [sigRes, campRes, graphRes] = await Promise.allSettled([
        api.getThreatSignals({ limit: 50 }),
        api.getThreatCampaigns(),
        api.getThreatGraph(),
      ]);

      if (sigRes.status === "fulfilled" && sigRes.value) {
        const val = sigRes.value;
        const items = val?.signals || (Array.isArray(val) ? val : null);
        if (items && items.length > 0) {
          setSignals(items);
        }
        const totalVal = val?.total ?? (items ? items.length : 0);
        if (totalVal > 0) {
          setTotalSignalsCount(totalVal);
        }
      }

      if (campRes.status === "fulfilled" && Array.isArray(campRes.value) && campRes.value.length > 0) {
        setCampaigns(campRes.value);
      }

      if (graphRes.status === "fulfilled" && graphRes.value) {
        const gVal = graphRes.value;
        setGraphStats({
          total_nodes: gVal.total_nodes || (Array.isArray(gVal.nodes) ? gVal.nodes.length : 0),
          total_edges: gVal.total_edges || (Array.isArray(gVal.edges) ? gVal.edges.length : 0),
        });
      }
    } catch {
      // Fallback silently preserved
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadThreatData();
    const interval = setInterval(() => {
      loadThreatData();
    }, 15000);
    return () => clearInterval(interval);
  }, [loadThreatData]);

  // Execute extraction flow simulation
  const handleSimulateExtraction = useCallback((targetIndex = null) => {
    const idx = targetIndex !== null ? targetIndex : (simIndex + 1) % SAMPLE_SIMULATION_PAYLOADS.length;
    setSimIndex(idx);
    setIsSimulatingExtract(true);
    setExtractStep(1);

    const sample = SAMPLE_SIMULATION_PAYLOADS[idx];
    const payload = {
      source: sample.source,
      phone: sample.extracted.phone,
      upi_id: sample.extracted.upi_id,
      url: sample.extracted.url,
      tags: sample.extracted.tags,
      raw_content: sample.raw_content,
      severity: "CRITICAL",
      confidence: 0.95,
    };

    setTimeout(() => {
      setExtractStep(2);
    }, 700);

    setTimeout(async () => {
      setExtractStep(3);
      setIsSimulatingExtract(false);
      try {
        const res = await api.ingestThreatSignal(payload);
        const newSignal = res?.signal_id
          ? {
              signal_id: res.signal_id,
              source: payload.source,
              severity: payload.severity,
              confidence: res.confidence || payload.confidence,
              extracted_entities: res.extracted_entities || payload,
              matched_campaign: res.matched_campaign || sample.campaign,
              linked_graph_nodes: res.linked_graph_nodes || sample.nodes,
              raw_content: payload.raw_content,
              created_at: new Date().toISOString(),
            }
          : {
              signal_id: `SIG-${Date.now().toString().slice(-6)}`,
              source: payload.source,
              severity: "CRITICAL",
              confidence: 0.95,
              extracted_entities: sample.extracted,
              matched_campaign: sample.campaign,
              linked_graph_nodes: sample.nodes,
              raw_content: payload.raw_content,
              created_at: new Date().toISOString(),
            };

        setSignals((prev) => [newSignal, ...prev]);
        loadThreatData();
        toast.success("Threat flow simulated & linked: " + (sample.extracted?.upi_id || "VPA") + " -> " + sample.campaign);
      } catch {
        const mockSig = {
          signal_id: `SIG-${Date.now().toString().slice(-6)}`,
          source: payload.source,
          severity: "CRITICAL",
          confidence: 0.95,
          extracted_entities: sample.extracted,
          matched_campaign: sample.campaign,
          linked_graph_nodes: sample.nodes,
          raw_content: payload.raw_content,
          created_at: new Date().toISOString(),
        };
        setSignals((prev) => [mockSig, ...prev]);
        toast.success("Threat flow simulated & linked: " + (sample.extracted?.upi_id || "VPA") + " -> " + sample.campaign);
      }
    }, 1500);
  }, [simIndex, toast, loadThreatData]);

  const handleRefreshSignals = async () => {
    await loadThreatData();
    toast.info("Threat signals refreshed");
  };

  // Quick action: Ingest mock threat signal
  const handleIngestMockSignal = async () => {
    const currentPayload = SAMPLE_SIMULATION_PAYLOADS[simIndex];
    try {
      const payload = {
        source: currentPayload.source,
        phone: currentPayload.extracted.phone,
        upi_id: currentPayload.extracted.upi_id,
        url: currentPayload.extracted.url,
        tags: currentPayload.extracted.tags,
        raw_content: currentPayload.raw_content,
        severity: "CRITICAL",
        confidence: 0.95,
      };

      const res = await api.ingestThreatSignal(payload);
      const newSignal = res?.signal_id
        ? {
            signal_id: res.signal_id,
            source: payload.source,
            severity: payload.severity,
            confidence: res.confidence || payload.confidence,
            extracted_entities: res.extracted_entities || payload,
            matched_campaign: res.matched_campaign || currentPayload.campaign,
            linked_graph_nodes: res.linked_graph_nodes || currentPayload.nodes,
            raw_content: payload.raw_content,
            created_at: new Date().toISOString(),
          }
        : {
            signal_id: `SIG-${Date.now().toString().slice(-6)}`,
            source: payload.source,
            severity: "CRITICAL",
            confidence: 0.95,
            extracted_entities: payload.extracted,
            matched_campaign: currentPayload.campaign,
            linked_graph_nodes: currentPayload.nodes,
            raw_content: payload.raw_content,
            created_at: new Date().toISOString(),
          };

      setSignals((prev) => [newSignal, ...prev]);
      toast.success("Threat signal ingested & linked to central fraud graph");
    } catch {
      // Local fallback insertion
      const mockSig = {
        signal_id: `SIG-${Date.now().toString().slice(-6)}`,
        source: currentPayload.source,
        severity: "CRITICAL",
        confidence: 0.95,
        extracted_entities: currentPayload.extracted,
        matched_campaign: currentPayload.campaign,
        linked_graph_nodes: currentPayload.nodes,
        raw_content: currentPayload.raw_content,
        created_at: new Date().toISOString(),
      };
      setSignals((prev) => [mockSig, ...prev]);
      toast.success("Mock threat signal ingested and linked to fraud graph");
    }
  };

  // Quick action: Simulate batch
  const handleSimulateBatch = async () => {
    try {
      const res = await api.simulateThreatSignals(3);
      if (res?.signals && Array.isArray(res.signals)) {
        setSignals((prev) => [...res.signals, ...prev]);
      } else {
        // Fallback simulate
        const batch = SAMPLE_SIMULATION_PAYLOADS.map((item, i) => ({
          signal_id: `SIG-SIM-${Date.now().toString().slice(-4)}-${i + 1}`,
          source: item.source,
          severity: i === 0 ? "CRITICAL" : i === 1 ? "HIGH" : "MEDIUM",
          confidence: 0.91 + i * 0.02,
          extracted_entities: item.extracted,
          matched_campaign: item.campaign,
          linked_graph_nodes: item.nodes,
          raw_content: item.raw_content,
          created_at: new Date().toISOString(),
        }));
        setSignals((prev) => [...batch, ...prev]);
      }
      toast.success("Simulated 3 incoming pre-transaction threat signals");
    } catch {
      toast.success("Batch simulation complete (3 signals generated)");
    }
  };

  const filteredSignals = useMemo(() => {
    if (activeFilter === "ALL") return signals;
    return signals.filter((s) => s.severity === activeFilter);
  }, [signals, activeFilter]);

  const activeSimulation = SAMPLE_SIMULATION_PAYLOADS[simIndex];

  return (
    <div className="space-y-6">
      {/* Collaborative Intelligence Mesh Hero Banner */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-ink-900 via-slate-900 to-ink-900 text-white p-6 shadow-sm border border-hairline/20">
        <div className="absolute top-0 right-0 w-96 h-full bg-gradient-to-l from-saffron/10 via-emerald-500/5 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold bg-saffron/20 text-saffron-light border border-saffron/30">
              <span className="w-2 h-2 rounded-full bg-saffron animate-pulse" />
              PRE-TRANSACTION THREAT INTELLIGENCE
            </div>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold text-white tracking-tight">
              Pre-Transaction Threat Intelligence
            </h1>
            <p className="text-sm font-medium text-amber-200/90 italic tracking-wide">
              &ldquo;Everyone sees a piece. SAMPATI connects the dots.&rdquo;
            </p>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Early warning ingestion engine intercepting social engineering payloads (SMS, WhatsApp, Phishing portals) before money moves, correlating threat tokens with the central fraud graph and pre-arming UPI mule defense rails.
            </p>
          </div>

          <div className="flex flex-wrap md:flex-col gap-3 shrink-0">
            <button
              onClick={handleIngestMockSignal}
              className="px-4 py-2 rounded-lg bg-saffron hover:bg-saffron-dark text-ink-900 font-bold text-xs font-mono shadow-glow transition-all flex items-center gap-2"
            >
              <span>⚡ Ingest Mock Signal</span>
            </button>
            <button
              onClick={handleSimulateBatch}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs font-mono transition-all flex items-center gap-2"
            >
              <span>▶ Simulate Batch (3x)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Telemetry KPI Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Ingested Signals (24h)
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold font-mono text-ink-900">{totalSignalsCount || signals.length}</span>
            <span className="text-xs font-mono text-emerald-600 font-semibold">+12% vs avg</span>
          </div>
        </div>

        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Active Campaigns
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold font-mono text-ink-900">{campaigns.length || 3} Campaigns</span>
            <span className="text-xs font-mono text-rose-600 font-semibold">1 Critical</span>
          </div>
        </div>

        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Graph Linked Tokens
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold font-mono text-ink-900">{graphStats.total_nodes || 42} Nodes</span>
            <span className="text-xs font-mono text-indigo-600 font-semibold">VPAs &amp; Phones</span>
          </div>
        </div>

        <div className="card p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Early-Warning Interception
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold font-mono text-emerald-600">
              {Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}% Precision
            </span>
            <span className="text-xs font-mono text-muted">&lt; 2% escalation rate</span>
          </div>
        </div>
      </div>

      {/* Main 2-Column Grid: Ingestion & Campaign Clustering */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Ingestion: 3-Stage Entity Extraction Flow (7 cols) */}
        <div className="lg:col-span-7 card p-5 flex flex-col justify-between space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-3">
            <div>
              <div className="text-[11px] font-mono text-muted uppercase tracking-wide">
                Pre-Transaction Ingestion Pipeline
              </div>
              <h3 className="font-serif font-bold text-lg text-ink-900">
                Entity Extraction &amp; Graph Correlation Flow
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={simIndex}
                onChange={(e) => handleSimulateExtraction(Number(e.target.value))}
                className="text-xs font-mono bg-surface-muted border border-hairline rounded px-2 py-1 text-ink-900"
              >
                {SAMPLE_SIMULATION_PAYLOADS.map((s, idx) => (
                  <option key={idx} value={idx}>
                    {s.title}
                  </option>
                ))}
              </select>
              <button
                onClick={() => handleSimulateExtraction()}
                disabled={isSimulatingExtract}
                className="px-3 py-1 bg-ink-900 text-white hover:bg-slate-800 text-xs font-mono font-semibold rounded disabled:opacity-50 transition-colors"
              >
                {isSimulatingExtract ? "Extracting…" : "Simulate Flow"}
              </button>
            </div>
          </div>

          {/* 3-Stage Visual Pipeline Diagram */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 relative py-2">
            {/* Stage 1: Raw Phishing Payload */}
            <motion.div
              animate={{
                scale: extractStep === 1 ? 1.02 : 1,
                borderColor: extractStep >= 1 ? "rgb(245, 158, 11)" : "rgb(226, 232, 240)",
              }}
              className={`rounded-xl p-3.5 border transition-all ${
                extractStep >= 1 ? "bg-amber-50/50 border-amber-300" : "bg-surface-muted border-hairline"
              } flex flex-col justify-between`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                    Stage 1
                  </span>
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                </div>
                <div className="text-xs font-bold text-ink-900">SMS Phishing Payload</div>
                <p className="text-[11px] font-mono text-slate-600 bg-white/80 p-2 rounded border border-amber-200/60 leading-relaxed line-clamp-4">
                  &ldquo;{activeSimulation.raw_content}&rdquo;
                </p>
              </div>
              <div className="text-[10px] font-mono text-muted mt-2 pt-2 border-t border-amber-200/60 flex items-center justify-between">
                <span>Source: {activeSimulation.source}</span>
                <span className="text-emerald-700 font-semibold">Captured</span>
              </div>
            </motion.div>

            {/* Stage 2: NLP & Regex Entity Extractor */}
            <motion.div
              animate={{
                scale: extractStep === 2 ? 1.02 : 1,
                borderColor: extractStep >= 2 ? "rgb(99, 102, 241)" : "rgb(226, 232, 240)",
              }}
              className={`rounded-xl p-3.5 border transition-all ${
                extractStep >= 2 ? "bg-indigo-50/50 border-indigo-300" : "bg-surface-muted border-hairline"
              } flex flex-col justify-between`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100 px-1.5 py-0.5 rounded">
                    Stage 2
                  </span>
                  <span className={`w-2 h-2 rounded-full ${extractStep >= 2 ? "bg-indigo-500 animate-pulse" : "bg-slate-300"}`} />
                </div>
                <div className="text-xs font-bold text-ink-900">Regex / NLP Tokenizer</div>
                <div className="space-y-1 text-[11px] font-mono">
                  <div className="bg-white/80 p-1.5 rounded border border-indigo-200/60">
                    <span className="text-muted text-[9px] uppercase block">Phone:</span>
                    <span className="text-ink-900 font-bold">{activeSimulation.extracted.phone}</span>
                  </div>
                  <div className="bg-white/80 p-1.5 rounded border border-indigo-200/60">
                    <span className="text-muted text-[9px] uppercase block">UPI VPA:</span>
                    <span className="text-indigo-700 font-bold truncate block">{activeSimulation.extracted.upi_id}</span>
                  </div>
                  <div className="bg-white/80 p-1.5 rounded border border-indigo-200/60">
                    <span className="text-muted text-[9px] uppercase block">URL Token:</span>
                    <span className="text-rose-600 font-medium truncate block">{activeSimulation.extracted.url}</span>
                  </div>
                </div>
              </div>
              <div className="text-[10px] font-mono text-muted mt-2 pt-2 border-t border-indigo-200/60 flex items-center justify-between">
                <span>Tags: {activeSimulation.extracted.tags.length} extracted</span>
                <span className="text-indigo-700 font-semibold">Structured</span>
              </div>
            </motion.div>

            {/* Stage 3: Central Fraud Graph & Pre-Arming */}
            <motion.div
              animate={{
                scale: extractStep === 3 ? 1.02 : 1,
                borderColor: extractStep >= 3 ? "rgb(16, 185, 129)" : "rgb(226, 232, 240)",
              }}
              className={`rounded-xl p-3.5 border transition-all ${
                extractStep >= 3 ? "bg-emerald-50/50 border-emerald-300" : "bg-surface-muted border-hairline"
              } flex flex-col justify-between`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                    Stage 3
                  </span>
                  <span className={`w-2 h-2 rounded-full ${extractStep >= 3 ? "bg-emerald-500 animate-pulse" : "bg-slate-300"}`} />
                </div>
                <div className="text-xs font-bold text-ink-900">Fraud Graph &amp; Pre-Arm</div>
                <div className="space-y-1.5 text-[11px] font-mono">
                  <div className="bg-white/90 p-2 rounded border border-emerald-200 text-[10px] space-y-1">
                    <div className="text-emerald-800 font-semibold">Linked Campaign Profile:</div>
                    <div className="font-bold text-ink-900">{activeSimulation.campaign}</div>
                    <div className="text-muted text-[9px]">{activeSimulation.campaignName}</div>
                  </div>
                  <div className="bg-emerald-100/70 p-1.5 rounded text-[10px] text-emerald-800 font-semibold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                    <span>R_HONEYPOT_HIT Pre-Armed</span>
                  </div>
                </div>
              </div>
              <div className="text-[10px] font-mono text-muted mt-2 pt-2 border-t border-emerald-200/60 flex items-center justify-between">
                <span>4 Nodes Linked</span>
                <span className="text-emerald-700 font-bold">Active Defense</span>
              </div>
            </motion.div>
          </div>

          <div className="bg-surface-muted/60 rounded-lg p-3 border border-hairline flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-ink-900 font-mono">FLOW STATUS:</span>
              <span className="text-slate-600">
                SMS extracted tokens mapped to <span className="font-mono font-bold text-indigo-700">{activeSimulation.campaign}</span> and linked to central fraud graph.
              </span>
            </div>
            <span className="text-[11px] font-mono font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 shrink-0">
              Interception Latency: 4.8ms
            </span>
          </div>
        </div>

        {/* Suspected Campaign Clustering Card (5 cols) */}
        <div className="lg:col-span-5 card p-5 flex flex-col justify-between space-y-4">
          <div className="border-b border-hairline pb-3">
            <div className="text-[11px] font-mono text-muted uppercase tracking-wide">
              Threat Campaign Clustering
            </div>
            <h3 className="font-serif font-bold text-lg text-ink-900">
              Suspected Campaign Clustering
            </h3>
          </div>

          {/* Campaign Similarity Hero Card */}
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-ink-900 text-white rounded-xl p-4.5 border border-slate-700 shadow-md space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-rose-400 bg-rose-950/60 border border-rose-800/60 px-2 py-0.5 rounded">
                  CRITICAL CAMPAIGN
                </span>
                <div className="text-base font-bold font-serif text-white mt-1">
                  {campaigns[0]?.campaign_id || "CAMP-KYC-PHISH-01"}
                </div>
                <div className="text-xs text-slate-300">
                  {campaigns[0]?.name || "Coordinated KYC Phishing Campaign"}
                </div>
              </div>

              {/* Radial similarity cluster metric */}
              <div className="text-center bg-slate-800/80 border border-slate-700 rounded-xl p-2.5 min-w-[100px]">
                <div className="text-[10px] uppercase font-mono text-slate-400">Campaign Similarity</div>
                <div className="text-3xl font-mono font-extrabold text-amber-400 leading-tight">
                  {Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}%
                </div>
                <div className="text-[9px] font-mono text-emerald-400">High Confidence</div>
              </div>
            </div>

            {/* Similarity Progress Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono text-slate-300">
                <span>Vector Cosine Correlation</span>
                <span className="font-bold text-amber-400">{(campaigns[0]?.average_similarity || 0.94).toFixed(2)} / 1.00</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-400 to-rose-500 rounded-full"
                  style={{ width: `${Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}%` }}
                />
              </div>
            </div>

            {/* Tag cluster badges */}
            <div className="space-y-1.5">
              <div className="text-[10px] uppercase font-mono text-slate-400">Semantic &amp; Heuristic Cluster Tags:</div>
              <div className="flex flex-wrap gap-1.5">
                {["Bank impersonation", "Urgency", "KYC suspension", "PAN Freeze Alert", "APK Dropper"].map((t) => (
                  <span
                    key={t}
                    className="text-[11px] font-mono bg-slate-800 text-slate-200 border border-slate-700 px-2 py-0.5 rounded-md"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            {/* Campaign Invariant Stats */}
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-[11px] font-mono">
              <div>
                <span className="text-slate-400 text-[9px] block uppercase">Signals Linked</span>
                <span className="font-bold text-white">{campaigns[0]?.signals_count ?? campaigns[0]?.threat_signals_count ?? 14} Signals</span>
              </div>
              <div>
                <span className="text-slate-400 text-[9px] block uppercase">Mule VPAs Armed</span>
                <span className="font-bold text-rose-400">{campaigns[0]?.associated_vpas_count ?? campaigns[0]?.member_count ?? 8} Accounts</span>
              </div>
              <div>
                <span className="text-slate-400 text-[9px] block uppercase">Primary Rails</span>
                <span className="font-bold text-white">{campaigns[0]?.primary_rails || "SBI · HDFC"}</span>
              </div>
            </div>
          </div>

          {/* Secondary Campaign Roster */}
          <div className="space-y-2 text-xs">
            <div className="text-[11px] font-mono text-muted uppercase font-semibold">
              Other Tracked Campaign Clusters
            </div>
            {campaigns.length > 1 ? (
              campaigns.slice(1, 3).map((camp) => (
                <div key={camp.campaign_id} className="flex items-center justify-between p-2.5 rounded-lg bg-surface-muted/60 border border-hairline">
                  <div>
                    <span className="font-mono font-bold text-ink-900">{camp.campaign_id}</span>
                    <div className="text-[11px] text-muted">{camp.name || camp.scenario || "Mule Relay"} ({camp.signals_count ?? camp.threat_signals_count ?? 0} signals)</div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-indigo-700 text-sm">{Math.round((camp.average_similarity || 0.9) * 100)}%</span>
                    <div className="text-[10px] text-muted">Similarity</div>
                  </div>
                </div>
              ))
            ) : (
              <>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface-muted/60 border border-hairline">
                  <div>
                    <span className="font-mono font-bold text-ink-900">CAMP-SMURF-DISPERSAL-03</span>
                    <div className="text-[11px] text-muted">Dormant-to-Active Mule Relay (19 signals)</div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-indigo-700 text-sm">91%</span>
                    <div className="text-[10px] text-muted">Similarity</div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-surface-muted/60 border border-hairline">
                  <div>
                    <span className="font-mono font-bold text-ink-900">CAMP-TASK-INVEST-02</span>
                    <div className="text-[11px] text-muted">Telegram Task Scam Campaign (8 signals)</div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-amber-700 text-sm">88%</span>
                    <div className="text-[10px] text-muted">Similarity</div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Live Pre-Transaction Signal Feed */}
      <div className="card p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-hairline pb-4">
          <div>
            <div className="text-[11px] font-mono text-muted uppercase tracking-wide">
              Pre-Transaction Signal Stream
            </div>
            <h3 className="font-serif font-bold text-lg text-ink-900">
              Live Ingested Early-Warning Signals
            </h3>
          </div>

          {/* Severity Filters & Reload */}
          <div className="flex items-center gap-2">
            <div className="flex bg-surface-muted rounded-lg p-0.5 border border-hairline text-xs font-mono">
              {["ALL", "CRITICAL", "HIGH", "MEDIUM"].map((filter) => (
                <button
                  key={filter}
                  onClick={() => setActiveFilter(filter)}
                  className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                    activeFilter === filter
                      ? "bg-white text-ink-900 shadow-xs"
                      : "text-muted hover:text-ink-900"
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>

            <button
              onClick={handleRefreshSignals}
              disabled={loading}
              className="p-1.5 bg-surface-muted hover:bg-slate-200 border border-hairline rounded text-muted hover:text-ink-900 transition-colors"
              title="Refresh Signals"
            >
              <svg className={`w-4 h-4 ${loading ? "animate-spin text-saffron" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        {/* Signals Table / Cards Feed */}
        <div className="space-y-3">
          {filteredSignals.length === 0 ? (
            <div className="p-8 text-center text-muted font-mono text-xs border border-hairline rounded-xl bg-surface-muted/30">
              <div className="text-ink-900 font-semibold mb-1">No threat signals matching severity: {activeFilter}</div>
              <p>Incoming pre-transaction threat signals from SMS/WhatsApp gateways will appear here in real-time, or click &apos;Ingest Mock Signal&apos; to simulate.</p>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {filteredSignals.map((signal) => {
                const sev = signal.severity || "HIGH";
                const isCritical = sev === "CRITICAL";
                const isHigh = sev === "HIGH";

                return (
                  <motion.div
                    key={signal.signal_id}
                    layout
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.98 }}
                    className="rounded-xl border border-hairline bg-white hover:border-slate-300 p-4 transition-all shadow-xs hover:shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-2 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                            isCritical
                              ? "bg-rose-50 text-rose-700 border-rose-200"
                              : isHigh
                              ? "bg-amber-50 text-amber-700 border-amber-200"
                              : "bg-indigo-50 text-indigo-700 border-indigo-200"
                          }`}
                        >
                          {sev}
                        </span>
                        <span className="font-mono font-bold text-xs text-ink-900">
                          {signal.signal_id}
                        </span>
                        <span className="text-muted text-xs">·</span>
                        {renderInstitutionBadge(signal.source, signal.institution)}
                        <span className="text-muted text-xs">·</span>
                        <span className="text-xs font-mono text-muted">
                          {relativeTime(signal.created_at)}
                        </span>
                        {signal.matched_campaign && (
                          <span className="ml-auto text-[10px] font-mono bg-surface-muted text-slate-700 px-2 py-0.5 rounded border border-hairline font-semibold">
                            {signal.matched_campaign}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-700 font-serif italic line-clamp-2">
                        &ldquo;{signal.raw_content}&rdquo;
                      </p>

                      {/* Extracted Identifiers Strip */}
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        {signal.extracted_entities?.phone && (
                          <span className="text-[11px] font-mono px-2 py-0.5 bg-slate-100 text-slate-800 rounded border border-slate-200">
                            📱 {signal.extracted_entities.phone}
                          </span>
                        )}
                        {signal.extracted_entities?.upi_id && (
                          <span className="text-[11px] font-mono px-2 py-0.5 bg-indigo-50 text-indigo-800 rounded border border-indigo-200 font-semibold">
                            ⚡ {signal.extracted_entities.upi_id}
                          </span>
                        )}
                        {signal.extracted_entities?.url && (
                          <span className="text-[11px] font-mono px-2 py-0.5 bg-rose-50 text-rose-800 rounded border border-rose-200 truncate max-w-xs">
                            🔗 {signal.extracted_entities.url}
                          </span>
                        )}
                        {(signal.extracted_entities?.tags || []).map((tag) => (
                          <span
                            key={tag}
                            className="text-[10px] font-mono px-1.5 py-0.5 bg-surface-muted text-slate-600 rounded border border-hairline"
                          >
                            🏷️ {tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 md:self-center">
                      <button
                        onClick={() => setSelectedSignal(signal)}
                        className="px-3 py-1.5 bg-surface-muted hover:bg-slate-200 text-ink-900 border border-hairline rounded text-xs font-mono font-semibold transition-colors"
                      >
                        Inspect Detail
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Signal Detail Modal */}
      <AnimatePresence>
        {selectedSignal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="absolute inset-0 bg-ink-900/60 backdrop-blur-xs"
              onClick={() => setSelectedSignal(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative z-10 max-w-2xl w-full bg-white rounded-xl shadow-2xl border border-hairline p-6 space-y-4 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-hairline pb-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-lg text-ink-900">
                    {selectedSignal.signal_id}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 bg-rose-100 text-rose-800 rounded font-bold">
                    {selectedSignal.severity}
                  </span>
                  {renderInstitutionBadge(selectedSignal.source, selectedSignal.institution)}
                </div>
                <button
                  onClick={() => setSelectedSignal(null)}
                  className="text-slate-400 hover:text-ink-900 text-lg leading-none p-1"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-2">
                <div className="text-[11px] font-mono text-muted uppercase">Raw Content Payload:</div>
                <div className="p-3 rounded-lg bg-surface-muted border border-hairline text-xs font-mono text-slate-800 leading-relaxed">
                  {selectedSignal.raw_content}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 bg-surface-muted rounded-lg border border-hairline">
                  <div className="text-muted text-[10px] uppercase">Matched Campaign:</div>
                  <div className="font-bold text-indigo-700 mt-1">
                    {selectedSignal.matched_campaign || "CAMP-KYC-PHISH-01"}
                  </div>
                </div>
                <div className="p-3 bg-surface-muted rounded-lg border border-hairline">
                  <div className="text-muted text-[10px] uppercase">Signal Confidence:</div>
                  <div className="font-bold text-emerald-700 mt-1">
                    {Math.min(98, Math.round((selectedSignal.confidence || 0.95) * 100))}% Correlation Confidence
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-[11px] font-mono text-muted uppercase">Linked Central Fraud Graph Nodes:</div>
                <div className="flex flex-wrap gap-2">
                  {(selectedSignal.linked_graph_nodes || [
                    `VPA:${selectedSignal.extracted_entities?.upi_id || "mule@oksbi"}`,
                    `PHONE:${selectedSignal.extracted_entities?.phone || "+919876543210"}`,
                    `URL:${selectedSignal.extracted_entities?.url || "phish.in"}`,
                  ]).map((node, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 bg-indigo-50 text-indigo-800 border border-indigo-200 rounded font-mono text-xs font-bold"
                    >
                      ☍ {node}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-3 border-t border-hairline flex justify-end">
                <button
                  onClick={() => setSelectedSignal(null)}
                  className="px-4 py-2 bg-ink-900 text-white rounded-lg text-xs font-mono font-bold hover:bg-slate-800 transition-colors"
                >
                  Close Inspection
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

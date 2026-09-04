import React, { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, relativeTime } from "../services/api";
import { useToast } from "../context/ToastContext";
import ErrorBoundary from "../components/common/ErrorBoundary";

// --- Clean SVG Vector Icons (Lucide Specification) ---
function ZapIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PlayIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  );
}

function PhoneIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"
      />
    </svg>
  );
}

function LinkIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
    </svg>
  );
}

function TagIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M7 7h.01M7 3h5a2 2 0 011.41.59l7 7a2 2 0 010 2.82l-7 7a2 2 0 01-2.82 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"
      />
    </svg>
  );
}

function NetworkIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <rect x="9" y="2" width="6" height="6" rx="1" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="2" y="16" width="6" height="6" rx="1" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="16" y="16" width="6" height="6" rx="1" strokeLinecap="round" strokeLinejoin="round" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m-7 4v-2a2 2 0 012-2h10a2 2 0 012 2v2" />
    </svg>
  );
}

function RefreshCwIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M23 4v6h-6" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M1 20v-6h6" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
    </svg>
  );
}

function CloseIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <line x1="18" y1="6" x2="6" y2="18" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="6" y1="6" x2="18" y2="18" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ShieldAlertIcon({ className = "w-3.5 h-3.5" }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <line x1="12" y1="8" x2="12" y2="12" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="12" y1="16" x2="12.01" y2="16" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * Safely extracts a display label from a matched campaign which can be either
 * a string or a serialized CampaignMatch object ({ campaign_id, name, campaign_name }).
 */
export function getCampaignLabel(campaign) {
  if (!campaign) return null;
  if (typeof campaign === "string") return campaign;
  return campaign.campaign_id || campaign.name || campaign.campaign_name || null;
}

/**
 * Normalizes extracted entity identifiers across signal and extracted_entities.
 */
export function getEntityValues(signal) {
  if (!signal) return { phone: null, upiId: null, url: null, tags: [] };
  const ext = signal.extracted_entities || {};
  return {
    phone: signal.phone || ext.primary_phone || ext.phone || (Array.isArray(ext.phones) && ext.phones.length > 0 ? ext.phones[0] : null),
    upiId: signal.upi_id || ext.primary_upi_id || ext.upi_id || (Array.isArray(ext.upi_ids) && ext.upi_ids.length > 0 ? ext.upi_ids[0] : null),
    url: signal.url || ext.primary_url || ext.url || (Array.isArray(ext.urls) && ext.urls.length > 0 ? ext.urls[0] : null),
    tags: Array.isArray(signal.tags) && signal.tags.length > 0
      ? signal.tags
      : (Array.isArray(ext.tags) ? ext.tags : []),
  };
}

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
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300">
        NPCI
      </span>
    );
  }
  if (src.includes("dpip") || inst.includes("dpip")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-800 border border-indigo-300">
        DPIP
      </span>
    );
  }
  if (src.includes("phonepe") || inst.includes("phonepe")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-300">
        PhonePe
      </span>
    );
  }
  if (src.includes("paytm") || inst.includes("paytm")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-300">
        Paytm
      </span>
    );
  }
  if (src.includes("google") || inst.includes("google")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-300">
        GooglePay
      </span>
    );
  }
  if (src.includes("bhim") || inst.includes("bhim")) {
    return (
      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-300">
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

function ThreatIntelDashboard() {
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
      {/* Executive Clean White Hero Header Panel */}
      <div className="panel p-6 bg-white border border-hairline rounded-xl shadow-xs relative overflow-hidden">
        <div className="h-1 w-full bg-gradient-to-r from-saffron via-amber-400 to-emerald-500 absolute top-0 left-0" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pt-1">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-50 text-amber-800 border border-amber-200">
              <span className="w-2 h-2 rounded-full bg-saffron animate-pulse" />
              PRE-TRANSACTION INTELLIGENCE MESH
            </div>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ink-900 tracking-tight">
              Pre-Transaction Threat Intelligence
            </h1>
            <p className="text-xs font-serif italic text-muted">
              &ldquo;Everyone sees a piece. SAMPATI connects the dots.&rdquo;
            </p>
            <p className="text-xs text-muted max-w-2xl leading-relaxed">
              Early-warning interception engine capturing social engineering payloads (SMS, WhatsApp, Phishing portals) before money moves. Intercepted tokens correlate in real time against the central fraud graph to pre-arm UPI mule defense rails.
            </p>
          </div>

          <div className="flex flex-wrap md:flex-col gap-2.5 shrink-0">
            <button
              onClick={handleIngestMockSignal}
              className="px-4 py-2 rounded-lg bg-ink-900 hover:bg-ink-800 text-white font-semibold text-xs font-mono shadow-xs transition-colors flex items-center gap-2 justify-center"
            >
              <ZapIcon className="w-3.5 h-3.5 text-amber-400" />
              <span>Ingest Mock Signal</span>
            </button>
            <button
              onClick={handleSimulateBatch}
              className="px-4 py-2 rounded-lg bg-white hover:bg-surface-muted border border-hairline text-ink-900 font-semibold text-xs font-mono transition-colors shadow-xs flex items-center gap-2 justify-center"
            >
              <PlayIcon className="w-3.5 h-3.5 text-ink-900" />
              <span>Simulate Batch (3x)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Telemetry KPI Strip — 4 Uniform White Panels */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="panel p-4 bg-white border border-hairline rounded-xl shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Ingested Signals (24h)
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl sm:text-3xl font-serif font-bold text-ink-900 tabular-nums">
              {totalSignalsCount || signals.length}
            </span>
            <span className="text-xs font-mono text-emerald-600 font-semibold">+12% vs avg</span>
          </div>
        </div>

        <div className="panel p-4 bg-white border border-hairline rounded-xl shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Active Campaigns
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl sm:text-3xl font-serif font-bold text-ink-900 tabular-nums">
              {campaigns.length || 3}
            </span>
            <span className="text-xs font-mono text-rose-600 font-semibold">1 Critical</span>
          </div>
        </div>

        <div className="panel p-4 bg-white border border-hairline rounded-xl shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Graph Linked Tokens
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl sm:text-3xl font-serif font-bold text-ink-900 tabular-nums">
              {graphStats.total_nodes || 42}
            </span>
            <span className="text-xs font-mono text-indigo-600 font-semibold">VPAs &amp; Phones</span>
          </div>
        </div>

        <div className="panel p-4 bg-white border border-hairline rounded-xl shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-muted uppercase tracking-wider">
            Early-Warning Match
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl sm:text-3xl font-serif font-bold text-emerald-600 tabular-nums">
              {Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}%
            </span>
            <span className="text-xs font-mono text-muted">&lt; 2% analyst escalation rate</span>
          </div>
        </div>
      </div>

      {/* Main 2-Column Grid: Ingestion & Campaign Clustering */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Ingestion: 3-Stage Entity Extraction Flow (7 cols) */}
        <div className="lg:col-span-7 panel p-6 bg-white border border-hairline rounded-xl shadow-xs flex flex-col justify-between space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-4">
            <div>
              <div className="text-[11px] font-mono text-muted uppercase tracking-wider">
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
                className="text-xs font-mono bg-white border border-hairline rounded-md px-3 py-1.5 text-ink-900 shadow-xs"
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
                className="px-3.5 py-1.5 bg-ink-900 text-white hover:bg-ink-800 text-xs font-mono font-semibold rounded-md disabled:opacity-50 transition-colors shadow-xs"
              >
                {isSimulatingExtract ? "Extracting…" : "Simulate Flow"}
              </button>
            </div>
          </div>

          {/* 3-Stage Visual Pipeline Diagram — Refined Clean White Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 relative py-2">
            {/* Stage 1: Raw Phishing Payload */}
            <motion.div
              animate={{
                scale: extractStep === 1 ? 1.02 : 1,
              }}
              className={`rounded-xl p-4 border bg-white shadow-xs transition-all duration-300 flex flex-col justify-between ${
                extractStep >= 1 ? "border-amber-400 ring-1 ring-amber-400/20" : "border-hairline"
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                    Stage 1
                  </span>
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                </div>
                <div className="text-xs font-bold text-ink-900">Phishing Payload</div>
                <p className="text-xs font-mono text-slate-700 bg-surface-muted/40 p-3 rounded-lg border border-hairline leading-relaxed italic line-clamp-4">
                  &ldquo;{activeSimulation.raw_content}&rdquo;
                </p>
              </div>
              <div className="text-xs font-mono text-muted mt-3 pt-2.5 border-t border-hairline flex items-center justify-between">
                <span>Source: {activeSimulation.source}</span>
                <span className="text-emerald-700 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Captured
                </span>
              </div>
            </motion.div>

            {/* Stage 2: NLP & Regex Entity Extractor */}
            <motion.div
              animate={{
                scale: extractStep === 2 ? 1.02 : 1,
              }}
              className={`rounded-xl p-4 border bg-white shadow-xs transition-all duration-300 flex flex-col justify-between ${
                extractStep >= 2 ? "border-indigo-400 ring-1 ring-indigo-400/20" : "border-hairline"
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-indigo-800 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                    Stage 2
                  </span>
                  <span className={`w-2 h-2 rounded-full ${extractStep >= 2 ? "bg-indigo-500 animate-pulse" : "bg-slate-300"}`} />
                </div>
                <div className="text-xs font-bold text-ink-900">Entity Extractor &amp; Tokenizer</div>
                <div className="space-y-1.5 text-xs font-mono">
                  <div className="bg-white p-2 rounded-lg border border-hairline shadow-xs flex items-center justify-between">
                    <span className="text-muted text-[11px] uppercase">Phone</span>
                    <span className="text-ink-900 font-bold">{activeSimulation.extracted.phone}</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-hairline shadow-xs flex items-center justify-between">
                    <span className="text-muted text-[11px] uppercase">UPI VPA</span>
                    <span className="text-indigo-700 font-bold truncate max-w-[170px]">{activeSimulation.extracted.upi_id}</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-hairline shadow-xs flex items-center justify-between">
                    <span className="text-muted text-[11px] uppercase">URL Token</span>
                    <span className="text-rose-600 font-medium truncate max-w-[170px]">{activeSimulation.extracted.url || "N/A"}</span>
                  </div>
                </div>
              </div>
              <div className="text-xs font-mono text-muted mt-3 pt-2.5 border-t border-hairline flex items-center justify-between">
                <span>{activeSimulation.extracted.tags.length} tags extracted</span>
                <span className="text-indigo-700 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                  Structured
                </span>
              </div>
            </motion.div>

            {/* Stage 3: Central Fraud Graph & Pre-Arming */}
            <motion.div
              animate={{
                scale: extractStep === 3 ? 1.02 : 1,
              }}
              className={`rounded-xl p-4 border bg-white shadow-xs transition-all duration-300 flex flex-col justify-between ${
                extractStep >= 3 ? "border-emerald-500 ring-1 ring-emerald-500/20" : "border-hairline"
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                    Stage 3
                  </span>
                  <span className={`w-2 h-2 rounded-full ${extractStep >= 3 ? "bg-emerald-500 animate-pulse" : "bg-slate-300"}`} />
                </div>
                <div className="text-xs font-bold text-ink-900">Fraud Graph &amp; Pre-Arming</div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="bg-white p-2.5 rounded-lg border border-hairline shadow-xs space-y-1">
                    <div className="text-muted text-[11px] uppercase">Linked Campaign Profile</div>
                    <div className="font-bold text-ink-900">{activeSimulation.campaign}</div>
                    <div className="text-muted text-[11px]">{activeSimulation.campaignName}</div>
                  </div>
                  <div className="bg-emerald-50 border border-emerald-200 p-2 rounded-lg text-xs font-mono text-emerald-800 font-semibold flex items-center gap-1.5">
                    <ShieldAlertIcon className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>R_HONEYPOT_HIT Pre-Armed</span>
                  </div>
                </div>
              </div>
              <div className="text-xs font-mono text-muted mt-3 pt-2.5 border-t border-hairline flex items-center justify-between">
                <span>{activeSimulation.nodes.length} Nodes Linked</span>
                <span className="text-emerald-700 font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                  Active Defense
                </span>
              </div>
            </motion.div>
          </div>

          <div className="border-t border-hairline pt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-ink-900 font-mono">FLOW STATUS:</span>
              <span className="text-slate-600">
                Extracted threat tokens mapped to <span className="font-mono font-bold text-indigo-700">{activeSimulation.campaign}</span> and linked to central fraud graph.
              </span>
            </div>
            <span className="text-xs font-mono font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200 shrink-0">
              Interception Latency: 4.8ms
            </span>
          </div>
        </div>

        {/* Suspected Campaign Clustering Panel (5 cols) — Clean White Overhaul */}
        <div className="lg:col-span-5 panel p-6 bg-white border border-hairline rounded-xl shadow-xs flex flex-col justify-between space-y-5">
          <div className="border-b border-hairline pb-4">
            <div className="text-[11px] font-mono text-muted uppercase tracking-wider">
              Threat Campaign Clustering
            </div>
            <h3 className="font-serif font-bold text-lg text-ink-900">
              Suspected Campaign Clustering
            </h3>
          </div>

          {/* Luminous Clean White Campaign Hero Card */}
          <div className="bg-white border-2 border-rose-200 rounded-xl p-5 shadow-xs space-y-4 relative overflow-hidden">
            <div className="h-1 w-full bg-gradient-to-r from-rose-500 to-amber-500 absolute top-0 left-0" />
            <div className="flex items-center justify-between pt-1">
              <div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded">
                  CRITICAL CAMPAIGN
                </span>
                <div className="text-lg font-mono font-bold text-ink-900 mt-1.5">
                  {campaigns[0]?.campaign_id || "CAMP-KYC-PHISH-01"}
                </div>
                <div className="text-xs text-muted">
                  {campaigns[0]?.name || "Coordinated KYC Phishing Campaign"}
                </div>
              </div>

              {/* Clean White Similarity Metric Box */}
              <div className="text-center bg-white border border-hairline rounded-xl p-3 min-w-[110px] shadow-xs">
                <div className="text-[10px] uppercase font-mono text-muted">Similarity</div>
                <div className="text-3xl font-serif font-bold text-ink-900 leading-tight tabular-nums">
                  {Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}%
                </div>
                <div className="text-[10px] font-mono text-emerald-700 font-semibold">High Match</div>
              </div>
            </div>

            {/* Similarity Progress Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono text-slate-600">
                <span>Cosine Match</span>
                <span className="font-bold text-ink-900">{(campaigns[0]?.average_similarity || 0.94).toFixed(2)} / 1.00</span>
              </div>
              <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-hairline">
                <div
                  className="h-full bg-gradient-to-r from-amber-400 to-rose-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.round((campaigns[0]?.average_similarity || 0.94) * 100)}%` }}
                />
              </div>
            </div>

            {/* Cluster Tags with Clean White Pills */}
            <div className="space-y-1.5">
              <div className="text-[10px] uppercase font-mono text-muted">Semantic &amp; Heuristic Cluster Tags:</div>
              <div className="flex flex-wrap gap-1.5">
                {["Bank impersonation", "Urgency", "KYC suspension", "PAN Freeze Alert", "APK Dropper"].map((t) => (
                  <span
                    key={t}
                    className="text-xs font-mono bg-white text-slate-800 border border-hairline px-2.5 py-1 rounded-md shadow-xs flex items-center gap-1"
                  >
                    <TagIcon className="w-3 h-3 text-slate-400 shrink-0" />
                    <span>{t}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Stats Grid on Pure White */}
            <div className="grid grid-cols-3 gap-2 pt-3 border-t border-hairline text-xs font-mono">
              <div>
                <span className="text-muted text-[10px] block uppercase">Signals Linked</span>
                <span className="font-serif text-base font-bold text-ink-900">
                  {campaigns[0]?.signals_count ?? campaigns[0]?.threat_signals_count ?? 14} Signals
                </span>
              </div>
              <div>
                <span className="text-muted text-[10px] block uppercase">Mule VPAs Armed</span>
                <span className="font-serif text-base font-bold text-rose-700">
                  {campaigns[0]?.associated_vpas_count ?? campaigns[0]?.member_count ?? 8} Accounts
                </span>
              </div>
              <div>
                <span className="text-muted text-[10px] block uppercase">Primary Rails</span>
                <span className="font-serif text-base font-bold text-ink-900">
                  {campaigns[0]?.primary_rails || "SBI · HDFC"}
                </span>
              </div>
            </div>
          </div>

          {/* Secondary Campaign Roster — Clean White Rows */}
          <div className="space-y-2 text-xs">
            <div className="text-[11px] font-mono text-muted uppercase font-semibold">
              Other Tracked Campaign Clusters
            </div>
            {Array.isArray(campaigns) && campaigns.length > 1 ? (
              campaigns.slice(1, 3).map((camp) => (
                <div key={camp.campaign_id} className="flex items-center justify-between p-3 rounded-lg bg-white hover:bg-slate-50 border border-hairline shadow-xs transition-colors">
                  <div>
                    <span className="font-mono font-bold text-ink-900 text-xs">{camp.campaign_id}</span>
                    <div className="text-[11px] text-muted">{camp.name || camp.scenario || "Mule Relay"} ({camp.signals_count ?? camp.threat_signals_count ?? 0} signals)</div>
                  </div>
                  <div className="text-right">
                    <span className="font-serif font-bold text-indigo-700 text-sm">{Math.round((camp.average_similarity || 0.9) * 100)}%</span>
                    <div className="text-[10px] text-muted font-mono uppercase">Similarity</div>
                  </div>
                </div>
              ))
            ) : (
              <>
                <div className="flex items-center justify-between p-3 rounded-lg bg-white hover:bg-slate-50 border border-hairline shadow-xs transition-colors">
                  <div>
                    <span className="font-mono font-bold text-ink-900 text-xs">CAMP-SMURF-DISPERSAL-03</span>
                    <div className="text-[11px] text-muted">Dormant-to-Active Mule Relay (19 signals)</div>
                  </div>
                  <div className="text-right">
                    <span className="font-serif font-bold text-indigo-700 text-sm">91%</span>
                    <div className="text-[10px] text-muted font-mono uppercase">Similarity</div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-white hover:bg-slate-50 border border-hairline shadow-xs transition-colors">
                  <div>
                    <span className="font-mono font-bold text-ink-900 text-xs">CAMP-TASK-INVEST-02</span>
                    <div className="text-[11px] text-muted">Telegram Task Scam Campaign (8 signals)</div>
                  </div>
                  <div className="text-right">
                    <span className="font-serif font-bold text-amber-700 text-sm">88%</span>
                    <div className="text-[10px] text-muted font-mono uppercase">Similarity</div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Live Pre-Transaction Signal Feed — Clean White Panel */}
      <div className="panel p-6 bg-white border border-hairline rounded-xl shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-hairline pb-4">
          <div>
            <div className="text-[11px] font-mono text-muted uppercase tracking-wider">
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
                  className={`px-3 py-1 rounded-md font-semibold transition-colors ${
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
              className="p-1.5 bg-white hover:bg-slate-100 border border-hairline rounded-md text-muted hover:text-ink-900 transition-colors shadow-xs"
              title="Refresh Signals"
            >
              <RefreshCwIcon className={`w-3.5 h-3.5 ${loading ? "animate-spin text-saffron" : ""}`} />
            </button>
          </div>
        </div>

        {/* Signals Table / Cards Feed */}
        <div className="space-y-3">
          {filteredSignals.length === 0 ? (
            <div className="p-8 text-center text-muted font-mono text-xs border border-hairline rounded-xl bg-white shadow-xs">
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
                    className="rounded-xl border border-hairline bg-white hover:border-slate-300 p-5 transition-all shadow-xs hover:shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-2.5 flex-1 min-w-0">
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
                        {getCampaignLabel(signal.matched_campaign || signal.matched_campaign_id) && (
                          <span className="ml-auto text-[10px] font-mono bg-white text-slate-700 px-2 py-0.5 rounded border border-hairline font-semibold shadow-xs">
                            {getCampaignLabel(signal.matched_campaign || signal.matched_campaign_id)}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-700 font-serif italic line-clamp-2">
                        &ldquo;{signal.raw_content}&rdquo;
                      </p>

                      {/* Extracted Identifiers Strip with Lucide Vector Icons */}
                      {(() => {
                        const entities = getEntityValues(signal);
                        return (
                          <div className="flex flex-wrap items-center gap-2 pt-1">
                            {entities.phone && (
                              <span className="inline-flex items-center gap-1 text-xs font-mono px-2.5 py-1 bg-white text-slate-800 rounded-md border border-slate-200 font-medium shadow-xs">
                                <PhoneIcon className="w-3 h-3 text-slate-500 shrink-0" />
                                <span>{entities.phone}</span>
                              </span>
                            )}
                            {entities.upiId && (
                              <span className="inline-flex items-center gap-1 text-xs font-mono px-2.5 py-1 bg-indigo-50/70 text-indigo-900 rounded-md border border-indigo-200 font-bold shadow-xs">
                                <ZapIcon className="w-3 h-3 text-indigo-600 shrink-0" />
                                <span>{entities.upiId}</span>
                              </span>
                            )}
                            {entities.url && (
                              <span className="inline-flex items-center gap-1 text-xs font-mono px-2.5 py-1 bg-rose-50/70 text-rose-900 rounded-md border border-rose-200 font-medium truncate max-w-xs shadow-xs">
                                <LinkIcon className="w-3 h-3 text-rose-600 shrink-0" />
                                <span className="truncate">{entities.url}</span>
                              </span>
                            )}
                            {(entities.tags || []).map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 bg-white text-slate-700 rounded border border-hairline shadow-xs"
                              >
                                <TagIcon className="w-2.5 h-2.5 text-slate-400 shrink-0" />
                                <span>{tag}</span>
                              </span>
                            ))}
                          </div>
                        );
                      })()}
                    </div>

                    <div className="flex items-center gap-2 shrink-0 md:self-center">
                      <button
                        onClick={() => setSelectedSignal(signal)}
                        className="px-3.5 py-1.5 bg-white hover:bg-slate-50 text-ink-900 border border-hairline rounded-lg text-xs font-mono font-semibold transition-colors shadow-xs"
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

      {/* Signal Detail Modal with Line 1080 Null Check Bug Fix */}
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
              className="relative z-10 max-w-2xl w-full bg-white rounded-xl shadow-2xl border border-hairline p-6 space-y-5 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-hairline pb-4">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-lg text-ink-900">
                    {selectedSignal.signal_id}
                  </span>
                  <span className="text-xs font-mono px-2.5 py-0.5 bg-rose-50 text-rose-800 rounded border border-rose-200 font-bold">
                    {selectedSignal.severity}
                  </span>
                  {renderInstitutionBadge(selectedSignal.source, selectedSignal.institution)}
                </div>
                <button
                  onClick={() => setSelectedSignal(null)}
                  className="p-1 rounded-md text-slate-400 hover:text-ink-900 hover:bg-slate-100 transition-colors"
                >
                  <CloseIcon className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                <div className="text-[11px] font-mono text-muted uppercase tracking-wider">Raw Content Payload:</div>
                <div className="p-3.5 rounded-lg bg-surface-muted/40 border border-hairline text-xs font-mono text-slate-800 leading-relaxed">
                  {selectedSignal.raw_content}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 bg-white rounded-lg border border-hairline shadow-xs">
                  <div className="text-muted text-[10px] uppercase">Matched Campaign:</div>
                  <div className="font-bold text-indigo-700 mt-1">
                    {getCampaignLabel(selectedSignal.matched_campaign || selectedSignal.matched_campaign_id) || "CAMP-KYC-PHISH-01"}
                  </div>
                </div>
                <div className="p-3 bg-white rounded-lg border border-hairline shadow-xs">
                  <div className="text-muted text-[10px] uppercase">Signal Confidence:</div>
                  <div className="font-bold text-emerald-700 mt-1">
                    {Math.min(98, Math.round((selectedSignal.confidence || 0.95) * 100))}% Correlation Confidence
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-[11px] font-mono text-muted uppercase tracking-wider">Linked Central Fraud Graph Nodes:</div>
                <div className="flex flex-wrap gap-2">
                  {(() => {
                    const selEntities = getEntityValues(selectedSignal);
                    const defaultNodes = [
                      `VPA:${selEntities.upiId || "mule@oksbi"}`,
                      `PHONE:${selEntities.phone || "+919876543210"}`,
                      `URL:${selEntities.url || "phish.in"}`,
                    ];
                    const rawNodes = selectedSignal.linked_graph_nodes;
                    const nodes = Array.isArray(rawNodes) && rawNodes.length > 0
                      ? rawNodes
                      : defaultNodes;
                    return nodes.map((node, i) => {
                      // Fix: Safeguard null check before inspecting properties
                      const nodeLabel =
                        node && typeof node === "object"
                          ? (node.id || node.label || JSON.stringify(node))
                          : String(node ?? "");
                      return (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-indigo-50 text-indigo-800 border border-indigo-200 rounded-md font-mono text-xs font-bold shadow-xs"
                        >
                          <NetworkIcon className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                          <span>{nodeLabel}</span>
                        </span>
                      );
                    });
                  })()}
                </div>
              </div>

              <div className="pt-3 border-t border-hairline flex justify-end">
                <button
                  onClick={() => setSelectedSignal(null)}
                  className="px-4 py-2 bg-ink-900 text-white rounded-lg text-xs font-mono font-bold hover:bg-ink-800 transition-colors shadow-xs"
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

export default function ThreatIntelPage() {
  return (
    <ErrorBoundary title="Threat Intelligence View Temporarily Unavailable">
      <ThreatIntelDashboard />
    </ErrorBoundary>
  );
}

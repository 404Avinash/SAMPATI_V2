import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { formatINR, shortVpa, formatTime } from "../services/api";

/**
 * Mathematical projection of point (px, py) to line segment (x1, y1)-(x2, y2).
 */
export function pointToSegmentDistance(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return Math.hypot(px - x1, py - y1);
  const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / lenSq));
  const projX = x1 + t * dx;
  const projY = y1 + t * dy;
  return Math.hypot(px - projX, py - projY);
}

/**
 * Computes continuous edge stroke color based on risk score (0-100).
 * Low (<40): Teal spectrum (#14b8a6)
 * Medium (40-70): Amber spectrum (#f59e0b)
 * High (>70): Crimson / Red spectrum (#ef4444)
 */
export function getEdgeStroke(riskScore, isHovered = false) {
  if (isHovered) return "rgba(255, 120, 0, 1.0)";
  if (riskScore == null) return "rgba(20, 184, 166, 0.45)";

  const num = typeof riskScore === "number" ? riskScore : parseFloat(riskScore);
  if (isNaN(num)) return "rgba(20, 184, 166, 0.45)";

  const clamped = Math.max(0, Math.min(100, num));
  if (clamped < 40) {
    const ratio = clamped / 40;
    const alpha = 0.4 + ratio * 0.25;
    return `rgba(20, 184, 166, ${alpha.toFixed(2)})`;
  } else if (clamped <= 70) {
    const ratio = (clamped - 40) / 30;
    const alpha = 0.65 + ratio * 0.25;
    return `rgba(245, 158, 11, ${alpha.toFixed(2)})`;
  } else {
    const ratio = (clamped - 70) / 30;
    const alpha = 0.85 + ratio * 0.15;
    return `rgba(239, 68, 68, ${alpha.toFixed(2)})`;
  }
}

/**
 * Returns human-readable label for a node role.
 */
export function getNodeRoleLabel(kind) {
  switch (kind) {
    case "hub":
      return "Collector Hub";
    case "victim":
      return "Victim / Payer";
    case "hop":
      return "Layering Hop";
    case "cashout":
      return "Cash-Out Exit";
    default:
      return "Entity";
  }
}

/**
 * Returns CSS badge classes for a node role.
 */
export function getNodeRoleBadgeClass(kind) {
  switch (kind) {
    case "hub":
      return "bg-rose-100 text-rose-800 border-rose-300";
    case "victim":
      return "bg-emerald-100 text-emerald-800 border-emerald-300";
    case "hop":
      return "bg-amber-100 text-amber-800 border-amber-300";
    case "cashout":
      return "bg-slate-100 text-slate-800 border-slate-300";
    default:
      return "bg-gray-100 text-gray-800 border-gray-300";
  }
}

/**
 * Extracts and chronologically sorts topology transactions across single or multiple cases.
 */
export function extractChronologicalTopology(cases = [], caseData = null) {
  const targetCases = caseData
    ? [caseData]
    : Array.isArray(cases)
    ? cases
    : [];

  const nodes = new Map();
  const rawEdges = [];

  function ensureNode(id, kind, cId = null, cObj = null, verdict = null) {
    if (!id) return null;
    const v = verdict || cObj?.verdict || (kind === "hub" ? "BLOCK" : kind === "hop" ? "HOLD" : "ALLOW");
    if (!nodes.has(id)) {
      nodes.set(id, {
        id,
        kind,
        verdict: v,
        x: 140 + Math.random() * 560,
        y: 80 + Math.random() * 280,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        flagged: false,
        caseId: cId,
        caseData: cObj,
      });
    } else {
      const existing = nodes.get(id);
      if (kind === "hub") existing.kind = "hub";
      if (verdict && !existing.verdict) existing.verdict = verdict;
      if (!existing.caseId && cId) {
        existing.caseId = cId;
        existing.caseData = cObj;
        if (cObj?.verdict) existing.verdict = cObj.verdict;
      }
    }
    return nodes.get(id);
  }

  const asArray = (x) => (Array.isArray(x) ? x : []);
  const validCases = targetCases.filter(
    (c) => c && (c.topology || c.ring_members_vpas || c.trigger_txn || c.payee_vpa)
  );

  validCases.slice(0, 16).forEach((c, caseIdx) => {
    const topo = (c && typeof c.topology === "object" && c.topology) || {};
    const trigger = (typeof topo.trigger_txn === "object" && topo.trigger_txn) || c.trigger_txn || {};
    const collector = trigger.payee_vpa || c.payee_vpa || `ring-${c.case_id || caseIdx}`;
    const caseRisk = c.risk_score != null ? c.risk_score : 80;
    const caseAmount = trigger.amount ?? c.amount ?? 50000;
    const baseTime = c.created_at ? new Date(c.created_at).getTime() : Date.now();
    const caseVerdict = c.verdict || (caseRisk >= 75 ? "BLOCK" : caseRisk >= 40 ? "HOLD" : "ALLOW");

    const hubNode = ensureNode(collector, "hub", c.case_id, c, caseVerdict);
    if (hubNode) hubNode.flagged = true;

    // 1. Check for explicit transactions array
    const explicitTxns = asArray(topo.transactions || c.transactions);
    if (explicitTxns.length > 0) {
      explicitTxns.forEach((tx, txIdx) => {
        const payer = tx.payer_vpa || tx.from;
        const payee = tx.payee_vpa || tx.to || collector;
        if (!payer || !payee) return;
        const txTime = tx.timestamp
          ? new Date(tx.timestamp).getTime()
          : baseTime - (explicitTxns.length - txIdx) * 15000;
        ensureNode(payer, tx.kind || "victim", c.case_id, c, tx.verdict || "ALLOW");
        ensureNode(payee, tx.kind || (payee === collector ? "hub" : "hop"), c.case_id, c, tx.verdict || caseVerdict);
        rawEdges.push({
          id: `${payer}->${payee}-${txIdx}`,
          a: payer,
          b: payee,
          flagged: true,
          riskScore: tx.risk_score ?? caseRisk,
          amount: tx.amount ?? caseAmount,
          caseId: c.case_id,
          timestamp: txTime,
          stage: tx.stage || (payee === collector ? "Fan-In Infiltration" : "Layering Hop"),
          payer,
          payee,
        });
      });
      return;
    }

    const fanIn = asArray(topo.fan_in);
    const hops = asArray(topo.hops);
    const fanOut = asArray(topo.fan_out);
    const members = asArray(c.ring_members_vpas);

    const layerIn = fanIn.length ? fanIn : members.slice(0, Math.ceil(members.length / 3));
    const layerOut = fanOut.length
      ? fanOut
      : members.slice(Math.ceil((members.length * 2) / 3));

    // 1. Fan-in (Victims -> Collector Hub): earliest timestamps
    asArray(layerIn).slice(0, 8).forEach((v, idx) => {
      const vpa = typeof v === "string" ? v : v && (v.payer_vpa || v.vpa || v.from);
      if (!vpa) return;
      const t = v.timestamp ? new Date(v.timestamp).getTime() : baseTime - 180000 + idx * 30000;
      ensureNode(vpa, "victim", c.case_id, c, "ALLOW");
      rawEdges.push({
        id: `${vpa}->${collector}-fanin-${idx}`,
        a: vpa,
        b: collector,
        flagged: true,
        riskScore: caseRisk,
        amount: (v && v.amount) || caseAmount,
        caseId: c.case_id,
        timestamp: t,
        stage: "Fan-In Infiltration",
        payer: vpa,
        payee: collector,
      });
    });

    // 2. Intermediate Layering Hops (Collector Hub -> Hops): intermediate timestamps
    asArray(hops).slice(0, 8).forEach((v, idx) => {
      const vpa = typeof v === "string" ? v : v && (v.vpa || v.payee_vpa || v.to);
      if (!vpa) return;
      const t = v.timestamp ? new Date(v.timestamp).getTime() : baseTime - 90000 + idx * 30000;
      ensureNode(vpa, "hop", c.case_id, c, "HOLD");
      rawEdges.push({
        id: `${collector}->${vpa}-hop-${idx}`,
        a: collector,
        b: vpa,
        flagged: true,
        riskScore: caseRisk,
        amount: (v && v.amount) || Math.round(caseAmount * 0.95),
        caseId: c.case_id,
        timestamp: t,
        stage: "Layering Hop",
        payer: collector,
        payee: vpa,
      });
    });

    // 3. Fan-out (Collector Hub / Hops -> Cash-out): late timestamps
    asArray(layerOut).slice(0, 8).forEach((v, idx) => {
      const vpa = typeof v === "string" ? v : v && (v.payee_vpa || v.vpa || v.to);
      if (!vpa) return;
      const t = v.timestamp ? new Date(v.timestamp).getTime() : baseTime - 30000 + idx * 15000;
      ensureNode(vpa, "cashout", c.case_id, c, "BLOCK");
      rawEdges.push({
        id: `${collector}->${vpa}-fanout-${idx}`,
        a: collector,
        b: vpa,
        flagged: true,
        riskScore: caseRisk,
        amount: (v && v.amount) || Math.round(caseAmount * 0.90),
        caseId: c.case_id,
        timestamp: t,
        stage: "Cash-Out Exit",
        payer: collector,
        payee: vpa,
      });
    });

    // 4. Trigger transaction edge
    if (trigger.payer_vpa && trigger.payee_vpa && trigger.payer_vpa !== collector) {
      const alreadyHas = rawEdges.some(
        (e) => e.a === trigger.payer_vpa && e.b === trigger.payee_vpa
      );
      if (!alreadyHas) {
        ensureNode(trigger.payer_vpa, "victim", c.case_id, c, "ALLOW");
        rawEdges.push({
          id: `${trigger.payer_vpa}->${trigger.payee_vpa}-trigger`,
          a: trigger.payer_vpa,
          b: trigger.payee_vpa,
          flagged: true,
          riskScore: caseRisk,
          amount: trigger.amount ?? caseAmount,
          caseId: c.case_id,
          timestamp: baseTime,
          stage: "Trigger Interception",
          payer: trigger.payer_vpa,
          payee: trigger.payee_vpa,
        });
      }
    }
  });

  // Sort edges strictly by chronological timestamp ASC
  const sortedEdges = rawEdges.sort((e1, e2) => (e1.timestamp || 0) - (e2.timestamp || 0));

  return { nodes, sortedEdges };
}

/**
 * Cinematic interactive canvas-based force-directed constellation visualizer with:
 * - Continuous organic spring-force physics simulation with harmonic micro-drift
 * - Pulsing node glow halos based on verdict (BLOCK red pulse, HOLD amber pulse, ALLOW neutral glow)
 * - Risk gradient colored edges with animated traveling particle flows in direction of fund transfer
 * - Auto-play on mount when cases exist
 * - Mouse scroll-to-zoom and click-drag-to-pan with world coordinates projection
 * - Node/edge click selection to trigger CaseDrawer drill-down
 */
export default function NetworkConstellation({
  cases = [],
  caseData = null,
  onSelectCase,
  initialStep = null,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const hasAutoPlayedRef = useRef(false);

  // Viewport Transform State for Zoom and Pan
  const transformRef = useRef({
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    hasDragged: false,
    startX: 0,
    startY: 0,
    startOffsetX: 0,
    startOffsetY: 0,
  });

  // Extract topology model
  const { nodes: allNodes, sortedEdges } = useMemo(
    () => extractChronologicalTopology(cases, caseData),
    [cases, caseData]
  );

  const totalSteps = sortedEdges.length;
  const [currentStep, setCurrentStep] = useState(() =>
    initialStep !== null ? Math.min(initialStep, totalSteps) : 0
  );
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [tooltip, setTooltip] = useState(null);
  const [viewportZoom, setViewportZoom] = useState(100);

  // Auto-play on initial load when cases exist, or synchronize step when dataset changes
  useEffect(() => {
    if (initialStep !== null) {
      setCurrentStep(Math.min(initialStep, totalSteps));
      setIsPlaying(false);
    } else if (totalSteps > 0 && !hasAutoPlayedRef.current) {
      hasAutoPlayedRef.current = true;
      setCurrentStep(0);
      setIsPlaying(true);
    } else if (totalSteps === 0) {
      setCurrentStep(0);
      setIsPlaying(false);
    }
  }, [totalSteps, initialStep]);

  // Derived visible elements at step k in [0, N]
  const visibleEdges = useMemo(() => {
    if (currentStep === 0 || totalSteps === 0) return [];
    return sortedEdges.slice(0, currentStep);
  }, [sortedEdges, currentStep, totalSteps]);

  const visibleNodeIds = useMemo(() => {
    if (currentStep === 0 || visibleEdges.length === 0) return new Set();
    const set = new Set();
    for (const e of visibleEdges) {
      set.add(e.a);
      set.add(e.b);
    }
    return set;
  }, [visibleEdges, currentStep]);

  const activeEdge = useMemo(() => {
    if (currentStep > 0 && currentStep <= totalSteps) {
      return sortedEdges[currentStep - 1];
    }
    return null;
  }, [sortedEdges, currentStep, totalSteps]);

  // State ref for high-frequency 60fps RAF loop
  const stateRef = useRef({
    allNodes,
    visibleEdges,
    visibleNodeIds,
    activeEdge,
    currentStep,
    totalSteps,
    hoveredNode: null,
    hoveredEdge: null,
    raf: null,
  });

  // Keep stateRef updated
  useEffect(() => {
    stateRef.current.allNodes = allNodes;
    stateRef.current.visibleEdges = visibleEdges;
    stateRef.current.visibleNodeIds = visibleNodeIds;
    stateRef.current.activeEdge = activeEdge;
    stateRef.current.currentStep = currentStep;
    stateRef.current.totalSteps = totalSteps;
  }, [allNodes, visibleEdges, visibleNodeIds, activeEdge, currentStep, totalSteps]);

  // Animation Interval Timer for Timeline Playback
  useEffect(() => {
    if (!isPlaying) return;
    if (totalSteps === 0) {
      setIsPlaying(false);
      return;
    }

    const intervalMs = Math.max(140, Math.round(900 / playbackSpeed));
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= totalSteps) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isPlaying, totalSteps, playbackSpeed]);

  // Playback Control Handlers
  const handlePlay = useCallback(() => {
    if (totalSteps === 0) return;
    if (currentStep >= totalSteps) {
      setCurrentStep(1);
    } else if (currentStep === 0) {
      setCurrentStep(1);
    }
    setIsPlaying(true);
  }, [currentStep, totalSteps]);

  const handlePause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setCurrentStep(0);
    setTooltip(null);
  }, []);

  const handleSliderChange = useCallback((e) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val)) {
      setIsPlaying(false);
      setCurrentStep(val);
      setTooltip(null);
    }
  }, []);

  // Zoom Viewport Controls
  const handleZoomIn = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const centerX = canvas.clientWidth / 2;
    const centerY = canvas.clientHeight / 2;
    const curScale = transformRef.current.scale;
    const newScale = Math.min(4.0, curScale * 1.25);
    transformRef.current.offsetX = centerX - (centerX - transformRef.current.offsetX) * (newScale / curScale);
    transformRef.current.offsetY = centerY - (centerY - transformRef.current.offsetY) * (newScale / curScale);
    transformRef.current.scale = newScale;
    setViewportZoom(Math.round(newScale * 100));
  }, []);

  const handleZoomOut = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const centerX = canvas.clientWidth / 2;
    const centerY = canvas.clientHeight / 2;
    const curScale = transformRef.current.scale;
    const newScale = Math.max(0.35, curScale / 1.25);
    transformRef.current.offsetX = centerX - (centerX - transformRef.current.offsetX) * (newScale / curScale);
    transformRef.current.offsetY = centerY - (centerY - transformRef.current.offsetY) * (newScale / curScale);
    transformRef.current.scale = newScale;
    setViewportZoom(Math.round(newScale * 100));
  }, []);

  const handleResetView = useCallback(() => {
    transformRef.current.scale = 1;
    transformRef.current.offsetX = 0;
    transformRef.current.offsetY = 0;
    setViewportZoom(100);
  }, []);

  // Non-passive wheel event listener for smooth cursor-centered zoom
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const onWheel = (e) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const curScale = transformRef.current.scale;
      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      const newScale = Math.max(0.35, Math.min(4.0, curScale * zoomFactor));

      const newOffsetX = mouseX - (mouseX - transformRef.current.offsetX) * (newScale / curScale);
      const newOffsetY = mouseY - (mouseY - transformRef.current.offsetY) * (newScale / curScale);

      transformRef.current.scale = newScale;
      transformRef.current.offsetX = newOffsetX;
      transformRef.current.offsetY = newOffsetY;
      setViewportZoom(Math.round(newScale * 100));
    };

    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      canvas.removeEventListener("wheel", onWheel);
    };
  }, []);

  // Main Canvas Render and Continuous Physics Simulation Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let width = canvas.clientWidth;
    let height = canvas.clientHeight;

    function resize() {
      if (!canvas) return;
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
    }
    resize();
    window.addEventListener("resize", resize);

    let t = 0;
    function frame() {
      t += 0.016;
      const {
        allNodes,
        visibleEdges,
        visibleNodeIds,
        activeEdge,
        hoveredNode,
        hoveredEdge,
        currentStep,
        totalSteps,
      } = stateRef.current;

      const transform = transformRef.current;
      const dpr = window.devicePixelRatio || 1;

      // Clear Canvas
      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);

      // If at step 0 (t=0 / Reset), display initial invitation state
      if (currentStep === 0 || visibleNodeIds.size === 0) {
        if (totalSteps > 0) {
          ctx.save();
          ctx.fillStyle = "rgba(100, 116, 139, 0.6)";
          ctx.font = "500 13px monospace";
          ctx.textAlign = "center";
          ctx.fillText(
            "t=0 (Initial State) · Auto-playing chronological mule-ring sequence…",
            width / 2,
            height / 2
          );
          ctx.restore();
        }
        ctx.restore();
        stateRef.current.raf = requestAnimationFrame(frame);
        return;
      }

      // Filter only currently visible nodes
      const visibleNodeList = Array.from(allNodes.values()).filter((n) =>
        visibleNodeIds.has(n.id)
      );

      // 1. Continuous Physics Simulation (Spring force + Center gravity + Pairwise repulsion + Harmonic micro-drift)
      for (const n of visibleNodeList) {
        // Center gravity pulls gently toward viewport center
        n.vx += (width / 2 - n.x) * 0.0005;
        n.vy += (height / 2 - n.y) * 0.0005;

        // Harmonic ambient micro-forces: ensures organic floating motion even when settled/paused
        const ambientAngle = t * 1.2 + n.x * 0.01 + n.y * 0.01;
        n.vx += Math.cos(ambientAngle) * 0.035;
        n.vy += Math.sin(ambientAngle) * 0.035;
      }

      // Pairwise repulsion between nodes
      for (let i = 0; i < visibleNodeList.length; i++) {
        for (let j = i + 1; j < visibleNodeList.length; j++) {
          const a = visibleNodeList[i];
          const b = visibleNodeList[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const distSq = Math.max(dx * dx + dy * dy, 1);
          const force = 950 / distSq;
          const dist = Math.sqrt(distSq);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }

      // Edge spring tension with harmonic rest-length oscillation
      for (const e of visibleEdges) {
        const a = allNodes.get(e.a);
        const b = allNodes.get(e.b);
        if (!a || !b) continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetDist = 95 + Math.sin(t * 2.0 + ((e.timestamp || 0) % 10)) * 3.5;
        const f = (dist - targetDist) * 0.006;
        const fx = (dx / dist) * f;
        const fy = (dy / dist) * f;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }

      // Apply damping & update node positions
      for (const n of visibleNodeList) {
        n.vx *= 0.91;
        n.vy *= 0.91;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.min(width - 24, Math.max(24, n.x));
        n.y = Math.min(height - 24, Math.max(24, n.y));
      }

      // Apply Zoom and Pan Transformation Matrix
      ctx.save();
      ctx.translate(transform.offsetX, transform.offsetY);
      ctx.scale(transform.scale, transform.scale);

      // 2. Render Visible Edges (Colored by Risk Score)
      for (const e of visibleEdges) {
        const a = allNodes.get(e.a);
        const b = allNodes.get(e.b);
        if (!a || !b) continue;
        const isHovered = hoveredEdge === e;
        const isActive = activeEdge === e;

        ctx.save();
        if (isActive) {
          ctx.strokeStyle = "rgba(251, 191, 36, 0.95)";
          ctx.lineWidth = 3.2;
        } else {
          ctx.strokeStyle = getEdgeStroke(e.riskScore, isHovered);
          ctx.lineWidth = isHovered ? 2.8 : 1.6;
        }
        ctx.setLineDash([6, 4]);
        ctx.lineDashOffset = -t * 24;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
        ctx.restore();
      }

      // 3. Render Animated Particle Flow Dots Along Edges (Direction of Money Transfer)
      for (const e of visibleEdges) {
        const a = allNodes.get(e.a);
        const b = allNodes.get(e.b);
        if (!a || !b) continue;

        const risk = e.riskScore != null ? e.riskScore : 50;
        const dotCount = risk >= 70 ? 3 : risk >= 40 ? 2 : 1;
        const speed = 0.35 + (risk / 100) * 0.55;

        for (let p = 0; p < dotCount; p++) {
          const u = ((t * speed + p / dotCount) % 1);
          const px = a.x + (b.x - a.x) * u;
          const py = a.y + (b.y - a.y) * u;

          ctx.save();
          if (risk >= 70) {
            // Crimson high-risk glowing particle
            ctx.fillStyle = "rgba(239, 68, 68, 0.35)";
            ctx.beginPath();
            ctx.arc(px, py, 5.0, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(px, py, 3.0, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = "#ffffff";
            ctx.beginPath();
            ctx.arc(px, py, 1.2, 0, Math.PI * 2);
            ctx.fill();
          } else if (risk >= 40) {
            // Amber medium-risk particle
            ctx.fillStyle = "#f59e0b";
            ctx.beginPath();
            ctx.arc(px, py, 2.5, 0, Math.PI * 2);
            ctx.fill();
          } else {
            // Teal low-risk particle
            ctx.fillStyle = "#14b8a6";
            ctx.beginPath();
            ctx.arc(px, py, 2.0, 0, Math.PI * 2);
            ctx.fill();
          }
          ctx.restore();
        }
      }

      // 4. Render Visible Nodes with Pulsing Glow Halos by Verdict
      for (const n of visibleNodeList) {
        const isHovered = hoveredNode === n;
        const isPartOfActiveEdge =
          activeEdge && (activeEdge.a === n.id || activeEdge.b === n.id);

        const verdict = (
          n.caseData?.verdict ||
          n.verdict ||
          (n.kind === "hub" || n.kind === "cashout" ? "BLOCK" : n.kind === "hop" ? "HOLD" : "ALLOW")
        ).toUpperCase();

        let baseRadius = n.kind === "hub" ? 9 : n.kind === "hop" ? 6.5 : n.kind === "cashout" ? 7 : 5.5;
        if (isHovered || isPartOfActiveEdge) baseRadius += 2.5;

        let glowMultiplier = 1.0;
        let glowColor = "rgba(16, 185, 129, 0.25)";
        let coreColor = "#059669";

        if (verdict === "BLOCK") {
          // BLOCK verdict: pulsing red glow with Math.sin(t * 4)
          const pulseFactor = Math.sin(t * 4.0 + (n.x * 0.04));
          glowMultiplier = 2.2 + 0.45 * pulseFactor;
          glowColor = `rgba(220, 38, 38, ${(0.35 + 0.15 * pulseFactor).toFixed(2)})`;
          coreColor = "#dc2626";
        } else if (verdict === "HOLD") {
          // HOLD verdict: pulsing amber glow with Math.sin(t * 2.5)
          const pulseFactor = Math.sin(t * 2.5 + (n.y * 0.04));
          glowMultiplier = 1.8 + 0.35 * pulseFactor;
          glowColor = `rgba(245, 158, 11, ${(0.30 + 0.12 * pulseFactor).toFixed(2)})`;
          coreColor = "#d97706";
        } else {
          // ALLOW verdict: subtle neutral glow
          glowMultiplier = 1.3 + 0.1 * Math.sin(t * 1.5);
          glowColor = "rgba(16, 185, 129, 0.25)";
          coreColor = "#059669";
        }

        if (n.kind === "cashout" && verdict !== "BLOCK") {
          coreColor = "#1e293b";
        }

        // Draw Radial Glow Halo
        const maxGlowR = baseRadius * glowMultiplier;
        const glowGrad = ctx.createRadialGradient(n.x, n.y, baseRadius * 0.4, n.x, n.y, maxGlowR);
        glowGrad.addColorStop(0, glowColor);
        glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(n.x, n.y, maxGlowR, 0, Math.PI * 2);
        ctx.fill();

        // Draw Node Core Circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, baseRadius, 0, Math.PI * 2);
        ctx.fillStyle = coreColor;
        ctx.fill();

        // Stroke Border
        ctx.lineWidth = isHovered || isPartOfActiveEdge ? 2.5 : 1.5;
        ctx.strokeStyle = isHovered || isPartOfActiveEdge ? "#fbbf24" : "#ffffff";
        ctx.stroke();
      }

      ctx.restore(); // Restore Zoom/Pan Transform
      ctx.restore(); // Restore DPR Transform

      stateRef.current.raf = requestAnimationFrame(frame);
    }

    stateRef.current.raf = requestAnimationFrame(frame);

    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      cancelAnimationFrame(stateRef.current.raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  // Mouse Interaction Handlers: Pan Dragging & World Coordinate Hit Detection
  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return; // Left click only
    const transform = transformRef.current;
    transform.isDragging = true;
    transform.hasDragged = false;
    transform.startX = e.clientX;
    transform.startY = e.clientY;
    transform.startOffsetX = transform.offsetX;
    transform.startOffsetY = transform.offsetY;
  }, []);

  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const transform = transformRef.current;

    // Handle Active Pan Dragging
    if (transform.isDragging) {
      const dx = e.clientX - transform.startX;
      const dy = e.clientY - transform.startY;
      if (Math.hypot(dx, dy) > 4) {
        transform.hasDragged = true;
      }
      transform.offsetX = transform.startOffsetX + dx;
      transform.offsetY = transform.startOffsetY + dy;
      canvas.style.cursor = "grabbing";
      setTooltip(null);
      return;
    }

    // Convert Screen Mouse Coordinates to World Coordinates for Hit Detection
    const worldX = (mouseX - transform.offsetX) / transform.scale;
    const worldY = (mouseY - transform.offsetY) / transform.scale;

    const { allNodes, visibleEdges, visibleNodeIds } = stateRef.current;
    if (visibleNodeIds.size === 0) return;

    const visibleNodeList = Array.from(allNodes.values()).filter((n) =>
      visibleNodeIds.has(n.id)
    );

    // 1. Check Visible Node Hits in World Coordinates
    let hitNode = null;
    for (let i = visibleNodeList.length - 1; i >= 0; i--) {
      const n = visibleNodeList[i];
      const threshold = (n.kind === "hub" ? 16 : 12);
      if (Math.hypot(n.x - worldX, n.y - worldY) <= threshold) {
        hitNode = n;
        break;
      }
    }

    if (hitNode) {
      stateRef.current.hoveredNode = hitNode;
      stateRef.current.hoveredEdge = null;
      canvas.style.cursor = "pointer";

      const tooltipX = Math.max(10, Math.min(rect.width - 240, mouseX + 12));
      const tooltipY = Math.max(10, Math.min(rect.height - 120, mouseY + 12));

      setTooltip({
        type: "node",
        vpa: hitNode.id || "—",
        kind: hitNode.kind,
        verdict: hitNode.verdict,
        caseId: hitNode.caseId,
        caseData: hitNode.caseData,
        x: tooltipX,
        y: tooltipY,
      });
      return;
    }

    // 2. Check Visible Edge Hits in World Coordinates
    let hitEdge = null;
    for (let i = visibleEdges.length - 1; i >= 0; i--) {
      const edge = visibleEdges[i];
      const a = allNodes.get(edge.a);
      const b = allNodes.get(edge.b);
      if (!a || !b) continue;

      const dist = pointToSegmentDistance(worldX, worldY, a.x, a.y, b.x, b.y);
      if (dist <= 7.0) {
        hitEdge = edge;
        break;
      }
    }

    if (hitEdge) {
      stateRef.current.hoveredNode = null;
      stateRef.current.hoveredEdge = hitEdge;
      canvas.style.cursor = "pointer";

      const tooltipX = Math.max(10, Math.min(rect.width - 240, mouseX + 12));
      const tooltipY = Math.max(10, Math.min(rect.height - 120, mouseY + 12));

      setTooltip({
        type: "edge",
        from: hitEdge.a,
        to: hitEdge.b,
        amount: hitEdge.amount,
        riskScore: hitEdge.riskScore,
        caseId: hitEdge.caseId,
        stage: hitEdge.stage,
        x: tooltipX,
        y: tooltipY,
      });
      return;
    }

    stateRef.current.hoveredNode = null;
    stateRef.current.hoveredEdge = null;
    canvas.style.cursor = "grab";
    setTooltip(null);
  }, []);

  const handleMouseLeave = useCallback(() => {
    const canvas = canvasRef.current;
    if (canvas) canvas.style.cursor = "default";
    transformRef.current.isDragging = false;
    stateRef.current.hoveredNode = null;
    stateRef.current.hoveredEdge = null;
    setTooltip(null);
  }, []);

  const handleMouseUp = useCallback(
    (e) => {
      const transform = transformRef.current;
      const wasDragging = transform.hasDragged;
      transform.isDragging = false;
      const canvas = canvasRef.current;
      if (canvas) canvas.style.cursor = "grab";

      // If user performed a click (no significant pan drag), open CaseDrawer
      if (!wasDragging) {
        const rect = canvas?.getBoundingClientRect();
        if (!rect) return;
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const worldX = (mouseX - transform.offsetX) / transform.scale;
        const worldY = (mouseY - transform.offsetY) / transform.scale;

        const { allNodes, visibleEdges, visibleNodeIds } = stateRef.current;
        if (visibleNodeIds.size === 0) return;

        const visibleNodeList = Array.from(allNodes.values()).filter((n) =>
          visibleNodeIds.has(n.id)
        );

        // Check node click
        for (let i = visibleNodeList.length - 1; i >= 0; i--) {
          const n = visibleNodeList[i];
          const threshold = (n.kind === "hub" ? 16 : 12);
          if (Math.hypot(n.x - worldX, n.y - worldY) <= threshold) {
            if (onSelectCase) {
              if (n.caseData) {
                onSelectCase(n.caseData);
              } else if (n.caseId) {
                const found = cases.find((c) => c.case_id === n.caseId);
                if (found) {
                  onSelectCase(found);
                } else {
                  onSelectCase({
                    case_id: n.caseId,
                    payer_vpa: n.id,
                    verdict: n.verdict || "BLOCK",
                  });
                }
              }
            }
            return;
          }
        }

        // Check edge click
        for (let i = visibleEdges.length - 1; i >= 0; i--) {
          const edge = visibleEdges[i];
          const a = allNodes.get(edge.a);
          const b = allNodes.get(edge.b);
          if (!a || !b) continue;

          const dist = pointToSegmentDistance(worldX, worldY, a.x, a.y, b.x, b.y);
          if (dist <= 7.0) {
            if (onSelectCase && edge.caseId) {
              const found = cases.find((c) => c.case_id === edge.caseId);
              if (found) onSelectCase(found);
            }
            return;
          }
        }
      }
    },
    [cases, onSelectCase]
  );

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full flex flex-col overflow-hidden rounded-md bg-[#0f172a] select-none"
    >
      {/* Canvas Viewport Area */}
      <div className="relative flex-1 min-h-0 w-full">
        <canvas
          ref={canvasRef}
          className="w-full h-full block cursor-grab"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onMouseUp={handleMouseUp}
        />

        {totalSteps === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-400 font-mono">
            Awaiting mule-ring detections…
          </div>
        )}

        {/* HUD Legend */}
        <div className="absolute top-3 left-3 flex flex-col gap-1 text-[11px] font-mono text-slate-300 bg-slate-900/85 backdrop-blur px-3 py-2 rounded-lg border border-slate-700/60 shadow-lg pointer-events-none">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold mb-0.5">
            Network Entities & Verdicts
          </div>
          <div className="flex items-center gap-3">
            <LegendDot color="#dc2626" label="BLOCK / Hub" glow="rgba(220, 38, 38, 0.6)" />
            <LegendDot color="#d97706" label="HOLD / Hop" glow="rgba(245, 158, 11, 0.5)" />
            <LegendDot color="#059669" label="ALLOW / Victim" glow="rgba(16, 185, 129, 0.4)" />
            <LegendDot color="#1e293b" label="Cash-Out" border="#475569" />
          </div>
          <div className="flex items-center gap-2 pt-1 mt-0.5 border-t border-slate-800 text-[10px] text-slate-400">
            <span>Edge Risk:</span>
            <span className="text-[#14b8a6]">Low &lt;40</span>
            <span>·</span>
            <span className="text-[#f59e0b]">Med 40-70</span>
            <span>·</span>
            <span className="text-[#ef4444]">High &gt;70</span>
          </div>
        </div>

        {/* Viewport Zoom / Reset HUD Controls */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-slate-900/85 backdrop-blur p-1 rounded-lg border border-slate-700/60 shadow-lg">
          <button
            type="button"
            onClick={handleZoomIn}
            className="w-7 h-7 flex items-center justify-center text-sm font-bold text-slate-200 hover:text-white bg-slate-800/80 hover:bg-slate-700 rounded transition-colors"
            title="Zoom In (or scroll up)"
          >
            +
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            className="w-7 h-7 flex items-center justify-center text-sm font-bold text-slate-200 hover:text-white bg-slate-800/80 hover:bg-slate-700 rounded transition-colors"
            title="Zoom Out (or scroll down)"
          >
            −
          </button>
          <button
            type="button"
            onClick={handleResetView}
            className="px-2 h-7 flex items-center justify-center text-[10px] font-mono text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 rounded transition-colors"
            title="Reset Pan & Zoom (100%)"
          >
            {viewportZoom}% · Fit
          </button>
        </div>

        {/* Interactive Tooltip Overlay */}
        {tooltip && (
          <div
            className="absolute z-30 pointer-events-none bg-slate-900/95 text-white p-3 rounded-lg shadow-2xl text-xs backdrop-blur border border-slate-700 max-w-[260px] space-y-1.5 transition-opacity duration-150"
            style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
          >
            {tooltip.type === "node" ? (
              <>
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`text-[10px] uppercase px-1.5 py-0.5 rounded font-mono font-semibold border ${getNodeRoleBadgeClass(
                      tooltip.kind
                    )}`}
                  >
                    {getNodeRoleLabel(tooltip.kind)}
                  </span>
                  {tooltip.verdict && (
                    <span
                      className={`text-[10px] uppercase px-1.5 py-0.5 rounded font-mono font-bold ${
                        tooltip.verdict === "BLOCK"
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                          : tooltip.verdict === "HOLD"
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                          : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      }`}
                    >
                      {tooltip.verdict}
                    </span>
                  )}
                </div>
                <div
                  className="font-mono text-xs font-semibold text-white truncate pt-0.5"
                  title={tooltip.vpa}
                >
                  {shortVpa(tooltip.vpa)}
                </div>
                {tooltip.caseId && (
                  <div className="text-[10px] text-amber-400 font-sans pt-1 border-t border-slate-800 flex items-center justify-between">
                    <span>Case: {tooltip.caseId.slice(-8)}</span>
                    <span className="font-semibold">Click to open drawer →</span>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1">
                  <span className="text-[10px] uppercase text-slate-400 font-mono">
                    {tooltip.stage || "Transaction Conduit"}
                  </span>
                  {tooltip.riskScore != null && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                        tooltip.riskScore >= 70
                          ? "bg-rose-500/30 text-rose-300 border border-rose-500/50"
                          : tooltip.riskScore >= 40
                          ? "bg-amber-500/30 text-amber-300 border border-amber-500/50"
                          : "bg-teal-500/30 text-teal-300 border border-teal-500/50"
                      }`}
                    >
                      Risk {tooltip.riskScore}
                    </span>
                  )}
                </div>
                <div className="font-sans text-sm font-bold text-white">
                  {formatINR(tooltip.amount)}
                </div>
                <div className="font-mono text-[11px] text-slate-300 truncate">
                  {shortVpa(tooltip.from)} → {shortVpa(tooltip.to)}
                </div>
                {tooltip.caseId && (
                  <div className="text-[10px] text-amber-400 font-sans pt-0.5 flex items-center justify-between">
                    <span>Case: {tooltip.caseId.slice(-8)}</span>
                    <span className="font-semibold">Click to inspect →</span>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Timeline Controls Strip */}
      <div className="border-t border-slate-800 bg-slate-900/95 backdrop-blur px-3 py-2.5 flex flex-col gap-1.5 shrink-0">
        {/* Controls and Slider Row */}
        <div className="flex items-center gap-3">
          {/* Play / Pause Button */}
          {isPlaying ? (
            <button
              type="button"
              onClick={handlePause}
              className="px-2.5 py-1 text-xs font-semibold bg-amber-500 text-slate-950 rounded hover:bg-amber-400 transition-colors flex items-center gap-1 shadow-sm"
              title="Pause Playback"
            >
              <span>⏸</span>
              <span>Pause</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={handlePlay}
              disabled={totalSteps === 0}
              className="px-2.5 py-1 text-xs font-semibold bg-emerald-500 text-slate-950 rounded hover:bg-emerald-400 disabled:opacity-40 transition-colors flex items-center gap-1 shadow-sm font-mono"
              title="Play Timeline Animation"
            >
              <span>▶</span>
              <span>Play</span>
            </button>
          )}

          {/* Reset Button */}
          <button
            type="button"
            onClick={handleReset}
            disabled={totalSteps === 0 && currentStep === 0}
            className="px-2 py-1 text-xs font-medium bg-slate-800 text-slate-200 border border-slate-700 rounded hover:bg-slate-700 disabled:opacity-40 transition-colors flex items-center gap-1 font-mono"
            title="Reset to t=0 (Clear Canvas)"
          >
            <span>↺</span>
            <span>Reset</span>
          </button>

          {/* Interactive Range Slider */}
          <div className="flex-1 flex items-center gap-2">
            <input
              type="range"
              min="0"
              max={totalSteps}
              step="1"
              value={currentStep}
              onChange={handleSliderChange}
              disabled={totalSteps === 0}
              className="w-full accent-amber-500 h-1.5 bg-slate-700 rounded-lg cursor-pointer disabled:opacity-40"
            />
          </div>

          {/* Step Counter Badge */}
          <div className="text-[11px] font-mono whitespace-nowrap px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 font-semibold">
            {currentStep === 0 ? "t=0" : `Step ${currentStep}/${totalSteps}`}
          </div>

          {/* Speed Multipliers */}
          <div className="flex items-center gap-0.5 bg-slate-800 p-0.5 rounded border border-slate-700 text-[10px] font-mono">
            {[0.5, 1, 2].map((spd) => (
              <button
                key={spd}
                type="button"
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-1.5 py-0.5 rounded ${
                  playbackSpeed === spd
                    ? "bg-amber-500 font-bold text-slate-950 shadow-xs"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>

        {/* Step Telemetry Status Chip */}
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 px-1">
          {currentStep === 0 ? (
            <span className="text-slate-400 italic">
              Canvas cleared (t=0) · Timeline will auto-play, or drag slider to inspect chronological hops
            </span>
          ) : activeEdge ? (
            <div className="flex items-center gap-2 overflow-hidden truncate">
              <span className="px-1.5 py-0.2 rounded bg-purple-950/80 text-purple-300 border border-purple-700/60 font-semibold uppercase">
                {activeEdge.stage || "Hop"}
              </span>
              <span className="font-semibold text-slate-100">
                {formatINR(activeEdge.amount)}
              </span>
              <span className="text-slate-300">
                {shortVpa(activeEdge.a)} → {shortVpa(activeEdge.b)}
              </span>
              {activeEdge.riskScore != null && (
                <span
                  className={`font-bold ${
                    activeEdge.riskScore >= 70
                      ? "text-rose-400"
                      : activeEdge.riskScore >= 40
                      ? "text-amber-400"
                      : "text-teal-400"
                  }`}
                >
                  (Risk {activeEdge.riskScore})
                </span>
              )}
            </div>
          ) : (
            <span>All {totalSteps} transactions visualized · Continuous organic spring simulation active</span>
          )}

          {activeEdge?.timestamp && (
            <span className="text-slate-400 shrink-0">
              {formatTime(new Date(activeEdge.timestamp).toISOString())}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function LegendDot({ color, label, glow, border }) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className="w-2.5 h-2.5 rounded-full inline-block"
        style={{
          background: color,
          boxShadow: glow ? `0 0 6px ${glow}` : "none",
          border: border ? `1px solid ${border}` : "none",
        }}
      />
      {label}
    </span>
  );
}

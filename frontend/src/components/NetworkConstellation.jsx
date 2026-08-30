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
 * 0-39: Slate spectrum
 * 40-74: Amber spectrum
 * 75-100: Crimson / Red spectrum
 */
export function getEdgeStroke(riskScore, isHovered = false) {
  if (isHovered) return "rgba(255, 120, 0, 1.0)";
  if (riskScore == null) return "rgba(100, 116, 139, 0.30)";

  const num = typeof riskScore === "number" ? riskScore : parseFloat(riskScore);
  if (isNaN(num)) return "rgba(100, 116, 139, 0.30)";

  const clamped = Math.max(0, Math.min(100, num));
  if (clamped < 40) {
    const ratio = clamped / 40;
    const alpha = 0.3 + ratio * 0.3;
    return `rgba(100, 116, 139, ${alpha.toFixed(2)})`;
  } else if (clamped < 75) {
    const ratio = (clamped - 40) / 35;
    const alpha = 0.6 + ratio * 0.3;
    return `rgba(245, 158, 11, ${alpha.toFixed(2)})`;
  } else {
    const ratio = (clamped - 75) / 25;
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
      return "Victim";
    case "hop":
      return "Layering Hop";
    case "cashout":
      return "Cash-Out";
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

  function ensureNode(id, kind, cId = null, cObj = null) {
    if (!id) return null;
    if (!nodes.has(id)) {
      nodes.set(id, {
        id,
        kind,
        x: 100 + Math.random() * 600,
        y: 60 + Math.random() * 320,
        vx: 0,
        vy: 0,
        flagged: false,
        caseId: cId,
        caseData: cObj,
      });
    } else {
      const existing = nodes.get(id);
      if (kind === "hub") existing.kind = "hub";
      if (!existing.caseId && cId) {
        existing.caseId = cId;
        existing.caseData = cObj;
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

    const hubNode = ensureNode(collector, "hub", c.case_id, c);
    if (hubNode) hubNode.flagged = true;

    // Check for explicit transactions array
    const explicitTxns = asArray(topo.transactions || c.transactions);
    if (explicitTxns.length > 0) {
      explicitTxns.forEach((tx, txIdx) => {
        const payer = tx.payer_vpa || tx.from;
        const payee = tx.payee_vpa || tx.to || collector;
        if (!payer || !payee) return;
        const txTime = tx.timestamp
          ? new Date(tx.timestamp).getTime()
          : baseTime - (explicitTxns.length - txIdx) * 15000;
        ensureNode(payer, tx.kind || "victim", c.case_id, c);
        ensureNode(payee, tx.kind || (payee === collector ? "hub" : "hop"), c.case_id, c);
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
      ensureNode(vpa, "victim", c.case_id, c);
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
      ensureNode(vpa, "hop", c.case_id, c);
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
      ensureNode(vpa, "cashout", c.case_id, c);
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
        ensureNode(trigger.payer_vpa, "victim", c.case_id, c);
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
 * Interactive canvas-based force-directed constellation visualizer with Fraud Playback Timeline.
 * Supports Play/Pause/Reset controls, interactive step scrubbing, chronological edge animation,
 * node/edge hit detection, hover tooltips, and case drill-down.
 */
export default function NetworkConstellation({
  cases = [],
  caseData = null,
  onSelectCase,
  initialStep = null,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Extract topology model
  const { nodes: allNodes, sortedEdges } = useMemo(
    () => extractChronologicalTopology(cases, caseData),
    [cases, caseData]
  );

  const totalSteps = sortedEdges.length;
  const [currentStep, setCurrentStep] = useState(() =>
    initialStep !== null ? Math.min(initialStep, totalSteps) : totalSteps
  );
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [tooltip, setTooltip] = useState(null);

  // Synchronize step when topology dataset changes
  useEffect(() => {
    if (initialStep !== null) {
      setCurrentStep(Math.min(initialStep, totalSteps));
    } else {
      setCurrentStep(totalSteps);
    }
    setIsPlaying(false);
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

    const intervalMs = Math.max(150, Math.round(1000 / playbackSpeed));
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

  // Main Canvas Render and Physics Loop
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
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
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

      ctx.clearRect(0, 0, width, height);

      // If at step 0 (t=0 / Reset), canvas is clear
      if (currentStep === 0 || visibleNodeIds.size === 0) {
        if (totalSteps > 0) {
          ctx.save();
          ctx.fillStyle = "rgba(100, 116, 139, 0.5)";
          ctx.font = "12px monospace";
          ctx.textAlign = "center";
          ctx.fillText(
            "t=0 (Initial State) · Click Play (▶) or drag slider to start playback",
            width / 2,
            height / 2
          );
          ctx.restore();
        }
        stateRef.current.raf = requestAnimationFrame(frame);
        return;
      }

      // Filter only currently visible nodes
      const visibleNodeList = Array.from(allNodes.values()).filter((n) =>
        visibleNodeIds.has(n.id)
      );

      // Physics Simulation: Center Gravity + Repulsion + Springs for visible nodes
      for (const n of visibleNodeList) {
        n.vx += (width / 2 - n.x) * 0.0006;
        n.vy += (height / 2 - n.y) * 0.0006;
      }

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

      for (const e of visibleEdges) {
        const a = allNodes.get(e.a);
        const b = allNodes.get(e.b);
        if (!a || !b) continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const target = 95;
        const k = 0.006;
        const f = (dist - target) * k;
        const fx = (dx / dist) * f;
        const fy = (dy / dist) * f;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }

      for (const n of visibleNodeList) {
        n.vx *= 0.88;
        n.vy *= 0.88;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.min(width - 16, Math.max(16, n.x));
        n.y = Math.min(height - 16, Math.max(16, n.y));
      }

      // Render Visible Edges
      for (const e of visibleEdges) {
        const a = allNodes.get(e.a);
        const b = allNodes.get(e.b);
        if (!a || !b) continue;
        const isHovered = hoveredEdge === e;
        const isActive = activeEdge === e;

        ctx.save();
        if (isActive) {
          ctx.strokeStyle = "rgba(251, 191, 36, 0.95)";
          ctx.lineWidth = 3.0;
        } else {
          ctx.strokeStyle = getEdgeStroke(e.riskScore, isHovered);
          ctx.lineWidth = isHovered ? 2.8 : 1.4;
        }
        ctx.setLineDash([5, 5]);
        ctx.lineDashOffset = -t * 26;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
        ctx.restore();
      }

      // Render Visible Nodes
      for (const n of visibleNodeList) {
        const isHovered = hoveredNode === n;
        const isPartOfActiveEdge =
          activeEdge && (activeEdge.a === n.id || activeEdge.b === n.id);
        const pulse = n.kind === "hub" ? 1 + Math.sin(t * 3 + n.x) * 0.18 : 1;
        const baseR = n.kind === "hub" ? 8.5 : n.kind === "hop" ? 6 : 5;
        const r = baseR * pulse + (isHovered || isPartOfActiveEdge ? 2.5 : 0);

        if (n.kind === "hub" || isHovered || isPartOfActiveEdge) {
          const glow = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 3.5);
          glow.addColorStop(
            0,
            n.kind === "hub"
              ? "rgba(179,38,30,0.38)"
              : isPartOfActiveEdge
              ? "rgba(251,191,36,0.35)"
              : "rgba(15,122,61,0.25)"
          );
          glow.addColorStop(1, "rgba(255,255,255,0)");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(n.x, n.y, r * 3.5, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle =
          n.kind === "hub"
            ? "#b3261e"
            : n.kind === "victim"
            ? "#0f7a3d"
            : n.kind === "hop"
            ? "#a8660a"
            : "#0b1f3a";
        ctx.fill();
        ctx.lineWidth = isHovered || isPartOfActiveEdge ? 2.5 : 1.5;
        ctx.strokeStyle = isHovered || isPartOfActiveEdge ? "#fbbf24" : "#ffffff";
        ctx.stroke();
      }

      stateRef.current.raf = requestAnimationFrame(frame);
    }

    stateRef.current.raf = requestAnimationFrame(frame);

    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      cancelAnimationFrame(stateRef.current.raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  // Hit Detection & Mouse Event Handlers for Visible Elements
  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const { allNodes, visibleEdges, visibleNodeIds } = stateRef.current;
    if (visibleNodeIds.size === 0) return;

    const visibleNodeList = Array.from(allNodes.values()).filter((n) =>
      visibleNodeIds.has(n.id)
    );

    // 1. Check Visible Node Hits
    let hitNode = null;
    for (let i = visibleNodeList.length - 1; i >= 0; i--) {
      const n = visibleNodeList[i];
      const threshold = n.kind === "hub" ? 14 : 11;
      if (Math.hypot(n.x - mouseX, n.y - mouseY) <= threshold) {
        hitNode = n;
        break;
      }
    }

    if (hitNode) {
      stateRef.current.hoveredNode = hitNode;
      stateRef.current.hoveredEdge = null;
      canvas.style.cursor = "pointer";

      const tooltipX = Math.max(10, Math.min(rect.width - 200, mouseX + 12));
      const tooltipY = Math.max(10, Math.min(rect.height - 110, mouseY + 12));

      setTooltip({
        type: "node",
        vpa: hitNode.id || "—",
        kind: hitNode.kind,
        caseId: hitNode.caseId,
        caseData: hitNode.caseData,
        x: tooltipX,
        y: tooltipY,
      });
      return;
    }

    // 2. Check Visible Edge Hits
    let hitEdge = null;
    for (let i = visibleEdges.length - 1; i >= 0; i--) {
      const edge = visibleEdges[i];
      const a = allNodes.get(edge.a);
      const b = allNodes.get(edge.b);
      if (!a || !b) continue;

      const dist = pointToSegmentDistance(mouseX, mouseY, a.x, a.y, b.x, b.y);
      if (dist <= 6.5) {
        hitEdge = edge;
        break;
      }
    }

    if (hitEdge) {
      stateRef.current.hoveredNode = null;
      stateRef.current.hoveredEdge = hitEdge;
      canvas.style.cursor = "pointer";

      const tooltipX = Math.max(10, Math.min(rect.width - 220, mouseX + 12));
      const tooltipY = Math.max(10, Math.min(rect.height - 110, mouseY + 12));

      setTooltip({
        type: "edge",
        from: hitEdge.a,
        to: hitEdge.b,
        amount: hitEdge.amount,
        riskScore: hitEdge.riskScore,
        caseId: hitEdge.caseId,
        x: tooltipX,
        y: tooltipY,
      });
      return;
    }

    stateRef.current.hoveredNode = null;
    stateRef.current.hoveredEdge = null;
    canvas.style.cursor = "default";
    setTooltip(null);
  }, []);

  const handleMouseLeave = useCallback(() => {
    const canvas = canvasRef.current;
    if (canvas) canvas.style.cursor = "default";
    stateRef.current.hoveredNode = null;
    stateRef.current.hoveredEdge = null;
    setTooltip(null);
  }, []);

  const handleClick = useCallback(() => {
    const { hoveredNode, hoveredEdge } = stateRef.current;
    if (!onSelectCase) return;

    if (hoveredNode && (hoveredNode.caseData || hoveredNode.caseId)) {
      if (hoveredNode.caseData) {
        onSelectCase(hoveredNode.caseData);
      } else {
        const found = cases.find((c) => c.case_id === hoveredNode.caseId);
        if (found) onSelectCase(found);
      }
    } else if (hoveredEdge && hoveredEdge.caseId) {
      const found = cases.find((c) => c.case_id === hoveredEdge.caseId);
      if (found) onSelectCase(found);
    }
  }, [cases, onSelectCase]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full flex flex-col overflow-hidden rounded-md bg-[#f8f9fc] select-none"
    >
      {/* Canvas Area */}
      <div className="relative flex-1 min-h-0 w-full">
        <canvas
          ref={canvasRef}
          className="w-full h-full block"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
        />

        {totalSteps === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-muted font-mono">
            Awaiting mule-ring detections…
          </div>
        )}

        {/* Legend */}
        <div className="absolute top-3 left-3 flex gap-3 text-[11px] font-mono text-muted bg-white/85 backdrop-blur px-2.5 py-1.5 rounded border border-hairline shadow-sm pointer-events-none">
          <LegendDot color="#0f7a3d" label="Victim" />
          <LegendDot color="#b3261e" label="Collector hub" />
          <LegendDot color="#a8660a" label="Layering hop" />
          <LegendDot color="#0b1f3a" label="Cash-out" />
        </div>

        {/* Interactive Tooltip Overlay */}
        {tooltip && (
          <div
            className="absolute z-30 pointer-events-none bg-ink-900/95 text-white p-3 rounded-lg shadow-xl text-xs backdrop-blur border border-white/15 max-w-[240px] space-y-1.5 transition-opacity duration-150"
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
                  {tooltip.caseId && (
                    <span className="text-[10px] text-white/60 font-mono">
                      {tooltip.caseId.slice(-8)}
                    </span>
                  )}
                </div>
                <div
                  className="font-mono text-xs font-semibold text-white truncate"
                  title={tooltip.vpa}
                >
                  {shortVpa(tooltip.vpa)}
                </div>
                {tooltip.caseId && (
                  <div className="text-[10px] text-amber-300 font-sans pt-1 border-t border-white/10 flex items-center gap-1">
                    <span>Click to view case details</span>
                    <span>→</span>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-1">
                  <span className="text-[10px] uppercase text-white/60 font-mono">
                    Transaction Flow
                  </span>
                  {tooltip.riskScore != null && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/30 text-rose-300 border border-rose-500/40 font-mono font-bold">
                      Risk {tooltip.riskScore}
                    </span>
                  )}
                </div>
                <div className="font-sans text-sm font-bold text-white">
                  {formatINR(tooltip.amount)}
                </div>
                <div className="font-mono text-[11px] text-white/80 truncate">
                  {shortVpa(tooltip.from)} → {shortVpa(tooltip.to)}
                </div>
                {tooltip.caseId && (
                  <div className="text-[10px] text-amber-300 font-sans pt-0.5 flex items-center gap-1">
                    <span>Click to open case</span>
                    <span>→</span>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Timeline Controls Strip */}
      <div className="border-t border-hairline bg-white/90 backdrop-blur px-3 py-2 flex flex-col gap-1.5 shrink-0">
        {/* Controls and Slider Row */}
        <div className="flex items-center gap-3">
          {/* Play / Pause Button */}
          {isPlaying ? (
            <button
              type="button"
              onClick={handlePause}
              className="px-2.5 py-1 text-xs font-semibold bg-amber-500 text-white rounded hover:bg-amber-600 transition-colors flex items-center gap-1 shadow-sm"
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
              className="px-2.5 py-1 text-xs font-semibold bg-ink-900 text-white rounded hover:bg-ink-800 disabled:opacity-40 transition-colors flex items-center gap-1 shadow-sm"
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
            className="px-2 py-1 text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 rounded hover:bg-slate-200 disabled:opacity-40 transition-colors flex items-center gap-1"
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
              className="w-full accent-amber-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer disabled:opacity-40"
            />
          </div>

          {/* Step Counter Badge */}
          <div className="text-[11px] font-mono whitespace-nowrap px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-semibold">
            {currentStep === 0 ? "t=0" : `Step ${currentStep}/${totalSteps}`}
          </div>

          {/* Speed Multipliers */}
          <div className="flex items-center gap-0.5 bg-slate-100 p-0.5 rounded border border-slate-200 text-[10px] font-mono">
            {[0.5, 1, 2].map((spd) => (
              <button
                key={spd}
                type="button"
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-1.5 py-0.5 rounded ${
                  playbackSpeed === spd
                    ? "bg-white font-bold text-ink-900 shadow-xs"
                    : "text-slate-600 hover:text-ink-900"
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>

        {/* Step Telemetry Status Chip */}
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-600 px-1">
          {currentStep === 0 ? (
            <span className="text-slate-400 italic">
              Canvas cleared (t=0) · Press Play (▶) or scrub slider to reveal chronological mule-ring sequence
            </span>
          ) : activeEdge ? (
            <div className="flex items-center gap-2 overflow-hidden truncate">
              <span className="px-1.5 py-0.2 rounded bg-purple-50 text-purple-700 border border-purple-200 font-semibold uppercase">
                {activeEdge.stage || "Hop"}
              </span>
              <span className="font-semibold text-slate-900">
                {formatINR(activeEdge.amount)}
              </span>
              <span className="text-slate-500">
                {shortVpa(activeEdge.a)} → {shortVpa(activeEdge.b)}
              </span>
              {activeEdge.riskScore != null && (
                <span className="text-rose-600 font-bold">
                  (Risk {activeEdge.riskScore})
                </span>
              )}
            </div>
          ) : (
            <span>All {totalSteps} transactions visible</span>
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

function LegendDot({ color, label }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full inline-block" style={{ background: color }} />
      {label}
    </span>
  );
}

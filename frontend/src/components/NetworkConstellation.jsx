import React, { useEffect, useRef, useState, useCallback } from "react";
import { formatINR, shortVpa } from "../services/api";

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
function getNodeRoleLabel(kind) {
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
function getNodeRoleBadgeClass(kind) {
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
 * Interactive canvas-based force-directed constellation visualizer.
 * Supports node/edge hit detection, hover tooltips, continuous risk gradients,
 * and click-to-case investigation drawer activation.
 */
export default function NetworkConstellation({ cases = [], onSelectCase }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const stateRef = useRef({
    nodes: new Map(),
    edges: [],
    raf: null,
    hoveredNode: null,
    hoveredEdge: null,
  });

  const [tooltip, setTooltip] = useState(null);
  const [nodeCount, setNodeCount] = useState(0);

  // Rebuild graph model whenever cases array changes
  useEffect(() => {
    const nodes = new Map();
    const edges = [];

    function ensureNode(id, kind, caseId = null, caseData = null) {
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
          caseId,
          caseData,
        });
      } else {
        const existing = nodes.get(id);
        if (kind === "hub") {
          existing.kind = "hub";
        }
        if (!existing.caseId && caseId) {
          existing.caseId = caseId;
          existing.caseData = caseData;
        }
      }
      return nodes.get(id);
    }

    const asArray = (x) => (Array.isArray(x) ? x : []);
    const ringCases = asArray(cases).filter((c) => c && (c.topology || c.ring_members_vpas || c.trigger_txn));

    asArray(ringCases).slice(0, 16).forEach((c) => {
      const topo = (c && typeof c.topology === "object" && c.topology) || {};
      const trigger = (typeof topo.trigger_txn === "object" && topo.trigger_txn) || c.trigger_txn || {};
      const collector = trigger.payee_vpa || c.payee_vpa || `ring-${c.case_id}`;
      const caseRisk = c.risk_score != null ? c.risk_score : 80;
      const caseAmount = trigger.amount ?? c.amount ?? 50000;

      const hubNode = ensureNode(collector, "hub", c.case_id, c);
      if (hubNode) hubNode.flagged = true;

      const fanIn = asArray(topo.fan_in);
      const hops = asArray(topo.hops);
      const fanOut = asArray(topo.fan_out);
      const members = asArray(c.ring_members_vpas);

      const layerIn = fanIn.length ? fanIn : members.slice(0, Math.ceil(members.length / 3));
      const layerOut = fanOut.length
        ? fanOut
        : members.slice(Math.ceil((members.length * 2) / 3));

      asArray(layerIn).slice(0, 8).forEach((v) => {
        const vpa = typeof v === "string" ? v : v && (v.payer_vpa || v.vpa);
        if (!vpa) return;
        ensureNode(vpa, "victim", c.case_id, c);
        edges.push({
          a: vpa,
          b: collector,
          flagged: true,
          riskScore: caseRisk,
          amount: caseAmount,
          caseId: c.case_id,
        });
      });

      asArray(hops).slice(0, 8).forEach((v) => {
        const vpa = typeof v === "string" ? v : v && (v.vpa || v.payee_vpa);
        if (!vpa) return;
        ensureNode(vpa, "hop", c.case_id, c);
        edges.push({
          a: collector,
          b: vpa,
          flagged: true,
          riskScore: caseRisk,
          amount: Math.round(caseAmount * 0.95),
          caseId: c.case_id,
        });
      });

      asArray(layerOut).slice(0, 8).forEach((v) => {
        const vpa = typeof v === "string" ? v : v && (v.payee_vpa || v.vpa);
        if (!vpa) return;
        ensureNode(vpa, "cashout", c.case_id, c);
        edges.push({
          a: collector,
          b: vpa,
          flagged: true,
          riskScore: caseRisk,
          amount: Math.round(caseAmount * 0.90),
          caseId: c.case_id,
        });
      });
    });

    stateRef.current.nodes = nodes;
    stateRef.current.edges = edges;
    setNodeCount(nodes.size);
  }, [cases]);

  // Main Canvas Render and Animation Loop
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
      const { nodes, edges, hoveredNode, hoveredEdge } = stateRef.current;
      const arr = Array.from(nodes.values());

      // Physics Simulation: Center Gravity + Repulsion + Springs
      for (const n of arr) {
        n.vx += (width / 2 - n.x) * 0.0006;
        n.vy += (height / 2 - n.y) * 0.0006;
      }
      for (let i = 0; i < arr.length; i++) {
        for (let j = i + 1; j < arr.length; j++) {
          const a = arr[i];
          const b = arr[j];
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
      for (const e of edges) {
        const a = nodes.get(e.a);
        const b = nodes.get(e.b);
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
      for (const n of arr) {
        n.vx *= 0.88;
        n.vy *= 0.88;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.min(width - 16, Math.max(16, n.x));
        n.y = Math.min(height - 16, Math.max(16, n.y));
      }

      ctx.clearRect(0, 0, width, height);

      // Render Edges with continuous risk gradient
      for (const e of edges) {
        const a = nodes.get(e.a);
        const b = nodes.get(e.b);
        if (!a || !b) continue;
        const isHovered = hoveredEdge === e;

        ctx.save();
        ctx.strokeStyle = getEdgeStroke(e.riskScore, isHovered);
        ctx.lineWidth = isHovered ? 2.8 : 1.4;
        ctx.setLineDash([5, 5]);
        ctx.lineDashOffset = -t * 26;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
        ctx.restore();
      }

      // Render Nodes
      for (const n of arr) {
        const isHovered = hoveredNode === n;
        const pulse = n.kind === "hub" ? 1 + Math.sin(t * 3 + n.x) * 0.18 : 1;
        const baseR = n.kind === "hub" ? 8.5 : n.kind === "hop" ? 6 : 5;
        const r = (baseR * pulse) + (isHovered ? 2.5 : 0);

        if (n.kind === "hub" || isHovered) {
          const glow = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 3.5);
          glow.addColorStop(0, n.kind === "hub" ? "rgba(179,38,30,0.38)" : "rgba(15,122,61,0.25)");
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
        ctx.lineWidth = isHovered ? 2.5 : 1.5;
        ctx.strokeStyle = isHovered ? "#fbbf24" : "#ffffff";
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

  // Hit Detection & Mouse Event Handlers
  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const { nodes, edges } = stateRef.current;
    const arr = Array.from(nodes.values());

    // 1. Check Node Hits (Euclidean distance <= radius threshold)
    let hitNode = null;
    for (let i = arr.length - 1; i >= 0; i--) {
      const n = arr[i];
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

      // Clamped tooltip positioning
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

    // 2. Check Edge Hits (Point-to-segment distance <= 6.5px)
    let hitEdge = null;
    for (let i = edges.length - 1; i >= 0; i--) {
      const edge = edges[i];
      const a = nodes.get(edge.a);
      const b = nodes.get(edge.b);
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

    // No hit
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
      className="relative w-full h-full overflow-hidden rounded-md bg-[#f8f9fc] select-none"
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      />

      {nodeCount === 0 && (
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
              <div className="font-mono text-xs font-semibold text-white truncate" title={tooltip.vpa}>
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
                <span className="text-[10px] uppercase text-white/60 font-mono">Transaction Flow</span>
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

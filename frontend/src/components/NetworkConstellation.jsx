import React, { useEffect, useRef } from "react";

/**
 * Canvas-based animated force-directed graph of mule-network topology.
 * Nodes derived from case topology (fan_in / hops / fan_out / trigger_txn).
 * Confirmed mule rings pulse red; a lightweight physics sim keeps it alive.
 */
export default function NetworkConstellation({ cases }) {
  const canvasRef = useRef(null);
  const stateRef = useRef({ nodes: new Map(), edges: [], raf: null });

  // Rebuild graph model whenever the case list changes.
  useEffect(() => {
    const nodes = new Map();
    const edges = [];

    function ensureNode(id, kind) {
      if (!id) return null;
      if (!nodes.has(id)) {
        nodes.set(id, {
          id,
          kind,
          x: Math.random() * 800,
          y: Math.random() * 460,
          vx: 0,
          vy: 0,
          flagged: false,
        });
      } else if (kind === "hub") {
        nodes.get(id).kind = "hub";
      }
      return nodes.get(id);
    }

    const asArray = (x) => (Array.isArray(x) ? x : []);

    const ringCases = asArray(cases).filter((c) => c && (c.topology || c.ring_members_vpas));

    asArray(ringCases)
      .slice(0, 14)
      .forEach((c) => {
        const topo = (c && typeof c.topology === "object" && c.topology) || {};
        const trigger = (typeof topo.trigger_txn === "object" && topo.trigger_txn) || c.trigger_txn || {};
        const collector = trigger.payee_vpa || `ring-${c.case_id}`;
        ensureNode(collector, "hub").flagged = true;

        const fanIn = asArray(topo.fan_in);
        const hops = asArray(topo.hops);
        const fanOut = asArray(topo.fan_out);
        const members = asArray(c.ring_members_vpas);

        const layerIn = fanIn.length ? fanIn : members.slice(0, Math.ceil(members.length / 3));
        const layerOut = fanOut.length
          ? fanOut
          : members.slice(Math.ceil((members.length * 2) / 3));

        asArray(layerIn)
          .slice(0, 10)
          .forEach((v) => {
            const vpa = typeof v === "string" ? v : v && (v.payer_vpa || v.vpa);
            if (!vpa) return;
            ensureNode(vpa, "victim");
            edges.push({ a: vpa, b: collector, flagged: true });
          });

        asArray(hops)
          .slice(0, 10)
          .forEach((v) => {
            const vpa = typeof v === "string" ? v : v && (v.vpa || v.payee_vpa);
            if (!vpa) return;
            ensureNode(vpa, "hop");
            edges.push({ a: collector, b: vpa, flagged: true });
          });

        asArray(layerOut)
          .slice(0, 10)
          .forEach((v) => {
            const vpa = typeof v === "string" ? v : v && (v.payee_vpa || v.vpa);
            if (!vpa) return;
            ensureNode(vpa, "cashout");
            edges.push({ a: collector, b: vpa, flagged: true });
          });
      });

    stateRef.current.nodes = nodes;
    stateRef.current.edges = edges;
  }, [cases]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let width = canvas.clientWidth;
    let height = canvas.clientHeight;

    function resize() {
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
      const { nodes, edges } = stateRef.current;
      const arr = Array.from(nodes.values());

      // Simple force simulation: center gravity + node repulsion + edge springs.
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
          const force = 900 / distSq;
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
        const target = 90;
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
        n.vx *= 0.9;
        n.vy *= 0.9;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.min(width - 12, Math.max(12, n.x));
        n.y = Math.min(height - 12, Math.max(12, n.y));
      }

      ctx.clearRect(0, 0, width, height);

      // Edges — animated dashed flow lines.
      ctx.lineWidth = 1.4;
      for (const e of edges) {
        const a = nodes.get(e.a);
        const b = nodes.get(e.b);
        if (!a || !b) continue;
        ctx.save();
        ctx.strokeStyle = e.flagged ? "rgba(179,38,30,0.55)" : "rgba(11,31,58,0.18)";
        ctx.setLineDash([5, 5]);
        ctx.lineDashOffset = -t * 26;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
        ctx.restore();
      }

      // Nodes.
      for (const n of arr) {
        const pulse = n.kind === "hub" ? 1 + Math.sin(t * 3 + n.x) * 0.18 : 1;
        const baseR = n.kind === "hub" ? 8 : n.kind === "hop" ? 5.5 : 4.5;
        const r = baseR * pulse;

        if (n.kind === "hub") {
          const glow = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 4);
          glow.addColorStop(0, "rgba(179,38,30,0.35)");
          glow.addColorStop(1, "rgba(179,38,30,0)");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(n.x, n.y, r * 4, 0, Math.PI * 2);
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
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();
      }

      stateRef.current.raf = requestAnimationFrame(frame);
    }
    stateRef.current.raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(stateRef.current.raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  const nodeCount = stateRef.current.nodes.size;

  return (
    <div className="relative w-full h-full overflow-hidden rounded-md bg-[#f8f9fc]">
      <canvas ref={canvasRef} className="w-full h-full block" />
      {nodeCount === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-sm text-muted font-mono">
          Awaiting mule-ring detections…
        </div>
      )}
      <div className="absolute top-3 left-3 flex gap-3 text-[11px] font-mono text-muted bg-white/80 backdrop-blur px-2 py-1 rounded border border-hairline">
        <LegendDot color="#0f7a3d" label="Victim" />
        <LegendDot color="#b3261e" label="Collector hub" />
        <LegendDot color="#a8660a" label="Layering hop" />
        <LegendDot color="#0b1f3a" label="Cash-out" />
      </div>
    </div>
  );
}

function LegendDot({ color, label }) {
  return (
    <span className="flex items-center gap-1">
      <span className="w-2 h-2 rounded-full inline-block" style={{ background: color }} />
      {label}
    </span>
  );
}

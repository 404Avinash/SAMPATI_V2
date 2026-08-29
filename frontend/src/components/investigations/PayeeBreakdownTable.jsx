import React from "react";
import { formatINR, shortVpa } from "../../services/api";

export default function PayeeBreakdownTable({ caseData }) {
  if (!caseData) return null;

  const topo = (typeof caseData.topology === "object" && caseData.topology) || {};
  const trigger = (typeof topo.trigger_txn === "object" && topo.trigger_txn) || caseData.trigger_txn || {};
  const collector = trigger.payee_vpa || caseData.payee_vpa || "—";
  const members = Array.isArray(caseData.ring_members_vpas) ? caseData.ring_members_vpas : [];

  const fanIn = Array.isArray(topo.fan_in) && topo.fan_in.length > 0
    ? topo.fan_in
    : members.slice(0, Math.ceil(members.length / 3));

  const hops = Array.isArray(topo.hops) && topo.hops.length > 0
    ? topo.hops
    : members.slice(Math.ceil(members.length / 3), Math.ceil((members.length * 2) / 3));

  const fanOut = Array.isArray(topo.fan_out) && topo.fan_out.length > 0
    ? topo.fan_out
    : members.slice(Math.ceil((members.length * 2) / 3));

  return (
    <div className="panel overflow-hidden">
      <div className="panel-header flex items-center justify-between">
        <div className="panel-title">
          <div className="text-[10px] uppercase tracking-wide text-muted font-mono">
            Mule Network Topology
          </div>
          <div className="font-serif font-bold text-sm text-ink-900">
            Payee &amp; Account Breakdown
          </div>
        </div>
        <span className="text-xs font-mono text-muted">
          {members.length || (fanIn.length + hops.length + fanOut.length + 1)} Entities
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs border-collapse">
          <thead>
            <tr className="bg-surface-muted/60 text-muted uppercase text-[10px] border-b border-hairline">
              <th className="py-2.5 px-4 font-semibold">Entity Role</th>
              <th className="py-2.5 px-4 font-semibold">VPA Address</th>
              <th className="py-2.5 px-4 font-semibold">Relationship</th>
              <th className="py-2.5 px-4 font-semibold text-right">Est. Volume</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {/* Collector Hub */}
            <tr className="bg-rose-50/40 hover:bg-rose-50/70 transition-colors">
              <td className="py-2.5 px-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
                  COLLECTOR HUB
                </span>
              </td>
              <td className="py-2.5 px-4 font-bold text-ink-900">{collector}</td>
              <td className="py-2.5 px-4 text-muted">Central aggregator account</td>
              <td className="py-2.5 px-4 text-right font-bold text-ink-900">
                {formatINR(trigger.amount ?? caseData.amount)}
              </td>
            </tr>

            {/* Fan-In Victims */}
            {fanIn.map((item, idx) => {
              const vpa = typeof item === "string" ? item : item?.payer_vpa || item?.vpa || `victim-${idx}`;
              const amt = typeof item === "object" ? item?.amount : null;
              return (
                <tr key={`in-${idx}`} className="hover:bg-surface-muted/50 transition-colors">
                  <td className="py-2.5 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      FAN-IN VICTIM
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-body">{vpa}</td>
                  <td className="py-2.5 px-4 text-muted">Direct inbound transfer</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-muted">
                    {amt ? formatINR(amt) : "—"}
                  </td>
                </tr>
              );
            })}

            {/* Layering Hops */}
            {hops.map((item, idx) => {
              const vpa = typeof item === "string" ? item : item?.payee_vpa || item?.vpa || `hop-${idx}`;
              return (
                <tr key={`hop-${idx}`} className="hover:bg-surface-muted/50 transition-colors">
                  <td className="py-2.5 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                      LAYERING HOP
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-body">{vpa}</td>
                  <td className="py-2.5 px-4 text-muted">Intermediate mule hop</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-muted">—</td>
                </tr>
              );
            })}

            {/* Cash-Out Destinations */}
            {fanOut.map((item, idx) => {
              const vpa = typeof item === "string" ? item : item?.payee_vpa || item?.vpa || `cashout-${idx}`;
              return (
                <tr key={`out-${idx}`} className="hover:bg-surface-muted/50 transition-colors">
                  <td className="py-2.5 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-800 border border-slate-300">
                      CASH-OUT DEST
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-body">{vpa}</td>
                  <td className="py-2.5 px-4 text-muted">Terminal withdrawal account</td>
                  <td className="py-2.5 px-4 text-right tabular-nums text-muted">—</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

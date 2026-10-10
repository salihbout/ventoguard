import type { Kpis } from "../lib/api";
import { eur, pct } from "../lib/format";
import { SkeletonBlock } from "./States";

export function KpiStrip({ k }: { k?: Kpis }) {
  if (!k) return <SkeletonBlock height={96} />;
  return (
    <section className="kpis" aria-label="Fleet key figures">
      <div className="kpi">
        <span className="kpi-label">Turbines at high or critical risk</span>
        <span className={`kpi-value ${k.critical > 0 ? "critical" : ""}`}>{k.at_risk} <span className="small muted">of {k.turbines}</span></span>
        <span className="kpi-note">{k.critical} critical · next 14 days</span>
      </div>
      <div className="kpi">
        <span className="kpi-label">Avoidable cost if acted on now</span>
        <span className="kpi-value">{eur(k.avoidable_if_acted_eur)}</span>
        <span className="kpi-note">planned swap instead of failure</span>
      </div>
      <div className="kpi">
        <span className="kpi-label">Risk-weighted value at stake</span>
        <span className="kpi-value">{eur(k.risk_weighted_eur)}</span>
        <span className="kpi-note">probability × avoidable cost</span>
      </div>
      <div className="kpi">
        <span className="kpi-label">Technical availability, 30 days</span>
        <span className="kpi-value">{pct(k.availability_30d)}</span>
        <span className="kpi-note">target 97.0 %</span>
      </div>
      <div className="kpi">
        <span className="kpi-label">Lost revenue, 30 days</span>
        <span className="kpi-value">{eur(k.lost_revenue_30d_eur)}</span>
        <span className="kpi-note">{Math.round(k.lost_energy_30d_mwh).toLocaleString("en-GB")} MWh not generated</span>
      </div>
    </section>
  );
}

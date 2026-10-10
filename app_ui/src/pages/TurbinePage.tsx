import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { AiBrief } from "../components/AiBrief";
import { RiskBadge } from "../components/RiskBadge";
import { ErrorState, Loading } from "../components/States";
import { TrendChart } from "../components/TrendChart";
import { WorkOrderForm } from "../components/WorkOrderForm";
import { api } from "../lib/api";
import { component, eur, farmLabel, pct } from "../lib/format";

export function TurbinePage() {
  const { id = "" } = useParams();
  const q = useQuery({ queryKey: ["turbine", id], queryFn: () => api.turbine(id) });
  if (q.isPending) return <main className="page"><Loading label={`Loading ${id}`} /></main>;
  if (q.isError) return <main className="page"><ErrorState error={q.error} onRetry={() => q.refetch()} /></main>;
  const { risk, brief, trend, work_orders } = q.data;

  return (
    <main className="page">
      <nav className="crumbs" aria-label="Breadcrumb"><Link to="/">Fleet risk</Link> / {risk.turbine_id}</nav>
      <header className="page-head">
        <div className="title-row">
          <h1 className="mono">{risk.turbine_id}</h1>
          <RiskBadge tier={risk.risk_tier} />
          <span className="muted">{risk.recommended_window}</span>
        </div>
        <p>{farmLabel(risk.farm_name)} · {risk.model} · {risk.turbine_age_years} years in service · gearbox by {risk.gearbox_supplier}</p>
      </header>

      <section className="panel" aria-label="Risk summary">
        <div className="facts">
          <div><div className="fact-label">Failure probability, 14 days</div><div className="fact-value">{pct(risk.failure_prob_14d)}</div></div>
          <div><div className="fact-label">Most likely component</div><div className="fact-value">{component(risk.likely_component)}</div></div>
          <div><div className="fact-label">Avoidable if planned now</div><div className="fact-value">{eur(risk.avoidable_cost_if_caught_eur)}</div></div>
          <div><div className="fact-label">Revenue at stake per day</div><div className="fact-value">{eur(risk.revenue_per_day_eur)}</div></div>
        </div>
        <div style={{ marginTop: 16 }}>
          <div className="fact-label" style={{ marginBottom: 6 }}>Strongest signals against the fleet, 7-day mean</div>
          <div className="evidence">{risk.top_signals}</div>
        </div>
      </section>

      <AiBrief brief={brief} />

      <div className="split-even">
        <section className="panel">
          <h2 className="section-title">Drivetrain temperatures</h2>
          <TrendChart data={trend} unitLeft="°C" series={[
            { key: "avg_gearbox_oil_temp_c", label: "Gearbox oil", color: "#0B2026" },
            { key: "avg_gearbox_bearing_temp_c", label: "Gearbox bearing", color: "#1B5162" },
            { key: "avg_main_bearing_temp_c", label: "Main bearing", color: "#618794" },
            { key: "avg_generator_bearing_temp_c", label: "Generator bearing", color: "#98102A" },
          ]} />
        </section>
        <section className="panel">
          <h2 className="section-title">Vibration and power curve</h2>
          <TrendChart data={trend} unitLeft="mm/s" unitRight="ratio" series={[
            { key: "p95_gearbox_vibration_mm_s", label: "Gearbox vibration p95", color: "#0B2026" },
            { key: "power_curve_ratio", label: "Actual / expected power", color: "#618794", axis: "right" },
          ]} />
        </section>
      </div>

      <section className="panel" aria-labelledby="wo-title">
        <h2 className="section-title" id="wo-title">Plan the repair</h2>
        <WorkOrderForm key={risk.turbine_id} risk={risk} defaultNotes={brief?.recommended_action.replace(/ ; /g, "\n") ?? ""} />
        {work_orders.length > 0 && (
          <table className="table" style={{ marginTop: 24 }}>
            <thead><tr><th>#</th><th>Priority</th><th>Status</th><th>Planned</th><th>Crew</th><th>Created by</th></tr></thead>
            <tbody>{work_orders.map((w) => (
              <tr key={w.wo_id}><td className="mono">{w.wo_id}</td><td>{w.priority}</td><td>{w.status.replace("_", " ").toLowerCase()}</td>
                <td>{w.planned_date}</td><td>{w.crew}</td><td className="muted">{w.created_by}</td></tr>
            ))}</tbody>
          </table>
        )}
      </section>
    </main>
  );
}

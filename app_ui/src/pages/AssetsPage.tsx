import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";
import { Empty, ErrorState, SkeletonBlock } from "../components/States";
import { api, type AssetsView } from "../lib/api";
import { component, eur, farmLabel, pct } from "../lib/format";

const axis = { fontSize: 12, fill: "#4A5568", fontFamily: "DM Sans" };
const tip = { fontFamily: "DM Sans", fontSize: 13, borderRadius: 8 };

/** Head of Asset Management view: reliability by farm, component, supplier and age, plus the maintenance calendar. */
export function AssetsPage() {
  const q = useQuery({ queryKey: ["view-assets"], queryFn: api.assets });
  return (
    <main className="page">
      <header className="page-head">
        <h1>Asset performance</h1>
        <p>Where the fleet loses availability and money, which assets fail most, and the planned maintenance calendar.</p>
      </header>
      {q.isPending ? <SkeletonBlock height={520} /> : q.isError ? <ErrorState error={q.error} onRetry={() => q.refetch()} /> : <Body d={q.data} />}
    </main>
  );
}

function Body({ d }: { d: AssetsView }) {
  const failures = d.components.reduce((s, c) => s + c.failures, 0);
  const mttrDays = d.components.reduce((s, c) => s + c.mttr_hours * c.failures, 0) / Math.max(failures, 1) / 24;
  const crane = d.components.reduce((s, c) => s + c.crane_share * c.failures, 0) / Math.max(failures, 1);
  const planned = d.mix.planned_orders, unplanned = d.mix.unplanned_failures_90d;
  return (
    <>
      <section className="kpis" aria-label="Asset key figures">
        <div className="kpi"><span className="kpi-label">Mean time to repair</span><span className="kpi-value">{mttrDays.toFixed(1)} days</span>
          <span className="kpi-note">across {failures} unplanned failures</span></div>
        <div className="kpi"><span className="kpi-label">Failures needing a crane</span><span className="kpi-value">{pct(crane, 0)}</span>
          <span className="kpi-note">the main driver of downtime and cost</span></div>
        <div className="kpi"><span className="kpi-label">Planned vs unplanned, last 90 days</span>
          <span className="kpi-value">{planned} : {unplanned}</span>
          <span className="kpi-note">planned work orders vs unplanned failures</span></div>
        <div className="kpi"><span className="kpi-label">Farms below the 97 % target</span>
          <span className="kpi-value">{d.farms.filter((f) => f.availability_period < d.target_availability).length} of {d.farms.length}</span>
          <span className="kpi-note">technical availability, whole period</span></div>
      </section>

      <section className="panel" aria-labelledby="farms-title">
        <h2 className="section-title" id="farms-title">Reliability by farm</h2>
        <div className="table-scroll">
          <table className="table">
            <thead><tr><th>Farm</th><th className="num">Availability</th><th className="num">30 days</th><th className="num">Unplanned failures</th>
              <th className="num">MTTR</th><th className="num">Repair cost</th><th className="num">Total failure cost</th><th className="num">At risk now</th></tr></thead>
            <tbody>{d.farms.map((f) => (
              <tr key={f.farm_name}>
                <td><b>{farmLabel(f.farm_name)}</b></td>
                <td className={`num ${f.availability_period < d.target_availability ? "neg" : ""}`}>{pct(f.availability_period)}</td>
                <td className="num">{pct(f.availability)}</td>
                <td className="num">{f.failures ?? 0}</td>
                <td className="num">{((f.mttr_hours ?? 0) / 24).toFixed(1)} d</td>
                <td className="num">{eur(f.repair_cost_eur)}</td>
                <td className="num">{eur(f.event_cost_eur)}</td>
                <td className="num">{f.critical + f.high > 0 ? <b className="neg">{f.critical + f.high}</b> : 0}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </section>

      <div className="split-even">
        <section className="panel" aria-labelledby="comp-title">
          <h2 className="section-title" id="comp-title">Reliability by component</h2>
          <table className="table">
            <thead><tr><th>Component</th><th className="num">Failures</th><th className="num">MTTR</th><th className="num">Cost per event</th><th className="num">Crane</th></tr></thead>
            <tbody>{d.components.map((c) => (
              <tr key={c.component}>
                <td>{component(c.component)}</td><td className="num">{c.failures}</td><td className="num">{(c.mttr_hours / 24).toFixed(1)} d</td>
                <td className="num">{eur(c.cost_per_event_eur)}</td><td className="num">{pct(c.crane_share, 0)}</td>
              </tr>
            ))}</tbody>
          </table>
        </section>
        <section className="panel" aria-labelledby="sup-title">
          <h2 className="section-title" id="sup-title">Gearbox failures per 10 turbines</h2>
          <ResponsiveContainer width="100%" height={110}>
            <BarChart layout="vertical" data={d.suppliers.map((s) => ({ name: s.supplier, rate: s.failures_per_10_turbines, s }))} margin={{ top: 0, right: 24, left: 8, bottom: 0 }}>
              <XAxis type="number" hide /><YAxis type="category" dataKey="name" tick={axis} tickLine={false} axisLine={false} width={110} />
              <Tooltip contentStyle={tip} formatter={(x: number, _n, p) => [`${x.toFixed(2)} (${p.payload.s.gearbox_failures} failures, ${p.payload.s.turbines} turbines, avg ${p.payload.s.avg_age_years} yrs)`, "Per 10 turbines"]} />
              <Bar dataKey="rate" fill="#1B5162" radius={[0, 4, 4, 0]} label={{ position: "right", style: axis, formatter: (x: number) => x.toFixed(2) }} />
            </BarChart>
          </ResponsiveContainer>
          <h2 className="section-title" style={{ marginTop: "var(--db-space-lg)" }}>All failures per 10 turbines, by age</h2>
          <ResponsiveContainer width="100%" height={140}>
            <BarChart layout="vertical" data={d.ages.map((a) => ({ name: a.cohort, rate: a.failures_per_10_turbines, a }))} margin={{ top: 0, right: 24, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="#EEEDE9" horizontal={false} />
              <XAxis type="number" hide /><YAxis type="category" dataKey="name" tick={axis} tickLine={false} axisLine={false} width={110} />
              <Tooltip contentStyle={tip} formatter={(x: number, _n, p) => [`${x.toFixed(2)} (${p.payload.a.failures} failures, ${p.payload.a.turbines} turbines)`, "Per 10 turbines"]} />
              <Bar dataKey="rate" fill="#618794" radius={[0, 4, 4, 0]} label={{ position: "right", style: axis, formatter: (x: number) => x.toFixed(1) }} />
            </BarChart>
          </ResponsiveContainer>
        </section>
      </div>

      <section className="panel" aria-labelledby="cal-title">
        <h2 className="section-title" id="cal-title">Maintenance calendar</h2>
        {d.calendar.length === 0 ? <Empty title="No planned repairs yet">Plan repairs from the <Link to="/">risk board</Link>.</Empty> : (
          <table className="table">
            <thead><tr><th>Planned</th><th>Turbine</th><th>Farm</th><th>Component</th><th>Priority</th><th>Status</th><th>Crew</th><th className="num">€ protected</th></tr></thead>
            <tbody>{d.calendar.map((w) => (
              <tr key={w.wo_id}>
                <td className="mono">{w.planned_date ?? "—"}</td><td><Link to={`/turbines/${w.turbine_id}`} className="mono">{w.turbine_id}</Link></td>
                <td>{farmLabel(w.farm_name ?? "")}</td><td>{component(w.component ?? "")}</td><td>{w.priority}</td>
                <td>{w.status.replace("_", " ").toLowerCase()}</td><td>{w.crew}</td><td className="num">{eur(w.expected_avoidable_eur)}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </section>
    </>
  );
}

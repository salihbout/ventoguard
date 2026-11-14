import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";
import { ErrorState, SkeletonBlock } from "../components/States";
import { api, type ExecutiveView, type Insight } from "../lib/api";
import { component, eur, farmLabel, pct } from "../lib/format";

const axis = { fontSize: 12, fill: "#4A5568", fontFamily: "DM Sans" };
const TONE: Record<Insight["tone"], { label: string; cls: string }> = {
  risk: { label: "Risk", cls: "tone-risk" }, action: { label: "Decision", cls: "tone-action" },
  good: { label: "On track", cls: "tone-good" }, insight: { label: "Insight", cls: "tone-insight" },
};
const MONTH = (m: string) => new Date(m + "-01").toLocaleDateString("en-GB", { month: "short" });

/** COO view: is the fleet earning what it should, what is VentoGuard worth, and what needs a decision this week. */
export function ExecutivePage() {
  const q = useQuery({ queryKey: ["view-executive"], queryFn: api.executive });
  return (
    <main className="page">
      <header className="page-head">
        <h1>Executive overview</h1>
        <p>Fleet performance, the value of planning repairs before they fail, and the decisions that need you this week.
           {q.data && <> Data as of <span className="mono">{q.data.as_of}</span>.</>}</p>
      </header>
      {q.isPending ? <SkeletonBlock height={520} /> : q.isError ? <ErrorState error={q.error} onRetry={() => q.refetch()} /> : <Body d={q.data} />}
    </main>
  );
}

function Body({ d }: { d: ExecutiveView }) {
  const v = d.value, n = d.now;
  const atRisk = n.critical + n.high;
  const availGap = (d.fleet_30d.availability - d.target_availability) * 100;
  const compTotal = d.components.reduce((s, c) => s + c.cost_eur, 0) || 1;
  return (
    <>
      <section className="kpis exec" aria-label="Executive key figures">
        <div className="kpi">
          <span className="kpi-label">Value of VentoGuard, per year</span>
          <span className="kpi-value big">{eur(v.net_benefit_annual_eur)}</span>
          <span className="kpi-note">net, at a {pct(v.catch_rate_assumed, 0)} catch rate · {eur(v.net_benefit_at_50pct_eur)} at 50 %</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Unplanned failure cost, run rate</span>
          <span className="kpi-value big">{eur(v.unplanned_cost_annual_eur)}<span className="small muted"> / yr</span></span>
          <span className="kpi-note">{v.failures_observed} failures in {v.observed_days} days, repair + lost revenue</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Technical availability, 30 days</span>
          <span className="kpi-value big">{pct(d.fleet_30d.availability)}</span>
          <span className={`kpi-note ${availGap < 0 ? "neg" : "pos"}`}>
            {availGap >= 0 ? "+" : ""}{availGap.toFixed(1)} pp vs 97 % target · +{v.availability_uplift_pp.toFixed(1)} pp with early warning
          </span>
        </div>
        <div className="kpi">
          <span className="kpi-label">At stake right now</span>
          <span className={`kpi-value big ${n.critical ? "critical" : ""}`}>{eur(n.avoidable_now_eur)}</span>
          <span className="kpi-note">{atRisk} turbine{atRisk !== 1 ? "s" : ""} at high or critical risk · {n.at_risk_without_order} without a work order</span>
        </div>
      </section>

      <div className="exec-grid">
        <section className="panel" aria-labelledby="ins-title">
          <h2 className="section-title" id="ins-title">Key insights</h2>
          <ul className="insights">
            {d.insights.map((i) => (
              <li key={i.title} className={TONE[i.tone].cls}>
                <span className="tone">{TONE[i.tone].label}</span>
                <div><b>{i.title}</b><p>{i.detail}</p></div>
                <Link to={i.link} className="more" aria-label={`Details: ${i.title}`}>Details →</Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel decision" aria-labelledby="dec-title">
          <h2 className="section-title" id="dec-title">Decisions this week</h2>
          {n.at_risk_without_order > 0 ? (
            <>
              <p className="dec-big">{eur(n.unprotected_eur)}</p>
              <p>avoidable by approving planned repairs on <b>{n.at_risk_without_order} turbine{n.at_risk_without_order !== 1 ? "s" : ""}</b> that
                 have no work order yet. Each needs a crane slot and a spare.</p>
              <Link to="/" className="cta">Review the risk board →</Link>
            </>
          ) : <p>All high and critical turbines have a planned repair. Nothing needs your sign-off.</p>}
          <div className="dec-foot">
            <span>Already protected</span><b>{eur(n.protected_eur)}</b>
            <span>Open work orders</span><b>{n.open_orders}</b>
          </div>
        </section>
      </div>

      <div className="split-even">
        <section className="panel" aria-labelledby="av-title">
          <h2 className="section-title" id="av-title">Technical availability by month</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={d.monthly.map((m) => ({ ...m, label: MONTH(m.month), pct: m.availability * 100 }))} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#EEEDE9" vertical={false} />
              <XAxis dataKey="label" tick={axis} tickLine={false} axisLine={{ stroke: "#C4CCD6" }} />
              <YAxis domain={[94, 100]} tick={axis} tickLine={false} axisLine={false} width={40} tickFormatter={(x) => `${x}%`} />
              <Tooltip contentStyle={{ fontFamily: "DM Sans", fontSize: 13, borderRadius: 8 }} formatter={(x: number) => [`${x.toFixed(1)} %`, "Availability"]} />
              <ReferenceLine y={97} stroke="#98102A" strokeDasharray="4 4" label={{ value: "Target 97 %", position: "insideBottomRight", style: { ...axis, fill: "#98102A" } }} />
              <Line type="monotone" dataKey="pct" stroke="#1B5162" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </section>
        <section className="panel" aria-labelledby="cost-title">
          <h2 className="section-title" id="cost-title">Where unplanned cost comes from</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart layout="vertical" data={d.components.map((c) => ({ name: component(c.component), cost: c.cost_eur, share: c.cost_eur / compTotal }))}
                      margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="#EEEDE9" horizontal={false} />
              <XAxis type="number" tick={axis} tickLine={false} axisLine={false} tickFormatter={(x) => eur(x)} />
              <YAxis type="category" dataKey="name" tick={axis} tickLine={false} axisLine={false} width={120} />
              <Tooltip contentStyle={{ fontFamily: "DM Sans", fontSize: 13, borderRadius: 8 }}
                       formatter={(x: number, _n, p) => [`${eur(x)} (${(p.payload.share * 100).toFixed(0)} %)`, "Unplanned cost"]} />
              <Bar dataKey="cost" fill="#1B5162" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>
      </div>

      <section className="panel" aria-labelledby="farm-title">
        <h2 className="section-title" id="farm-title">Farm scorecard</h2>
        <div className="table-scroll">
          <table className="table">
            <thead><tr><th>Farm</th><th>Status</th><th className="num">Availability, {v.observed_days} days</th><th className="num">Availability, 30 days</th>
              <th className="num">Lost revenue, 30 days</th><th className="num">Turbines</th><th className="num">At risk now</th></tr></thead>
            <tbody>{d.farms.map((f) => {
              const below = f.availability_period < d.target_availability;
              return (
                <tr key={f.farm_name}>
                  <td><b>{farmLabel(f.farm_name)}</b></td>
                  <td><span className={`status ${below ? "below" : "ok"}`}>{below ? "Below target" : "On target"}</span></td>
                  <td className="num">{pct(f.availability_period)}</td>
                  <td className="num">{pct(f.availability)}</td>
                  <td className="num">{eur(f.lost_revenue_eur)}</td>
                  <td className="num">{f.turbines}</td>
                  <td className="num">{f.critical + f.high > 0 ? <b className="neg">{f.critical + f.high}</b> : 0}</td>
                </tr>
              );
            })}</tbody>
          </table>
        </div>
      </section>
    </>
  );
}

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { FleetMap } from "../components/FleetMap";
import { KpiStrip } from "../components/KpiStrip";
import { RiskTable } from "../components/RiskTable";
import { ErrorState, SkeletonBlock } from "../components/States";
import { api, type Tier } from "../lib/api";
import { farmLabel } from "../lib/format";

const TIERS: Tier[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "DOWN"];
const axis = { fontSize: 12, fill: "#4A5568", fontFamily: "DM Sans" };

export function FleetPage() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: api.kpis });
  const board = useQuery({ queryKey: ["risk-board"], queryFn: api.riskBoard });
  const daily = useQuery({ queryKey: ["fleet-daily"], queryFn: () => api.fleetDaily(30) });
  const [farm, setFarm] = useState<string>("all");
  const [tiers, setTiers] = useState<Tier[]>(["CRITICAL", "HIGH", "MEDIUM"]);

  const farms = useMemo(() => [...new Set((board.data ?? []).map((r) => r.farm_name))].sort(), [board.data]);
  const rows = (board.data ?? []).filter((r) => tiers.includes(r.risk_tier) && (farm === "all" || r.farm_name === farm));
  const toggle = (t: Tier) => setTiers((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]));

  return (
    <main className="page">
      <header className="page-head">
        <h1>Fleet risk</h1>
        <p>Probability of a major drivetrain failure in the next 14 days for every turbine, with the component most likely to fail and
           the cost avoided by planning the repair now. Scored daily from SCADA telemetry and technician notes.</p>
      </header>

      {kpis.isError ? <ErrorState error={kpis.error} onRetry={() => kpis.refetch()} /> : <KpiStrip k={kpis.data} />}

      <div className="split">
        <section className="panel" aria-labelledby="map-title">
          <h2 className="section-title" id="map-title">Turbines by risk</h2>
          {board.isPending ? <SkeletonBlock height={480} /> : board.isError ? <ErrorState error={board.error} onRetry={() => board.refetch()} /> : <FleetMap rows={board.data} />}
        </section>
        <section className="panel" aria-labelledby="board-title">
          <h2 className="section-title" id="board-title">Risk board</h2>
          <div className="toolbar" role="group" aria-label="Filters">
            {TIERS.map((t) => (
              <button key={t} type="button" className="chip" aria-pressed={tiers.includes(t)} onClick={() => toggle(t)}>
                {t === "DOWN" ? "In repair" : t[0] + t.slice(1).toLowerCase()}
              </button>
            ))}
            <label className="field" style={{ marginLeft: "auto", gridAutoFlow: "column", alignItems: "center" }}>
              <span className="muted">Farm</span>
              <select value={farm} onChange={(e) => setFarm(e.target.value)}>
                <option value="all">All farms</option>
                {farms.map((f) => <option key={f} value={f}>{farmLabel(f)}</option>)}
              </select>
            </label>
          </div>
          {board.isPending ? <SkeletonBlock height={360} /> : board.isError ? <ErrorState error={board.error} /> : <RiskTable rows={rows} />}
        </section>
      </div>

      <section className="panel" aria-labelledby="prod-title">
        <h2 className="section-title" id="prod-title">Generation and losses, last 30 days</h2>
        {daily.isPending ? <SkeletonBlock height={240} /> : daily.isError ? <ErrorState error={daily.error} /> : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={daily.data.map((d) => ({ ...d, day: d.reading_date.slice(5) }))} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#EEEDE9" vertical={false} />
              <XAxis dataKey="day" tick={axis} tickLine={false} axisLine={{ stroke: "#C4CCD6" }} minTickGap={20} />
              <YAxis tick={axis} tickLine={false} axisLine={false} width={56} label={{ value: "MWh", angle: -90, position: "insideLeft", style: axis }} />
              <Tooltip contentStyle={{ fontFamily: "DM Sans", fontSize: 13, borderRadius: 8 }} formatter={(v: number) => v.toFixed(0) + " MWh"} />
              <Legend wrapperStyle={{ fontSize: 13, fontFamily: "DM Sans" }} />
              <Bar dataKey="energy_mwh" name="Generated" stackId="e" fill="#1B5162" />
              <Bar dataKey="lost_energy_mwh" name="Lost to faults and derating" stackId="e" fill="#98102A" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>
    </main>
  );
}

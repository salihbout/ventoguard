import { useNavigate } from "react-router-dom";
import type { RiskRow } from "../lib/api";
import { component, eur, farmLabel } from "../lib/format";
import { ProbBar, RiskBadge } from "./RiskBadge";
import { Empty } from "./States";

export function RiskTable({ rows }: { rows: RiskRow[] }) {
  const nav = useNavigate();
  if (!rows.length) return <Empty title="No turbines match these filters">Widen the risk tiers or choose another farm.</Empty>;
  return (
    <div className="table-scroll">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Turbine</th><th scope="col">Farm</th><th scope="col">Risk</th>
            <th scope="col">Failure probability, 14 d</th><th scope="col">Likely component</th>
            <th scope="col">Act</th><th scope="col" className="num">Expected € avoidable</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.turbine_id} className="link" tabIndex={0} onClick={() => nav(`/turbines/${r.turbine_id}`)}
                onKeyDown={(e) => e.key === "Enter" && nav(`/turbines/${r.turbine_id}`)}>
              <td className="mono">{r.turbine_id}</td>
              <td>{farmLabel(r.farm_name)}</td>
              <td><RiskBadge tier={r.risk_tier} /></td>
              <td><ProbBar p={r.failure_prob_14d} tier={r.risk_tier} /></td>
              <td>{component(r.likely_component)}</td>
              <td className="muted">{r.recommended_window}</td>
              <td className="num">{eur(r.expected_avoidable_cost_eur)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

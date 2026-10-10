import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { RiskBadge } from "../components/RiskBadge";
import { Empty, ErrorState, Loading } from "../components/States";
import { api, type WoStatus } from "../lib/api";
import { component, eur, farmLabel } from "../lib/format";

const STATUSES: WoStatus[] = ["OPEN", "SCHEDULED", "IN_PROGRESS", "DONE"];

export function WorkOrdersPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["work-orders"], queryFn: api.workOrders });
  const update = useMutation({
    mutationFn: ({ id, status }: { id: number; status: WoStatus }) => api.updateWorkOrder(id, { status }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["work-orders"] }); qc.invalidateQueries({ queryKey: ["kpis"] }); },
  });
  const open = (q.data ?? []).filter((w) => w.status !== "DONE");

  return (
    <main className="page">
      <header className="page-head">
        <h1>Work orders</h1>
        <p>Planned repairs created from the risk board. They are stored transactionally in Lakebase (<span className="mono">vg_ops.work_orders</span>).</p>
      </header>
      {q.isPending ? <Loading label="Loading work orders" /> : q.isError ? <ErrorState error={q.error} onRetry={() => q.refetch()} /> : (
        <>
          <section className="kpis" aria-label="Work order summary">
            <div className="kpi"><span className="kpi-label">Open work orders</span><span className="kpi-value">{open.length}</span></div>
            <div className="kpi"><span className="kpi-label">P1, within 72 hours</span><span className="kpi-value">{open.filter((w) => w.priority === "P1").length}</span></div>
            <div className="kpi"><span className="kpi-label">Value protected by open orders</span>
              <span className="kpi-value">{eur(open.reduce((s, w) => s + Number(w.expected_avoidable_eur ?? 0), 0))}</span></div>
          </section>
          <section className="panel">
            {q.data.length === 0 ? <Empty title="No work orders yet">Open a turbine from the risk board and plan the repair.</Empty> : (
              <div className="table-scroll">
                <table className="table">
                  <thead><tr><th>#</th><th>Turbine</th><th>Farm</th><th>Risk now</th><th>Component</th><th>Priority</th><th>Planned</th>
                    <th>Crew</th><th>Status</th><th className="num">Expected € avoidable</th><th>Created by</th></tr></thead>
                  <tbody>{q.data.map((w) => (
                    <tr key={w.wo_id}>
                      <td className="mono">{w.wo_id}</td>
                      <td className="mono"><Link to={`/turbines/${w.turbine_id}`}>{w.turbine_id}</Link></td>
                      <td>{w.farm_name ? farmLabel(w.farm_name) : "–"}</td>
                      <td>{w.risk_tier && <RiskBadge tier={w.risk_tier} />}</td>
                      <td>{component(w.component ?? "")}</td>
                      <td>{w.priority}</td><td>{w.planned_date}</td><td>{w.crew}</td>
                      <td>
                        <label className="field" style={{ display: "block" }}>
                          <span className="sr-only" style={{ position: "absolute", left: -9999 }}>Status of work order {w.wo_id}</span>
                          <select value={w.status} disabled={update.isPending}
                                  onChange={(e) => update.mutate({ id: w.wo_id, status: e.target.value as WoStatus })}>
                            {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ").toLowerCase()}</option>)}
                          </select>
                        </label>
                      </td>
                      <td className="num">{eur(w.expected_avoidable_eur)}</td>
                      <td className="muted">{w.created_by}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            )}
            {update.isError && <p role="alert" style={{ color: "#C2260F" }}>Could not update: {(update.error as Error).message}</p>}
          </section>
        </>
      )}
    </main>
  );
}

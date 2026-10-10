import { Button } from "@databricks/design-system";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, type RiskRow } from "../lib/api";

const CREWS = ["North crew (Uckermark)", "Coast crew (Ostfriesland)", "West crew (Eifel / Hunsrück)", "OEM service team"];
const DEFAULT_CREW: Record<string, string> = { F01: CREWS[0], F02: CREWS[1], F03: CREWS[2], F04: CREWS[2] };

function plusDays(days: number) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export function WorkOrderForm({ risk, defaultNotes }: { risk: RiskRow; defaultNotes: string }) {
  const qc = useQueryClient();
  const tier = risk.risk_tier;
  const [priority, setPriority] = useState(tier === "CRITICAL" ? "P1" : tier === "HIGH" ? "P2" : "P3");
  const [planned, setPlanned] = useState(plusDays(tier === "CRITICAL" ? 2 : tier === "HIGH" ? 6 : 21));
  const [crew, setCrew] = useState(DEFAULT_CREW[risk.farm_id] ?? CREWS[0]);
  const [notes, setNotes] = useState(defaultNotes);
  const m = useMutation({
    mutationFn: () => api.createWorkOrder({ turbine_id: risk.turbine_id, priority, planned_date: planned, crew, notes }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["turbine", risk.turbine_id] });
      qc.invalidateQueries({ queryKey: ["work-orders"] });
      qc.invalidateQueries({ queryKey: ["kpis"] });
    },
  });

  return (
    <form className="form" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
      <div className="form-row">
        <label className="field">Priority
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="P1">P1 · within 72 hours</option>
            <option value="P2">P2 · within 7 days</option>
            <option value="P3">P3 · next scheduled visit</option>
          </select>
        </label>
        <label className="field">Planned date
          <input type="date" value={planned} onChange={(e) => setPlanned(e.target.value)} required />
        </label>
        <label className="field">Crew
          <select value={crew} onChange={(e) => setCrew(e.target.value)}>{CREWS.map((c) => <option key={c}>{c}</option>)}</select>
        </label>
      </div>
      <label className="field">Notes
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={2000} />
      </label>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <Button componentId="vg.wo.create" type="primary" htmlType="submit" loading={m.isPending}>Create work order</Button>
        {m.isSuccess && <span className="small" role="status">Work order #{m.data.wo_id} saved to Lakebase.</span>}
        {m.isError && <span className="small" role="alert" style={{ color: "#C2260F" }}>Could not save: {(m.error as Error).message}</span>}
      </div>
    </form>
  );
}

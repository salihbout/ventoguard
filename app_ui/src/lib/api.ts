export type Tier = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "DOWN";

export interface Kpis {
  score_date: string; model_version: number; turbines: number; at_risk: number; critical: number;
  avoidable_if_acted_eur: number; risk_weighted_eur: number; availability_30d: number;
  lost_revenue_30d_eur: number; lost_energy_30d_mwh: number; open_work_orders: number;
}
export interface RiskRow {
  turbine_id: string; farm_id: string; farm_name: string; model: string; latitude: number; longitude: number;
  turbine_age_years: number; gearbox_supplier: string; score_date: string; failure_prob_14d: number; risk_tier: Tier;
  recommended_window: string; likely_component: string; anomaly_zscore: number; top_signals: string;
  avoidable_cost_if_caught_eur: number; expected_avoidable_cost_eur: number;
  corrective_cost_eur?: number; planned_cost_eur?: number; revenue_per_day_eur?: number;
}
export interface FleetDay { reading_date: string; energy_mwh: number; lost_energy_mwh: number; lost_revenue_eur: number; technical_availability: number }
export interface Brief {
  headline: string; diagnosis: string; recommended_action: string; urgency_days: number; crew_and_parts: string;
  business_case: string; llm_endpoint: string; generated_at: string;
}
export interface TrendDay {
  reading_date: string; avg_gearbox_oil_temp_c: number; avg_gearbox_bearing_temp_c: number; avg_main_bearing_temp_c: number;
  avg_generator_bearing_temp_c: number; p95_gearbox_vibration_mm_s: number; avg_hydraulic_pressure_bar: number;
  power_curve_ratio: number; energy_mwh: number; technical_availability: number;
}
export type WoStatus = "OPEN" | "SCHEDULED" | "IN_PROGRESS" | "DONE";
export interface WorkOrder {
  wo_id: number; turbine_id: string; component: string; priority: "P1" | "P2" | "P3"; status: WoStatus;
  planned_date: string; crew: string; notes: string; failure_prob_14d: number; expected_avoidable_eur: number;
  created_by: string; created_at: string; farm_name?: string; risk_tier?: Tier;
}
export interface TurbineDetail { risk: RiskRow; brief: Brief | null; trend: TrendDay[]; work_orders: WorkOrder[] }
export interface Farm { farm_id: string; farm_name: string; turbines: number; at_risk: number; latitude: number; longitude: number }
export interface GenieAnswer {
  conversation_id: string; message_id: string; status: string; text: string; sql: string | null;
  columns: string[]; rows: (string | null)[][]; row_count: number;
}


export interface ValueCase {
  failures_observed: number; observed_days: number; unplanned_cost_annual_eur: number; net_benefit_annual_eur: number;
  net_benefit_at_50pct_eur: number; false_alarm_cost_annual_eur: number; downtime_days_avoided_annual: number;
  availability_uplift_pp: number; catch_rate_assumed: number;
}
export interface FarmScore {
  farm_name: string; availability_period: number; availability: number; lost_revenue_eur: number; lost_revenue_period_eur: number;
  energy_mwh: number; turbines: number; critical: number; high: number;
  failures?: number; mttr_hours?: number; repair_cost_eur?: number; event_cost_eur?: number;
}
export interface Insight { tone: "risk" | "action" | "good" | "insight"; title: string; detail: string; link: string }
export interface ExecutiveView {
  as_of: string; target_availability: number; value: ValueCase;
  now: { critical: number; high: number; avoidable_now_eur: number; risk_weighted_eur: number; at_risk_without_order: number;
         unprotected_eur: number; open_orders: number; protected_eur: number };
  fleet_30d: { availability: number; lost_revenue_eur: number; revenue_eur: number; as_of: string };
  monthly: { month: string; availability: number; lost_revenue_eur: number; days: number }[];
  components: { component: string; failures: number; cost_eur: number; avg_days_down: number }[];
  farms: FarmScore[]; insights: Insight[];
}
export interface Supplier { supplier: string; turbines: number; avg_age_years: number; gearbox_failures: number; failures_per_10_turbines: number }
export interface AssetsView {
  target_availability: number; farms: FarmScore[];
  components: { component: string; failures: number; mttr_hours: number; cost_per_event_eur: number; crane_share: number }[];
  suppliers: Supplier[]; ages: { cohort: string; turbines: number; failures: number; failures_per_10_turbines: number }[];
  calendar: { wo_id: number; turbine_id: string; farm_name: string; component: string; priority: string; status: string;
              planned_date: string; crew: string; expected_avoidable_eur: number }[];
  mix: { planned_orders: number; unplanned_failures_90d: number };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, { headers: { "content-type": "application/json" }, ...init });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* body was not JSON */ }
    throw new Error(`${res.status}: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  kpis: () => request<Kpis>("/kpis"),
  executive: () => request<ExecutiveView>("/views/executive"),
  assets: () => request<AssetsView>("/views/assets"),
  farms: () => request<Farm[]>("/farms"),
  riskBoard: () => request<RiskRow[]>("/risk-board"),
  fleetDaily: (days = 30) => request<FleetDay[]>(`/fleet/daily?days=${days}`),
  turbine: (id: string) => request<TurbineDetail>(`/turbines/${encodeURIComponent(id)}`),
  workOrders: () => request<WorkOrder[]>("/work-orders"),
  createWorkOrder: (body: { turbine_id: string; priority: string; planned_date: string; crew: string; notes: string }) =>
    request<WorkOrder>("/work-orders", { method: "POST", body: JSON.stringify(body) }),
  updateWorkOrder: (id: number, body: Partial<Pick<WorkOrder, "status" | "planned_date" | "priority" | "crew">>) =>
    request<WorkOrder>(`/work-orders/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  askGenie: (question: string, conversation_id?: string) =>
    request<GenieAnswer>("/genie/ask", { method: "POST", body: JSON.stringify({ question, conversation_id }) }),
};

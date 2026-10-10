"""Derive every figure used in the deck from the committed evidence files -> deck/numbers.json.

Usage: python deck/extract_numbers.py   (run from the repo root, after the evidence has been exported)
"""
import json
import re

EV = "evidence/"
vc = json.load(open(EV + "queries/value_case.result.json"))[0]
comp = json.load(open(EV + "queries/failure_cost_by_component.result.json"))
farms = {r["farm_name"]: r for r in json.load(open(EV + "queries/availability_by_farm.result.json"))}
risk = json.load(open(EV + "queries/risk_board_top.result.json"))
briefs = json.load(open(EV + "queries/ai_briefs.result.json"))
exp = json.load(open(EV + "queries/pipeline_expectations.result.txt"))
train = open(EV + "notebook_runs/02_train_failure_model.md").read()
score = open(EV + "notebook_runs/03_score_and_genai.md").read()


def metric(k):
    return float(re.search(rf"^{k}\s+([\d.]+)", train, re.M).group(1))


backtest = re.findall(r"^\| (F\d\d-T\d\d) \| (\w+) \| (2026-\d\d-\d\d) \| (\d+) \| [\d.]+ \| True \|", train, re.M)
live = re.findall(r"^\| (F\d\d-T\d\d) \| (\w+) \| 2026-[\d\-T:.Z]+ \| (\d+) \| True \| (\w+) \| ([\d.]+) \|", score, re.M)
brief = briefs[0]
N = dict(
    net_annual_benefit_eur=float(vc["net_annual_benefit_eur"]), unplanned_cost_annualised_eur=float(vc["unplanned_cost_annualised_eur"]),
    avoidable_100=float(vc["avoidable_annualised_at_100pct_eur"]), avoidable_75=float(vc["avoidable_annualised_at_75pct_eur"]),
    false_alarm_cost=float(vc["false_alarm_inspection_cost_annualised_eur"]), availability_uplift_pp=float(vc["availability_uplift_pp"]),
    downtime_days_avoided=int(float(vc["turbine_downtime_days_avoided_per_year"])), failures_observed=int(vc["failures_observed"]),
    observed_days=int(vc["observed_days"]), median_lead_days=metric("median_lead_days_caught"),
    bt_caught=int(metric("test_failures_caught_3d_ahead")), bt_total=int(metric("test_failures")),
    auc=metric("test_roc_auc"), pr_auc=metric("test_pr_auc"), precision=metric("test_precision_at_0_5"),
    false_alarm_weeks=int(metric("false_alarm_turbine_weeks")),
    avail_hunsrueck=float(farms["Hunsrueck Hoehe"]["technical_availability_pct"]),
    avail_fleet=round(sum(float(f["technical_availability_pct"]) for f in farms.values()) / len(farms), 2),
    by_component=[dict(component=c["component"], failures=int(c["failures"]), avg_downtime_days=float(c["avg_downtime_days"]),
                       total_eur=float(c["total_event_cost_eur"])) for c in comp],
    n_critical=sum(r["risk_tier"] == "CRITICAL" for r in risk), n_high=sum(r["risk_tier"] == "HIGH" for r in risk),
    brief_turbine=brief["turbine_id"], brief_headline=brief["headline"], brief_diagnosis=brief["diagnosis"],
    brief_business_case=brief["business_case"],
    backtest=[dict(turbine_id=t, component=c, failure_date=d, lead=int(lead)) for t, c, d, lead in backtest],
    live_check=[dict(turbine_id=t, component=c, days_until=int(d), tier=tier, prob=float(p))
                for t, c, d, tier, p in sorted(live, key=lambda x: int(x[2]))],
    dq_dropped=sum(int(e["failed_records"]) for e in exp
                   if e["dataset"].endswith("silver_scada") and e["expectation"] in ("oil_temp_sensor_ok", "power_present", "wind_speed_physical")),
)
json.dump(N, open("deck/numbers.json", "w"), indent=2, ensure_ascii=False)
print("deck/numbers.json written:", {k: v for k, v in N.items() if isinstance(v, (int, float))})

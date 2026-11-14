"""Role views: the executive overview (COO) and asset performance (Head of Asset Management).

Everything is computed in Lakebase from the synced gold tables and the app's own work orders, so these screens use the
same numbers as the rest of the app. The value case mirrors evidence/queries/value_case.sql (same cost model and the
same conservative 75 % catch rate), so the COO view and the deck agree.
"""
from fastapi import APIRouter

from ..config import OPS, SERVING
from ..lakebase import db

router = APIRouter(tags=["views"])

AVAILABILITY_TARGET = 0.97
CATCH_RATE = 0.75
FALSE_ALARM_COST_EUR = 2500
FALSE_ALARM_WEEKS, BACKTEST_DAYS = 13, 61  # from the model back-test (02_train_failure_model)
FLEET_TURBINES = 120

PLANNED_COST = """(VALUES ('gearbox', 205000.0, 7.0), ('main_bearing', 175000.0, 9.0),
                          ('generator_bearing', 38000.0, 2.0), ('pitch_hydraulics', 9000.0, 0.5))
                  AS c(component, planned_cost_eur, planned_downtime_days)"""

LAST_30 = f"reading_date > (SELECT max(reading_date) FROM {SERVING}.gold_turbine_daily) - 30"


def f(x) -> float:
    return float(x or 0)


def label(farm: str) -> str:
    return farm.replace("Hunsrueck Hoehe", "Hunsrück Höhe").replace("Kueste", "Küste")


def value_case() -> dict:
    """Annualised value of turning observed unplanned failures into planned repairs."""
    r = db.query(f"""
        WITH cost AS (SELECT * FROM {PLANNED_COST}),
        rev AS (SELECT turbine_id, avg(revenue_eur + lost_revenue_eur) AS revenue_per_day_eur
                FROM {SERVING}.gold_turbine_daily GROUP BY turbine_id),
        per_event AS (
          SELECT h.total_event_cost_eur,
                 c.planned_cost_eur + c.planned_downtime_days * r.revenue_per_day_eur AS planned_event_cost_eur,
                 h.downtime_hours / 24 - c.planned_downtime_days AS downtime_days_avoided
          FROM {SERVING}.gold_failure_history h JOIN cost c USING (component) JOIN rev r USING (turbine_id)),
        period AS (SELECT (max(reading_date) - min(reading_date)) + 1 AS days FROM {SERVING}.gold_turbine_daily)
        SELECT count(*) AS failures, max(p.days) AS days, sum(total_event_cost_eur) AS unplanned_cost,
               sum(total_event_cost_eur - planned_event_cost_eur) AS avoidable, sum(downtime_days_avoided) AS days_avoided
        FROM per_event CROSS JOIN period p""")[0]
    days = f(r["days"]) or 1
    yearly = 365 / days
    false_alarms = FALSE_ALARM_WEEKS * 365 / BACKTEST_DAYS * FALSE_ALARM_COST_EUR
    avoidable = f(r["avoidable"]) * yearly
    days_avoided = CATCH_RATE * f(r["days_avoided"]) * yearly
    return {
        "failures_observed": int(r["failures"] or 0), "observed_days": int(days),
        "unplanned_cost_annual_eur": f(r["unplanned_cost"]) * yearly,
        "net_benefit_annual_eur": CATCH_RATE * avoidable - false_alarms,
        "net_benefit_at_50pct_eur": 0.5 * avoidable - false_alarms,
        "false_alarm_cost_annual_eur": false_alarms,
        "downtime_days_avoided_annual": days_avoided,
        "availability_uplift_pp": days_avoided / (FLEET_TURBINES * 365) * 100,
        "catch_rate_assumed": CATCH_RATE,
    }


def farms_30d() -> list[dict]:
    """Per farm: availability over the whole observed period (the KPI the deck uses) and over the last 30 days."""
    return db.query(f"""
        SELECT d.farm_name, avg(d.technical_availability) AS availability_period,
               avg(d.technical_availability) FILTER (WHERE d.{LAST_30}) AS availability,
               sum(d.lost_revenue_eur) FILTER (WHERE d.{LAST_30}) AS lost_revenue_eur,
               sum(d.lost_revenue_eur) AS lost_revenue_period_eur,
               sum(d.energy_mwh) FILTER (WHERE d.{LAST_30}) AS energy_mwh,
               r.turbines, r.critical, r.high
        FROM {SERVING}.gold_turbine_daily d
        JOIN (SELECT farm_name, count(*) AS turbines, count(*) FILTER (WHERE risk_tier = 'CRITICAL') AS critical,
                     count(*) FILTER (WHERE risk_tier = 'HIGH') AS high
              FROM {SERVING}.turbine_risk_scores GROUP BY farm_name) r USING (farm_name)
        GROUP BY d.farm_name, r.turbines, r.critical, r.high ORDER BY availability_period""")


def gearbox_suppliers() -> list[dict]:
    return db.query(f"""
        SELECT t.gearbox_supplier AS supplier, count(*) AS turbines, round(avg(t.turbine_age_years), 1) AS avg_age_years,
               coalesce(max(h.failures), 0) AS gearbox_failures,
               coalesce(max(h.failures), 0) * 10.0 / count(*) AS failures_per_10_turbines
        FROM {SERVING}.turbine_risk_scores t
        LEFT JOIN (SELECT gearbox_supplier, count(*) AS failures FROM {SERVING}.gold_failure_history
                   WHERE component = 'gearbox' GROUP BY gearbox_supplier) h USING (gearbox_supplier)
        GROUP BY t.gearbox_supplier ORDER BY failures_per_10_turbines DESC""")


@router.get("/views/executive")
def executive():
    vc = value_case()
    now = db.query(f"""
        SELECT count(*) FILTER (WHERE r.risk_tier = 'CRITICAL') AS critical,
               count(*) FILTER (WHERE r.risk_tier = 'HIGH') AS high,
               coalesce(sum(r.avoidable_cost_if_caught_eur) FILTER (WHERE r.risk_tier IN ('CRITICAL', 'HIGH')), 0) AS avoidable_now_eur,
               coalesce(sum(r.expected_avoidable_cost_eur), 0) AS risk_weighted_eur,
               count(*) FILTER (WHERE r.risk_tier IN ('CRITICAL', 'HIGH') AND w.turbine_id IS NULL) AS at_risk_without_order,
               coalesce(sum(r.avoidable_cost_if_caught_eur) FILTER (WHERE r.risk_tier IN ('CRITICAL', 'HIGH') AND w.turbine_id IS NULL), 0)
                 AS unprotected_eur
        FROM {SERVING}.turbine_risk_scores r
        LEFT JOIN (SELECT DISTINCT turbine_id FROM {OPS}.work_orders WHERE status <> 'DONE') w USING (turbine_id)""")[0]
    orders = db.query(f"""
        SELECT count(*) AS open_orders, coalesce(sum(expected_avoidable_eur), 0) AS protected_eur
        FROM {OPS}.work_orders WHERE status <> 'DONE'""")[0]
    fleet = db.query(f"""
        SELECT avg(technical_availability) AS availability, sum(lost_revenue_eur) AS lost_revenue_eur,
               sum(revenue_eur) AS revenue_eur, max(reading_date) AS as_of
        FROM {SERVING}.gold_turbine_daily WHERE {LAST_30}""")[0]
    monthly = db.query(f"""
        SELECT to_char(date_trunc('month', reading_date), 'YYYY-MM') AS month, avg(technical_availability) AS availability,
               sum(lost_revenue_eur) AS lost_revenue_eur, count(DISTINCT reading_date) AS days
        FROM {SERVING}.gold_turbine_daily GROUP BY 1 ORDER BY 1""")
    components = db.query(f"""
        SELECT component, count(*) AS failures, sum(total_event_cost_eur) AS cost_eur, avg(downtime_hours) / 24 AS avg_days_down
        FROM {SERVING}.gold_failure_history GROUP BY component ORDER BY cost_eur DESC""")
    farms = farms_30d()
    suppliers = gearbox_suppliers()

    insights = []
    worst = farms[0] if farms else None
    if worst and f(worst["availability_period"]) < AVAILABILITY_TARGET:
        gap = (AVAILABILITY_TARGET - f(worst["availability_period"])) * 100
        n = worst["critical"] + worst["high"]
        insights.append({"tone": "risk", "title": f"{label(worst['farm_name'])} runs {gap:.1f} pp below the 97 % availability target",
                         "detail": f"{f(worst['availability_period']) * 100:.1f} % over the last {vc['observed_days']} days, "
                                   f"€{f(worst['lost_revenue_period_eur']) / 1e3:,.0f} k revenue lost, and {n} turbine{'s' if n != 1 else ''} "
                                   f"{'are' if n != 1 else 'is'} at high or critical risk now. The proposed pilot farm.",
                         "link": "/assets"})
    if now["at_risk_without_order"]:
        insights.append({"tone": "action", "title": f"{now['at_risk_without_order']} at-risk turbines have no work order yet",
                         "detail": f"€{f(now['unprotected_eur']) / 1e3:,.0f} k is avoidable if they are planned this week. "
                                   "Each needs a crane slot and a spare booked.", "link": "/"})
    if orders["open_orders"]:
        insights.append({"tone": "good", "title": f"€{f(orders['protected_eur']) / 1e3:,.0f} k already protected by "
                                                  f"{orders['open_orders']} open work order{'s' if orders['open_orders'] != 1 else ''}",
                         "detail": "These failures are now planned repairs instead of surprises.", "link": "/work-orders"})
    if len(suppliers) > 1 and f(suppliers[0]["failures_per_10_turbines"]) > 0:
        a, b = suppliers[0], suppliers[-1]
        if f(b["failures_per_10_turbines"]) == 0:
            title = f"All {a['gearbox_failures']} gearbox failures were {a['supplier']} units"
            detail = (f"{a['supplier']} is {a['turbines']} of {a['turbines'] + b['turbines']} turbines (average age {a['avg_age_years']} years); "
                      f"{b['supplier']} ({b['avg_age_years']} years) had none. Input for the retrofit plan and the next supplier negotiation.")
        else:
            ratio = f(a["failures_per_10_turbines"]) / f(b["failures_per_10_turbines"])
            title = f"{a['supplier']} gearboxes fail {ratio:.1f}× as often as {b['supplier']}"
            detail = (f"{f(a['failures_per_10_turbines']):.1f} vs {f(b['failures_per_10_turbines']):.1f} gearbox failures per 10 turbines "
                      f"(average age {a['avg_age_years']} vs {b['avg_age_years']} years). Input for the retrofit plan and the next supplier negotiation.")
        insights.append({"tone": "insight", "title": title, "detail": detail, "link": "/assets"})
    if components:
        top = components[0]
        total = sum(f(c["cost_eur"]) for c in components) or 1
        insights.append({"tone": "insight", "title": f"{top['component'].replace('_', ' ').capitalize()} failures drive "
                                                     f"{f(top['cost_eur']) / total * 100:.0f} % of unplanned cost",
                         "detail": f"{top['failures']} events, about {f(top['avg_days_down']):.0f} days down each. "
                                   "This is where early warning pays most.", "link": "/assets"})

    return {"as_of": fleet["as_of"], "target_availability": AVAILABILITY_TARGET, "value": vc, "now": {**now, **orders},
            "fleet_30d": fleet, "monthly": monthly, "components": components, "farms": farms, "insights": insights}


@router.get("/views/assets")
def assets():
    farms = farms_30d()
    reliability = {r["farm_name"]: r for r in db.query(f"""
        SELECT farm_name, count(*) AS failures, avg(downtime_hours) AS mttr_hours, sum(repair_cost_eur) AS repair_cost_eur,
               sum(total_event_cost_eur) AS event_cost_eur
        FROM {SERVING}.gold_failure_history GROUP BY farm_name""")}
    for fm in farms:
        fm.update({k: reliability.get(fm["farm_name"], {}).get(k, 0) for k in ("failures", "mttr_hours", "repair_cost_eur", "event_cost_eur")})
    components = db.query(f"""
        SELECT component, count(*) AS failures, avg(downtime_hours) AS mttr_hours, avg(total_event_cost_eur) AS cost_per_event_eur,
               avg(CASE WHEN crane_required THEN 1.0 ELSE 0 END) AS crane_share
        FROM {SERVING}.gold_failure_history GROUP BY component ORDER BY failures DESC""")
    ages = db.query(f"""
        WITH t AS (SELECT turbine_id, turbine_age_years,
                          CASE WHEN turbine_age_years < 6 THEN '0–5 years' WHEN turbine_age_years < 11 THEN '6–10 years'
                               ELSE '11+ years' END AS cohort FROM {SERVING}.turbine_risk_scores)
        SELECT cohort, count(DISTINCT t.turbine_id) AS turbines, count(h.failure_id) AS failures,
               count(h.failure_id) * 10.0 / count(DISTINCT t.turbine_id) AS failures_per_10_turbines
        FROM t LEFT JOIN {SERVING}.gold_failure_history h USING (turbine_id) GROUP BY cohort ORDER BY min(t.turbine_age_years)""")
    calendar = db.query(f"""
        SELECT w.wo_id, w.turbine_id, r.farm_name, w.component, w.priority, w.status, w.planned_date, w.crew, w.expected_avoidable_eur
        FROM {OPS}.work_orders w LEFT JOIN {SERVING}.turbine_risk_scores r USING (turbine_id)
        WHERE w.status <> 'DONE' ORDER BY w.planned_date NULLS LAST, w.priority""")
    mix = db.query(f"""
        SELECT (SELECT count(*) FROM {OPS}.work_orders) AS planned_orders,
               (SELECT count(*) FROM {SERVING}.gold_failure_history
                WHERE failure_ts > (SELECT max(failure_ts) FROM {SERVING}.gold_failure_history) - interval '90 days') AS unplanned_failures_90d""")[0]
    return {"target_availability": AVAILABILITY_TARGET, "farms": farms, "components": components,
            "suppliers": gearbox_suppliers(), "ages": ages, "calendar": calendar, "mix": mix}

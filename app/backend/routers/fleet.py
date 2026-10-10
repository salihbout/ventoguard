from fastapi import APIRouter, Query

from ..config import OPS, SERVING
from ..lakebase import db

router = APIRouter(tags=["fleet"])

TIERS = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "DOWN")


@router.get("/kpis")
def kpis():
    risk = db.query(f"""
        SELECT max(score_date) AS score_date, max(model_version) AS model_version, count(*) AS turbines,
               count(*) FILTER (WHERE risk_tier IN ('CRITICAL', 'HIGH')) AS at_risk,
               count(*) FILTER (WHERE risk_tier = 'CRITICAL') AS critical,
               coalesce(sum(avoidable_cost_if_caught_eur) FILTER (WHERE risk_tier IN ('CRITICAL', 'HIGH')), 0) AS avoidable_if_acted_eur,
               coalesce(sum(expected_avoidable_cost_eur), 0) AS risk_weighted_eur
        FROM {SERVING}.turbine_risk_scores""")[0]
    ops = db.query(f"""
        SELECT avg(technical_availability) AS availability_30d, sum(lost_revenue_eur) AS lost_revenue_30d_eur,
               sum(lost_energy_mwh) AS lost_energy_30d_mwh
        FROM {SERVING}.gold_turbine_daily
        WHERE reading_date > (SELECT max(reading_date) FROM {SERVING}.gold_turbine_daily) - 30""")[0]
    wo = db.query(f"SELECT count(*) FILTER (WHERE status <> 'DONE') AS open_work_orders FROM {OPS}.work_orders")[0]
    return {**risk, **ops, **wo}


@router.get("/risk-board")
def risk_board(farm: str | None = None, tier: list[str] = Query(default=list(TIERS))):
    sql = f"""
        SELECT turbine_id, farm_id, farm_name, model, latitude, longitude, turbine_age_years, gearbox_supplier,
               score_date, failure_prob_14d, risk_tier, recommended_window, likely_component, anomaly_zscore,
               top_signals, avoidable_cost_if_caught_eur, expected_avoidable_cost_eur
        FROM {SERVING}.turbine_risk_scores
        WHERE risk_tier = ANY(%s) {"AND farm_name = %s" if farm else ""}
        ORDER BY failure_prob_14d DESC"""
    return db.query(sql, (list(tier), farm) if farm else (list(tier),))


@router.get("/fleet/daily")
def fleet_daily(days: int = Query(default=30, ge=7, le=180)):
    return db.query(f"""
        SELECT reading_date, sum(energy_mwh) AS energy_mwh, sum(lost_energy_mwh) AS lost_energy_mwh,
               sum(lost_revenue_eur) AS lost_revenue_eur, avg(technical_availability) AS technical_availability
        FROM {SERVING}.gold_turbine_daily
        WHERE reading_date > (SELECT max(reading_date) FROM {SERVING}.gold_turbine_daily) - %s
        GROUP BY reading_date ORDER BY reading_date""", (days,))


@router.get("/farms")
def farms():
    return db.query(f"""
        SELECT farm_id, farm_name, count(*) AS turbines,
               count(*) FILTER (WHERE risk_tier IN ('CRITICAL', 'HIGH')) AS at_risk,
               avg(latitude) AS latitude, avg(longitude) AS longitude
        FROM {SERVING}.turbine_risk_scores GROUP BY farm_id, farm_name ORDER BY farm_id""")

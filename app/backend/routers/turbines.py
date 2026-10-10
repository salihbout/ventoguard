from fastapi import APIRouter, HTTPException, Query

from ..config import OPS, SERVING
from ..lakebase import db

router = APIRouter(tags=["turbines"])


@router.get("/turbines/{turbine_id}")
def turbine(turbine_id: str, days: int = Query(default=45, ge=7, le=180)):
    risk = db.query(f"SELECT * FROM {SERVING}.turbine_risk_scores WHERE turbine_id = %s", (turbine_id,))
    if not risk:
        raise HTTPException(404, f"Unknown turbine {turbine_id}")
    brief = db.query(f"SELECT * FROM {SERVING}.turbine_ai_briefs WHERE turbine_id = %s AND headline IS NOT NULL", (turbine_id,))
    trend = db.query(f"""
        SELECT reading_date, avg_gearbox_oil_temp_c, avg_gearbox_bearing_temp_c, avg_main_bearing_temp_c,
               avg_generator_bearing_temp_c, p95_gearbox_vibration_mm_s, avg_hydraulic_pressure_bar,
               power_curve_ratio, energy_mwh, technical_availability
        FROM {SERVING}.gold_turbine_daily
        WHERE turbine_id = %s AND reading_date > (SELECT max(reading_date) FROM {SERVING}.gold_turbine_daily) - %s
        ORDER BY reading_date""", (turbine_id, days))
    orders = db.query(f"SELECT * FROM {OPS}.work_orders WHERE turbine_id = %s ORDER BY created_at DESC", (turbine_id,))
    return {"risk": risk[0], "brief": brief[0] if brief else None, "trend": trend, "work_orders": orders}

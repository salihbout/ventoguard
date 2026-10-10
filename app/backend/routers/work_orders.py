from fastapi import APIRouter, HTTPException, Request

from ..config import OPS, SERVING
from ..lakebase import db
from ..models import WorkOrderIn, WorkOrderPatch

router = APIRouter(tags=["work-orders"])


def user_of(request: Request) -> str:
    return request.headers.get("X-Forwarded-Email") or "local-dev"


@router.get("/work-orders")
def list_work_orders():
    return db.query(f"""
        SELECT w.*, r.farm_name, r.risk_tier
        FROM {OPS}.work_orders w LEFT JOIN {SERVING}.turbine_risk_scores r USING (turbine_id)
        ORDER BY (w.status = 'DONE'), w.priority, w.planned_date""")


@router.post("/work-orders", status_code=201)
def create_work_order(body: WorkOrderIn, request: Request):
    risk = db.query(f"SELECT likely_component, failure_prob_14d, expected_avoidable_cost_eur FROM {SERVING}.turbine_risk_scores WHERE turbine_id = %s",
                    (body.turbine_id,))
    if not risk:
        raise HTTPException(404, f"Unknown turbine {body.turbine_id}")
    r = risk[0]
    return db.query(f"""
        INSERT INTO {OPS}.work_orders (turbine_id, component, priority, planned_date, crew, notes,
                                       failure_prob_14d, expected_avoidable_eur, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
        (body.turbine_id, r["likely_component"], body.priority, body.planned_date, body.crew, body.notes,
         r["failure_prob_14d"], r["expected_avoidable_cost_eur"], user_of(request)))[0]


@router.patch("/work-orders/{wo_id}")
def update_work_order(wo_id: int, body: WorkOrderPatch):
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(400, "Nothing to update")
    sets = ", ".join(f"{k} = %s" for k in fields)  # keys come from the pydantic model, never from user input
    rows = db.query(f"UPDATE {OPS}.work_orders SET {sets}, updated_at = now() WHERE wo_id = %s RETURNING *",
                    (*fields.values(), wo_id))
    if not rows:
        raise HTTPException(404, f"Work order {wo_id} not found")
    return rows[0]

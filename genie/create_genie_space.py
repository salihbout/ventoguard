"""Create (or update) the 'VentoGuard Reliability' Genie space over the governed gold/serving tables.

Usage: python genie/create_genie_space.py <profile> <warehouse_id> [<space_id_to_update>]
Writes the space definition to genie/space_definition.json and prints the space id.
"""
import json
import subprocess
import sys
import uuid
from pathlib import Path

FQ = "serverless_stable_7zqte5_catalog.wind_reliability"


def nid(seed: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, "ventoguard/" + seed).hex


TABLES = {
    "gold_farm_daily": [("farm_name", ["wind park", "site", "farm"], True)],
    "gold_failure_history": [("component", ["part", "failed component"], True), ("total_event_cost_eur", ["cost of failure", "total cost"], False)],
    "gold_turbine_daily": [("farm_name", ["wind park", "site"], True), ("lost_revenue_eur", ["revenue loss", "lost income"], False),
                           ("technical_availability", ["availability", "uptime"], False)],
    "maintenance_log_insights": [("ai_component", ["component mentioned"], True), ("category", ["work order type"], True)],
    "silver_turbines": [("farm_name", ["wind park", "site"], True), ("gearbox_supplier", ["gearbox vendor", "supplier"], True)],
    "turbine_risk_history": [],
    "turbine_risk_scores": [("risk_tier", ["risk level", "priority"], True), ("likely_component", ["predicted component"], True),
                            ("failure_prob_14d", ["failure probability", "risk score"], False)],
}

INSTRUCTIONS = [
    "You are the analytics assistant of an onshore wind operator's reliability engineering team (4 wind farms in Germany, 120 turbines).",
    "Money is always EUR; energy is MWh. Format currency with thousands separators.",
    "Technical availability = share of 10-minute intervals the turbine was NOT in FAULT. Fleet target is 97%. Express as a percentage.",
    "Lost production / lost revenue (gold_turbine_daily.lost_energy_mwh / lost_revenue_eur) = expected energy from the power curve minus actual, incl. full loss during FAULT/MAINT.",
    "For the cost of failures use gold_failure_history.total_event_cost_eur (repair cost + lost revenue during downtime).",
    "For current/forward-looking risk use turbine_risk_scores (one row per turbine, latest score). risk_tier is CRITICAL (>=60%), HIGH (>=30%), MEDIUM (>=10%), LOW, or DOWN (already in repair).",
    "'At risk' means risk_tier IN ('CRITICAL','HIGH'). expected_avoidable_cost_eur is risk-weighted; avoidable_cost_if_caught_eur is the full saving if the failure is prevented.",
    "For risk trends over time use turbine_risk_history.failure_prob_14d by reading_date.",
    "Maintenance notes: maintenance_log_insights holds technician notes with LLM-extracted ai_component, ai_severity (1-5) and ai_failure_precursor. technician_name is masked PII; never try to unmask it.",
    "Join turbine-level tables on turbine_id; farm attributes come from silver_turbines.",
]

EXAMPLES = [
    ("Which wind farm lost the most revenue to unplanned failures?",
     f"SELECT farm_name, count(*) AS failures, round(sum(lost_revenue_eur)) AS lost_revenue_eur, round(sum(repair_cost_eur)) AS repair_cost_eur, "
     f"round(sum(total_event_cost_eur)) AS total_event_cost_eur FROM {FQ}.gold_failure_history GROUP BY farm_name ORDER BY total_event_cost_eur DESC"),
    ("What is the total cost of failures by component?",
     f"SELECT component, count(*) AS failures, round(avg(downtime_hours)/24, 1) AS avg_downtime_days, round(sum(total_event_cost_eur)) AS total_event_cost_eur "
     f"FROM {FQ}.gold_failure_history GROUP BY component ORDER BY total_event_cost_eur DESC"),
    ("What was technical availability per farm by month?",
     f"SELECT farm_name, date_trunc('MONTH', reading_date) AS month, round(avg(technical_availability) * 100, 2) AS technical_availability_pct "
     f"FROM {FQ}.gold_farm_daily GROUP BY ALL ORDER BY month, farm_name"),
    ("Which turbines are currently at risk of failure?",
     f"SELECT turbine_id, farm_name, risk_tier, round(failure_prob_14d * 100, 1) AS failure_prob_pct, likely_component, recommended_window, "
     f"round(avoidable_cost_if_caught_eur) AS avoidable_cost_if_caught_eur FROM {FQ}.turbine_risk_scores WHERE risk_tier IN ('CRITICAL', 'HIGH') ORDER BY failure_prob_14d DESC"),
    ("How has the failure risk of the riskiest turbine developed over the last 30 days?",
     f"SELECT h.reading_date, round(h.failure_prob_14d * 100, 1) AS failure_prob_pct FROM {FQ}.turbine_risk_history h "
     f"WHERE h.turbine_id = (SELECT turbine_id FROM {FQ}.turbine_risk_scores ORDER BY failure_prob_14d DESC LIMIT 1) "
     f"AND h.reading_date >= (SELECT max(reading_date) FROM {FQ}.turbine_risk_history) - INTERVAL 30 DAYS ORDER BY h.reading_date"),
    ("Do older gearboxes or a specific supplier fail more often?",
     f"SELECT t.gearbox_supplier, t.farm_name, count(DISTINCT t.turbine_id) AS turbines, count(f.failure_id) AS gearbox_failures, "
     f"round(count(f.failure_id) / count(DISTINCT t.turbine_id) * 100, 1) AS failures_per_100_turbines, round(avg(t.turbine_age_years), 1) AS avg_age_years "
     f"FROM {FQ}.silver_turbines t LEFT JOIN {FQ}.gold_failure_history f ON f.turbine_id = t.turbine_id AND f.component = 'gearbox' "
     f"GROUP BY ALL ORDER BY failures_per_100_turbines DESC"),
]

SAMPLE_QUESTIONS = [
    "Which wind farm lost the most revenue to unplanned failures, and which component caused it?",
    "Show the 10 turbines with the highest failure probability and their likely component",
    "What was technical availability per farm by month?",
    "Which technician notes mention failure precursors in the last 30 days?",
    "How much money is at stake on turbines currently at risk?",
]

BENCHMARKS = [
    ("How many turbines are currently HIGH or CRITICAL risk?",
     f"SELECT count(*) AS turbines FROM {FQ}.turbine_risk_scores WHERE risk_tier IN ('CRITICAL', 'HIGH')"),
    ("What is the total cost of all gearbox failures?",
     f"SELECT round(sum(total_event_cost_eur)) FROM {FQ}.gold_failure_history WHERE component = 'gearbox'"),
    ("What was the fleet's total lost revenue in September 2026?",
     f"SELECT round(sum(lost_revenue_eur)) FROM {FQ}.gold_farm_daily WHERE reading_date BETWEEN '2026-09-01' AND '2026-09-30'"),
]


def build() -> dict:
    tables = []
    for t, cols in sorted(TABLES.items()):
        entry = {"identifier": f"{FQ}.{t}"}
        if cols:
            entry["column_configs"] = sorted([
                {"column_name": c, "synonyms": syn, **({"enable_format_assistance": True, "enable_entity_matching": True} if cat else {})}
                for c, syn, cat in cols], key=lambda x: x["column_name"])
        tables.append(entry)
    return {
        "version": 2,
        "config": {"sample_questions": sorted([{"id": nid("sq" + q), "question": [q]} for q in SAMPLE_QUESTIONS], key=lambda x: x["id"])},
        "data_sources": {"tables": tables},
        "instructions": {
            "text_instructions": [{"id": nid("instructions"), "content": [s + "\n" for s in INSTRUCTIONS]}],
            "example_question_sqls": sorted([{"id": nid("ex" + q), "question": [q], "sql": [s]} for q, s in EXAMPLES], key=lambda x: x["id"]),
            "join_specs": [{
                "id": nid("join_risk_turbines"),
                "left": {"identifier": f"{FQ}.turbine_risk_scores", "alias": "turbine_risk_scores"},
                "right": {"identifier": f"{FQ}.silver_turbines", "alias": "silver_turbines"},
                "sql": ["`turbine_risk_scores`.`turbine_id` = `silver_turbines`.`turbine_id`", "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_ONE--"]}],
        },
        "benchmarks": {"questions": sorted([{"id": nid("bm" + q), "question": [q], "answer": [{"format": "SQL", "content": [s]}]} for q, s in BENCHMARKS],
                                           key=lambda x: x["id"])},
    }


if __name__ == "__main__":
    profile, warehouse = sys.argv[1], sys.argv[2]
    space = build()
    Path(__file__).with_name("space_definition.json").write_text(json.dumps(space, indent=2))
    title = "VentoGuard Reliability: Wind Fleet Analytics"
    desc = "Ask about turbine failures, lost production and revenue, availability, 14-day failure risk and technician notes for the 4-farm onshore wind fleet."
    if len(sys.argv) > 3:
        body = {"serialized_space": json.dumps(space), "title": title, "description": desc, "warehouse_id": warehouse}
        cmd = ["databricks", "genie", "update-space", sys.argv[3], "--json", json.dumps(body)]
    else:
        cmd = ["databricks", "genie", "create-space", warehouse, json.dumps(space), "--title", title, "--description", desc]
    out = subprocess.run(cmd + ["--profile", profile, "-o", "json"], capture_output=True, text=True)
    print(out.stdout or out.stderr)

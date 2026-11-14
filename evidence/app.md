# Deployed Databricks App: API execution evidence

> Email addresses in this file were redacted on 2026-11-14 (`<demo-user>` = the person who ran the build, `<workspace-user>` = other users of the shared demo workspace). Nothing else was changed.

App `ventoguard` at https://ventoguard-7474660468503815.aws.databricksapps.com, captured 2026-10-10 20:29 UTC.
React front end (`app_ui/`, built into `app/static`) and FastAPI back end (`app/backend`). Every response below comes from the
deployed app: reads from Lakebase synced tables (`ventoguard_serving`), writes to the app-owned OLTP schema (`vg_ops`), and Genie via the Conversation API.

```json
{
  "name": "ventoguard",
  "url": "https://ventoguard-7474660468503815.aws.databricksapps.com",
  "app_status": {
    "message": "App has status: App is running",
    "state": "RUNNING"
  },
  "compute_status": {
    "message": "App compute is running.",
    "state": "ACTIVE"
  },
  "active_deployment": {
    "deployment_id": "01f1c4d9aaca170098053e677a2a8041",
    "status": {
      "message": "App started successfully",
      "state": "SUCCEEDED"
    },
    "create_time": "2026-10-10T18:37:37Z"
  },
  "resources": [
    {
      "name": "postgres",
      "postgres": {
        "branch": "projects/ventoguard/branches/production",
        "database": "projects/ventoguard/branches/production/databases/databricks-postgres",
        "permission": "CAN_CONNECT_AND_CREATE"
      }
    },
    {
      "name": "genie-space",
      "genie_space": {
        "name": "VentoGuard Reliability",
        "permission": "CAN_RUN",
        "space_id": "01f1c4d953cb132e838ecd828813a354"
      }
    },
    {
      "name": "sql-warehouse",
      "sql_warehouse": {
        "id": "ff71bfa95247db89",
        "permission": "CAN_USE"
      }
    }
  ]
}
```

### `GET /api/health`
```json
{
  "ok": true,
  "lakebase": true
}
```

### `GET /api/kpis`
```json
{
  "score_date": "2026-10-09",
  "model_version": 3,
  "turbines": 120,
  "at_risk": 4,
  "critical": 3,
  "avoidable_if_acted_eur": 805598.33015625,
  "risk_weighted_eur": 849349.0,
  "availability_30d": 0.9774074166666666,
  "lost_revenue_30d_eur": 170789.71999999988,
  "lost_energy_30d_mwh": 2270.659000000002,
  "open_work_orders": 1
}
```

### `GET /api/risk-board?tier=CRITICAL&tier=HIGH`
```json
[
  {
    "turbine_id": "F03-T07",
    "farm_id": "F03",
    "farm_name": "Hunsrueck Hoehe",
    "model": "VG-2.3-108",
    "latitude": 49.94732,
    "longitude": 7.26875,
    "turbine_age_years": 13,
    "gearbox_supplier": "Hansa Drives",
    "score_date": "2026-10-09",
    "failure_prob_14d": 0.9953,
    "risk_tier": "CRITICAL",
    "recommended_window": "Act within 72 h",
    "likely_component": "gearbox",
    "anomaly_zscore": 5.8,
    "top_signals": "Power-curve ratio -0.05 vs fleet (7d); Gearbox vibration p95 +1.58mm/s vs fleet (7d); Gearbox bearing temp +6.09°C vs fleet (7d)",
    "avoidable_cost_if_caught_eur": 206523.00098958332,
    "expected_avoidable_cost_eur": 205562.0
  },
  {
    "turbine_id": "F03-T09",
    "farm_id": "F03",
    "farm_name": "Hunsrueck Hoehe",
    "model": "VG-2.3-108",
    "latitude": 49.97025,
    "longitude": 7.31466,
    "turbine_age_years": 12,
    "gearbox_supplier": "Hansa Drives",
    "score_date": "2026-10-09",
    "failure_prob_14d": 0.9912,
    "risk_tier": "CRITICAL",
    "recommended_window": "Act within 72 h",
    "likely_component": "gearbox",
    "anomaly_zscore": 7.15,
    "top_signals": "Gearbox vibration p95 +1.95mm/s vs fleet (7d); Power-curve ratio -0.06 vs fleet (7d); Gearbox bearing temp +7.51°C vs fleet (7d)",
    "avoidable_cost_if_caught_eur": 207747.4541666667,
    "expected_avoidable_cost_eur": 205914.0
  },
  {
    "turbine_id": "F01-T20",
    "farm_id": "F01",
    "farm_name": "Uckermark Nord",
    "model": "VG-3.6-136",
    "latitude": 53.20075,
    "longitude": 13.90574,
    "turbine_age_years": 9,
    "gearbox_supplier": "Hansa Drives",
    "score_date": "2026-10-09",
    "failure_prob_14d": 0.9578,
    "risk_tier": "CRITICAL",
    "recommended_window": "Act within 72 h",
    "likely_component": "gearbox",
    "anomaly_zscore": 2.19,
    "top_signals": "Gearbox vibration p95 +0.60mm/s vs fleet (7d); Gearbox bearing temp +2.44°C vs fleet (7d); Power-curve ratio -0.02 vs fleet (7d)",
    "avoidable_cost_if_caught_eur": 224811.12968749998,
    "expected_avoidable_cost_eur": 215327.0
  },
  {
    "turbine_id": "F04-T16",
```

### `GET /api/farms`
```json
[
  {
    "farm_id": "F01",
    "farm_name": "Uckermark Nord",
    "turbines": 36,
    "at_risk": 1,
    "latitude": 53.206610555555564,
    "longitude": 13.878761944444442
  },
  {
    "farm_id": "F02",
    "farm_name": "Ostfriesland Kueste",
    "turbines": 32,
    "at_risk": 0,
    "latitude": 53.460770000000004,
    "longitude": 7.407749375
  },
  {
    "farm_id": "F03",
    "farm_name": "Hunsrueck Hoehe",
    "turbines": 28,
    "at_risk": 2,
    "latitude": 49.95494857142858,
    "longitude": 7.299087142857145
  },
  {
    "farm_id": "F04",
    "farm_name": "Eifel West",
    "turbines": 24,
    "at_risk": 1,
    "latitude": 50.40370208333332,
    "longitude": 6.518559166666667
  }
]
```

### `GET /api/turbines/F01-T20`
```json
{
  "risk": {
    "turbine_id": "F01-T20",
    "farm_id": "F01",
    "farm_name": "Uckermark Nord",
    "model": "VG-3.6-136",
    "latitude": 53.20075,
    "longitude": 13.90574,
    "turbine_age_years": 9,
    "gearbox_supplier": "Hansa Drives",
    "score_date": "2026-10-09",
    "failure_prob_14d": 0.9578,
    "risk_tier": "CRITICAL",
    "recommended_window": "Act within 72 h",
    "likely_component": "gearbox",
    "anomaly_zscore": 2.19,
    "top_signals": "Gearbox vibration p95 +0.60mm/s vs fleet (7d); Gearbox bearing temp +2.44°C vs fleet (7d); Power-curve ratio -0.02 vs fleet (7d)",
    "oil_temp_resid_7d": 1.8428571428571427,
    "gbx_bearing_temp_resid_7d": 2.44,
    "main_bearing_temp_resid_7d": -0.0071428571428577515,
    "gen_bearing_temp_resid_7d": 0.052857142857143505,
    "vibration_resid_7d": 0.5979999999999999,
    "hydraulic_resid_7d": 0.014285714285717534,
    "power_curve_resid_7d": -0.01798571428571427,
    "corrective_cost_eur": 385000,
    "planned_cost_eur": 205000,
    "revenue_per_day_eur": 1445.5203124999996,
    "avoidable_cost_if_caught_eur": 224811.12968749998,
    "expected_avoidable_cost_eur": 215327.0,
    "model_version": 3,
    "scored_at": "2026-10-10T19:08:00.063735+00:00"
  },
  "brief": {
    "turbine_id": "F01-T20",
    "farm_name": "Uckermark Nord",
    "risk_tier": "CRITICAL",
    "failure_prob_14d": 0.9578,
    "likely_component": "gearbox",
    "expected_avoidable_cost_eur": 215327.0,
    "score_date": "2026-10-09",
    "headline": "F01-T20 Gearbox Critical: 95.8% Failure Risk Within 14 Days",
    "diagnosis": "Gearbox shows elevated vibration (+0.60mm/s above fleet average) and bearing temperature (+2.44°C above fleet) over the past 7 days, indicating imminent bearing or gear mesh failure. The 14-day failure probability model rates this turbine CRITICAL at 95.8% despite iron content at 18 ppm on 2026-09-01.",
    "recommended_action": "Schedule immediate gearbox replacement within 3 days ; Procure Hansa Drives gearbox or exchange unit ; Coordinate crane and specialist gearbox crew",
    "urgency_days": 3,
    "crew_and_parts": "Require specialist gearbox technicians, mobile crane, and replacement VG-3.6 gearbox (Hansa Drives compatible).",
    "business_case": "Planned intervention avoids EUR 224,811 in additional costs compared to unplanned failure (EUR 385,000 corrective vs EUR 205,000 planned plus EUR 1,446 daily revenue loss).",
    "llm_endpoint": "databricks-claude-sonnet-4-5",
    "generated_at": "2026-10-10T19:14:03.317019+00:00",
    "ai_error": null
  },
  "trend": [
    {
      "reading_date": "2026-08-26",
      "avg_gearbox_oil_temp_c": 50.56,
      "avg_gearbox_bearing_temp_c": 54.16,
      "avg_main_bearing_temp_c": 39.43,
      "avg_generator_bearing_temp_c": 48.82,
      "p95_gearbox_vibration_mm_s": 2.081,
      "avg_hydraulic_pressure_bar": 179.96,
      "power_curve_ratio": 1.0001,
```

### `POST /api/work-orders` (transactional write to Lakebase `vg_ops.work_orders`)
```json
{
  "wo_id": 2,
  "turbine_id": "F01-T20",
  "component": "gearbox",
  "priority": "P1",
  "status": "OPEN",
  "planned_date": "2026-10-12",
  "crew": "North crew (Uckermark)",
  "notes": "Planned gearbox swap; crane booked for low-wind window",
  "failure_prob_14d": 0.9578,
  "expected_avoidable_eur": 215327,
  "created_by": "<demo-user>",
  "created_at": "2026-10-10T20:29:06.194624+00:00",
  "updated_at": "2026-10-10T20:29:06.194624+00:00"
}
```

### `PATCH /api/work-orders/2`
Request body: `{"status":"SCHEDULED"}`
```json
{
  "wo_id": 2,
  "turbine_id": "F01-T20",
  "component": "gearbox",
  "priority": "P1",
  "status": "SCHEDULED",
  "planned_date": "2026-10-12",
  "crew": "North crew (Uckermark)",
  "notes": "Planned gearbox swap; crane booked for low-wind window",
  "failure_prob_14d": 0.9578,
  "expected_avoidable_eur": 215327,
  "created_by": "<demo-user>",
  "created_at": "2026-10-10T20:29:06.194624+00:00",
  "updated_at": "2026-10-10T20:29:06.710491+00:00"
}
```

### `GET /api/work-orders`
```json
[
  {
    "wo_id": 1,
    "turbine_id": "F01-T20",
    "component": "gearbox",
    "priority": "P1",
    "status": "SCHEDULED",
    "planned_date": "2026-10-12",
    "crew": "North crew (Uckermark)",
    "notes": "Planned gearbox swap; crane booked for low-wind window",
    "failure_prob_14d": 0.9578,
    "expected_avoidable_eur": 215327,
    "created_by": "<demo-user>",
    "created_at": "2026-10-10T17:22:38.541454+00:00",
    "updated_at": "2026-10-10T17:22:39.076726+00:00",
    "farm_name": "Uckermark Nord",
    "risk_tier": "CRITICAL"
  },
  {
    "wo_id": 2,
    "turbine_id": "F01-T20",
    "component": "gearbox",
    "priority": "P1",
    "status": "SCHEDULED",
    "planned_date": "2026-10-12",
    "crew": "North crew (Uckermark)",
    "notes": "Planned gearbox swap; crane booked for low-wind window",
    "failure_prob_14d": 0.9578,
    "expected_avoidable_eur": 215327,
    "created_by": "<demo-user>",
    "created_at": "2026-10-10T20:29:06.194624+00:00",
    "updated_at": "2026-10-10T20:29:06.710491+00:00",
    "farm_name": "Uckermark Nord",
    "risk_tier": "CRITICAL"
  }
]
```

### `POST /api/genie/ask`
Request body: `{"question":"Which turbines are currently at risk of failure and what is the avoidable cost?"}`
```json
{
  "conversation_id": "01f1c4e93e5f1f8699bbbbab217e260e",
  "message_id": "01f1c4e93e75129cb60ffc02d1f5e417",
  "status": "COMPLETED",
  "text": "You want to see a list of turbines that are currently at high or critical risk of failure, including details about their risk level, failure probability as a percentage, the component likely to fail, the recommended maintenance window, and the avoidable cost if the failure is prevented.\n\nThere are **4 turbines** currently at risk of failure (**3 CRITICAL**, **1 HIGH**). Examples include:\n- **F03-T07** (Hunsrueck Hoehe) — **CRITICAL**, **99.5%** failure risk, likely **gearbox**, avoidable cost if caught **€206,523**; expected avoidable cost **€205,562**\n- **F03-T09** (Hunsrueck Hoehe) — **CRITICAL**, **99.1%** failure risk, likely **gearbox**, avoidable cost if caught **€207,747**; expected avoidable cost **€205,914**\n- **F01-T20** (Uckermark Nord) — **CRITICAL**, **95.8%** failure risk, likely **gearbox**, avoidable cost if caught **€224,811**; expected avoidable cost **€215,327**\n- **F04-T16** (Eifel West) — **HIGH**, **55.3%** failure risk, likely **main_bearing**, avoidable cost if caught **€166,517**; expected avoidable cost **€92,062**\nThe highest avoidable cost if prevented is **F01-T20** at **€224,811**, and the three most urgent cases are all **gearbox-related CRITICAL** risks with action recommended **within 72 h**.",
  "sql": "SELECT `turbine_id`, `farm_name`, `risk_tier`, ROUND(`failure_prob_14d` * 100, 1) AS `failure_prob_pct`, `likely_component`, `recommended_window`, ROUND(`avoidable_cost_if_caught_eur`) AS `avoidable_cost_if_caught_eur`, ROUND(`expected_avoidable_cost_eur`) AS `expected_avoidable_cost_eur` FROM `serverless_stable_7zqte5_catalog`.`ventoguard_gold`.`turbine_risk_scores` WHERE `risk_tier` IN ('CRITICAL', 'HIGH') ORDER BY `failure_prob_14d` DESC",
  "columns": [
    "turbine_id",
    "farm_name",
    "risk_tier",
    "failure_prob_pct",
    "likely_component",
    "recommended_window",
    "avoidable_cost_if_caught_eur",
    "expected_avoidable_cost_eur"
  ],
  "rows": [
    [
      "F03-T07",
      "Hunsrueck Hoehe",
      "CRITICAL",
      "99.5",
      "gearbox",
      "Act within 72 h",
      "206523.0",
      "205562.0"
    ],
    [
      "F03-T09",
      "Hunsrueck Hoehe",
      "CRITICAL",
      "99.1",
      "gearbox",
      "Act within 72 h",
      "207747.0",
      "205914.0"
    ],
    [
      "F01-T20",
      "Uckermark Nord",
      "CRITICAL",
      "95.8",
      "gearbox",
      "Act within 72 h",
      "224811.0",
      "215327.0"
    ],
    [
      "F04-T16",
      "Eifel West",
      "HIGH",
      "55.3",
      "main_bearing",
      "Plan within 7 days",
      "166517.0",
      "92062.0"
    ]
  ],
  "row_count": 4
}
```


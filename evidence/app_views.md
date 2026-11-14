# Role views (COO, asset management): API execution evidence

Captured 2026-11-14 20:11 UTC by `scripts/views_evidence.sh`. The app's FastAPI back end (`app/backend/routers/views.py`)
ran locally against the **production** Lakebase project `ventoguard` (synced tables in `ventoguard_serving`, work orders in `vg_ops`).
Read-only GET requests. The deployed app serves the same code; its status at capture time:

```json
{
  "name": "ventoguard",
  "url": "https://ventoguard-7474660468503815.aws.databricksapps.com",
  "app_status": {
    "message": "App has status: App is running",
    "state": "RUNNING"
  },
  "active_deployment": {
    "deployment_id": "01f1e0606d771120b73951b6764d8056",
    "status": {
      "message": "App started successfully",
      "state": "SUCCEEDED"
    },
    "create_time": "2026-11-14T19:20:18Z"
  }
}
```

The value case below is computed live in Postgres with the same cost model as `evidence/queries/value_case.sql`,
so it matches the deck (net benefit €4,188,999 a year, unplanned cost €11,325,980 a year).

### `GET /api/health`
```json
{
  "ok": true,
  "lakebase": true
}
```

### `GET /api/views/executive`
```json
{
  "as_of": "2026-10-09",
  "target_availability": 0.97,
  "value": {
    "failures_observed": 22,
    "observed_days": 192,
    "unplanned_cost_annual_eur": 11325980.416666668,
    "net_benefit_annual_eur": 4188998.7892579883,
    "net_benefit_at_50pct_eur": 2727843.455133741,
    "false_alarm_cost_annual_eur": 194467.21311475412,
    "downtime_days_avoided_annual": 663.8140462239584,
    "availability_uplift_pp": 1.5155571831597223,
    "catch_rate_assumed": 0.75
  },
  "now": {
    "critical": 3,
    "high": 1,
    "avoidable_now_eur": 805598.33015625,
    "risk_weighted_eur": 849349.0,
    "at_risk_without_order": 3,
    "unprotected_eur": 580787.2004687501,
    "open_orders": 1,
    "protected_eur": 215327
  },
  "fleet_30d": {
    "availability": 0.9774074166666666,
    "lost_revenue_eur": 170789.71999999988,
    "revenue_eur": 5726784.280000002,
    "as_of": "2026-10-09"
  },
  "monthly": [
    {
      "month": "2026-04",
      "availability": 1.0,
      "lost_revenue_eur": 68092.82,
      "days": 30
    },
    {
      "month": "2026-05",
      "availability": 0.9896253494623656,
      "lost_revenue_eur": 116330.23000000019,
      "days": 31
    },
    {
      "month": "2026-06",
      "availability": 0.981758388888889,
      "lost_revenue_eur": 168315.9899999999,
      "days": 30
    },
    {
      "month": "2026-07",
      "availability": 0.9547904569892472,
      "lost_revenue_eur": 305191.93999999977,
      "days": 31
    },
    {
      "month": "2026-08",
      "availability": 0.9557888709677418,
      "lost_revenue_eur": 245010.57000000065,
      "days": 31
    },
    {
      "month": "2026-09",
      "availability": 0.9709960000000001,
      "lost_revenue_eur": 199304.82999999996,
      "days": 30
    },
    {
      "month": "2026-10",
      "availability": 0.9856481481481482,
      "lost_revenue_eur": 42641.72999999995,
      "days": 9
    }
  ],
  "components": [
    {
      "component": "gearbox",
      "failures": 8,
      "cost_eur": 3423975.0,
      "avg_days_down": 36.378125
    },
    {
      "component": "main_bearing",
      "failures": 5,
      "cost_eur": 1886143.0,
      "avg_days_down": 43.5975
    },
    {
      "component": "generator_bearing",
      "failures": 5,
      "cost_eur": 520832.0,
      "avg_days_down": 11.434999999999997
    },
    {
      "component": "pitch_hydraulics",
      "failures": 4,
      "cost_eur": 126826.0,
      "avg_days_down": 3.0979166666666664
    }
  ],
  "farms": [
    {
      "farm_name": "Hunsrueck Hoehe",
      "availability_period": 0.9501885230654763,
      "availability": 0.9619378571428572,
      "lost_revenue_eur": 42238.35999999999,
      "lost_revenue_period_eur": 312580.6099999998,
      "energy_mwh": 9453.099999999993,
      "turbines": 28,
      "critical": 2,
      "high": 0
    },
    {
      "farm_name": "Uckermark Nord",
      "availability_period": 0.972229079861111,
      "availability": 0.9542952777777777,
      "lost_revenue_eur": 87587.15000000011,
      "lost_revenue_period_eur": 403255.3399999989,
      "energy_mwh": 21578.730000000003,
      "turbines": 36,
      "critical": 1,
      "high": 0
    },
    {
      "farm_name": "Eifel West",
      "availability_period": 0.9886880642361111,
      "availability": 1.0,
      "lost_revenue_eur": 9402.080000000007,
      "lost_revenue_period_eur": 128592.04000000011,
      "energy_mwh": 11050.874000000005,
      "turbines": 24,
      "critical": 0,
      "high": 1
    },
    {
      "farm_name": "Ostfriesland Kueste",
      "availability_period": 0.992682568359375,
      "availability": 1.0,
      "lost_revenue_eur": 31562.130000000012,
      "lost_revenue_period_eur": 300460.1199999996,
      "energy_mwh": 34580.461999999934,
      "turbines": 32,
      "critical": 0,
      "high": 0
    }
  ],
  "insights": [
    {
      "tone": "risk",
      "title": "Hunsrück Höhe runs 2.0 pp below the 97 % availability target",
      "detail": "95.0 % over the last 192 days, €313 k revenue lost, and 2 turbines are at high or critical risk now. The proposed pilot farm.",
      "link": "/assets"
    },
    {
      "tone": "action",
      "title": "3 at-risk turbines have no work order yet",
      "detail": "€581 k is avoidable if they are planned this week. Each needs a crane slot and a spare booked.",
      "link": "/"
    },
    {
      "tone": "good",
      "title": "€215 k already protected by 1 open work order",
      "detail": "These failures are now planned repairs instead of surprises.",
      "link": "/work-orders"
    },
    {
      "tone": "insight",
      "title": "All 8 gearbox failures were Hansa Drives units",
      "detail": "Hansa Drives is 64 of 120 turbines (average age 10.5 years); NordGear (7.0 years) had none. Input for the retrofit plan and the next supplier negotiation.",
      "link": "/assets"
    },
    {
      "tone": "insight",
      "title": "Gearbox failures drive 57 % of unplanned cost",
      "detail": "8 events, about 36 days down each. This is where early warning pays most.",
      "link": "/assets"
    }
  ]
}
```

### `GET /api/views/assets`
```json
{
  "target_availability": 0.97,
  "farms": [
    {
      "farm_name": "Hunsrueck Hoehe",
      "availability_period": 0.9501885230654763,
      "availability": 0.9619378571428572,
      "lost_revenue_eur": 42238.35999999999,
      "lost_revenue_period_eur": 312580.6099999998,
      "energy_mwh": 9453.099999999993,
      "turbines": 28,
      "critical": 2,
      "high": 0,
      "failures": 10,
      "mttr_hours": 643.13,
      "repair_cost_eur": 2402000.0,
      "event_cost_eur": 2652351.0
    },
    {
      "farm_name": "Uckermark Nord",
      "availability_period": 0.972229079861111,
      "availability": 0.9542952777777777,
      "lost_revenue_eur": 87587.15000000011,
      "lost_revenue_period_eur": 403255.3399999989,
      "energy_mwh": 21578.730000000003,
      "turbines": 36,
      "critical": 1,
      "high": 0,
      "failures": 9,
      "mttr_hours": 569.3,
      "repair_cost_eur": 2139500.0,
      "event_cost_eur": 2414762.0
    },
    {
      "farm_name": "Eifel West",
      "availability_period": 0.9886880642361111,
      "availability": 1.0,
      "lost_revenue_eur": 9402.080000000007,
      "lost_revenue_period_eur": 128592.04000000011,
      "energy_mwh": 11050.874000000005,
      "turbines": 24,
      "critical": 0,
      "high": 1,
      "failures": 2,
      "mttr_hours": 625.65,
      "repair_cost_eur": 442900.0,
      "event_cost_eur": 508606.0
    },
    {
      "farm_name": "Ostfriesland Kueste",
      "availability_period": 0.992682568359375,
      "availability": 1.0,
      "lost_revenue_eur": 31562.130000000012,
      "lost_revenue_period_eur": 300460.1199999996,
      "energy_mwh": 34580.461999999934,
      "turbines": 32,
      "critical": 0,
      "high": 0,
      "failures": 1,
      "mttr_hours": 1079.6,
      "repair_cost_eur": 276100.0,
      "event_cost_eur": 382057.0
    }
  ],
  "components": [
    {
      "component": "gearbox",
      "failures": 8,
      "mttr_hours": 873.0749999999999,
      "cost_per_event_eur": 427996.875,
      "crane_share": 1.0
    },
    {
      "component": "main_bearing",
      "failures": 5,
      "mttr_hours": 1046.34,
      "cost_per_event_eur": 377228.6,
      "crane_share": 1.0
    },
    {
      "component": "generator_bearing",
      "failures": 5,
      "mttr_hours": 274.43999999999994,
      "cost_per_event_eur": 104166.4,
      "crane_share": 0.0
    },
    {
      "component": "pitch_hydraulics",
      "failures": 4,
      "mttr_hours": 74.35,
      "cost_per_event_eur": 31706.5,
      "crane_share": 0.0
    }
  ],
  "suppliers": [
    {
      "supplier": "Hansa Drives",
      "turbines": 64,
      "avg_age_years": 10.5,
      "gearbox_failures": 8,
      "failures_per_10_turbines": 1.25
    },
    {
      "supplier": "NordGear",
      "turbines": 56,
      "avg_age_years": 7.0,
      "gearbox_failures": 0,
      "failures_per_10_turbines": 0.0
    }
  ],
  "ages": [
    {
      "cohort": "0–5 years",
      "turbines": 19,
      "failures": 1,
      "failures_per_10_turbines": 0.5263157894736842
    },
    {
      "cohort": "6–10 years",
      "turbines": 69,
      "failures": 10,
      "failures_per_10_turbines": 1.4492753623188406
    },
    {
      "cohort": "11+ years",
      "turbines": 32,
      "failures": 11,
      "failures_per_10_turbines": 3.4375
    }
  ],
  "calendar": [
    {
      "wo_id": 2,
      "turbine_id": "F01-T20",
      "farm_name": "Uckermark Nord",
      "component": "gearbox",
      "priority": "P1",
      "status": "SCHEDULED",
      "planned_date": "2026-10-12",
      "crew": "North crew (Uckermark)",
      "expected_avoidable_eur": 215327
    }
  ],
  "mix": {
    "planned_orders": 1,
    "unplanned_failures_90d": 15
  }
}
```


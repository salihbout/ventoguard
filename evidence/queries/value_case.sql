-- Value case: what would the observed failures have cost if VentoGuard had converted them into planned repairs?
-- Planned-repair assumptions match the cost model in 03_score_and_genai.py. Production catch rate is set conservatively
-- at 75% (back-test caught 8/8) and every false alarm is charged a €2,500 inspection.
WITH cost AS (
  SELECT * FROM VALUES
    ('gearbox', 205000, 7), ('main_bearing', 175000, 9), ('generator_bearing', 38000, 2), ('pitch_hydraulics', 9000, 0.5)
  AS c(component, planned_cost_eur, planned_downtime_days)
),
rev AS (
  SELECT turbine_id, avg(revenue_eur + lost_revenue_eur) AS revenue_per_day_eur
  FROM serverless_stable_7zqte5_catalog.wind_reliability.gold_turbine_daily GROUP BY turbine_id
),
per_event AS (
  SELECT f.component, f.total_event_cost_eur,
         c.planned_cost_eur + c.planned_downtime_days * r.revenue_per_day_eur AS planned_event_cost_eur,
         f.downtime_hours / 24 - c.planned_downtime_days AS downtime_days_avoided
  FROM serverless_stable_7zqte5_catalog.wind_reliability.gold_failure_history f
  JOIN cost c USING (component) JOIN rev r USING (turbine_id)
),
period AS (
  SELECT datediff(max(reading_date), min(reading_date)) + 1 AS days FROM serverless_stable_7zqte5_catalog.wind_reliability.gold_farm_daily
)
SELECT
  count(*)                                                        AS failures_observed,
  max(p.days)                                                     AS observed_days,
  round(sum(total_event_cost_eur))                                AS unplanned_cost_observed_eur,
  round(sum(total_event_cost_eur) * 365 / max(p.days))            AS unplanned_cost_annualised_eur,
  round(sum(total_event_cost_eur - planned_event_cost_eur) * 365 / max(p.days))          AS avoidable_annualised_at_100pct_eur,
  round(0.75 * sum(total_event_cost_eur - planned_event_cost_eur) * 365 / max(p.days))   AS avoidable_annualised_at_75pct_eur,
  round(13 * 365 / 61 * 2500)                                     AS false_alarm_inspection_cost_annualised_eur,
  round(0.75 * sum(total_event_cost_eur - planned_event_cost_eur) * 365 / max(p.days) - 13 * 365 / 61 * 2500) AS net_annual_benefit_eur,
  round(0.75 * sum(downtime_days_avoided) * 365 / max(p.days))    AS turbine_downtime_days_avoided_per_year,
  round(0.75 * sum(downtime_days_avoided) * 365 / max(p.days) / (120 * 365) * 100, 2) AS availability_uplift_pp
FROM per_event CROSS JOIN period p

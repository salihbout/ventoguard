CREATE OR REFRESH MATERIALIZED VIEW gold_failure_history
COMMENT 'Every confirmed failure with total cost of the unplanned event: repair cost plus lost revenue during the downtime window (EUR).'
TBLPROPERTIES ('quality' = 'gold')
AS
WITH lost AS (
  SELECT f.failure_id, sum(d.lost_energy_mwh) AS lost_energy_mwh, sum(d.lost_revenue_eur) AS lost_revenue_eur
  FROM silver_failure_events f
  JOIN gold_turbine_daily d
    ON d.turbine_id = f.turbine_id
   AND d.reading_date BETWEEN to_date(f.failure_ts) AND to_date(f.failure_ts + make_interval(0, 0, 0, 0, CAST(f.downtime_hours AS INT), 0, 0))
  GROUP BY f.failure_id
)
SELECT
  f.failure_id, f.turbine_id, t.farm_id, t.farm_name, t.model, t.gearbox_supplier, t.turbine_age_years,
  f.component, f.failure_ts, f.downtime_hours, f.crane_required, f.repair_cost_eur,
  round(coalesce(l.lost_energy_mwh, 0), 1) AS lost_energy_mwh,
  round(coalesce(l.lost_revenue_eur, 0), 0) AS lost_revenue_eur,
  round(f.repair_cost_eur + coalesce(l.lost_revenue_eur, 0), 0) AS total_event_cost_eur
FROM silver_failure_events f
JOIN silver_turbines t USING (turbine_id)
LEFT JOIN lost l USING (failure_id);

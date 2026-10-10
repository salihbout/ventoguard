CREATE OR REFRESH MATERIALIZED VIEW ${catalog}.${gold_schema}.gold_farm_daily
COMMENT 'Daily wind-farm KPIs for the asset-management dashboard and Genie: energy, availability, lost production and lost revenue.'
TBLPROPERTIES ('quality' = 'gold')
AS SELECT
  farm_id, farm_name, reading_date,
  count(DISTINCT turbine_id) AS turbines,
  round(sum(energy_mwh), 2) AS energy_mwh,
  round(sum(expected_energy_mwh), 2) AS expected_energy_mwh,
  round(sum(lost_energy_mwh), 2) AS lost_energy_mwh,
  round(sum(lost_revenue_eur), 0) AS lost_revenue_eur,
  round(sum(revenue_eur), 0) AS revenue_eur,
  round(avg(technical_availability), 4) AS technical_availability,
  sum(CASE WHEN had_fault THEN 1 ELSE 0 END) AS turbines_with_fault
FROM ${catalog}.${gold_schema}.gold_turbine_daily
GROUP BY farm_id, farm_name, reading_date;

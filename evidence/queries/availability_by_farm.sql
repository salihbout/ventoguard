-- Technical availability and lost revenue per farm (whole observation window)
SELECT farm_name, round(avg(technical_availability) * 100, 2) AS technical_availability_pct,
       round(sum(energy_mwh)) AS energy_mwh, round(sum(lost_energy_mwh)) AS lost_energy_mwh, round(sum(lost_revenue_eur)) AS lost_revenue_eur
FROM serverless_stable_7zqte5_catalog.wind_reliability.gold_farm_daily GROUP BY farm_name ORDER BY technical_availability_pct

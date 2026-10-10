-- Gold: one row per turbine per day. Health signals, energy, availability and lost production (MWh and EUR).
-- Expected power uses the design power curve at the measured wind speed, so fault/derate losses are visible.
CREATE OR REFRESH MATERIALIZED VIEW gold_turbine_daily
COMMENT 'Daily turbine KPIs: energy, technical availability, lost production (MWh & EUR) and drivetrain health signals. Grain: turbine_id x reading_date.'
CLUSTER BY (turbine_id, reading_date)
TBLPROPERTIES ('quality' = 'gold')
AS
WITH s AS (
  SELECT
    s.*, t.farm_id, t.farm_name, t.model, t.rated_power_kw,
    CASE WHEN s.wind_speed_ms < 3 OR s.wind_speed_ms > 25 THEN 0.0
         WHEN s.wind_speed_ms >= 12.5 THEN 1.0
         ELSE (pow(s.wind_speed_ms, 3) - 27) / (pow(12.5, 3) - 27) END * t.rated_power_kw AS expected_power_kw,
    p.price_eur_mwh
  FROM silver_scada s
  JOIN silver_turbines t USING (turbine_id)
  LEFT JOIN silver_market_prices p ON date_trunc('HOUR', s.reading_ts) = p.hour_start_utc
)
SELECT
  turbine_id, farm_id, farm_name, model, reading_date,
  count(*) AS n_readings,
  round(sum(power_kw) / 6 / 1000, 3) AS energy_mwh,
  round(sum(expected_power_kw) / 6 / 1000, 3) AS expected_energy_mwh,
  round(sum(CASE WHEN status_code IN ('FAULT', 'MAINT') THEN expected_power_kw ELSE greatest(expected_power_kw - power_kw, 0) END) / 6 / 1000, 3) AS lost_energy_mwh,
  round(sum(CASE WHEN status_code IN ('FAULT', 'MAINT') THEN expected_power_kw ELSE greatest(expected_power_kw - power_kw, 0) END * price_eur_mwh) / 6 / 1000, 2) AS lost_revenue_eur,
  round(sum(power_kw * price_eur_mwh) / 6 / 1000, 2) AS revenue_eur,
  round(1 - sum(CASE WHEN status_code = 'FAULT' THEN 1 ELSE 0 END) / count(*), 4) AS technical_availability,
  max(CASE WHEN status_code = 'FAULT' THEN 1 ELSE 0 END) = 1 AS had_fault,
  round(avg(wind_speed_ms), 2) AS avg_wind_speed_ms,
  round(avg(ambient_temp_c), 2) AS avg_ambient_temp_c,
  round(avg(CASE WHEN status_code = 'RUN' THEN power_kw / rated_power_kw END), 4) AS avg_load_factor,
  round(avg(CASE WHEN status_code = 'RUN' THEN gearbox_oil_temp_c END), 2) AS avg_gearbox_oil_temp_c,
  round(max(CASE WHEN status_code = 'RUN' THEN gearbox_oil_temp_c END), 2) AS max_gearbox_oil_temp_c,
  round(avg(CASE WHEN status_code = 'RUN' THEN gearbox_bearing_temp_c END), 2) AS avg_gearbox_bearing_temp_c,
  round(avg(CASE WHEN status_code = 'RUN' THEN main_bearing_temp_c END), 2) AS avg_main_bearing_temp_c,
  round(avg(CASE WHEN status_code = 'RUN' THEN generator_bearing_temp_c END), 2) AS avg_generator_bearing_temp_c,
  round(percentile_approx(CASE WHEN status_code = 'RUN' THEN gearbox_vibration_mm_s END, 0.95), 3) AS p95_gearbox_vibration_mm_s,
  round(avg(hydraulic_pressure_bar), 2) AS avg_hydraulic_pressure_bar,
  round(avg(CASE WHEN status_code = 'RUN' AND expected_power_kw > 0 THEN power_kw / expected_power_kw END), 4) AS power_curve_ratio
FROM s
GROUP BY turbine_id, farm_id, farm_name, model, reading_date;

-- Silver: typed, validated telemetry. Sensor faults and impossible readings are dropped and counted by expectations.
CREATE OR REFRESH STREAMING TABLE silver_scada (
  CONSTRAINT valid_turbine EXPECT (turbine_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_timestamp EXPECT (reading_ts IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT power_present EXPECT (power_kw IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT wind_speed_physical EXPECT (wind_speed_ms BETWEEN 0 AND 60) ON VIOLATION DROP ROW,
  CONSTRAINT oil_temp_sensor_ok EXPECT (gearbox_oil_temp_c BETWEEN -40 AND 150) ON VIOLATION DROP ROW,
  CONSTRAINT known_status EXPECT (status_code IN ('RUN', 'LOW_WIND', 'STORM_STOP', 'MAINT', 'FAULT'))
)
COMMENT 'Validated 10-minute SCADA telemetry. Rows with sensor faults (999 °C), negative wind or missing power are dropped by expectations.'
CLUSTER BY (turbine_id, reading_date)
TBLPROPERTIES ('quality' = 'silver')
AS SELECT
  turbine_id,
  to_timestamp(`timestamp`) AS reading_ts,
  to_date(to_timestamp(`timestamp`)) AS reading_date,
  status_code,
  wind_speed_ms, wind_dir_deg, ambient_temp_c, rotor_rpm, power_kw, pitch_angle_deg, nacelle_temp_c,
  gearbox_oil_temp_c, gearbox_bearing_temp_c, main_bearing_temp_c, generator_bearing_temp_c,
  gearbox_vibration_mm_s, hydraulic_pressure_bar
FROM STREAM(bronze_scada);

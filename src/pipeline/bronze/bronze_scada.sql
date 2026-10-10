-- Bronze: 10-minute SCADA telemetry, incrementally ingested from the landing Volume with Auto Loader
CREATE OR REFRESH STREAMING TABLE bronze_scada
COMMENT 'Raw 10-minute SCADA telemetry from turbine historians (JSON, Auto Loader). Synthetic.'
TBLPROPERTIES ('quality' = 'bronze')
AS SELECT
  *,
  _metadata.file_path AS _source_file,
  current_timestamp() AS _ingested_at
FROM STREAM read_files(
  '${landing_root}/scada',
  format => 'json',
  schemaHints => 'turbine_id STRING, timestamp STRING, status_code STRING, wind_speed_ms DOUBLE, wind_dir_deg DOUBLE, ambient_temp_c DOUBLE, rotor_rpm DOUBLE, power_kw DOUBLE, pitch_angle_deg DOUBLE, nacelle_temp_c DOUBLE, gearbox_oil_temp_c DOUBLE, gearbox_bearing_temp_c DOUBLE, main_bearing_temp_c DOUBLE, generator_bearing_temp_c DOUBLE, gearbox_vibration_mm_s DOUBLE, hydraulic_pressure_bar DOUBLE'
);

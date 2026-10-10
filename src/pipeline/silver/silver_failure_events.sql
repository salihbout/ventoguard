CREATE OR REFRESH MATERIALIZED VIEW silver_failure_events (
  CONSTRAINT known_component EXPECT (component IN ('gearbox', 'main_bearing', 'generator_bearing', 'pitch_hydraulics'))
)
COMMENT 'Confirmed component failures with downtime and corrective repair cost (EUR).'
TBLPROPERTIES ('quality' = 'silver')
AS SELECT
  failure_id, turbine_id, component,
  to_timestamp(failure_ts) AS failure_ts,
  CAST(downtime_hours AS DOUBLE) AS downtime_hours,
  CAST(repair_cost_eur AS DOUBLE) AS repair_cost_eur,
  CAST(crane_required AS BOOLEAN) AS crane_required
FROM bronze_failure_events;

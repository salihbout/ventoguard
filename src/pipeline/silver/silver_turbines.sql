CREATE OR REFRESH MATERIALIZED VIEW silver_turbines (
  CONSTRAINT pk_present EXPECT (turbine_id IS NOT NULL) ON VIOLATION FAIL UPDATE
)
COMMENT 'Turbine asset register: farm, location, model, rated power, gearbox supplier, age.'
TBLPROPERTIES ('quality' = 'silver')
AS SELECT
  turbine_id, farm_id, farm_name, federal_state,
  CAST(latitude AS DOUBLE) AS latitude, CAST(longitude AS DOUBLE) AS longitude,
  model, CAST(rated_power_kw AS INT) AS rated_power_kw,
  CAST(commissioning_year AS INT) AS commissioning_year,
  year(current_date()) - CAST(commissioning_year AS INT) AS turbine_age_years,
  CAST(hub_height_m AS INT) AS hub_height_m, gearbox_supplier
FROM bronze_turbines;

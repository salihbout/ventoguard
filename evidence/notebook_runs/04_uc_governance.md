# aef4dbbb-6d6a-4a8f-89b8-cbce488eb21a: executed notebook (task run 429474403016476)

> Exported from the Databricks job run with `databricks jobs export-run`; cell sources and their outputs exactly as executed on serverless compute.


# 04 · Unity Catalog governance

Everything in VentoGuard (raw files, pipeline tables, features, model, AI outputs, Lakebase-synced tables,
Genie space and app) sits under **one governed schema**. This notebook applies and then *verifies*:

* **Classification tags** on the schema, tables and PII columns, using the account's governed tag policies (`domain`, `medallion_layer`, `class.name`, `system.certification_status`, `ai.model_family`)
* **Column mask**: technician names are personal data under GDPR. Only `vg_reliability_leads` see them in clear
* **Access model**: the app service principal and Genie users get read access to gold/serving tables only
* **Data quality**: Lakeflow expectation results read back from the pipeline event log
* **Lineage**: end-to-end lineage from the raw Volume to the risk board, read from system tables

### Cell 2
```python
dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("schema", "wind_reliability")
CATALOG, SCHEMA = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
FQ = f"{CATALOG}.{SCHEMA}"
spark.sql(f"USE CATALOG {CATALOG}"); spark.sql(f"USE SCHEMA {SCHEMA}")

def q(sql, show=True):
    df = spark.sql(sql)
    if show:
        display(df)
    return df

TYPES = {r.table_name: r.table_type for r in spark.sql(f"SELECT table_name, table_type FROM {CATALOG}.information_schema.tables WHERE table_schema = '{SCHEMA}'").collect()}
KEYWORD = {"MATERIALIZED_VIEW": "MATERIALIZED VIEW", "STREAMING_TABLE": "STREAMING TABLE"}

def alter(table, clause):
    # Lakeflow-managed datasets are altered with ALTER MATERIALIZED VIEW / ALTER STREAMING TABLE
    spark.sql(f"ALTER {KEYWORD.get(TYPES.get(table), 'TABLE')} {FQ}.{table} {clause}")
```

## Classification tags

### Cell 4
```python
# Keys like domain / business_unit / owner_team / medallion_layer / certified are governed tag policies in this
# account, so only their allowed values are used. Free-form context goes into ungoverned keys (vg_use_case, vg_layer).
spark.sql(f"ALTER SCHEMA {FQ} SET TAGS ('domain' = 'operations', 'business_unit' = 'Operations', 'owner_team' = 'analytics', 'vg_use_case' = 'wind_drivetrain_reliability', 'data_origin' = 'synthetic')")

layers = {
    "bronze": ["bronze_scada", "bronze_maintenance_logs", "bronze_turbines", "bronze_failure_events", "bronze_market_prices"],
    "silver": ["silver_scada", "silver_maintenance_logs", "silver_turbines", "silver_failure_events", "silver_market_prices"],
    "gold": ["gold_turbine_daily", "gold_farm_daily", "gold_failure_history"],
    "ml": ["turbine_health_features", "turbine_risk_history"],
    "serving": ["turbine_risk_scores", "turbine_ai_briefs", "maintenance_log_insights"],
}
for layer, tables in layers.items():
    for t in tables:
        medallion = layer if layer in ("bronze", "silver") else "gold"
        certified = layer in ("gold", "serving")
        alter(t, f"SET TAGS ('medallion_layer' = '{medallion}', 'vg_layer' = '{layer}', 'certified' = '{str(certified).lower()}'"
                 + (", 'system.certification_status' = 'certified'" if certified else "") + ")")

for t in ["bronze_maintenance_logs", "silver_maintenance_logs", "maintenance_log_insights"]:
    alter(t, "ALTER COLUMN technician_name SET TAGS ('class.name')")  # system classification tag (key-only, own statement)
    alter(t, "ALTER COLUMN technician_name SET TAGS ('gdpr_category' = 'employee_data')")
spark.sql(f"ALTER TABLE {FQ}.turbine_ai_briefs SET TAGS ('ai_generated' = 'true', 'ai.model_creator' = 'anthropic', 'ai.model_family' = 'claude-sonnet')")
spark.sql(f"ALTER TABLE {FQ}.maintenance_log_insights SET TAGS ('ai_generated' = 'true', 'ai.model_creator' = 'anthropic', 'ai.model_family' = 'claude-haiku')")

q(f"""SELECT table_name, tag_name, tag_value FROM {CATALOG}.information_schema.table_tags
      WHERE schema_name = '{SCHEMA}' AND tag_name IN ('medallion_layer', 'vg_layer', 'system.certification_status', 'ai_generated', 'ai.model_family') ORDER BY table_name, tag_name""")
```
**Output:**

| table_name | tag_name | tag_value |
|---|---|---|
| bronze_failure_events | medallion_layer | bronze |
| bronze_failure_events | vg_layer | bronze |
| bronze_maintenance_logs | medallion_layer | bronze |
| bronze_maintenance_logs | vg_layer | bronze |
| bronze_market_prices | medallion_layer | bronze |
| bronze_market_prices | vg_layer | bronze |
| bronze_scada | medallion_layer | bronze |
| bronze_scada | vg_layer | bronze |
| bronze_turbines | medallion_layer | bronze |
| bronze_turbines | vg_layer | bronze |
| gold_failure_history | medallion_layer | gold |
| gold_failure_history | system.certification_status | certified |
| gold_failure_history | vg_layer | gold |
| gold_farm_daily | medallion_layer | gold |
| gold_farm_daily | system.certification_status | certified |
| gold_farm_daily | vg_layer | gold |
| gold_turbine_daily | medallion_layer | gold |
| gold_turbine_daily | system.certification_status | certified |
| gold_turbine_daily | vg_layer | gold |
| maintenance_log_insights | ai.model_family | claude-haiku |
| maintenance_log_insights | ai_generated | true |
| maintenance_log_insights | medallion_layer | gold |
| maintenance_log_insights | system.certification_status | certified |
| maintenance_log_insights | vg_layer | serving |
| silver_failure_events | medallion_layer | silver |
| silver_failure_events | vg_layer | silver |
| silver_maintenance_logs | medallion_layer | silver |
| silver_maintenance_logs | vg_layer | silver |
| silver_market_prices | medallion_layer | silver |
| silver_market_prices | vg_layer | silver |
| silver_scada | medallion_layer | silver |
| silver_scada | vg_layer | silver |
| silver_turbines | medallion_layer | silver |
| silver_turbines | vg_layer | silver |
| turbine_ai_briefs | ai.model_family | claude-sonnet |
| turbine_ai_briefs | ai_generated | true |
| turbine_ai_briefs | medallion_layer | gold |
| turbine_ai_briefs | system.certification_status | certified |
| turbine_ai_briefs | vg_layer | serving |
| turbine_health_features | medallion_layer | gold |

_… 6 more rows_

### Cell 5
```python
q(f"""SELECT table_name, column_name, tag_name, tag_value FROM {CATALOG}.information_schema.column_tags
      WHERE schema_name = '{SCHEMA}' ORDER BY table_name""")
```
**Output:**

| table_name | column_name | tag_name | tag_value |
|---|---|---|---|
| bronze_maintenance_logs | technician_name | class.name |  |
| bronze_maintenance_logs | technician_name | gdpr_category | employee_data |
| maintenance_log_insights | technician_name | gdpr_category | employee_data |
| maintenance_log_insights | technician_name | class.name |  |
| silver_maintenance_logs | technician_name | class.name |  |
| silver_maintenance_logs | technician_name | gdpr_category | employee_data |

## Column mask on personal data (GDPR)

### Cell 7
```python
spark.sql(f"""
CREATE OR REPLACE FUNCTION {FQ}.mask_person_name(name STRING)
RETURNS STRING
COMMENT 'GDPR: reveal technician names only to members of vg_reliability_leads; everyone else sees initials.'
RETURN CASE WHEN is_account_group_member('vg_reliability_leads') THEN name
            ELSE concat(left(name, 2), '***') END
""")
spark.sql(f"ALTER TABLE {FQ}.maintenance_log_insights ALTER COLUMN technician_name SET MASK {FQ}.mask_person_name")
q(f"SELECT log_id, turbine_id, technician_name, ai_summary_en FROM {FQ}.maintenance_log_insights ORDER BY created_ts DESC LIMIT 5")
```
**Output:**

| log_id | turbine_id | technician_name | ai_summary_en |
|---|---|---|---|
| WO-00244 | F02-T29 | A.*** | Elevator and climbing safety inspection completed successfully. No defects found. |
| WO-00355 | F03-T26 | T.*** | Routine 6-month inspection completed. Bolt torque and oil level normal. |
| WO-00314 | F03-T16 | T.*** | Gearbox oil sample analysis completed. Iron content within normal limits at 18 ppm. |
| WO-00386 | F04-T06 | T.*** | Routine six-month maintenance completed. No anomalies detected, oil level normal, filter replaced. |
| WO-00093 | F01-T25 | K.*** | Gearbox oil sample analyzed. Iron content within normal limits at 18 ppm. |

## Access model

### Cell 9
```python
q(f"SHOW GRANTS ON SCHEMA {FQ}")
```
**Output:**

| Principal | ActionType | ObjectType | ObjectKey |
|---|---|---|---|
| isabella.altergott@databricks.com | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| d44291ff-6f77-48e5-9417-8a6887fb3d86 | SELECT | SCHEMA | serverless_stable_7zqte5_catalog.wind_reliability |
| d44291ff-6f77-48e5-9417-8a6887fb3d86 | USE SCHEMA | SCHEMA | serverless_stable_7zqte5_catalog.wind_reliability |
| account users | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| salih.boutadghart@databricks.com | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| salih.boutadghart@databricks.com | MANAGE | CATALOG | serverless_stable_7zqte5_catalog |
| anton.vlasov@databricks.com | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| sophie.bauer@databricks.com | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| suraj.bang@databricks.com | READ METADATA | METASTORE | metastore_aws_us_east_1 |

## Data quality: Lakeflow expectation results from the pipeline event log

### Cell 11
```python
q(f"""
SELECT
  e.details:flow_progress:data_quality:expectations[0]:dataset AS dataset,
  x.name AS expectation, sum(x.passed_records) AS passed_records, sum(x.failed_records) AS failed_records
FROM event_log(TABLE({FQ}.silver_scada)) e
LATERAL VIEW explode(from_json(e.details:flow_progress:data_quality:expectations,
  'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>')) t AS x
WHERE e.event_type = 'flow_progress' AND e.details:flow_progress:data_quality IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 2
""")
```
**Output:**

| dataset | expectation | passed_records | failed_records |
|---|---|---|---|
| serverless_stable_7zqte5_catalog.wind_reliability.silver_failure_events | known_component | 66 | 0 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_maintenance_logs | has_text | 519 | 0 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | known_status | 3317760 | 0 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | oil_temp_sensor_ok | 3316017 | 1743 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | power_present | 3312743 | 5017 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | valid_timestamp | 3317760 | 0 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | valid_turbine | 3317760 | 0 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | wind_speed_physical | 3316803 | 957 |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_turbines | pk_present | 360 | 0 |

## Lineage: raw files → pipeline → features → risk board (system tables)

### Cell 13
```python
q(f"""
SELECT DISTINCT
  coalesce(source_table_full_name, source_path) AS source,
  target_table_full_name AS target, entity_type
FROM system.access.table_lineage
WHERE (target_table_full_name LIKE '{FQ}.%' OR source_table_full_name LIKE '{FQ}.%')
  AND event_date >= current_date() - INTERVAL 7 DAYS
  AND target_table_full_name IS NOT NULL
ORDER BY target, source
""")
```
**Output:**

| source | target | entity_type |
|---|---|---|
| null | serverless_stable_7zqte5_catalog.wind_reliability.bronze_failure_events | PIPELINE |
| null | serverless_stable_7zqte5_catalog.wind_reliability.bronze_maintenance_logs | PIPELINE |
| null | serverless_stable_7zqte5_catalog.wind_reliability.bronze_market_prices | PIPELINE |
| null | serverless_stable_7zqte5_catalog.wind_reliability.bronze_scada | PIPELINE |
| null | serverless_stable_7zqte5_catalog.wind_reliability.bronze_turbines | PIPELINE |
| null | serverless_stable_7zqte5_catalog.wind_reliability.event_log_6c84e3c6_18a3_4951_a75d_32be1e8d21f2 | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.gold_turbine_daily | serverless_stable_7zqte5_catalog.wind_reliability.gold_failure_history | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_failure_events | serverless_stable_7zqte5_catalog.wind_reliability.gold_failure_history | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_turbines | serverless_stable_7zqte5_catalog.wind_reliability.gold_failure_history | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.gold_turbine_daily | serverless_stable_7zqte5_catalog.wind_reliability.gold_farm_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_market_prices | serverless_stable_7zqte5_catalog.wind_reliability.gold_turbine_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | serverless_stable_7zqte5_catalog.wind_reliability.gold_turbine_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_turbines | serverless_stable_7zqte5_catalog.wind_reliability.gold_turbine_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_maintenance_logs | serverless_stable_7zqte5_catalog.wind_reliability.maintenance_log_insights | JOB |
| serverless_stable_7zqte5_catalog.wind_reliability.bronze_failure_events | serverless_stable_7zqte5_catalog.wind_reliability.silver_failure_events | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.bronze_maintenance_logs | serverless_stable_7zqte5_catalog.wind_reliability.silver_maintenance_logs | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.bronze_market_prices | serverless_stable_7zqte5_catalog.wind_reliability.silver_market_prices | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.bronze_scada | serverless_stable_7zqte5_catalog.wind_reliability.silver_scada | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.bronze_turbines | serverless_stable_7zqte5_catalog.wind_reliability.silver_turbines | PIPELINE |
| serverless_stable_7zqte5_catalog.wind_reliability.maintenance_log_insights | serverless_stable_7zqte5_catalog.wind_reliability.turbine_ai_briefs | JOB |
| serverless_stable_7zqte5_catalog.wind_reliability.turbine_risk_scores | serverless_stable_7zqte5_catalog.wind_reliability.turbine_ai_briefs | JOB |
| serverless_stable_7zqte5_catalog.wind_reliability.gold_turbine_daily | serverless_stable_7zqte5_catalog.wind_reliability.turbine_health_features | JOB |
| serverless_stable_7zqte5_catalog.wind_reliability.silver_turbines | serverless_stable_7zqte5_catalog.wind_reliability.turbine_health_features | JOB |
| null | serverless_stable_7zqte5_catalog.wind_reliability.turbine_risk_history | JOB |
| null | serverless_stable_7zqte5_catalog.wind_reliability.turbine_risk_scores | JOB |

### Cell 14
```python
q(f"""SELECT table_name, table_type, comment FROM {CATALOG}.information_schema.tables
      WHERE table_schema = '{SCHEMA}' ORDER BY table_name""")
```
**Output:**

| table_name | table_type | comment |
|---|---|---|
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_bronze_failure_events_1 | MANAGED | Raw confirmed component failure events from CMMS (CSV). Synthetic. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_bronze_maintenance_logs_1 | MANAGED | Raw CMMS maintenance work-order notes written by field technicians (JSON). Synthetic. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_bronze_market_prices_1 | MANAGED | Raw hourly EPEX day-ahead prices for bidding zone DE-LU (CSV). Synthetic. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_bronze_scada_1 | MANAGED | Raw 10-minute SCADA telemetry from turbine historians (JSON, Auto Loader). Synthetic. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_bronze_turbines_1 | MANAGED | Raw asset register export (CSV): one row per turbine. Synthetic. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_gold_failure_history_1 | MANAGED | Every confirmed failure with total cost of the unplanned event: repair cost plus lost revenue during the downtime window (EUR). |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_gold_farm_daily_1 | MANAGED | Daily wind-farm KPIs for the asset-management dashboard and Genie: energy, availability, lost production and lost revenue. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_gold_turbine_daily_1 | MANAGED | Daily turbine KPIs: energy, technical availability, lost production (MWh & EUR) and drivetrain health signals. Grain: turbine_id x reading_date. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_silver_failure_events_1 | MANAGED | Confirmed component failures with downtime and corrective repair cost (EUR). |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_silver_maintenance_logs_1 | MANAGED | Technician work-order notes (German/English free text). technician_name is personal data and is masked for non-reliability users. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_silver_market_prices_1 | MANAGED | Hourly day-ahead price, EUR/MWh, bidding zone DE-LU. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_silver_scada_1 | MANAGED | Validated 10-minute SCADA telemetry. Rows with sensor faults (999 °C), negative wind or missing power are dropped by expectations. |
| __materialization_mat_6c84e3c6_18a3_4951_a75d_32be1e8d21f2_silver_turbines_1 | MANAGED | Turbine asset register: farm, location, model, rated power, gearbox supplier, age. |
| bronze_failure_events | STREAMING_TABLE | Raw confirmed component failure events from CMMS (CSV). Synthetic. |
| bronze_maintenance_logs | STREAMING_TABLE | Raw CMMS maintenance work-order notes written by field technicians (JSON). Synthetic. |
| bronze_market_prices | STREAMING_TABLE | Raw hourly EPEX day-ahead prices for bidding zone DE-LU (CSV). Synthetic. |
| bronze_scada | STREAMING_TABLE | Raw 10-minute SCADA telemetry from turbine historians (JSON, Auto Loader). Synthetic. |
| bronze_turbines | STREAMING_TABLE | Raw asset register export (CSV): one row per turbine. Synthetic. |
| event_log_6c84e3c6_18a3_4951_a75d_32be1e8d21f2 | MANAGED | null |
| gold_failure_history | MATERIALIZED_VIEW | Every confirmed failure with total cost of the unplanned event: repair cost plus lost revenue during the downtime window (EUR). |
| gold_farm_daily | MATERIALIZED_VIEW | Daily wind-farm KPIs for the asset-management dashboard and Genie: energy, availability, lost production and lost revenue. |
| gold_turbine_daily | MATERIALIZED_VIEW | Daily turbine KPIs: energy, technical availability, lost production (MWh & EUR) and drivetrain health signals. Grain: turbine_id x reading_date. |
| maintenance_log_insights | MANAGED | Technician notes enriched by an LLM (ai_query): component, severity 1-5, precursor flag and English summary. technician_name is masked. |
| silver_failure_events | MATERIALIZED_VIEW | Confirmed component failures with downtime and corrective repair cost (EUR). |
| silver_maintenance_logs | STREAMING_TABLE | Technician work-order notes (German/English free text). technician_name is personal data and is masked for non-reliability users. |
| silver_market_prices | MATERIALIZED_VIEW | Hourly day-ahead price, EUR/MWh, bidding zone DE-LU. |
| silver_scada | STREAMING_TABLE | Validated 10-minute SCADA telemetry. Rows with sensor faults (999 °C), negative wind or missing power are dropped by expectations. |
| silver_turbines | MATERIALIZED_VIEW | Turbine asset register: farm, location, model, rated power, gearbox supplier, age. |
| turbine_ai_briefs | MANAGED | LLM-generated maintenance briefs for at-risk turbines: diagnosis, recommended action, crew/parts and business case. Grounded on model score, sensor residuals and technician notes. |
| turbine_health_features | MANAGED | Daily per-turbine health features: fleet-relative residuals, 7-day means and 7-day trends. Feature table for turbine_failure_risk. |
| turbine_risk_history | MANAGED | Daily 14-day failure probability per turbine from the turbine_failure_risk model (full history, for back-testing and trend charts). |
| turbine_risk_scores | MANAGED | Operational risk board: latest 14-day failure probability per turbine, likely component, top signals and expected avoidable cost (EUR). Synced to Lakebase for the VentoGuard app. |

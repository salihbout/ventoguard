# 39a9a9b1-4207-4e8d-a765-34ceddeaaf88: executed notebook (task run 200421997264907)

> Email addresses in this file were redacted on 2026-11-14 (`<demo-user>` = the person who ran the build, `<workspace-user>` = other users of the shared demo workspace). Nothing else was changed.

> Exported from the Databricks job run with `databricks jobs export-run`; cell sources and their outputs exactly as executed on serverless compute.


# 04 · Unity Catalog governance

VentoGuard lives in one catalog, with one schema per layer:

| Schema | Holds | Who reads it |
|---|---|---|
| `ventoguard_bronze` | raw landing Volume + Auto Loader bronze tables | data engineering only |
| `ventoguard_silver` | validated, typed tables (expectations applied) | data engineering, data science |
| `ventoguard_gold` | business KPIs, features, model, risk scores, AI outputs | analysts, Genie, the app |
| `ventoguard_serving` | Lakebase synced tables used by the app | the app service principal |

This notebook applies and then *verifies*:
* **Classification tags** on schemas, tables and PII columns, using the account's governed tag policies (`domain`, `medallion_layer`, `class.name`, `system.certification_status`, `ai.model_family`)
* **Column mask**: technician names are personal data under GDPR. Only `vg_reliability_leads` see them in clear
* **Access model**: grants per schema
* **Data quality**: Lakeflow expectation results read back from the pipeline event log
* **Lineage**: bronze → silver → gold → risk board, read from system tables

### Cell 2
```python
dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("bronze_schema", "ventoguard_bronze")
dbutils.widgets.text("silver_schema", "ventoguard_silver")
dbutils.widgets.text("gold_schema", "ventoguard_gold")
CATALOG = dbutils.widgets.get("catalog")
SCHEMAS = {"bronze": dbutils.widgets.get("bronze_schema"), "silver": dbutils.widgets.get("silver_schema"), "gold": dbutils.widgets.get("gold_schema")}
BRONZE, SILVER, GOLD = (f"{CATALOG}.{SCHEMAS[k]}" for k in ("bronze", "silver", "gold"))
IN_SCHEMAS = ", ".join(f"'{s}'" for s in SCHEMAS.values())
spark.sql(f"USE CATALOG {CATALOG}")

def q(sql, show=True):
    df = spark.sql(sql)
    if show:
        display(df)
    return df

TYPES = {(r.table_schema, r.table_name): r.table_type for r in spark.sql(
    f"SELECT table_schema, table_name, table_type FROM {CATALOG}.information_schema.tables WHERE table_schema IN ({IN_SCHEMAS})").collect()}
KEYWORD = {"MATERIALIZED_VIEW": "MATERIALIZED VIEW", "STREAMING_TABLE": "STREAMING TABLE"}

def fq(table):
    """Resolve a table to its layer schema from its name prefix (bronze_*, silver_*, everything else is gold)."""
    layer = table.split("_")[0] if table.split("_")[0] in ("bronze", "silver") else "gold"
    return SCHEMAS[layer], f"{CATALOG}.{SCHEMAS[layer]}.{table}"

def alter(table, clause):
    # Lakeflow-managed datasets are altered with ALTER MATERIALIZED VIEW / ALTER STREAMING TABLE
    schema, name = fq(table)
    spark.sql(f"ALTER {KEYWORD.get(TYPES.get((schema, table)), 'TABLE')} {name} {clause}")
```

## Classification tags

### Cell 4
```python
# Keys like domain / business_unit / owner_team / medallion_layer / certified are governed tag policies in this
# account, so only their allowed values are used. Free-form context goes into ungoverned keys (vg_use_case, vg_layer).
for layer, schema in SCHEMAS.items():
    spark.sql(f"ALTER SCHEMA {CATALOG}.{schema} SET TAGS ('domain' = 'operations', 'business_unit' = 'Operations', 'owner_team' = 'analytics', "
              f"'medallion_layer' = '{layer}', 'vg_use_case' = 'wind_drivetrain_reliability', 'data_origin' = 'synthetic')")
spark.sql(f"COMMENT ON SCHEMA {BRONZE} IS 'VentoGuard bronze: raw landing Volume and Auto Loader ingests (SCADA, CMMS notes, asset register, failures, prices). Synthetic data.'")
spark.sql(f"COMMENT ON SCHEMA {SILVER} IS 'VentoGuard silver: validated, typed tables with Lakeflow data-quality expectations applied.'")
spark.sql(f"COMMENT ON SCHEMA {GOLD} IS 'VentoGuard gold: certified business KPIs, ML features, failure-risk model and scores, GenAI outputs. Source for Genie and the app.'")

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
spark.sql(f"ALTER TABLE {GOLD}.turbine_ai_briefs SET TAGS ('ai_generated' = 'true', 'ai.model_creator' = 'anthropic', 'ai.model_family' = 'claude-sonnet')")
spark.sql(f"ALTER TABLE {GOLD}.maintenance_log_insights SET TAGS ('ai_generated' = 'true', 'ai.model_creator' = 'anthropic', 'ai.model_family' = 'claude-haiku')")

q(f"""SELECT schema_name, tag_name, tag_value FROM {CATALOG}.information_schema.schema_tags
      WHERE schema_name IN ({IN_SCHEMAS}) ORDER BY schema_name, tag_name""")
```
**Output:**

| schema_name | tag_name | tag_value |
|---|---|---|
| ventoguard_bronze | business_unit | Operations |
| ventoguard_bronze | data_origin | synthetic |
| ventoguard_bronze | domain | operations |
| ventoguard_bronze | medallion_layer | bronze |
| ventoguard_bronze | owner_team | analytics |
| ventoguard_bronze | vg_use_case | wind_drivetrain_reliability |
| ventoguard_gold | business_unit | Operations |
| ventoguard_gold | data_origin | synthetic |
| ventoguard_gold | domain | operations |
| ventoguard_gold | medallion_layer | gold |
| ventoguard_gold | owner_team | analytics |
| ventoguard_gold | vg_use_case | wind_drivetrain_reliability |
| ventoguard_silver | business_unit | Operations |
| ventoguard_silver | data_origin | synthetic |
| ventoguard_silver | domain | operations |
| ventoguard_silver | medallion_layer | silver |
| ventoguard_silver | owner_team | analytics |
| ventoguard_silver | vg_use_case | wind_drivetrain_reliability |

### Cell 5
```python
q(f"""SELECT schema_name, table_name, tag_name, tag_value FROM {CATALOG}.information_schema.table_tags
      WHERE schema_name IN ({IN_SCHEMAS}) AND tag_name IN ('medallion_layer', 'vg_layer', 'system.certification_status', 'ai_generated', 'ai.model_family')
      ORDER BY schema_name, table_name, tag_name""")
```
**Output:**

| schema_name | table_name | tag_name | tag_value |
|---|---|---|---|
| ventoguard_bronze | bronze_failure_events | medallion_layer | bronze |
| ventoguard_bronze | bronze_failure_events | vg_layer | bronze |
| ventoguard_bronze | bronze_maintenance_logs | medallion_layer | bronze |
| ventoguard_bronze | bronze_maintenance_logs | vg_layer | bronze |
| ventoguard_bronze | bronze_market_prices | medallion_layer | bronze |
| ventoguard_bronze | bronze_market_prices | vg_layer | bronze |
| ventoguard_bronze | bronze_scada | medallion_layer | bronze |
| ventoguard_bronze | bronze_scada | vg_layer | bronze |
| ventoguard_bronze | bronze_turbines | medallion_layer | bronze |
| ventoguard_bronze | bronze_turbines | vg_layer | bronze |
| ventoguard_gold | gold_failure_history | medallion_layer | gold |
| ventoguard_gold | gold_failure_history | system.certification_status | certified |
| ventoguard_gold | gold_failure_history | vg_layer | gold |
| ventoguard_gold | gold_farm_daily | medallion_layer | gold |
| ventoguard_gold | gold_farm_daily | system.certification_status | certified |
| ventoguard_gold | gold_farm_daily | vg_layer | gold |
| ventoguard_gold | gold_turbine_daily | medallion_layer | gold |
| ventoguard_gold | gold_turbine_daily | system.certification_status | certified |
| ventoguard_gold | gold_turbine_daily | vg_layer | gold |
| ventoguard_gold | maintenance_log_insights | ai.model_family | claude-haiku |
| ventoguard_gold | maintenance_log_insights | ai_generated | true |
| ventoguard_gold | maintenance_log_insights | medallion_layer | gold |
| ventoguard_gold | maintenance_log_insights | system.certification_status | certified |
| ventoguard_gold | maintenance_log_insights | vg_layer | serving |
| ventoguard_gold | turbine_ai_briefs | ai.model_family | claude-sonnet |
| ventoguard_gold | turbine_ai_briefs | ai_generated | true |
| ventoguard_gold | turbine_ai_briefs | medallion_layer | gold |
| ventoguard_gold | turbine_ai_briefs | system.certification_status | certified |
| ventoguard_gold | turbine_ai_briefs | vg_layer | serving |
| ventoguard_gold | turbine_health_features | medallion_layer | gold |
| ventoguard_gold | turbine_health_features | vg_layer | ml |
| ventoguard_gold | turbine_risk_history | medallion_layer | gold |
| ventoguard_gold | turbine_risk_history | vg_layer | ml |
| ventoguard_gold | turbine_risk_scores | medallion_layer | gold |
| ventoguard_gold | turbine_risk_scores | system.certification_status | certified |
| ventoguard_gold | turbine_risk_scores | vg_layer | serving |
| ventoguard_silver | silver_failure_events | medallion_layer | silver |
| ventoguard_silver | silver_failure_events | vg_layer | silver |
| ventoguard_silver | silver_maintenance_logs | medallion_layer | silver |
| ventoguard_silver | silver_maintenance_logs | vg_layer | silver |

_… 6 more rows_

### Cell 6
```python
q(f"""SELECT schema_name, table_name, column_name, tag_name, tag_value FROM {CATALOG}.information_schema.column_tags
      WHERE schema_name IN ({IN_SCHEMAS}) ORDER BY schema_name, table_name""")
```
**Output:**

| schema_name | table_name | column_name | tag_name | tag_value |
|---|---|---|---|---|
| ventoguard_bronze | bronze_maintenance_logs | technician_name | class.name |  |
| ventoguard_bronze | bronze_maintenance_logs | technician_name | gdpr_category | employee_data |
| ventoguard_gold | maintenance_log_insights | technician_name | gdpr_category | employee_data |
| ventoguard_gold | maintenance_log_insights | technician_name | class.name |  |
| ventoguard_silver | silver_maintenance_logs | technician_name | gdpr_category | employee_data |
| ventoguard_silver | silver_maintenance_logs | technician_name | class.name |  |

## Column mask on personal data (GDPR)

### Cell 8
```python
spark.sql(f"""
CREATE OR REPLACE FUNCTION {GOLD}.mask_person_name(name STRING)
RETURNS STRING
COMMENT 'GDPR: reveal technician names only to members of vg_reliability_leads; everyone else sees initials.'
RETURN CASE WHEN is_account_group_member('vg_reliability_leads') THEN name
            ELSE concat(left(name, 2), '***') END
""")
spark.sql(f"ALTER TABLE {GOLD}.maintenance_log_insights ALTER COLUMN technician_name SET MASK {GOLD}.mask_person_name")
q(f"SELECT log_id, turbine_id, technician_name, ai_summary_en FROM {GOLD}.maintenance_log_insights ORDER BY created_ts DESC LIMIT 5")
```
**Output:**

| log_id | turbine_id | technician_name | ai_summary_en |
|---|---|---|---|
| WO-00244 | F02-T29 | A.*** | Safety inspection of elevator and climbing protection completed successfully. No defects found. |
| WO-00355 | F03-T26 | T.*** | Routine 6-month inspection completed. All checks passed, no issues found. |
| WO-00314 | F03-T16 | T.*** | Gearbox oil sample analysis completed. Iron content within acceptable limits at 18 ppm. |
| WO-00386 | F04-T06 | T.*** | Semi-annual maintenance completed. No abnormalities detected, oil level normal, filter replaced. |
| WO-00093 | F01-T25 | K.*** | Gearbox oil sample analysis completed. Iron content within normal limits at 18 ppm. |

## Access model: grants per layer schema

### Cell 10
```python
for schema in SCHEMAS.values():
    q(f"SHOW GRANTS ON SCHEMA {CATALOG}.{schema}")
```
**Output:**

| Principal | ActionType | ObjectType | ObjectKey |
|---|---|---|---|
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| account users | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| <demo-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <demo-user> | MANAGE | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | READ METADATA | METASTORE | metastore_aws_us_east_1 |
**Output:**

| Principal | ActionType | ObjectType | ObjectKey |
|---|---|---|---|
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| d44291ff-6f77-48e5-9417-8a6887fb3d86 | USE SCHEMA | SCHEMA | serverless_stable_7zqte5_catalog.ventoguard_silver |
| account users | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| <demo-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <demo-user> | MANAGE | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | READ METADATA | METASTORE | metastore_aws_us_east_1 |
**Output:**

| Principal | ActionType | ObjectType | ObjectKey |
|---|---|---|---|
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| d44291ff-6f77-48e5-9417-8a6887fb3d86 | SELECT | SCHEMA | serverless_stable_7zqte5_catalog.ventoguard_gold |
| d44291ff-6f77-48e5-9417-8a6887fb3d86 | USE SCHEMA | SCHEMA | serverless_stable_7zqte5_catalog.ventoguard_gold |
| account users | READ METADATA | METASTORE | metastore_aws_us_east_1 |
| <demo-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <demo-user> | MANAGE | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | ALL PRIVILEGES | CATALOG | serverless_stable_7zqte5_catalog |
| <workspace-user> | READ METADATA | METASTORE | metastore_aws_us_east_1 |

## Data quality: Lakeflow expectation results from the pipeline event log

### Cell 12
```python
q(f"""
SELECT
  x.dataset, x.name AS expectation, sum(x.passed_records) AS passed_records, sum(x.failed_records) AS failed_records
FROM event_log(TABLE({SILVER}.silver_scada)) e
LATERAL VIEW explode(from_json(e.details:flow_progress:data_quality:expectations,
  'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>')) t AS x
WHERE e.event_type = 'flow_progress' AND e.details:flow_progress:data_quality IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 2
""")
```
**Output:**

| dataset | expectation | passed_records | failed_records |
|---|---|---|---|
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_failure_events | known_component | 66 | 0 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_maintenance_logs | has_text | 519 | 0 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | known_status | 3317760 | 0 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | oil_temp_sensor_ok | 3316017 | 1743 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | power_present | 3312743 | 5017 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | valid_timestamp | 3317760 | 0 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | valid_turbine | 3317760 | 0 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | wind_speed_physical | 3316803 | 957 |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_turbines | pk_present | 360 | 0 |

## Lineage: bronze → silver → gold → features → risk board (system tables)

### Cell 14
```python
q(f"""
SELECT DISTINCT
  coalesce(source_table_full_name, source_path) AS source,
  target_table_full_name AS target, entity_type
FROM system.access.table_lineage
WHERE (target_table_full_name LIKE '{CATALOG}.ventoguard_%' OR source_table_full_name LIKE '{CATALOG}.ventoguard_%')
  AND event_date >= current_date() - INTERVAL 7 DAYS
  AND target_table_full_name IS NOT NULL
ORDER BY target, source
""")
```
**Output:**

| source | target | entity_type |
|---|---|---|
| null | serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_failure_events | PIPELINE |
| null | serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_maintenance_logs | PIPELINE |
| null | serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_market_prices | PIPELINE |
| null | serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_scada | PIPELINE |
| null | serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_turbines | PIPELINE |
| null | serverless_stable_7zqte5_catalog.ventoguard_bronze.event_log_7960386e_d964_4067_a736_b4871849e2c4 | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_gold.gold_turbine_daily | serverless_stable_7zqte5_catalog.ventoguard_gold.gold_failure_history | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_failure_events | serverless_stable_7zqte5_catalog.ventoguard_gold.gold_failure_history | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_turbines | serverless_stable_7zqte5_catalog.ventoguard_gold.gold_failure_history | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_gold.gold_turbine_daily | serverless_stable_7zqte5_catalog.ventoguard_gold.gold_farm_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_market_prices | serverless_stable_7zqte5_catalog.ventoguard_gold.gold_turbine_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | serverless_stable_7zqte5_catalog.ventoguard_gold.gold_turbine_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_turbines | serverless_stable_7zqte5_catalog.ventoguard_gold.gold_turbine_daily | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_maintenance_logs | serverless_stable_7zqte5_catalog.ventoguard_gold.maintenance_log_insights | JOB |
| serverless_stable_7zqte5_catalog.ventoguard_gold.maintenance_log_insights | serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_ai_briefs | JOB |
| serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_risk_scores | serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_ai_briefs | JOB |
| serverless_stable_7zqte5_catalog.ventoguard_gold.gold_turbine_daily | serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_health_features | JOB |
| serverless_stable_7zqte5_catalog.ventoguard_silver.silver_turbines | serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_health_features | JOB |
| null | serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_risk_history | JOB |
| null | serverless_stable_7zqte5_catalog.ventoguard_gold.turbine_risk_scores | JOB |
| null | serverless_stable_7zqte5_catalog.ventoguard_serving.event_log_ad4d2067_fc8a_4c36_8048_df2a2e36cd14 | PIPELINE |
| null | serverless_stable_7zqte5_catalog.ventoguard_serving.event_log_bd6d3837_f7db_4a63_ba1d_6c9082b95fe4 | PIPELINE |
| null | serverless_stable_7zqte5_catalog.ventoguard_serving.event_log_c92ad48a_fb1e_4c0e_8e83_1569bd79cbe2 | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_failure_events | serverless_stable_7zqte5_catalog.ventoguard_silver.silver_failure_events | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_maintenance_logs | serverless_stable_7zqte5_catalog.ventoguard_silver.silver_maintenance_logs | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_market_prices | serverless_stable_7zqte5_catalog.ventoguard_silver.silver_market_prices | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_scada | serverless_stable_7zqte5_catalog.ventoguard_silver.silver_scada | PIPELINE |
| serverless_stable_7zqte5_catalog.ventoguard_bronze.bronze_turbines | serverless_stable_7zqte5_catalog.ventoguard_silver.silver_turbines | PIPELINE |

### Cell 15
```python
q(f"""SELECT table_schema, table_name, table_type, comment FROM {CATALOG}.information_schema.tables
      WHERE table_schema IN ({IN_SCHEMAS}) ORDER BY table_schema, table_name""")
```
**Output:**

| table_schema | table_name | table_type | comment |
|---|---|---|---|
| ventoguard_bronze | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_bronze_failure_events_1 | MANAGED | Raw confirmed component failure events from CMMS (CSV). Synthetic. |
| ventoguard_bronze | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_bronze_maintenance_logs_1 | MANAGED | Raw CMMS maintenance work-order notes written by field technicians (JSON). Synthetic. |
| ventoguard_bronze | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_bronze_market_prices_1 | MANAGED | Raw hourly EPEX day-ahead prices for bidding zone DE-LU (CSV). Synthetic. |
| ventoguard_bronze | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_bronze_scada_1 | MANAGED | Raw 10-minute SCADA telemetry from turbine historians (JSON, Auto Loader). Synthetic. |
| ventoguard_bronze | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_bronze_turbines_1 | MANAGED | Raw asset register export (CSV): one row per turbine. Synthetic. |
| ventoguard_bronze | bronze_failure_events | STREAMING_TABLE | Raw confirmed component failure events from CMMS (CSV). Synthetic. |
| ventoguard_bronze | bronze_maintenance_logs | STREAMING_TABLE | Raw CMMS maintenance work-order notes written by field technicians (JSON). Synthetic. |
| ventoguard_bronze | bronze_market_prices | STREAMING_TABLE | Raw hourly EPEX day-ahead prices for bidding zone DE-LU (CSV). Synthetic. |
| ventoguard_bronze | bronze_scada | STREAMING_TABLE | Raw 10-minute SCADA telemetry from turbine historians (JSON, Auto Loader). Synthetic. |
| ventoguard_bronze | bronze_turbines | STREAMING_TABLE | Raw asset register export (CSV): one row per turbine. Synthetic. |
| ventoguard_bronze | event_log_7960386e_d964_4067_a736_b4871849e2c4 | MANAGED | null |
| ventoguard_gold | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_gold_failure_history_1 | MANAGED | Every confirmed failure with total cost of the unplanned event: repair cost plus lost revenue during the downtime window (EUR). |
| ventoguard_gold | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_gold_farm_daily_1 | MANAGED | Daily wind-farm KPIs for the asset-management dashboard and Genie: energy, availability, lost production and lost revenue. |
| ventoguard_gold | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_gold_turbine_daily_1 | MANAGED | Daily turbine KPIs: energy, technical availability, lost production (MWh & EUR) and drivetrain health signals. Grain: turbine_id x reading_date. |
| ventoguard_gold | gold_failure_history | MATERIALIZED_VIEW | Every confirmed failure with total cost of the unplanned event: repair cost plus lost revenue during the downtime window (EUR). |
| ventoguard_gold | gold_farm_daily | MATERIALIZED_VIEW | Daily wind-farm KPIs for the asset-management dashboard and Genie: energy, availability, lost production and lost revenue. |
| ventoguard_gold | gold_turbine_daily | MATERIALIZED_VIEW | Daily turbine KPIs: energy, technical availability, lost production (MWh & EUR) and drivetrain health signals. Grain: turbine_id x reading_date. |
| ventoguard_gold | maintenance_log_insights | MANAGED | Technician notes enriched by an LLM (ai_query): component, severity 1-5, precursor flag and English summary. technician_name is masked. |
| ventoguard_gold | turbine_ai_briefs | MANAGED | LLM-generated maintenance briefs for at-risk turbines: diagnosis, recommended action, crew/parts and business case. Grounded on model score, sensor residuals and technician notes. |
| ventoguard_gold | turbine_health_features | MANAGED | Daily per-turbine health features: fleet-relative residuals, 7-day means and 7-day trends. Feature table for turbine_failure_risk. |
| ventoguard_gold | turbine_risk_history | MANAGED | Daily 14-day failure probability per turbine from the turbine_failure_risk model (full history, for back-testing and trend charts). |
| ventoguard_gold | turbine_risk_scores | MANAGED | Operational risk board: latest 14-day failure probability per turbine, likely component, top signals and expected avoidable cost (EUR). Synced to Lakebase for the VentoGuard app. |
| ventoguard_silver | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_silver_failure_events_1 | MANAGED | Confirmed component failures with downtime and corrective repair cost (EUR). |
| ventoguard_silver | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_silver_maintenance_logs_1 | MANAGED | Technician work-order notes (German/English free text). technician_name is personal data and is masked for non-reliability users. |
| ventoguard_silver | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_silver_market_prices_1 | MANAGED | Hourly day-ahead price, EUR/MWh, bidding zone DE-LU. |
| ventoguard_silver | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_silver_scada_1 | MANAGED | Validated 10-minute SCADA telemetry. Rows with sensor faults (999 °C), negative wind or missing power are dropped by expectations. |
| ventoguard_silver | __materialization_mat_7960386e_d964_4067_a736_b4871849e2c4_silver_turbines_1 | MANAGED | Turbine asset register: farm, location, model, rated power, gearbox supplier, age. |
| ventoguard_silver | silver_failure_events | MATERIALIZED_VIEW | Confirmed component failures with downtime and corrective repair cost (EUR). |
| ventoguard_silver | silver_maintenance_logs | STREAMING_TABLE | Technician work-order notes (German/English free text). technician_name is personal data and is masked for non-reliability users. |
| ventoguard_silver | silver_market_prices | MATERIALIZED_VIEW | Hourly day-ahead price, EUR/MWh, bidding zone DE-LU. |
| ventoguard_silver | silver_scada | STREAMING_TABLE | Validated 10-minute SCADA telemetry. Rows with sensor faults (999 °C), negative wind or missing power are dropped by expectations. |
| ventoguard_silver | silver_turbines | MATERIALIZED_VIEW | Turbine asset register: farm, location, model, rated power, gearbox supplier, age. |

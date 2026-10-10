# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Unity Catalog governance
# MAGIC
# MAGIC Everything in VentoGuard (raw files, pipeline tables, features, model, AI outputs, Lakebase-synced tables,
# MAGIC Genie space and app) sits under **one governed schema**. This notebook applies and then *verifies*:
# MAGIC
# MAGIC * **Classification tags** on the schema, tables and PII columns, using the account's governed tag policies (`domain`, `medallion_layer`, `class.name`, `system.certification_status`, `ai.model_family`)
# MAGIC * **Column mask**: technician names are personal data under GDPR. Only `vg_reliability_leads` see them in clear
# MAGIC * **Access model**: the app service principal and Genie users get read access to gold/serving tables only
# MAGIC * **Data quality**: Lakeflow expectation results read back from the pipeline event log
# MAGIC * **Lineage**: end-to-end lineage from the raw Volume to the risk board, read from system tables

# COMMAND ----------

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

# COMMAND ----------

# MAGIC %md ## Classification tags

# COMMAND ----------

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

# COMMAND ----------

q(f"""SELECT table_name, column_name, tag_name, tag_value FROM {CATALOG}.information_schema.column_tags
      WHERE schema_name = '{SCHEMA}' ORDER BY table_name""")

# COMMAND ----------

# MAGIC %md ## Column mask on personal data (GDPR)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {FQ}.mask_person_name(name STRING)
RETURNS STRING
COMMENT 'GDPR: reveal technician names only to members of vg_reliability_leads; everyone else sees initials.'
RETURN CASE WHEN is_account_group_member('vg_reliability_leads') THEN name
            ELSE concat(left(name, 2), '***') END
""")
spark.sql(f"ALTER TABLE {FQ}.maintenance_log_insights ALTER COLUMN technician_name SET MASK {FQ}.mask_person_name")
q(f"SELECT log_id, turbine_id, technician_name, ai_summary_en FROM {FQ}.maintenance_log_insights ORDER BY created_ts DESC LIMIT 5")

# COMMAND ----------

# MAGIC %md ## Access model

# COMMAND ----------

q(f"SHOW GRANTS ON SCHEMA {FQ}")

# COMMAND ----------

# MAGIC %md ## Data quality: Lakeflow expectation results from the pipeline event log

# COMMAND ----------

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

# COMMAND ----------

# MAGIC %md ## Lineage: raw files → pipeline → features → risk board (system tables)

# COMMAND ----------

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

# COMMAND ----------

q(f"""SELECT table_name, table_type, comment FROM {CATALOG}.information_schema.tables
      WHERE table_schema = '{SCHEMA}' ORDER BY table_name""")

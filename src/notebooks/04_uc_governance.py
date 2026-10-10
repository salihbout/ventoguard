# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Unity Catalog governance
# MAGIC
# MAGIC VentoGuard lives in one catalog, with one schema per layer:
# MAGIC
# MAGIC | Schema | Holds | Who reads it |
# MAGIC |---|---|---|
# MAGIC | `ventoguard_bronze` | raw landing Volume + Auto Loader bronze tables | data engineering only |
# MAGIC | `ventoguard_silver` | validated, typed tables (expectations applied) | data engineering, data science |
# MAGIC | `ventoguard_gold` | business KPIs, features, model, risk scores, AI outputs | analysts, Genie, the app |
# MAGIC | `ventoguard_serving` | Lakebase synced tables used by the app | the app service principal |
# MAGIC
# MAGIC This notebook applies and then *verifies*:
# MAGIC * **Classification tags** on schemas, tables and PII columns, using the account's governed tag policies (`domain`, `medallion_layer`, `class.name`, `system.certification_status`, `ai.model_family`)
# MAGIC * **Column mask**: technician names are personal data under GDPR. Only `vg_reliability_leads` see them in clear
# MAGIC * **Access model**: grants per schema
# MAGIC * **Data quality**: Lakeflow expectation results read back from the pipeline event log
# MAGIC * **Lineage**: bronze → silver → gold → risk board, read from system tables

# COMMAND ----------

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

# COMMAND ----------

# MAGIC %md ## Classification tags

# COMMAND ----------

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

# COMMAND ----------

q(f"""SELECT schema_name, table_name, tag_name, tag_value FROM {CATALOG}.information_schema.table_tags
      WHERE schema_name IN ({IN_SCHEMAS}) AND tag_name IN ('medallion_layer', 'vg_layer', 'system.certification_status', 'ai_generated', 'ai.model_family')
      ORDER BY schema_name, table_name, tag_name""")

# COMMAND ----------

q(f"""SELECT schema_name, table_name, column_name, tag_name, tag_value FROM {CATALOG}.information_schema.column_tags
      WHERE schema_name IN ({IN_SCHEMAS}) ORDER BY schema_name, table_name""")

# COMMAND ----------

# MAGIC %md ## Column mask on personal data (GDPR)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {GOLD}.mask_person_name(name STRING)
RETURNS STRING
COMMENT 'GDPR: reveal technician names only to members of vg_reliability_leads; everyone else sees initials.'
RETURN CASE WHEN is_account_group_member('vg_reliability_leads') THEN name
            ELSE concat(left(name, 2), '***') END
""")
spark.sql(f"ALTER TABLE {GOLD}.maintenance_log_insights ALTER COLUMN technician_name SET MASK {GOLD}.mask_person_name")
q(f"SELECT log_id, turbine_id, technician_name, ai_summary_en FROM {GOLD}.maintenance_log_insights ORDER BY created_ts DESC LIMIT 5")

# COMMAND ----------

# MAGIC %md ## Access model: grants per layer schema

# COMMAND ----------

for schema in SCHEMAS.values():
    q(f"SHOW GRANTS ON SCHEMA {CATALOG}.{schema}")

# COMMAND ----------

# MAGIC %md ## Data quality: Lakeflow expectation results from the pipeline event log

# COMMAND ----------

q(f"""
SELECT
  x.dataset, x.name AS expectation, sum(x.passed_records) AS passed_records, sum(x.failed_records) AS failed_records
FROM event_log(TABLE({SILVER}.silver_scada)) e
LATERAL VIEW explode(from_json(e.details:flow_progress:data_quality:expectations,
  'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>')) t AS x
WHERE e.event_type = 'flow_progress' AND e.details:flow_progress:data_quality IS NOT NULL
GROUP BY 1, 2 ORDER BY 1, 2
""")

# COMMAND ----------

# MAGIC %md ## Lineage: bronze → silver → gold → features → risk board (system tables)

# COMMAND ----------

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

# COMMAND ----------

q(f"""SELECT table_schema, table_name, table_type, comment FROM {CATALOG}.information_schema.tables
      WHERE table_schema IN ({IN_SCHEMAS}) ORDER BY table_schema, table_name""")

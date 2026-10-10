# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Score the fleet + GenAI maintenance intelligence
# MAGIC
# MAGIC 1. **Batch inference.** The `@champion` model scores every turbine-day: `turbine_risk_history` holds all days for back-testing,
# MAGIC    and `turbine_risk_scores` holds the latest day, which is the operational table synced to Lakebase.
# MAGIC 2. **Business translation.** Each risk score becomes *expected avoidable cost* (€): the probability times the
# MAGIC    corrective-minus-planned cost of that component, including lost revenue at this turbine's own earning rate.
# MAGIC 3. **GenAI on unstructured notes.** `ai_query` reads every German/English technician note and extracts
# MAGIC    component, severity, a precursor flag and an English summary into `maintenance_log_insights`.
# MAGIC 4. **GenAI maintenance briefs.** For each at-risk turbine, Claude writes a dispatcher-ready brief from the sensor evidence,
# MAGIC    recent notes and the cost case. The output goes to `turbine_ai_briefs`, which is synced to Lakebase and shown in the app.

# COMMAND ----------

# MAGIC %pip install -q scikit-learn==1.5.2 "mlflow>=3.1"
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("schema", "wind_reliability")
dbutils.widgets.text("llm_endpoint", "databricks-claude-sonnet-4-5")
dbutils.widgets.text("llm_endpoint_fast", "databricks-claude-haiku-4-5")
CATALOG, SCHEMA = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
LLM, LLM_FAST = dbutils.widgets.get("llm_endpoint"), dbutils.widgets.get("llm_endpoint_fast")
FQ = f"{CATALOG}.{SCHEMA}"
MODEL_NAME = f"{FQ}.turbine_failure_risk"
spark.sql(f"USE CATALOG {CATALOG}"); spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

# MAGIC %md ## 1 · Batch inference with the UC `@champion` model

# COMMAND ----------

import mlflow, pandas as pd, numpy as np
from mlflow import MlflowClient
from pyspark.sql import functions as F

mlflow.set_registry_uri("databricks-uc")
client = MlflowClient()
try:
    mv = client.get_model_version_by_alias(MODEL_NAME, "champion"); alias = "champion"
except Exception:
    mv = client.get_model_version_by_alias(MODEL_NAME, "challenger"); alias = "challenger"
    print("WARNING: no @champion yet: scoring with @challenger")
model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@{alias}")
FEATURES = client.get_model_version(MODEL_NAME, mv.version).tags["features"].split(",")
print(f"Scoring with {MODEL_NAME} v{mv.version} (@{alias}), {len(FEATURES)} features")

feat = spark.table(f"{FQ}.turbine_health_features").toPandas()
feat["failure_prob_14d"] = model.predict_proba(feat[FEATURES])[:, 1]

hist = feat[["turbine_id", "farm_id", "reading_date", "technical_availability", "failure_prob_14d"]].copy()
hist["model_version"] = int(mv.version)
spark.createDataFrame(hist).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.turbine_risk_history")
spark.sql(f"COMMENT ON TABLE {FQ}.turbine_risk_history IS 'Daily 14-day failure probability per turbine from the turbine_failure_risk model (full history, for back-testing and trend charts).'")

# COMMAND ----------

# MAGIC %md ## 2 · Latest-day risk with component attribution and € value at stake

# COMMAND ----------

latest_date = feat.reading_date.max()
cur = feat[feat.reading_date == latest_date].copy()

# Component attribution: which subsystem's fleet-relative signal is most abnormal (z-score of 7-day residual)
sig = {
    "gearbox": ["oil_temp_resid_7d", "gbx_bearing_temp_resid_7d", "vibration_resid_7d"],
    "main_bearing": ["main_bearing_temp_resid_7d"],
    "generator_bearing": ["gen_bearing_temp_resid_7d"],
    "pitch_hydraulics": ["hydraulic_resid_7d"],
}
std = feat[sum(sig.values(), [])].std()
z = pd.DataFrame(index=cur.index)
z["gearbox"] = cur[sig["gearbox"]].div(std[sig["gearbox"]]).max(axis=1)
z["main_bearing"] = cur["main_bearing_temp_resid_7d"] / std["main_bearing_temp_resid_7d"]
z["generator_bearing"] = cur["gen_bearing_temp_resid_7d"] / std["gen_bearing_temp_resid_7d"]
z["pitch_hydraulics"] = -cur["hydraulic_resid_7d"] / std["hydraulic_resid_7d"]
cur["likely_component"] = z.idxmax(axis=1)
cur["anomaly_zscore"] = z.max(axis=1).round(2)

LABELS = {"oil_temp_resid_7d": ("Gearbox oil temp", "°C"), "gbx_bearing_temp_resid_7d": ("Gearbox bearing temp", "°C"),
          "vibration_resid_7d": ("Gearbox vibration p95", "mm/s"), "main_bearing_temp_resid_7d": ("Main bearing temp", "°C"),
          "gen_bearing_temp_resid_7d": ("Generator bearing temp", "°C"), "hydraulic_resid_7d": ("Pitch hydraulic pressure", "bar"),
          "power_curve_resid_7d": ("Power-curve ratio", "")}
# Direction-aware: only deviations that indicate damage count (hotter / more vibration / lower pressure / lower output)
DIRECTION = {"hydraulic_resid_7d": -1, "power_curve_resid_7d": -1}
def top_signals(r):
    zz = {k: DIRECTION.get(k, 1) * r[k] / feat[k].std() for k in LABELS}
    best = sorted(zz, key=zz.get, reverse=True)[:3]
    return "; ".join(f"{LABELS[k][0]} {r[k]:+.2f}{LABELS[k][1]} vs fleet (7d)" for k in best)
cur["top_signals"] = cur.apply(top_signals, axis=1)

# Cost model (EUR). Corrective = unplanned failure incl. crane mobilisation; planned = caught early, swapped in a low-wind window
COST = pd.DataFrame([
    ("gearbox",           385_000, 38, 205_000, 7),
    ("main_bearing",      310_000, 44, 175_000, 9),
    ("generator_bearing",  92_000, 11,  38_000, 2),
    ("pitch_hydraulics",   26_000,  3,   9_000, 0.5),
], columns=["likely_component", "corrective_cost_eur", "corrective_downtime_days", "planned_cost_eur", "planned_downtime_days"])
rev = spark.sql(f"SELECT turbine_id, avg(revenue_eur + lost_revenue_eur) AS revenue_per_day_eur FROM {FQ}.gold_turbine_daily GROUP BY turbine_id").toPandas()
cur = cur.merge(COST, on="likely_component").merge(rev, on="turbine_id")
cur["avoidable_cost_if_caught_eur"] = (cur.corrective_cost_eur + cur.corrective_downtime_days * cur.revenue_per_day_eur) - (cur.planned_cost_eur + cur.planned_downtime_days * cur.revenue_per_day_eur)
cur["expected_avoidable_cost_eur"] = (cur.failure_prob_14d * cur.avoidable_cost_if_caught_eur).round(0)
cur["risk_tier"] = pd.cut(cur.failure_prob_14d, [-1, 0.10, 0.30, 0.60, 1.01], labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"]).astype(str)
cur.loc[cur.technical_availability < 0.5, "risk_tier"] = "DOWN"
cur["recommended_window"] = cur.risk_tier.map({"CRITICAL": "Act within 72 h", "HIGH": "Plan within 7 days", "MEDIUM": "Inspect at next visit", "LOW": "Routine", "DOWN": "In repair"})

turb = spark.table(f"{FQ}.silver_turbines").select("turbine_id", "farm_name", "model", "latitude", "longitude", "turbine_age_years", "gearbox_supplier").toPandas()
out = cur.merge(turb, on="turbine_id", suffixes=("", "_t"))
cols = ["turbine_id", "farm_id", "farm_name", "model", "latitude", "longitude", "turbine_age_years", "gearbox_supplier",
        "reading_date", "failure_prob_14d", "risk_tier", "recommended_window", "likely_component", "anomaly_zscore", "top_signals",
        "oil_temp_resid_7d", "gbx_bearing_temp_resid_7d", "main_bearing_temp_resid_7d", "gen_bearing_temp_resid_7d",
        "vibration_resid_7d", "hydraulic_resid_7d", "power_curve_resid_7d",
        "corrective_cost_eur", "planned_cost_eur", "revenue_per_day_eur", "avoidable_cost_if_caught_eur", "expected_avoidable_cost_eur"]
out = out[cols].rename(columns={"reading_date": "score_date"})
out["failure_prob_14d"] = out.failure_prob_14d.round(4)
out["model_version"] = int(mv.version)
sdf = spark.createDataFrame(out).withColumn("scored_at", F.current_timestamp())
sdf.write.mode("overwrite").option("overwriteSchema", "true").option("delta.enableChangeDataFeed", "true").saveAsTable(f"{FQ}.turbine_risk_scores")
spark.sql(f"ALTER TABLE {FQ}.turbine_risk_scores SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
spark.sql(f"COMMENT ON TABLE {FQ}.turbine_risk_scores IS 'Operational risk board: latest 14-day failure probability per turbine, likely component, top signals and expected avoidable cost (EUR). Synced to Lakebase for the VentoGuard app.'")
print("score_date =", latest_date)
display(spark.sql(f"SELECT risk_tier, count(*) turbines, round(sum(expected_avoidable_cost_eur)) expected_avoidable_eur FROM {FQ}.turbine_risk_scores GROUP BY 1 ORDER BY 3 DESC"))

# COMMAND ----------

display(spark.sql(f"""SELECT turbine_id, farm_name, risk_tier, failure_prob_14d, likely_component, top_signals, expected_avoidable_cost_eur
                      FROM {FQ}.turbine_risk_scores ORDER BY failure_prob_14d DESC LIMIT 12"""))

# COMMAND ----------

# MAGIC %md ### Back-test against the hidden ground truth
# MAGIC The generator scheduled failures **after** the data cut-off and never exposed them to the pipeline or the model.
# MAGIC Did today's risk board catch the ones that were already degrading?

# COMMAND ----------

gt = pd.read_csv(f"/Volumes/{CATALOG}/{SCHEMA}/raw_landing/_ground_truth/future_failures.csv", parse_dates=["degradation_start_ts", "failure_ts"])
gt["degrading_at_cutoff"] = gt.degradation_start_ts < pd.Timestamp(latest_date) + pd.Timedelta(days=1)
chk = gt.merge(out[["turbine_id", "risk_tier", "failure_prob_14d", "likely_component"]], on="turbine_id", how="left")
chk["days_until_failure"] = (chk.failure_ts - pd.Timestamp(latest_date)).dt.days
display(chk[["turbine_id", "component", "failure_ts", "days_until_failure", "degrading_at_cutoff", "risk_tier", "failure_prob_14d", "likely_component"]].sort_values("failure_ts"))
flagged = chk[chk.degrading_at_cutoff & chk.risk_tier.isin(["HIGH", "CRITICAL"])]
print(f"Upcoming failures already degrading at cut-off: {int(chk.degrading_at_cutoff.sum())}; flagged HIGH/CRITICAL today: {len(flagged)}")
print(f"Turbines flagged HIGH/CRITICAL in total: {int(out.risk_tier.isin(['HIGH','CRITICAL']).sum())}")

# COMMAND ----------

# MAGIC %md ## 3 · GenAI: structured extraction from multilingual technician notes (`ai_query`)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {FQ}.maintenance_log_insights
COMMENT 'Technician notes enriched by an LLM (ai_query): component, severity 1-5, precursor flag and English summary. technician_name is masked.'
AS
WITH src AS (
  SELECT log_id, turbine_id, created_ts, category, technician_name, note_text
  FROM {FQ}.silver_maintenance_logs
),
llm AS (
  SELECT *, ai_query(
    '{LLM_FAST}',
    concat(
      'You are a wind-turbine reliability engineer. Analyse this maintenance note (it may be German or English). ',
      'Return ONLY a JSON object with keys: component (one of gearbox, main_bearing, generator_bearing, pitch_hydraulics, blades, converter, yaw, tower_safety, none), ',
      'severity (integer 1-5, 5 = imminent failure), failure_precursor (true if the note describes symptoms that typically precede a major component failure), ',
      'summary_en (max 20 words, English). Note: ', note_text),
    failOnError => false) AS resp
  FROM src
)
SELECT log_id, turbine_id, created_ts, category, technician_name, note_text,
  j.component AS ai_component, CAST(j.severity AS INT) AS ai_severity, CAST(j.failure_precursor AS BOOLEAN) AS ai_failure_precursor,
  j.summary_en AS ai_summary_en, resp.errorMessage AS ai_error
FROM (SELECT *, from_json(regexp_extract(resp.result, '(?s)\\\\{{.*\\\\}}', 0),
  'component STRING, severity INT, failure_precursor BOOLEAN, summary_en STRING') AS j FROM llm)
""")
display(spark.sql(f"""SELECT ai_component, count(*) notes, round(avg(ai_severity),2) avg_severity, sum(CAST(ai_failure_precursor AS INT)) precursors, sum(CASE WHEN ai_error IS NOT NULL THEN 1 ELSE 0 END) errors
                      FROM {FQ}.maintenance_log_insights GROUP BY 1 ORDER BY 2 DESC"""))

# COMMAND ----------

display(spark.sql(f"SELECT log_id, turbine_id, note_text, ai_component, ai_severity, ai_failure_precursor, ai_summary_en FROM {FQ}.maintenance_log_insights WHERE ai_severity >= 3 ORDER BY created_ts DESC LIMIT 10"))

# COMMAND ----------

# MAGIC %md ## 4 · GenAI maintenance briefs for at-risk turbines (Claude via `ai_query`)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TEMP VIEW brief_input AS
WITH at_risk AS (
  SELECT * FROM {FQ}.turbine_risk_scores
  WHERE risk_tier IN ('CRITICAL', 'HIGH', 'MEDIUM')
  QUALIFY row_number() OVER (ORDER BY failure_prob_14d DESC) <= 15
),
notes AS (
  SELECT turbine_id, concat_ws(' | ', collect_list(concat(date_format(created_ts, 'yyyy-MM-dd'), ': ', ai_summary_en))) AS recent_notes
  FROM (SELECT * FROM {FQ}.maintenance_log_insights WHERE created_ts >= date_sub(current_date(), 60)
        QUALIFY row_number() OVER (PARTITION BY turbine_id ORDER BY created_ts DESC) <= 4)
  GROUP BY turbine_id
)
SELECT r.*, coalesce(n.recent_notes, 'none in last 60 days') AS recent_notes
FROM at_risk r LEFT JOIN notes n USING (turbine_id)
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {FQ}.turbine_ai_briefs
TBLPROPERTIES (delta.enableChangeDataFeed = true)
COMMENT 'LLM-generated maintenance briefs for at-risk turbines: diagnosis, recommended action, crew/parts and business case. Grounded on model score, sensor residuals and technician notes.'
AS
WITH gen AS (
  SELECT turbine_id, farm_name, risk_tier, failure_prob_14d, likely_component, expected_avoidable_cost_eur, score_date,
    ai_query('{LLM}', concat(
      'You are the reliability lead at a German onshore wind operator. Write a maintenance brief for the dispatcher. ',
      'Use ONLY the facts below; do not invent measurements. Return ONLY JSON with keys: ',
      'headline (max 12 words), diagnosis (2 sentences, cite the sensor evidence), recommended_action (3 short imperative steps separated by \" ; \"), ',
      'urgency_days (integer: days within which to act), crew_and_parts (1 sentence), business_case (1 sentence quantifying EUR avoided vs. waiting for failure).',
      '\\nTurbine: ', turbine_id, ' (', model, ', ', CAST(turbine_age_years AS STRING), ' years, gearbox supplier ', gearbox_supplier, ') at ', farm_name,
      '\\nModel: 14-day failure probability ', CAST(round(failure_prob_14d*100,1) AS STRING), '% (tier ', risk_tier, '), most likely component: ', likely_component,
      '\\nSensor evidence vs fleet (7-day): ', top_signals,
      '\\nRecent technician notes: ', recent_notes,
      '\\nCost if it fails unplanned vs planned swap: avoidable EUR ', CAST(round(avoidable_cost_if_caught_eur) AS STRING),
      '; corrective repair EUR ', CAST(corrective_cost_eur AS STRING), ', planned repair EUR ', CAST(planned_cost_eur AS STRING),
      ', revenue at stake per day EUR ', CAST(round(revenue_per_day_eur) AS STRING)),
      failOnError => false) AS resp
  FROM brief_input
)
SELECT turbine_id, farm_name, risk_tier, failure_prob_14d, likely_component, expected_avoidable_cost_eur, score_date,
  j.headline, j.diagnosis, j.recommended_action, CAST(j.urgency_days AS INT) AS urgency_days, j.crew_and_parts, j.business_case,
  '{LLM}' AS llm_endpoint, current_timestamp() AS generated_at, resp.errorMessage AS ai_error
FROM (SELECT *, from_json(regexp_extract(resp.result, '(?s)\\\\{{.*\\\\}}', 0),
  'headline STRING, diagnosis STRING, recommended_action STRING, urgency_days INT, crew_and_parts STRING, business_case STRING') AS j FROM gen)
""")
spark.sql(f"ALTER TABLE {FQ}.turbine_ai_briefs ALTER COLUMN turbine_id SET NOT NULL")
display(spark.sql(f"SELECT turbine_id, risk_tier, failure_prob_14d, headline, diagnosis, recommended_action, urgency_days, business_case, ai_error FROM {FQ}.turbine_ai_briefs ORDER BY failure_prob_14d DESC"))

# COMMAND ----------

n_err = spark.sql(f"SELECT count(*) FROM {FQ}.turbine_ai_briefs WHERE headline IS NULL").first()[0]
summary = spark.sql(f"""SELECT count(*) AS turbines_scored, sum(CASE WHEN risk_tier IN ('HIGH','CRITICAL') THEN 1 ELSE 0 END) AS high_or_critical,
                        round(sum(expected_avoidable_cost_eur)) AS fleet_expected_avoidable_eur FROM {FQ}.turbine_risk_scores""").first().asDict()
print(summary, "| briefs without headline:", n_err)
assert n_err == 0, "Some briefs failed to generate"

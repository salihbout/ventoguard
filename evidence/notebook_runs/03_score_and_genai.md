# a892cca0-015e-4b12-9cfc-74572aeb9371: executed notebook (task run 75994340528623)

> Exported from the Databricks job run with `databricks jobs export-run`; cell sources and their outputs exactly as executed on serverless compute.


# 03 · Score the fleet + GenAI maintenance intelligence

1. **Batch inference.** The `@champion` model scores every turbine-day: `turbine_risk_history` holds all days for back-testing,
   and `turbine_risk_scores` holds the latest day, which is the operational table synced to Lakebase.
2. **Business translation.** Each risk score becomes *expected avoidable cost* (€): the probability times the
   corrective-minus-planned cost of that component, including lost revenue at this turbine's own earning rate.
3. **GenAI on unstructured notes.** `ai_query` reads every German/English technician note and extracts
   component, severity, a precursor flag and an English summary into `maintenance_log_insights`.
4. **GenAI maintenance briefs.** For each at-risk turbine, Claude writes a dispatcher-ready brief from the sensor evidence,
   recent notes and the cost case. The output goes to `turbine_ai_briefs`, which is synced to Lakebase and shown in the app.

### Cell 2
```python
%pip install -q scikit-learn==1.5.2 "mlflow>=3.1"
%restart_python
```
**Output:**
```text
[43mNote: you may need to restart the kernel using %restart_python or dbutils.library.restartPython() to use updated packages.[0m
```

### Cell 3
```python
dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("schema", "wind_reliability")
dbutils.widgets.text("llm_endpoint", "databricks-claude-sonnet-4-5")
dbutils.widgets.text("llm_endpoint_fast", "databricks-claude-haiku-4-5")
CATALOG, SCHEMA = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
LLM, LLM_FAST = dbutils.widgets.get("llm_endpoint"), dbutils.widgets.get("llm_endpoint_fast")
FQ = f"{CATALOG}.{SCHEMA}"
MODEL_NAME = f"{FQ}.turbine_failure_risk"
spark.sql(f"USE CATALOG {CATALOG}"); spark.sql(f"USE SCHEMA {SCHEMA}")
```

## 1 · Batch inference with the UC `@champion` model

### Cell 5
```python
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
```
**Output:**
```text
Scoring with serverless_stable_7zqte5_catalog.wind_reliability.turbine_failure_risk v3 (@champion), 23 features
```

## 2 · Latest-day risk with component attribution and € value at stake

### Cell 7
```python
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
```

### Cell 8
```python
display(spark.sql(f"""SELECT turbine_id, farm_name, risk_tier, failure_prob_14d, likely_component, top_signals, expected_avoidable_cost_eur
                      FROM {FQ}.turbine_risk_scores ORDER BY failure_prob_14d DESC LIMIT 12"""))
```
**Output:**

| turbine_id | farm_name | risk_tier | failure_prob_14d | likely_component | top_signals | expected_avoidable_cost_eur |
|---|---|---|---|---|---|---|
| F03-T07 | Hunsrueck Hoehe | CRITICAL | 0.9953 | gearbox | Power-curve ratio -0.05 vs fleet (7d); Gearbox vibration p95 +1.58mm/s vs fleet (7d); Gearbox bearing temp +6.09°C vs fleet (7d) | 205562.0 |
| F03-T09 | Hunsrueck Hoehe | CRITICAL | 0.9912 | gearbox | Gearbox vibration p95 +1.95mm/s vs fleet (7d); Power-curve ratio -0.06 vs fleet (7d); Gearbox bearing temp +7.51°C vs fleet (7d) | 205914.0 |
| F01-T20 | Uckermark Nord | CRITICAL | 0.9578 | gearbox | Gearbox vibration p95 +0.60mm/s vs fleet (7d); Gearbox bearing temp +2.44°C vs fleet (7d); Power-curve ratio -0.02 vs fleet (7d) | 215327.0 |
| F04-T16 | Eifel West | HIGH | 0.5529 | main_bearing | Power-curve ratio -0.01 vs fleet (7d); Main bearing temp +0.35°C vs fleet (7d); Pitch hydraulic pressure -0.01bar vs fleet (7d) | 92062.0 |
| F01-T06 | Uckermark Nord | MEDIUM | 0.2516 | generator_bearing | Generator bearing temp +0.26°C vs fleet (7d); Gearbox bearing temp +0.30°C vs fleet (7d); Gearbox oil temp +0.19°C vs fleet (7d) | 16861.0 |
| F03-T14 | Hunsrueck Hoehe | MEDIUM | 0.1439 | pitch_hydraulics | Pitch hydraulic pressure -0.12bar vs fleet (7d); Power-curve ratio +0.00 vs fleet (7d); Gearbox vibration p95 -0.08mm/s vs fleet (7d) | 2745.0 |
| F02-T07 | Ostfriesland Kueste | MEDIUM | 0.1032 | pitch_hydraulics | Pitch hydraulic pressure -0.17bar vs fleet (7d); Main bearing temp +0.12°C vs fleet (7d); Gearbox vibration p95 +0.04mm/s vs fleet (7d) | 2437.0 |
| F02-T15 | Ostfriesland Kueste | LOW | 0.0979 | gearbox | Power-curve ratio -0.00 vs fleet (7d); Gearbox oil temp +0.20°C vs fleet (7d); Gearbox bearing temp +0.23°C vs fleet (7d) | 25680.0 |
| F03-T16 | Hunsrueck Hoehe | LOW | 0.0932 | generator_bearing | Generator bearing temp +0.87°C vs fleet (7d); Gearbox bearing temp +0.88°C vs fleet (7d); Gearbox oil temp +0.67°C vs fleet (7d) | 5942.0 |
| F03-T02 | Hunsrueck Hoehe | LOW | 0.0707 | pitch_hydraulics | Pitch hydraulic pressure -0.01bar vs fleet (7d); Power-curve ratio +0.00 vs fleet (7d); Main bearing temp -0.29°C vs fleet (7d) | 1330.0 |
| F01-T22 | Uckermark Nord | LOW | 0.0662 | pitch_hydraulics | Pitch hydraulic pressure -0.16bar vs fleet (7d); Main bearing temp +0.14°C vs fleet (7d); Gearbox bearing temp +0.17°C vs fleet (7d) | 1356.0 |
| F03-T23 | Hunsrueck Hoehe | LOW | 0.0615 | pitch_hydraulics | Power-curve ratio -0.00 vs fleet (7d); Pitch hydraulic pressure -0.07bar vs fleet (7d); Main bearing temp -0.13°C vs fleet (7d) | 1169.0 |

### Back-test against the hidden ground truth
The generator scheduled failures **after** the data cut-off and never exposed them to the pipeline or the model.
Did today's risk board catch the ones that were already degrading?

### Cell 10
```python
gt = pd.read_csv(f"/Volumes/{CATALOG}/{SCHEMA}/raw_landing/_ground_truth/future_failures.csv", parse_dates=["degradation_start_ts", "failure_ts"])
gt["degrading_at_cutoff"] = gt.degradation_start_ts < pd.Timestamp(latest_date) + pd.Timedelta(days=1)
chk = gt.merge(out[["turbine_id", "risk_tier", "failure_prob_14d", "likely_component"]], on="turbine_id", how="left")
chk["days_until_failure"] = (chk.failure_ts - pd.Timestamp(latest_date)).dt.days
display(chk[["turbine_id", "component", "failure_ts", "days_until_failure", "degrading_at_cutoff", "risk_tier", "failure_prob_14d", "likely_component"]].sort_values("failure_ts"))
flagged = chk[chk.degrading_at_cutoff & chk.risk_tier.isin(["HIGH", "CRITICAL"])]
print(f"Upcoming failures already degrading at cut-off: {int(chk.degrading_at_cutoff.sum())}; flagged HIGH/CRITICAL today: {len(flagged)}")
print(f"Turbines flagged HIGH/CRITICAL in total: {int(out.risk_tier.isin(['HIGH','CRITICAL']).sum())}")
```
**Output:**

| turbine_id | component | failure_ts | days_until_failure | degrading_at_cutoff | risk_tier | failure_prob_14d | likely_component |
|---|---|---|---|---|---|---|---|
| F03-T09 | gearbox | 2026-10-13T19:07:00.000Z | 4 | True | CRITICAL | 0.9912 | gearbox |
| F03-T07 | gearbox | 2026-10-19T02:02:00.000Z | 10 | True | CRITICAL | 0.9953 | gearbox |
| F01-T20 | gearbox | 2026-10-23T13:10:00.000Z | 14 | True | CRITICAL | 0.9578 | gearbox |
| F02-T07 | generator_bearing | 2026-10-26T17:24:00.000Z | 17 | False | MEDIUM | 0.1032 | pitch_hydraulics |
| F04-T16 | main_bearing | 2026-10-28T04:15:00.000Z | 19 | True | HIGH | 0.5529 | main_bearing |
| F03-T17 | pitch_hydraulics | 2026-10-28T07:54:00.000Z | 19 | False | LOW | 0.0108 | generator_bearing |
**Output:**
```text
Upcoming failures already degrading at cut-off: 4; flagged HIGH/CRITICAL today: 4
Turbines flagged HIGH/CRITICAL in total: 4
```

## 3 · GenAI: structured extraction from multilingual technician notes (`ai_query`)

### Cell 12
```python
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
```
**Output:**

| ai_component | notes | avg_severity | precursors | errors |
|---|---|---|---|---|
| none | 191 | 1.0 | 0 | 0 |
| gearbox | 101 | 1.76 | 14 | 0 |
| pitch_hydraulics | 74 | 1.16 | 4 | 0 |
| blades | 65 | 1.0 | 0 | 0 |
| tower_safety | 63 | 1.0 | 0 | 0 |
| generator_bearing | 15 | 2.0 | 8 | 0 |
| main_bearing | 10 | 4.5 | 5 | 0 |

### Cell 13
```python
display(spark.sql(f"SELECT log_id, turbine_id, note_text, ai_component, ai_severity, ai_failure_precursor, ai_summary_en FROM {FQ}.maintenance_log_insights WHERE ai_severity >= 3 ORDER BY created_ts DESC LIMIT 10"))
```
**Output:**

| log_id | turbine_id | note_text | ai_component | ai_severity | ai_failure_precursor | ai_summary_en |
|---|---|---|---|---|---|---|
| WO-00508 | F03-T07 | Customer remote alarm: gearbox oil temperature high warnings during full load. On site noticed faint metallic whine from intermediate stage. Oil sample sent to lab. | gearbox | 4 | True | High gearbox oil temperature and metallic noise indicate potential bearing wear or gear damage. |
| WO-00509 | F03-T07 | Ölprobe Getriebe: erhöhter Eisengehalt (Fe 74 ppm) und Partikel auf Magnetstopfen. Leichte Geräusche bei Volllast. Empfehle Endoskopie. | gearbox | 3 | True | Oil analysis shows elevated iron content and particles. Noise under full load detected. |
| WO-00507 | F03-T09 | Customer remote alarm: gearbox oil temperature high warnings during full load. On site noticed faint metallic whine from intermediate stage. Oil sample sent to lab. | gearbox | 4 | True | High gearbox oil temperature with metallic whine indicates potential bearing wear or gear damage. |
| WO-00478 | F01-T27 | Hauptlagerschaden bestätigt. Anlage außer Betrieb, Kran und Rotordemontage erforderlich. | main_bearing | 5 | False | Main bearing damage confirmed. Turbine offline, crane and rotor removal required. |
| WO-00502 | F01-T25 | Hydraulikdruck Pitch schwankend, Leckage an Achse 3 festgestellt. Dichtungen bestellt. | pitch_hydraulics | 3 | True | Fluctuating pitch hydraulic pressure with leak at axis 3. Seals ordered. |
| WO-00501 | F01-T25 | Pitch hydraulic pressure drops during gusts, small oil leak at axis 2 cylinder. Topped up hydraulic oil. | pitch_hydraulics | 3 | True | Pitch hydraulic pressure drop during gusts with oil leak at cylinder axis 2. Oil topped up. |
| WO-00475 | F01-T21 | Gearbox failure confirmed (HSS bearing seizure). Turbine stopped. Crane mobilisation requested, exchange gearbox ordered. Expected downtime 5-6 weeks. | gearbox | 5 | False | HSS bearing seizure confirmed. Gearbox failure. Crane mobilisation and exchange ordered. 5-6 weeks downtime. |
| WO-00473 | F03-T28 | Gearbox failure confirmed (HSS bearing seizure). Turbine stopped. Crane mobilisation requested, exchange gearbox ordered. Expected downtime 5-6 weeks. | gearbox | 5 | False | HSS bearing seizure confirmed. Gearbox failed. Crane and replacement ordered. 5-6 weeks downtime. |
| WO-00474 | F01-T21 | Customer remote alarm: gearbox oil temperature high warnings during full load. On site noticed faint metallic whine from intermediate stage. Oil sample sent to lab. | gearbox | 4 | True | High gearbox oil temperature with metallic whine from intermediate stage. Oil analysis pending. |
| WO-00458 | F01-T06 | Gearbox failure confirmed (HSS bearing seizure). Turbine stopped. Crane mobilisation requested, exchange gearbox ordered. Expected downtime 5-6 weeks. | gearbox | 5 | False | HSS bearing seizure confirmed. Gearbox failed. Crane and replacement ordered. 5-6 weeks downtime. |

## 4 · GenAI maintenance briefs for at-risk turbines (Claude via `ai_query`)

### Cell 15
```python
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
```
**Output:**

| turbine_id | risk_tier | failure_prob_14d | headline | diagnosis | recommended_action | urgency_days | business_case | ai_error |
|---|---|---|---|---|---|---|---|---|
| F03-T07 | CRITICAL | 0.9953 | F03-T07 Gearbox Bearing Failure Imminent Within Days | Gearbox bearing temperature is elevated +6.09°C above fleet average and vibration increased +1.58mm/s, consistent with technician observations of metallic noise and oil analysis showing elevated iron content and particles on 2026-10-03 and 2026-10-04. Power curve ratio has degraded -0.05 vs fleet over 7 days, indicating mechanical deterioration. | Stop turbine immediately to prevent catastrophic gearbox failure ; Schedule planned gearbox replacement with Hansa Drives parts ; Conduct borescope inspection and final oil sample before removal | 2 | Planned intervention avoids EUR 206,523 in additional damage costs versus unplanned failure (EUR 385,000 corrective vs EUR 205,000 planned repair). | null |
| F03-T09 | CRITICAL | 0.9912 | F03-T09 Gearbox Bearing Failure Imminent Within Two Weeks | Gearbox vibration elevated +1.95 mm/s above fleet average, bearing temperature +7.51°C above fleet, and power-curve ratio degraded by -0.06 over the past 7 days. Technician observed high oil temperature with metallic whine on 2026-10-02, confirming bearing wear or gear damage. | Stop turbine immediately to prevent catastrophic gearbox failure ; Schedule planned gearbox replacement with Hansa Drives-compatible unit ; Arrange heavy-lift crane and certified gearbox technician crew | 2 | Planned intervention avoids EUR 207,747 in additional costs versus unplanned failure (EUR 385,000 corrective vs EUR 205,000 planned repair). | null |
| F01-T20 | CRITICAL | 0.9578 | F01-T20 Gearbox Critical: 95.8% Failure Risk Within 14 Days | Gearbox shows elevated vibration (+0.60 mm/s above fleet average) and bearing temperature (+2.44°C above fleet average) over the past 7 days, indicating imminent bearing or gear mesh failure. The 14-day failure probability model rates this turbine CRITICAL at 95.8% with gearbox as the most likely failing component. | Stop turbine immediately and lock out ; Mobilize gearbox replacement crew and crane within 48 hours ; Execute planned gearbox swap before catastrophic failure | 2 | Planned intervention avoids EUR 224,811 in additional damage costs versus waiting for unplanned failure (EUR 385,000 corrective vs EUR 205,000 planned repair). | null |
| F04-T16 | HIGH | 0.5529 | F04-T16 Main Bearing Failure Predicted Within 14 Days | The predictive model indicates 55.3% failure probability for the main bearing within 14 days. Main bearing temperature is elevated +0.35°C versus fleet average over the past 7 days, while power curve and pitch pressure remain normal. | Schedule immediate main bearing inspection and vibration analysis ; Prepare main bearing replacement parts and specialized crew ; Execute planned bearing swap within 7 days to avoid unplanned failure | 7 | Planned intervention avoids EUR 166,517 in additional costs versus waiting for unplanned failure (EUR 310,000 corrective vs EUR 175,000 planned plus lost revenue). | null |
| F01-T06 | MEDIUM | 0.2516 | F01-T06 Generator Bearing Elevated Temperature, 25% Failure Risk | Generator bearing temperature is +0.26°C above fleet average over 7 days, with gearbox bearing and oil temperatures also elevated (+0.30°C and +0.19°C respectively). Model predicts 25.2% failure probability within 14 days, identifying generator bearing as most likely failure component. | Schedule borescope inspection of generator bearing within 5 days ; Arrange planned generator bearing replacement with Hansa Drives gearbox compatibility check ; Monitor bearing temperature daily until intervention | 7 | Planned intervention avoids EUR 67,006 in additional costs versus unplanned failure (EUR 92,000 corrective vs EUR 38,000 planned, plus EUR 1,445 daily revenue loss). | null |
| F03-T14 | MEDIUM | 0.1439 | F03-T14 Pitch Hydraulic Pressure Drop Indicates Medium Failure Risk | Pitch hydraulic pressure has decreased by 0.12 bar relative to fleet average over the past 7 days, while power curve and gearbox vibration remain normal. The 14-day failure probability model flags pitch hydraulics as the most likely failure component at 14.4% risk. | Schedule pitch hydraulic system inspection within 10 days ; Prepare pitch hydraulic pump and accumulator replacement parts ; Plan controlled turbine shutdown for preventive intervention | 10 | Planned intervention avoids EUR 19,075 in additional costs compared to unplanned failure (EUR 26,000 corrective vs EUR 9,000 planned repair). | null |
| F02-T07 | MEDIUM | 0.1032 | F02-T07 Pitch Hydraulics Degradation Detected, 10% Failure Risk | Pitch hydraulic pressure has dropped 0.17 bar below fleet average over the past 7 days, indicating potential accumulator or seal degradation in the pitch system. Despite recent verification of accumulator pre-charge in August, the pressure deviation suggests progressive deterioration requiring intervention. | Schedule borescope inspection of pitch hydraulic cylinders and seals ; Verify accumulator pre-charge pressure and nitrogen loss rate on all axes ; Prepare pitch hydraulic component replacement if leak confirmed | 10 | Planned intervention avoids EUR 23,610 in additional costs compared to unplanned failure (EUR 26,000 corrective vs EUR 9,000 planned repair). | null |

### Cell 16
```python
n_err = spark.sql(f"SELECT count(*) FROM {FQ}.turbine_ai_briefs WHERE headline IS NULL").first()[0]
summary = spark.sql(f"""SELECT count(*) AS turbines_scored, sum(CASE WHEN risk_tier IN ('HIGH','CRITICAL') THEN 1 ELSE 0 END) AS high_or_critical,
                        round(sum(expected_avoidable_cost_eur)) AS fleet_expected_avoidable_eur FROM {FQ}.turbine_risk_scores""").first().asDict()
print(summary, "| briefs without headline:", n_err)
assert n_err == 0, "Some briefs failed to generate"
```
**Output:**
```text
{'turbines_scored': 120, 'high_or_critical': 4, 'fleet_expected_avoidable_eur': 849349.0} | briefs without headline: 0
```

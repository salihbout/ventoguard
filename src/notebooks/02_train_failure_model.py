# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Train the 14-day drivetrain failure-risk model
# MAGIC
# MAGIC **Question the model answers:** *"Which turbines will suffer a major component failure in the next 14 days?"*
# MAGIC A 14-day horizon is long enough to book a crane, pull a spare gearbox from the pool and schedule
# MAGIC the swap in a low-wind window. That turns a €350 k+ unplanned event into a planned one.
# MAGIC
# MAGIC * **Features**: daily health signals from `gold_turbine_daily`, expressed as residuals against the fleet
# MAGIC   (same model, same day). This removes ambient-temperature and wind-regime effects. 7-day means and 7-day trends are added on top.
# MAGIC * **Label**: a confirmed failure (`silver_failure_events`) within the following 14 days.
# MAGIC * **Validation**: a strict time split. Train on April to July, test on August onwards. Results are reported at
# MAGIC   the business level (how many failures were caught, with how many days' warning) as well as AUC.
# MAGIC * **Registry**: Unity Catalog model `turbine_failure_risk` with the `@champion` alias.

# COMMAND ----------

# MAGIC %pip install -q scikit-learn==1.5.2 "mlflow>=3.1"
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("schema", "wind_reliability")
CATALOG, SCHEMA = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
FQ = f"{CATALOG}.{SCHEMA}"
MODEL_NAME = f"{FQ}.turbine_failure_risk"
HORIZON_DAYS = 14
TEST_START = "2026-08-01"
spark.sql(f"USE CATALOG {CATALOG}"); spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

# MAGIC %md ## Feature engineering → UC feature table `turbine_health_features`

# COMMAND ----------

features_sql = f"""
WITH d AS (
  SELECT g.*, t.turbine_age_years, t.gearbox_supplier, t.rated_power_kw
  FROM {FQ}.gold_turbine_daily g JOIN {FQ}.silver_turbines t USING (turbine_id)
),
fleet AS (  -- fleet reference: same model, same day, healthy-running turbines only
  SELECT model, reading_date,
    percentile_approx(avg_gearbox_oil_temp_c, 0.5)        AS f_oil,
    percentile_approx(avg_gearbox_bearing_temp_c, 0.5)    AS f_gbb,
    percentile_approx(avg_main_bearing_temp_c, 0.5)       AS f_mb,
    percentile_approx(avg_generator_bearing_temp_c, 0.5)  AS f_gen,
    percentile_approx(p95_gearbox_vibration_mm_s, 0.5)    AS f_vib,
    percentile_approx(avg_hydraulic_pressure_bar, 0.5)    AS f_hyd,
    percentile_approx(power_curve_ratio, 0.5)             AS f_pcr,
    percentile_approx(avg_load_factor, 0.5)               AS f_load
  FROM d WHERE technical_availability > 0.9
  GROUP BY model, reading_date
),
r AS (
  SELECT d.turbine_id, d.farm_id, d.model, d.reading_date, d.turbine_age_years,
    CASE WHEN d.gearbox_supplier = 'Hansa Drives' THEN 1 ELSE 0 END AS supplier_hansa,
    d.technical_availability, d.avg_load_factor - f.f_load AS load_resid,
    d.avg_gearbox_oil_temp_c       - f.f_oil AS oil_temp_resid,
    d.avg_gearbox_bearing_temp_c   - f.f_gbb AS gbx_bearing_temp_resid,
    d.avg_main_bearing_temp_c      - f.f_mb  AS main_bearing_temp_resid,
    d.avg_generator_bearing_temp_c - f.f_gen AS gen_bearing_temp_resid,
    d.p95_gearbox_vibration_mm_s   - f.f_vib AS vibration_resid,
    d.avg_hydraulic_pressure_bar   - f.f_hyd AS hydraulic_resid,
    d.power_curve_ratio            - f.f_pcr AS power_curve_resid
  FROM d JOIN fleet f USING (model, reading_date)
),
w AS (
  SELECT *,
    {", ".join(f"avg({c}) OVER (PARTITION BY turbine_id ORDER BY reading_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS {c}_7d" for c in ["oil_temp_resid","gbx_bearing_temp_resid","main_bearing_temp_resid","gen_bearing_temp_resid","vibration_resid","hydraulic_resid","power_curve_resid"])},
    {", ".join(f"avg({c}) OVER (PARTITION BY turbine_id ORDER BY reading_date ROWS BETWEEN 13 PRECEDING AND 7 PRECEDING) AS {c}_prev7d" for c in ["oil_temp_resid","gbx_bearing_temp_resid","main_bearing_temp_resid","gen_bearing_temp_resid","vibration_resid","hydraulic_resid","power_curve_resid"])}
  FROM r
)
SELECT turbine_id, farm_id, model, reading_date, turbine_age_years, supplier_hansa, technical_availability, load_resid,
  oil_temp_resid, gbx_bearing_temp_resid, main_bearing_temp_resid, gen_bearing_temp_resid, vibration_resid, hydraulic_resid, power_curve_resid,
  oil_temp_resid_7d, gbx_bearing_temp_resid_7d, main_bearing_temp_resid_7d, gen_bearing_temp_resid_7d, vibration_resid_7d, hydraulic_resid_7d, power_curve_resid_7d,
  oil_temp_resid_7d - oil_temp_resid_prev7d AS oil_temp_trend,
  gbx_bearing_temp_resid_7d - gbx_bearing_temp_resid_prev7d AS gbx_bearing_temp_trend,
  main_bearing_temp_resid_7d - main_bearing_temp_resid_prev7d AS main_bearing_temp_trend,
  gen_bearing_temp_resid_7d - gen_bearing_temp_resid_prev7d AS gen_bearing_temp_trend,
  vibration_resid_7d - vibration_resid_prev7d AS vibration_trend,
  hydraulic_resid_7d - hydraulic_resid_prev7d AS hydraulic_trend
FROM w
"""
feat = spark.sql(features_sql).na.fill(0.0)
(feat.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.turbine_health_features"))
spark.sql(f"ALTER TABLE {FQ}.turbine_health_features ALTER COLUMN turbine_id SET NOT NULL")
spark.sql(f"ALTER TABLE {FQ}.turbine_health_features ALTER COLUMN reading_date SET NOT NULL")
try:
    spark.sql(f"ALTER TABLE {FQ}.turbine_health_features ADD CONSTRAINT turbine_health_features_pk PRIMARY KEY (turbine_id, reading_date TIMESERIES)")
except Exception as e:
    print("PK already present:", str(e)[:80])
spark.sql(f"COMMENT ON TABLE {FQ}.turbine_health_features IS 'Daily per-turbine health features: fleet-relative residuals, 7-day means and 7-day trends. Feature table for turbine_failure_risk.'")
print(spark.table(f"{FQ}.turbine_health_features").count(), "feature rows")

# COMMAND ----------

# MAGIC %md ## Labels: failure within the next 14 days

# COMMAND ----------

labeled = spark.sql(f"""
SELECT f.*,
  CASE WHEN EXISTS (SELECT 1 FROM {FQ}.silver_failure_events e
                    WHERE e.turbine_id = f.turbine_id
                      AND to_date(e.failure_ts) >  f.reading_date
                      AND to_date(e.failure_ts) <= date_add(f.reading_date, {HORIZON_DAYS})) THEN 1 ELSE 0 END AS label,
  (SELECT min(to_date(e.failure_ts)) FROM {FQ}.silver_failure_events e
    WHERE e.turbine_id = f.turbine_id AND to_date(e.failure_ts) > f.reading_date) AS next_failure_date
FROM {FQ}.turbine_health_features f
WHERE f.technical_availability > 0.5         -- exclude days the turbine is already down
  AND f.reading_date >= '2026-04-14'          -- need 14 days of history for trend features
  AND f.reading_date <= date_sub((SELECT max(reading_date) FROM {FQ}.turbine_health_features), {HORIZON_DAYS})  -- label must be observable
""")
pdf = labeled.toPandas()
FEATURES = [c for c in pdf.columns if c not in ("turbine_id", "farm_id", "model", "reading_date", "label", "next_failure_date", "technical_availability")]

# COMMAND ----------

import pandas as pd, numpy as np
pdf["reading_date"] = pd.to_datetime(pdf["reading_date"])
train = pdf[pdf.reading_date < TEST_START]
test = pdf[pdf.reading_date >= TEST_START]
print(f"train rows={len(train):,} positives={int(train.label.sum())} | test rows={len(test):,} positives={int(test.label.sum())}")
print("features:", FEATURES)

# COMMAND ----------

# MAGIC %md ## Train & track with MLflow → register in Unity Catalog

# COMMAND ----------

import mlflow
from mlflow.models import infer_signature
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score
from sklearn.inspection import permutation_importance

mlflow.set_registry_uri("databricks-uc")
user = spark.sql("SELECT current_user()").first()[0]
mlflow.set_experiment(f"/Users/{user}/ventoguard_turbine_failure_risk")

params = dict(max_iter=300, learning_rate=0.05, max_depth=4, l2_regularization=1.0, class_weight="balanced", random_state=7)
THRESHOLD = 0.5

with mlflow.start_run(run_name="hgb_14d_failure_risk") as run:
    model = HistGradientBoostingClassifier(**params).fit(train[FEATURES], train["label"])
    p_test = model.predict_proba(test[FEATURES])[:, 1]
    test = test.assign(prob=p_test)

    metrics = {
        "test_roc_auc": roc_auc_score(test.label, p_test),
        "test_pr_auc": average_precision_score(test.label, p_test),
        "test_precision_at_0_5": precision_score(test.label, p_test >= THRESHOLD),
        "test_recall_at_0_5": recall_score(test.label, p_test >= THRESHOLD),
        "base_rate": float(test.label.mean()),
    }

    # Business-level back-test: of the failures in the test window, how many were flagged in advance, and how early?
    fails = spark.sql(f"SELECT turbine_id, to_date(failure_ts) AS fdate, component FROM {FQ}.silver_failure_events WHERE failure_ts >= '{TEST_START}'").toPandas()
    fails["fdate"] = pd.to_datetime(fails["fdate"])
    rows = []
    for _, f in fails.iterrows():
        win = test[(test.turbine_id == f.turbine_id) & (test.reading_date < f.fdate) & (test.reading_date >= f.fdate - pd.Timedelta(days=HORIZON_DAYS))]
        flagged = win[win.prob >= THRESHOLD]
        lead = int((f.fdate - flagged.reading_date.min()).days) if len(flagged) else 0
        rows.append(dict(turbine_id=f.turbine_id, component=f.component, failure_date=f.fdate.date(), first_alert_lead_days=lead,
                         max_prob_before_failure=round(float(win.prob.max()), 3) if len(win) else None, caught=lead >= 3))
    backtest = pd.DataFrame(rows)
    metrics["test_failures"] = len(backtest)
    metrics["test_failures_caught_3d_ahead"] = int(backtest.caught.sum()) if len(backtest) else 0
    metrics["median_lead_days_caught"] = float(backtest[backtest.caught].first_alert_lead_days.median()) if backtest.caught.any() else 0.0
    # False alarms: distinct turbine-weeks flagged where no failure followed
    fa = test[(test.prob >= THRESHOLD) & (test.label == 0)]
    metrics["false_alarm_turbine_weeks"] = int(fa.assign(wk=fa.reading_date.dt.isocalendar().week).groupby(["turbine_id", "wk"]).ngroups)

    mlflow.log_params({**params, "horizon_days": HORIZON_DAYS, "test_start": TEST_START, "threshold": THRESHOLD, "n_features": len(FEATURES)})
    mlflow.log_metrics(metrics)

    imp = permutation_importance(model, test[FEATURES], test.label, scoring="average_precision", n_repeats=5, random_state=7)
    importance = pd.DataFrame({"feature": FEATURES, "importance": imp.importances_mean}).sort_values("importance", ascending=False)
    mlflow.log_table(importance, "feature_importance.json")
    mlflow.log_table(backtest.astype(str), "failure_backtest.json")

    signature = infer_signature(train[FEATURES].head(50), model.predict_proba(train[FEATURES].head(50)))
    info = mlflow.sklearn.log_model(model, name="model", signature=signature, input_example=train[FEATURES].head(3),
                                    registered_model_name=MODEL_NAME, pyfunc_predict_fn="predict_proba")
    run_id = run.info.run_id

for k, v in metrics.items():
    print(f"{k:35s} {v:.4f}" if isinstance(v, float) else f"{k:35s} {v}")

# COMMAND ----------

display(backtest)

# COMMAND ----------

display(importance.head(12))

# COMMAND ----------

# MAGIC %md ## Promote to `@champion` (quality gate: PR-AUC ≥ 0.30 and ≥ 60 % of test failures caught ≥ 3 days ahead)

# COMMAND ----------

from mlflow import MlflowClient
client = MlflowClient()
version = info.registered_model_version
caught_share = metrics["test_failures_caught_3d_ahead"] / max(metrics["test_failures"], 1)
gate = metrics["test_pr_auc"] >= 0.30 and caught_share >= 0.6
client.set_registered_model_alias(MODEL_NAME, "challenger", version)
if gate:
    client.set_registered_model_alias(MODEL_NAME, "champion", version)
client.update_model_version(MODEL_NAME, version, description=f"HistGradientBoosting, 14-day horizon. PR-AUC={metrics['test_pr_auc']:.3f}, caught {metrics['test_failures_caught_3d_ahead']}/{metrics['test_failures']} test failures >=3d ahead.")
client.set_model_version_tag(MODEL_NAME, version, "features", ",".join(FEATURES))
print(f"Registered {MODEL_NAME} v{version} (run {run_id}); quality gate passed = {gate}; champion -> v{client.get_model_version_by_alias(MODEL_NAME, 'champion').version}")
dbutils.jobs.taskValues.set("model_version", str(version))

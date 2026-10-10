# 806aac25-999f-45ef-90c4-8139b8d81224: executed notebook (task run 802053186807278)

> Exported from the Databricks job run with `databricks jobs export-run`; cell sources and their outputs exactly as executed on serverless compute.


# 00 · Generate raw landing data (synthetic)

**Customer problem:** a German onshore wind operator (120 turbines across 4 farms) loses €0.3–0.4 M
every time a gearbox or main bearing fails without warning. Most of that is crane mobilisation,
5–6 weeks of downtime and lost generation. This notebook simulates the raw data the operator's
systems would drop into the landing zone:

| Source system | File | Format | Cadence |
|---|---|---|---|
| SCADA historian | `scada/event_date=YYYY-MM-DD/*.json` | JSON lines | 10-minute telemetry |
| CMMS (maintenance) | `maintenance_logs/*.json` | JSON lines | free-text technician notes (DE/EN) |
| Asset register | `turbines/turbines.csv` | CSV | master data |
| CMMS failures | `failure_events/failure_events.csv` | CSV | confirmed component failures |
| EPEX day-ahead | `market_prices/prices.csv` | CSV | hourly €/MWh |

The failure physics: each failure has a 12–35 day degradation window. Over that window the
component temperatures, vibration and derating rise roughly quadratically. "Confuser" turbines get a
drift that a technician then fixes, which keeps the model honest. Failures scheduled **after** the
data end date stay in a hidden `_ground_truth` folder. They are used only to back-test what the
app flags today.

### Cell 2
```python
dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("schema", "wind_reliability")
dbutils.widgets.text("start_date", "2026-04-01")
dbutils.widgets.text("end_date", "2026-10-09")
dbutils.widgets.dropdown("reset", "false", ["true", "false"])

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
START = dbutils.widgets.get("start_date")
END = dbutils.widgets.get("end_date")
RESET = dbutils.widgets.get("reset") == "true"
ROOT = f"/Volumes/{CATALOG}/{SCHEMA}/raw_landing"
print(ROOT, START, END, "reset =", RESET)
```
**Output:**
```text
/Volumes/serverless_stable_7zqte5_catalog/wind_reliability/raw_landing 2026-04-01 2026-10-09 reset = False
```

### Cell 3
```python
import json, random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pyspark.sql import functions as F

def path_exists(p):
    try:
        dbutils.fs.ls(p)
        return True
    except Exception:
        return False

if RESET and path_exists(ROOT + "/scada"):
    for sub in ["scada", "maintenance_logs", "turbines", "failure_events", "market_prices", "_ground_truth"]:
        dbutils.fs.rm(f"{ROOT}/{sub}", recurse=True)
    print("Landing zone cleared")

ALREADY_GENERATED = path_exists(ROOT + "/scada")
print("Already generated:", ALREADY_GENERATED)
```
**Output:**
```text
Already generated: True
```

## Asset register: 4 farms, 120 turbines

### Cell 5
```python
rng = np.random.default_rng(42)
random.seed(42)

FARMS = [
    # farm_id, name, state, lat, lon, n_turbines, model, rated_kw, commissioning range, mean wind m/s, gearbox supplier
    ("F01", "Uckermark Nord", "Brandenburg", 53.21, 13.88, 36, "VG-3.6-136", 3600, (2016, 2019), 7.0, "Hansa Drives"),
    ("F02", "Ostfriesland Kueste", "Niedersachsen", 53.46, 7.41, 32, "VG-4.2-150", 4200, (2019, 2022), 8.1, "NordGear"),
    ("F03", "Hunsrueck Hoehe", "Rheinland-Pfalz", 49.95, 7.31, 28, "VG-2.3-108", 2300, (2011, 2014), 6.6, "Hansa Drives"),
    ("F04", "Eifel West", "Nordrhein-Westfalen", 50.41, 6.52, 24, "VG-3.6-136", 3600, (2015, 2018), 6.4, "NordGear"),
]

turbines = []
for farm_id, fname, state, lat, lon, n, model, rated, (y0, y1), wind, supplier in FARMS:
    for i in range(1, n + 1):
        turbines.append(dict(
            turbine_id=f"{farm_id}-T{i:02d}", farm_id=farm_id, farm_name=fname, federal_state=state,
            latitude=round(lat + rng.normal(0, 0.02), 5), longitude=round(lon + rng.normal(0, 0.03), 5),
            model=model, rated_power_kw=rated, commissioning_year=int(rng.integers(y0, y1 + 1)),
            hub_height_m=int({"VG-3.6-136": 132, "VG-4.2-150": 155, "VG-2.3-108": 98}[model]),
            gearbox_supplier=supplier, farm_mean_wind_ms=wind,
            wind_offset=float(rng.normal(0, 0.35)),
        ))
turb_pdf = pd.DataFrame(turbines)
print(len(turb_pdf), "turbines")
display(turb_pdf.groupby(["farm_id", "farm_name", "model"]).size().reset_index(name="turbines"))
```
**Output:**
```text
120 turbines
```
**Output:**

| farm_id | farm_name | model | turbines |
|---|---|---|---|
| F01 | Uckermark Nord | VG-3.6-136 | 36 |
| F02 | Ostfriesland Kueste | VG-4.2-150 | 32 |
| F03 | Hunsrueck Hoehe | VG-2.3-108 | 28 |
| F04 | Eifel West | VG-3.6-136 | 24 |

## Failure schedule (the hidden "physics")

### Cell 7
```python
COMPONENTS = {
    # component: (degradation days range, corrective downtime days, corrective cost €, crane needed)
    "gearbox":           ((18, 35), 38, 385_000, True),
    "main_bearing":      ((20, 35), 44, 310_000, True),
    "generator_bearing": ((12, 24), 11,  92_000, False),
    "pitch_hydraulics":  ((10, 18),  3,  26_000, False),
}
start_ts = datetime.fromisoformat(START)
end_ts = datetime.fromisoformat(END) + timedelta(hours=23, minutes=50)

# 22 historical failures + 6 that will happen in the 3 weeks after the data cut-off (hidden)
hist_mix = ["gearbox"] * 8 + ["main_bearing"] * 5 + ["generator_bearing"] * 5 + ["pitch_hydraulics"] * 4
future_mix = ["gearbox", "gearbox", "main_bearing", "generator_bearing", "gearbox", "pitch_hydraulics"]
# Older Hansa Drives gearboxes (F03) fail more often: realistic fleet-cohort signal for Genie / analysis
weights = np.array([2.6 if t["farm_id"] == "F03" else (1.3 if t["gearbox_supplier"] == "Hansa Drives" else 1.0) for t in turbines])
chosen = rng.choice(len(turbines), size=len(hist_mix) + len(future_mix), replace=False, p=weights / weights.sum())

failures = []
for k, comp in enumerate(hist_mix + future_mix):
    t = turbines[chosen[k]]
    (dmin, dmax), down_days, cost, crane = COMPONENTS[comp]
    if k < len(hist_mix):
        f_ts = start_ts + timedelta(days=float(rng.uniform(38, (end_ts - start_ts).days - 12)))
    else:
        f_ts = end_ts + timedelta(days=float(rng.uniform(3, 21)))
    deg_days = float(rng.uniform(dmin, dmax))
    failures.append(dict(
        failure_id=f"FE-{2026}{k+1:04d}", turbine_id=t["turbine_id"], component=comp,
        degradation_start_ts=(f_ts - timedelta(days=deg_days)).replace(microsecond=0),
        failure_ts=f_ts.replace(microsecond=0, second=0),
        downtime_hours=round(down_days * 24 * float(rng.uniform(0.8, 1.25)), 1),
        repair_cost_eur=round(cost * float(rng.uniform(0.85, 1.2)), -2),
        crane_required=crane, is_future=k >= len(hist_mix),
    ))
fail_pdf = pd.DataFrame(failures)

# Confusers: sensor/cooling drifts that a technician fixes (no failure follows)
conf_idx = rng.choice([i for i in range(len(turbines)) if i not in set(chosen)], size=10, replace=False)
confusers = []
for i in conf_idx:
    s = start_ts + timedelta(days=float(rng.uniform(10, (end_ts - start_ts).days - 5)))
    confusers.append(dict(turbine_id=turbines[i]["turbine_id"], drift_start_ts=s,
                          drift_end_ts=s + timedelta(days=float(rng.uniform(4, 9))),
                          drift_signal=random.choice(["gearbox_oil_temp_c", "generator_bearing_temp_c"])))
conf_pdf = pd.DataFrame(confusers)
display(fail_pdf.sort_values("failure_ts"))
```
**Output:**

| failure_id | turbine_id | component | degradation_start_ts | failure_ts | downtime_hours | repair_cost_eur | crane_required | is_future |
|---|---|---|---|---|---|---|---|---|
| FE-20260018 | F01-T24 | generator_bearing | 2026-04-26T00:05:37.000Z | 2026-05-10T12:18:00.000Z | 273.6 | 83500.0 | False | False |
| FE-20260014 | F03-T11 | generator_bearing | 2026-04-19T03:27:38.000Z | 2026-05-11T01:41:00.000Z | 313.0 | 90200.0 | False | False |
| FE-20260012 | F03-T18 | main_bearing | 2026-04-16T12:43:50.000Z | 2026-05-19T03:50:00.000Z | 871.2 | 293900.0 | True | False |
| FE-20260015 | F01-T08 | generator_bearing | 2026-05-11T10:47:02.000Z | 2026-05-30T15:49:00.000Z | 225.4 | 90000.0 | False | False |
| FE-20260019 | F01-T13 | pitch_hydraulics | 2026-05-15T16:51:30.000Z | 2026-06-01T09:25:00.000Z | 89.6 | 27200.0 | False | False |
| FE-20260003 | F01-T17 | gearbox | 2026-05-25T00:41:17.000Z | 2026-06-17T05:00:00.000Z | 905.2 | 409600.0 | True | False |
| FE-20260011 | F02-T01 | main_bearing | 2026-05-20T18:38:36.000Z | 2026-06-22T08:06:00.000Z | 1079.6 | 276100.0 | True | False |
| FE-20260013 | F04-T21 | main_bearing | 2026-06-02T12:25:05.000Z | 2026-06-25T02:41:00.000Z | 994.0 | 344100.0 | True | False |
| FE-20260009 | F03-T20 | main_bearing | 2026-06-01T03:52:41.000Z | 2026-06-28T20:27:00.000Z | 1194.9 | 359700.0 | True | False |
| FE-20260021 | F03-T01 | pitch_hydraulics | 2026-06-22T17:05:47.000Z | 2026-07-03T08:27:00.000Z | 82.1 | 26000.0 | False | False |
| FE-20260002 | F01-T28 | gearbox | 2026-06-08T21:47:29.000Z | 2026-07-04T23:15:00.000Z | 778.5 | 345300.0 | True | False |
| FE-20260022 | F03-T23 | pitch_hydraulics | 2026-07-02T23:16:23.000Z | 2026-07-14T04:12:00.000Z | 63.5 | 30400.0 | False | False |
| FE-20260006 | F03-T13 | gearbox | 2026-06-23T00:25:23.000Z | 2026-07-14T20:27:00.000Z | 964.5 | 403500.0 | True | False |
| FE-20260005 | F03-T21 | gearbox | 2026-07-07T13:28:32.000Z | 2026-07-30T22:49:00.000Z | 744.4 | 383600.0 | True | False |
| FE-20260004 | F03-T04 | gearbox | 2026-07-12T11:33:57.000Z | 2026-08-06T11:35:00.000Z | 897.4 | 356600.0 | True | False |
| FE-20260001 | F01-T06 | gearbox | 2026-07-05T13:14:32.000Z | 2026-08-08T13:00:00.000Z | 790.5 | 395800.0 | True | False |
| FE-20260017 | F04-T04 | generator_bearing | 2026-07-24T11:54:05.000Z | 2026-08-13T23:03:00.000Z | 257.3 | 98800.0 | False | False |
| FE-20260007 | F03-T28 | gearbox | 2026-07-17T23:12:44.000Z | 2026-08-15T23:34:00.000Z | 997.4 | 369900.0 | True | False |
| FE-20260008 | F01-T21 | gearbox | 2026-07-31T16:37:11.000Z | 2026-08-28T00:40:00.000Z | 906.7 | 411600.0 | True | False |
| FE-20260020 | F01-T25 | pitch_hydraulics | 2026-08-17T09:16:12.000Z | 2026-09-04T07:24:00.000Z | 62.2 | 26200.0 | False | False |
| FE-20260010 | F01-T27 | main_bearing | 2026-08-19T07:32:58.000Z | 2026-09-15T20:51:00.000Z | 1092.0 | 350300.0 | True | False |
| FE-20260016 | F03-T12 | generator_bearing | 2026-08-28T04:37:50.000Z | 2026-09-21T03:19:00.000Z | 302.9 | 88200.0 | False | False |
| FE-20260023 | F03-T09 | gearbox | 2026-09-21T20:07:04.000Z | 2026-10-13T19:07:00.000Z | 849.5 | 393300.0 | True | True |
| FE-20260027 | F03-T07 | gearbox | 2026-09-16T17:29:56.000Z | 2026-10-19T02:02:00.000Z | 927.6 | 430800.0 | True | True |
| FE-20260024 | F01-T20 | gearbox | 2026-09-27T03:54:55.000Z | 2026-10-23T13:10:00.000Z | 764.1 | 360100.0 | True | True |
| FE-20260026 | F02-T07 | generator_bearing | 2026-10-14T00:40:19.000Z | 2026-10-26T17:24:00.000Z | 254.8 | 95600.0 | False | True |
| FE-20260025 | F04-T16 | main_bearing | 2026-09-28T14:43:53.000Z | 2026-10-28T04:15:00.000Z | 1153.3 | 336200.0 | True | True |
| FE-20260028 | F03-T17 | pitch_hydraulics | 2026-10-14T06:59:02.000Z | 2026-10-28T07:54:00.000Z | 87.1 | 27400.0 | False | True |

## 10-minute SCADA telemetry (Spark-generated, ~3.3 M rows)

### Cell 9
```python
turb_sdf = spark.createDataFrame(turb_pdf)
fail_sdf = spark.createDataFrame(fail_pdf[["turbine_id", "component", "degradation_start_ts", "failure_ts", "downtime_hours"]])
conf_sdf = spark.createDataFrame(conf_pdf)

ts_sdf = spark.sql(f"""
  SELECT explode(sequence(to_timestamp('{START} 00:00:00'), to_timestamp('{END} 23:50:00'), interval 10 minutes)) AS ts
""")

TWO_PI = 2 * np.pi
base = (ts_sdf.crossJoin(turb_sdf.select("turbine_id", "farm_id", "rated_power_kw", "farm_mean_wind_ms", "wind_offset"))
        .join(fail_sdf, "turbine_id", "left")
        .join(conf_sdf, "turbine_id", "left"))

hours = F.unix_timestamp("ts") / 3600.0
farm_phase = F.conv(F.substring(F.md5("farm_id"), 1, 4), 16, 10).cast("double") / 65535.0 * TWO_PI
doy = F.dayofyear("ts")
hod = F.hour("ts") + F.minute("ts") / 60.0

def degr(col_component):
    # 0 → 1 (quadratic) across the degradation window of the given component
    frac = (F.unix_timestamp("ts") - F.unix_timestamp("degradation_start_ts")) / (F.unix_timestamp("failure_ts") - F.unix_timestamp("degradation_start_ts"))
    return F.when((F.col("component") == col_component) & (F.col("ts") >= F.col("degradation_start_ts")) & (F.col("ts") < F.col("failure_ts")),
                  F.pow(frac, 2)).otherwise(F.lit(0.0))

down = (F.col("ts") >= F.col("failure_ts")) & (F.col("ts") < F.col("failure_ts") + F.expr("make_interval(0,0,0,0, cast(downtime_hours as int), 0, 0)"))
drift = F.when((F.col("ts") >= F.col("drift_start_ts")) & (F.col("ts") < F.col("drift_end_ts")), F.lit(1.0)).otherwise(F.lit(0.0))

df = (base
  .withColumn("d_gb", degr("gearbox"))
  .withColumn("d_mb", degr("main_bearing"))
  .withColumn("d_gen", degr("generator_bearing"))
  .withColumn("d_pitch", degr("pitch_hydraulics"))
  .withColumn("is_down", F.coalesce(down, F.lit(False)))
  .withColumn("drift", drift)
  .withColumn("wind_speed_ms", F.greatest(F.lit(0.0),
        F.col("farm_mean_wind_ms") * (1 + 0.42 * F.sin(TWO_PI * hours / 127 + farm_phase) + 0.18 * F.sin(TWO_PI * hours / 41 + 2 * farm_phase))
        + 0.7 * F.sin(TWO_PI * (hod - 14) / 24) + F.col("wind_offset") + F.randn(7) * 1.1))
  .withColumn("ambient_temp_c", 14 + 7 * F.sin(TWO_PI * (doy - 105) / 365) + 4 * F.sin(TWO_PI * (hod - 9) / 24) + F.randn(11) * 0.9)
  .withColumn("planned_maint", (F.rand(13) < 0.002))
)

v = F.col("wind_speed_ms")
curve = F.when((v < 3) | (v > 25), 0.0).when(v >= 12.5, 1.0).otherwise((F.pow(v, 3) - 27) / (F.pow(F.lit(12.5), 3) - 27))
derate = 1 - 0.14 * F.col("d_gb") - 0.10 * F.col("d_mb") - 0.06 * F.col("d_gen") - 0.08 * F.col("d_pitch")
df = (df
  .withColumn("status_code", F.when(F.col("is_down"), "FAULT").when(F.col("planned_maint"), "MAINT")
                              .when(v < 3, "LOW_WIND").when(v > 25, "STORM_STOP").otherwise("RUN"))
  .withColumn("load", F.when(F.col("status_code") == "RUN", curve * derate * (1 + F.randn(17) * 0.025)).otherwise(0.0))
  .withColumn("load", F.least(F.greatest(F.col("load"), F.lit(0.0)), F.lit(1.0)))
  .withColumn("power_kw", F.round(F.col("load") * F.col("rated_power_kw"), 1))
  .withColumn("rotor_rpm", F.round(F.when(F.col("status_code") == "RUN", 6 + 8.5 * F.least(F.lit(1.0), (v - 3) / 9)).otherwise(F.abs(F.randn(19)) * 0.3), 2))
  .withColumn("idle", F.col("status_code") != "RUN")
  .withColumn("gearbox_oil_temp_c", F.round(F.when(F.col("idle"), F.col("ambient_temp_c") + 9 + F.randn(23)) .otherwise(
        38 + 0.55 * F.col("ambient_temp_c") + 18 * F.col("load") + F.randn(23) * 1.2 + 14 * F.col("d_gb")
        + 7 * F.col("drift") * F.coalesce((F.col("drift_signal") == "gearbox_oil_temp_c").cast("double"), F.lit(0.0))), 2))
  .withColumn("gearbox_bearing_temp_c", F.round(F.when(F.col("idle"), F.col("ambient_temp_c") + 11 + F.randn(29)).otherwise(
        42 + 0.5 * F.col("ambient_temp_c") + 22 * F.col("load") + F.randn(29) * 1.5 + 18 * F.col("d_gb") + 3 * F.col("d_mb")), 2))
  .withColumn("main_bearing_temp_c", F.round(F.when(F.col("idle"), F.col("ambient_temp_c") + 4 + F.randn(31) * 0.6).otherwise(
        25 + 0.7 * F.col("ambient_temp_c") + 8 * F.col("load") + F.randn(31) * 1.0 + 16 * F.col("d_mb")), 2))
  .withColumn("generator_bearing_temp_c", F.round(F.when(F.col("idle"), F.col("ambient_temp_c") + 8 + F.randn(37)).otherwise(
        35 + 0.6 * F.col("ambient_temp_c") + 20 * F.col("load") + F.randn(37) * 1.5 + 20 * F.col("d_gen")
        + 8 * F.col("drift") * F.coalesce((F.col("drift_signal") == "generator_bearing_temp_c").cast("double"), F.lit(0.0))), 2))
  .withColumn("gearbox_vibration_mm_s", F.round(F.when(F.col("idle"), F.abs(F.randn(41)) * 0.15).otherwise(
        1.2 + 1.8 * F.col("load") + F.abs(F.randn(41)) * 0.3 + 4.5 * F.col("d_gb") + 2.4 * F.col("d_mb")), 3))
  .withColumn("hydraulic_pressure_bar", F.round(180 - 38 * F.col("d_pitch") + F.randn(43) * 3, 1))
  .withColumn("pitch_angle_deg", F.round(F.when(v < 12.5, 0.5 + F.abs(F.randn(47)) * 0.4).otherwise(4 + (v - 12.5) * 1.6) + 2.5 * F.col("d_pitch"), 2))
  .withColumn("nacelle_temp_c", F.round(F.col("ambient_temp_c") + 6 + 5 * F.col("load") + F.randn(53) * 0.8, 2))
  .withColumn("wind_dir_deg", F.round((240 + 60 * F.sin(TWO_PI * hours / 97 + farm_phase) + F.randn(59) * 12) % 360, 1))
  .withColumn("wind_speed_ms", F.round("wind_speed_ms", 2))
  .withColumn("ambient_temp_c", F.round("ambient_temp_c", 2))
)

# Realistic data-quality defects for the silver-layer expectations to catch
df = (df
  .withColumn("_r", F.rand(61))
  .withColumn("power_kw", F.when(F.col("_r") < 0.0015, F.lit(None)).otherwise(F.col("power_kw")))
  .withColumn("gearbox_oil_temp_c", F.when((F.col("_r") >= 0.0015) & (F.col("_r") < 0.0020), F.lit(999.0)).otherwise(F.col("gearbox_oil_temp_c")))
  .withColumn("wind_speed_ms", F.when((F.col("_r") >= 0.0020) & (F.col("_r") < 0.0023), F.lit(-1.0)).otherwise(F.col("wind_speed_ms")))
)

scada = df.select(
    "turbine_id", F.date_format("ts", "yyyy-MM-dd'T'HH:mm:ss'Z'").alias("timestamp"),
    "status_code", "wind_speed_ms", "wind_dir_deg", "ambient_temp_c", "rotor_rpm", "power_kw", "pitch_angle_deg",
    "nacelle_temp_c", "gearbox_oil_temp_c", "gearbox_bearing_temp_c", "main_bearing_temp_c",
    "generator_bearing_temp_c", "gearbox_vibration_mm_s", "hydraulic_pressure_bar",
    F.to_date("ts").alias("event_date"))

if not ALREADY_GENERATED:
    scada.repartition("event_date").write.mode("overwrite").partitionBy("event_date").json(f"{ROOT}/scada")
    print("SCADA written")
else:
    print("SCADA already present: skipping (use reset=true to regenerate)")
```
**Output:**
```text
SCADA already present: skipping (use reset=true to regenerate)
```

## Maintenance logs (free-text, mixed German / English), the input for GenAI extraction

### Cell 11
```python
TECHS = ["J. Becker", "M. Schulz", "A. Wagner", "L. Hoffmann", "K. Fischer", "S. Krause", "T. Neumann", "P. Lehmann"]
ROUTINE = [
    "Routine 6-month inspection completed. Bolt torque checked, no findings. Oil level OK.",
    "Halbjahreswartung durchgeführt. Keine Auffälligkeiten, Ölstand in Ordnung, Filter gewechselt.",
    "Visual blade inspection from ground, minor leading edge erosion on blade B, monitor at next service.",
    "Converter cabinet cleaned, cooling fans tested OK. Yaw brake pads within tolerance.",
    "Sicherheitsprüfung Aufzug und Steigschutz erfolgreich. Keine Mängel.",
    "Oil sample taken from gearbox for lab analysis, results within limits (Fe 18 ppm).",
    "Pitch accumulator pre-charge pressure checked, all three axes within spec.",
]
PRE_FAILURE = {
    "gearbox": [
        "Customer remote alarm: gearbox oil temperature high warnings during full load. On site noticed faint metallic whine from intermediate stage. Oil sample sent to lab.",
        "Ölprobe Getriebe: erhöhter Eisengehalt (Fe 74 ppm) und Partikel auf Magnetstopfen. Leichte Geräusche bei Volllast. Empfehle Endoskopie.",
        "Endoscopy of HSS stage shows micropitting on pinion teeth. Vibration trending up on CMS. Recommend planning gearbox exchange, crane availability to be checked.",
    ],
    "main_bearing": [
        "Main bearing temperature trending ~8°C above fleet at similar load. Grease purge shows dark discoloration and fine metal particles.",
        "Hauptlager: Temperatur deutlich erhöht, Fettaustritt am Dichtring. Schwingungen niederfrequent auffällig.",
    ],
    "generator_bearing": [
        "Generator DE bearing temperature alarms (warning level) at high load. Slight noise audible near generator. Greasing performed, observe.",
        "Generatorlager NDE: Temperaturspitzen bis 92°C, Nachschmierung durchgeführt. Weiter beobachten.",
    ],
    "pitch_hydraulics": [
        "Pitch hydraulic pressure drops during gusts, small oil leak at axis 2 cylinder. Topped up hydraulic oil.",
        "Hydraulikdruck Pitch schwankend, Leckage an Achse 3 festgestellt. Dichtungen bestellt.",
    ],
}
CORRECTIVE = {
    "gearbox": "Gearbox failure confirmed (HSS bearing seizure). Turbine stopped. Crane mobilisation requested, exchange gearbox ordered. Expected downtime 5-6 weeks.",
    "main_bearing": "Hauptlagerschaden bestätigt. Anlage außer Betrieb, Kran und Rotordemontage erforderlich.",
    "generator_bearing": "Generator bearing replaced up-tower, alignment checked, turbine back in service.",
    "pitch_hydraulics": "Pitch cylinder seals replaced on axis, hydraulic system flushed, test run OK.",
}
CONFUSER = [
    "Gearbox oil cooler radiator heavily clogged with insects/pollen, cleaned. Oil temperature back to normal after cleaning.",
    "Temperatursensor Generatorlager defekt (Wackelkontakt), Sensor getauscht. Werte wieder plausibel.",
]

logs = []
n = 0
def add_log(tid, ts, cat, text):
    global n
    n += 1
    logs.append(dict(log_id=f"WO-{n:05d}", turbine_id=tid, created_ts=ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                     category=cat, technician_name=random.choice(TECHS), note_text=text))

for t in turbines:
    d = start_ts + timedelta(days=float(rng.uniform(0, 40)))
    while d < end_ts:
        add_log(t["turbine_id"], d.replace(hour=int(rng.integers(7, 16))), "routine", random.choice(ROUTINE))
        d += timedelta(days=float(rng.uniform(35, 70)))
for f in failures:
    deg_start, f_ts = f["degradation_start_ts"], f["failure_ts"]
    notes = PRE_FAILURE[f["component"]]
    for j in range(int(rng.integers(1, len(notes) + 1))):
        if rng.random() < 0.8:
            ts = deg_start + (f_ts - deg_start) * float(rng.uniform(0.45, 0.95))
            if ts < end_ts:
                add_log(f["turbine_id"], ts, "inspection", notes[j])
    if not f["is_future"]:
        add_log(f["turbine_id"], f_ts + timedelta(hours=3), "corrective", CORRECTIVE[f["component"]])
for c in confusers:
    add_log(c["turbine_id"], c["drift_end_ts"], "corrective",
            CONFUSER[0] if c["drift_signal"] == "gearbox_oil_temp_c" else CONFUSER[1])
logs_pdf = pd.DataFrame(logs).sort_values("created_ts")
print(len(logs_pdf), "maintenance log entries")
```
**Output:**
```text
519 maintenance log entries
```

## Day-ahead market prices (hourly €/MWh)

### Cell 13
```python
hrs = pd.date_range(START, pd.Timestamp(END) + pd.Timedelta(hours=23), freq="h")
h = hrs.hour.values
price = 88 + 22 * np.sin(2 * np.pi * (h - 13) / 24 + np.pi) + 18 * np.sin(2 * np.pi * (h - 7) / 12) - 30 * np.sin(2 * np.pi * np.arange(len(hrs)) / 127) + rng.normal(0, 14, len(hrs))
price_pdf = pd.DataFrame({"hour_start_utc": hrs.strftime("%Y-%m-%dT%H:%M:%SZ"), "bidding_zone": "DE-LU",
                          "price_eur_mwh": np.round(np.maximum(price, -15), 2)})
```

### Cell 14
```python
import os

def write_single(pdf, path, fmt="csv"):
    # Volumes are FUSE-mounted on serverless, so pandas can write straight into the landing zone
    os.makedirs(path.rsplit("/", 1)[0], exist_ok=True)
    if fmt == "csv":
        pdf.to_csv(path, index=False)
    else:
        pdf.to_json(path, orient="records", lines=True, date_format="iso", force_ascii=False)

if not ALREADY_GENERATED:
    write_single(turb_pdf.drop(columns=["wind_offset", "farm_mean_wind_ms"]), f"{ROOT}/turbines/turbines.csv")
    hist = fail_pdf[~fail_pdf.is_future].drop(columns=["degradation_start_ts", "is_future"]).copy()
    hist["failure_ts"] = hist["failure_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    write_single(hist, f"{ROOT}/failure_events/failure_events.csv")
    write_single(logs_pdf, f"{ROOT}/maintenance_logs/maintenance_logs_{END}.json", fmt="json")
    write_single(price_pdf, f"{ROOT}/market_prices/prices.csv")
    gt = fail_pdf[fail_pdf.is_future].copy()
    write_single(gt, f"{ROOT}/_ground_truth/future_failures.csv")
    write_single(conf_pdf, f"{ROOT}/_ground_truth/confusers.csv")
```

## Landing-zone inventory (execution evidence)

### Cell 16
```python
inventory = []
for sub in ["turbines", "failure_events", "maintenance_logs", "market_prices", "_ground_truth"]:
    for f in dbutils.fs.ls(f"{ROOT}/{sub}"):
        inventory.append((sub, f.name, f.size))
n_scada_days = len([f for f in dbutils.fs.ls(f"{ROOT}/scada") if f.name.startswith("event_date=")])
inventory.append(("scada", f"{n_scada_days} daily partitions", None))
display(spark.createDataFrame(inventory, "folder string, file string, bytes long"))
print("SCADA rows in landing zone:", spark.read.json(f"{ROOT}/scada").count())
```
**Output:**

| folder | file | bytes |
|---|---|---|
| turbines | turbines.csv | 11621 |
| failure_events | failure_events.csv | 1717 |
| maintenance_logs | maintenance_logs_2026-10-09.json | 122945 |
| market_prices | prices.csv | 153297 |
| _ground_truth | confusers.csv | 874 |
| _ground_truth | future_failures.csv | 702 |
| scada | 192 daily partitions | null |
**Output:**
```text
SCADA rows in landing zone: 3317760
```

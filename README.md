# VentoGuard: predictive drivetrain reliability for onshore wind

**Industry:** Energy & Utilities, renewable generation (onshore wind O&M)
**Customer problem:** A German onshore wind operator runs 120 turbines across 4 farms. It loses **€11 M a year** to *unplanned*
gearbox, main-bearing, generator-bearing and pitch failures. Each surprise gearbox costs about **€430 k** (repair, crane mobilisation
and lost revenue) and keeps the turbine down for **5+ weeks**, while the degradation was visible in SCADA and in technicians'
German free-text notes 2 to 5 weeks earlier. VentoGuard predicts failures **14 days ahead**, explains them, writes a
dispatcher-ready brief and turns each alert into a planned work order.

| Business KPI | Today | With VentoGuard | Evidence |
|---|---|---|---|
| Unplanned failure cost / year | €11.3 M | **−€4.2 M net** (75 % catch rate, false alarms deducted) | [`evidence/queries/value_case.sql`](evidence/queries/value_case.sql) → [result](evidence/queries/value_case.result.json) |
| Technical availability | 97.6 % (Hunsrück 95.0 %) | **+1.5 pp** (664 turbine-days/yr recovered) | same |
| Early warning | days (threshold alarms) | **median 13 days** | [`evidence/notebook_runs/02_train_failure_model.md`](evidence/notebook_runs/02_train_failure_model.md) |
| Hold-out failures caught ≥ 3 days ahead | n/a | **8 / 8** | same |
| Upcoming (hidden) failures flagged today | n/a | **4 / 4** of those already degrading | [`evidence/notebook_runs/03_score_and_genai.md`](evidence/notebook_runs/03_score_and_genai.md) |

> All data is **synthetic** (generated in `00_generate_raw_data.py`, seeded). No customer data is used. The degradation
> physics produce a strong signal, so model metrics will be lower on real fleet data. That is why the value case assumes a 75 % catch rate.

## How each part of the problem maps to Databricks

| Business need | Databricks capability | What it does here |
|---|---|---|
| Combine SCADA, CMMS notes, asset register and power prices that live in silos | **Lakeflow** declarative pipeline + Auto Loader, orchestrated by a **Lakeflow Job** (DAB) | Incremental ingest from a UC Volume; expectations drop sensor faults; gold tables compute lost MWh and € per turbine-day |
| Trust the numbers and protect technician data (GDPR) | **Unity Catalog** | One governed schema, account tag policies, `class.name` PII tag + column mask, lineage, grants, model registry |
| Know *which* turbine will fail, and when | **MLflow + UC Model Registry** | 14-day failure model on fleet-relative features, time-split back-test, `@champion` quality gate |
| Use what technicians already wrote (German/English) and tell the dispatcher what to do | **AI Functions (`ai_query`) + Claude** | Structured extraction from 519 notes; grounded maintenance briefs with action, crew, parts, € case |
| Millisecond reads and transactional work orders for an operational app | **Lakebase** (Autoscaling Postgres) | Synced tables for risk board, briefs and trends; app-owned `vg_ops.work_orders` |
| Let asset managers answer their own questions | **Genie space** | NL → SQL over governed gold/serving tables, with instructions, examples and benchmarks |
| Put it in front of the reliability team | **Databricks App** (React + FastAPI) | Risk map, AI brief, work orders and Genie chat in one workflow |

## Unity Catalog layout

Everything sits in the workspace's default ("main") catalog `serverless_stable_7zqte5_catalog`, with one schema per layer:

| Schema | Contents | Read by |
|---|---|---|
| `ventoguard_bronze` | Volume `raw_landing` (raw JSON/CSV) + 5 Auto Loader streaming tables `bronze_*` | data engineering |
| `ventoguard_silver` | 5 validated tables `silver_*` (Lakeflow expectations) | data engineering, data science |
| `ventoguard_gold` | `gold_turbine_daily`, `gold_farm_daily`, `gold_failure_history`, `turbine_health_features`, model `turbine_failure_risk`, `turbine_risk_scores` / `_history`, `maintenance_log_insights`, `turbine_ai_briefs`, mask function | analysts, Genie, the app |
| `ventoguard_serving` | Lakebase synced tables (UC side). Postgres schema of the same name | the app's service principal |

The bundle target is `demo` (`databricks bundle deploy -t demo --profile demo`). One pipeline publishes bronze to its default schema, and silver/gold to theirs via fully-qualified names.

## End-to-end journey (all stages integrated, governed in one catalog)

```
 Raw landing (UC Volume)           Lakeflow Spark Declarative Pipeline            ML + GenAI                         Serving
 ───────────────────────           ───────────────────────────────────            ──────────                         ───────
 scada/*.json  (3.3 M rows) ─┐     bronze_* (Auto Loader, STREAM read_files)       turbine_health_features           Lakebase Postgres (synced tables)
 maintenance_logs/*.json     ├──►  silver_* (expectations: drop 999°C, −1 m/s…) ──► turbine_failure_risk @champion ─► ventoguard_serving.turbine_risk_scores
 turbines.csv                │     gold_turbine_daily / gold_farm_daily /           turbine_risk_scores / history     ventoguard_serving.turbine_ai_briefs
 failure_events.csv          │     gold_failure_history (lost MWh & €)              ai_query → maintenance_log_       ventoguard_serving.gold_turbine_daily
 market_prices.csv          ─┘                                                       insights, turbine_ai_briefs      vg_ops.work_orders (app writes, OLTP)
                                   └────────────── Unity Catalog: tags · GDPR column mask · lineage · grants · model registry ──────────────┘
                                                                                                    Genie space ◄── Databricks App "ventoguard" ──► Lakebase
```

| Stage | What was built | Where |
|---|---|---|
| **Lakeflow** (ingest) | Serverless declarative pipeline `ventoguard-medallion`: 5 Auto Loader bronze streaming tables, 5 silver tables with data-quality expectations, 3 gold materialized views. Orchestrated by Lakeflow Job `ventoguard-end-to-end` (6 tasks, daily 05:00 CET schedule). | [`src/pipeline/`](src/pipeline), [`resources/`](resources), [`databricks.yml`](databricks.yml) |
| **Unity Catalog** (govern) | Layer schemas `ventoguard_bronze` / `_silver` / `_gold` / `_serving` in the default catalog; layer, certification and AI tags; `class.name` PII classification; `mask_person_name` column mask (GDPR) on technician names; tags follow the account's governed tag policies; grants for the app SP; lineage and expectation results read back from system tables / event log. | [`src/notebooks/04_uc_governance.py`](src/notebooks/04_uc_governance.py) |
| **Lakebase** (operational serving) | Lakebase Autoscaling project `ventoguard` (PG 17). 3 synced tables (UC `ventoguard_gold` → Postgres `ventoguard_serving`), refreshed by the job; app-owned transactional table `vg_ops.work_orders`. | [`src/notebooks/05_refresh_lakebase.py`](src/notebooks/05_refresh_lakebase.py), [`scripts/setup_serving.sh`](scripts/setup_serving.sh) |
| **ML** | Fleet-relative health features → `HistGradientBoostingClassifier` (14-day horizon, time-split back-test), tracked in MLflow, registered in UC as `turbine_failure_risk` with a quality gate on the `@champion` alias; batch scoring + € cost model. | [`02_train_failure_model.py`](src/notebooks/02_train_failure_model.py), [`03_score_and_genai.py`](src/notebooks/03_score_and_genai.py) |
| **GenAI** | `ai_query` (Claude Haiku) extracts component / severity / precursor / English summary from 519 German+English technician notes; `ai_query` (Claude Sonnet) writes grounded maintenance briefs for at-risk turbines. | [`03_score_and_genai.py`](src/notebooks/03_score_and_genai.py) |
| **Genie Agent** | Genie space *VentoGuard Reliability* (`01f1c4d953cb132e838ecd828813a354`) over 7 governed tables, with instructions, 6 example SQLs (all validated), join spec and 3 benchmarks; embedded in the app through the Conversation API. | [`genie/`](genie) |
| **Databricks App** | App `ventoguard`. **React** front end (Vite + TypeScript + Du Bois `@databricks/design-system`, Databricks brand tokens) and **FastAPI** back end. Four screens: *Fleet risk* (KPI strip, farm map, risk board), *Turbine* (AI brief, 45-day drivetrain trends, plan-the-repair form), *Work orders* (editable status, written to Lakebase), *Ask the fleet* (Genie chat that shows its SQL and result table). | [`app_ui/`](app_ui) (React source) → built into [`app/static`](app/static); [`app/backend/`](app/backend) (FastAPI) |

## Execution evidence (text, committed)

| File | What it shows |
|---|---|
| [`evidence/notebook_runs/`](evidence/notebook_runs) | Every job notebook **with its cell outputs**, exported from the actual job run (`scripts/export_run_evidence.py` decodes `jobs export-run`) |
| [`evidence/job_run.json`](evidence/job_run.json) | Final Lakeflow Job run (bundle target `demo`, layer-schema parameters): **all 6 tasks SUCCESS on the first attempt**, with durations |
| [`evidence/queries/pipeline_expectations.sql`](evidence/queries/pipeline_expectations.sql) → [result](evidence/queries/pipeline_expectations.result.txt) | Lakeflow expectation pass/fail counts from the pipeline event log (7,717 bad SCADA rows dropped) |
| [`evidence/queries/`](evidence/queries) | Verification SQL + results: table inventory, value case, failure costs, risk board, AI outputs |
| [`evidence/lakebase.txt`](evidence/lakebase.txt) | `psql` session against Lakebase: synced tables, risk board query, work orders written by the app |
| [`evidence/genie_conversations.md`](evidence/genie_conversations.md) | Real Genie Conversation API questions → generated SQL → results |
| [`evidence/app.md`](evidence/app.md) | Deployed app: status, resources, and real responses from every `/api/*` endpoint, including a work-order write and a Genie answer |

## Reproduce

```bash
databricks bundle deploy -t demo --profile demo                    # creates job + pipeline; schemas are created by the setup below / generator
databricks bundle run ventoguard_end_to_end -t demo --profile demo   # first run: the refresh_lakebase task needs step 2
./scripts/setup_serving.sh <profile> <warehouse_id>               # Lakebase synced tables, Genie space, React build, app deploy, grants
databricks bundle run ventoguard_end_to_end -t demo --profile demo   # full run incl. Lakebase refresh

# evidence
python scripts/export_run_evidence.py <profile> evidence/notebook_runs <name>=<task_run_id> ...
python scripts/genie_evidence.py <profile> <genie_space_id> evidence/genie_conversations.md
./scripts/app_evidence.sh <profile> evidence/app.md
python deck/extract_numbers.py && python deck/build_deck.py      # deck numbers come only from evidence/

# local app development
cd app_ui && npm install && npm run dev                          # http://localhost:5173, proxies /api to :8765
cd app && OPS_SCHEMA=vg_ops_dev PGUSER=<you> uvicorn backend.main:app --port 8765   # use a dev OPS schema locally; the app SP owns vg_ops
```

## Business deck

[`deck/VentoGuard_deck.pdf`](deck/VentoGuard_deck.pdf) · text version [`deck/VentoGuard_deck.md`](deck/VentoGuard_deck.md)

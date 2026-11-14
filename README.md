# VentoGuard: predictive drivetrain reliability for onshore wind

**Customer:** Aerion Windkraft AG (fictional) · **Industry:** Energy & Utilities, renewable generation (onshore wind O&M)
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

## For evaluators: where to look

| If you want… | Read |
|---|---|
| The business story (problem, € value, pilot ask) | [`deck/VentoGuard_deck.md`](deck/VentoGuard_deck.md) (text) or [`.pdf`](deck/VentoGuard_deck.pdf) |
| Proof that the stages are one integrated journey | [Follow one turbine through every stage](#follow-one-turbine-through-every-stage-f03-t07) |
| Proof that it ran | [Execution evidence](#execution-evidence-text-committed): notebook outputs, job run, SQL results, Lakebase `psql`, Genie answers, live app API responses |
| Why it is built this way | [Decisions and trade-offs](#decisions-and-trade-offs) |
| How AI was used to build it | [How AI was used to build VentoGuard](#how-ai-was-used-to-build-ventoguard) |
| How it will be presented | [`deck/ROLEPLAY_PLAYBOOK.md`](deck/ROLEPLAY_PLAYBOOK.md): tell-show-tell talk track, demo click path, Q&A for both stakeholders |


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
| **Lakebase** (operational serving) | Lakebase Autoscaling project `ventoguard` (PG 17). 4 synced tables (UC `ventoguard_gold` → Postgres `ventoguard_serving`, including `gold_failure_history` for the executive and asset views), refreshed by the job; app-owned transactional table `vg_ops.work_orders`. | [`src/notebooks/05_refresh_lakebase.py`](src/notebooks/05_refresh_lakebase.py), [`scripts/setup_serving.sh`](scripts/setup_serving.sh) |
| **ML** | Fleet-relative health features → `HistGradientBoostingClassifier` (14-day horizon, time-split back-test), tracked in MLflow, registered in UC as `turbine_failure_risk` with a quality gate on the `@champion` alias; batch scoring + € cost model. | [`02_train_failure_model.py`](src/notebooks/02_train_failure_model.py), [`03_score_and_genai.py`](src/notebooks/03_score_and_genai.py) |
| **GenAI** | `ai_query` (Claude Haiku) extracts component / severity / precursor / English summary from 519 German+English technician notes; `ai_query` (Claude Sonnet) writes grounded maintenance briefs for at-risk turbines. | [`03_score_and_genai.py`](src/notebooks/03_score_and_genai.py) |
| **Genie Agent** | Genie space *VentoGuard Reliability* (`01f1c4d953cb132e838ecd828813a354`) over 7 governed tables, with instructions, 6 example SQLs (all validated), join spec and 3 benchmarks; embedded in the app through the Conversation API. | [`genie/`](genie) |
| **Databricks App** | App `ventoguard`. **React** front end (Vite + TypeScript + Du Bois `@databricks/design-system`, Databricks brand tokens) and **FastAPI** back end. Role-based views (*View as* Executive / Asset management / Operations in the header). *Executive overview* for the COO (value of VentoGuard per year, unplanned-cost run rate, availability vs target, € at stake now, key insights computed from the data, decisions this week, farm scorecard). *Asset performance* for the Head of Asset Management (MTTR, crane share, planned vs unplanned, reliability by farm and component, gearbox supplier and age cohorts, maintenance calendar). *Fleet risk* for operations (KPI strip, interactive OpenStreetMap of every turbine with hover status and farm zoom, risk board), *Turbine* (AI brief, 45-day drivetrain trends, plan-the-repair form), *Work orders* (editable status, written to Lakebase), *Ask the fleet* (Genie chat that shows its SQL and result table). | [`app_ui/`](app_ui) (React source) → built into [`app/static`](app/static); [`app/backend/`](app/backend) (FastAPI) |

## Follow one turbine through every stage: F03-T07

One turbine at Hunsrück Höhe shows that the stages are a single data flow, not separate demos. Every row below is in the committed evidence.

| # | Stage | What happens to F03-T07 | Evidence |
|---|---|---|---|
| 1 | **Raw data** (synthetic) | The simulator plants a hidden gearbox failure: degradation starts on 2026-09-16 and failure is due on 2026-10-19 (`FE-20260027`). The ground truth is never exposed to the pipeline | [`00_generate_raw_data.md`](evidence/notebook_runs/00_generate_raw_data.md) |
| 2 | **Lakeflow** | 10-minute SCADA JSON and two technician notes arrive in the UC Volume. One note is in English (`WO-00508`, "metallic whine"), the other in German (`WO-00509`, *"Ölprobe Getriebe: erhöhter Eisengehalt (Fe 74 ppm)"*). Auto Loader picks them up into bronze, then silver with expectations, then gold `gold_turbine_daily` | [`pipeline_expectations.result.txt`](evidence/queries/pipeline_expectations.result.txt), [`table_inventory.result.json`](evidence/queries/table_inventory.result.json) |
| 3 | **GenAI** (extraction) | `ai_query` with Claude Haiku reads both notes and returns component `gearbox`, severity 4 and 3, `failure_precursor = true`, plus an English summary | [`ai_log_insights.result.json`](evidence/queries/ai_log_insights.result.json) |
| 4 | **ML** | The UC model `turbine_failure_risk@champion` scores **99.5 %** failure probability within 14 days (tier CRITICAL, component gearbox), **10 days before** the hidden failure | [`03_score_and_genai.md`](evidence/notebook_runs/03_score_and_genai.md) |
| 5 | **GenAI** (brief) | Claude Sonnet writes *"F03-T07 Gearbox Imminent Failure: 99.5% Probability Within 14 Days"*, citing +1.58 mm/s vibration, +6.09 °C bearing temperature and the oil-analysis note. Business case: **€206,523 avoided** with a planned repair | [`ai_briefs.result.json`](evidence/queries/ai_briefs.result.json) |
| 6 | **Unity Catalog** | Scores and briefs are governed gold tables tagged `ai_generated`. The technician's name on the notes is masked by `mask_person_name`, and lineage runs back to the raw file | [`04_uc_governance.md`](evidence/notebook_runs/04_uc_governance.md) |
| 7 | **Lakebase** | Synced into Postgres `ventoguard_serving.turbine_risk_scores`. A primary-key lookup takes **0.029 ms** | [`lakebase.txt`](evidence/lakebase.txt) |
| 8 | **Databricks App** | `/api/risk-board` puts F03-T07 at the top of the board, and the turbine page shows the brief and the trends | [`app.md`](evidence/app.md) |
| 9 | **Genie Agent** | Asked which turbines are at risk, Genie answers *"F03-T07 (Hunsrueck Hoehe), CRITICAL, 99.5 %, likely gearbox, avoidable cost €206,523"* and shows its SQL | [`genie_conversations.md`](evidence/genie_conversations.md), [`app.md`](evidence/app.md) |
| 10 | **Action** (Lakebase OLTP) | The dispatcher creates a P1 work order from the same screen. It is a transactional write to `vg_ops.work_orders`. The committed evidence shows this write for F01-T20, the next CRITICAL gearbox | [`app.md`](evidence/app.md), [`lakebase.txt`](evidence/lakebase.txt) |


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

## Decisions and trade-offs

| Decision | Why | What we gave up, and the mitigation |
|---|---|---|
| **Synthetic data** with physically motivated degradation, rather than a public SCADA set | Public wind SCADA sets don't link sensor data, technician notes, failure costs and power prices for the same turbines. A seeded simulator also lets us hide future failures and prove live detection (4/4) | Metrics are optimistic (ROC-AUC 0.999). The value case assumes only a 75 % catch rate, and the pilot replays 24 months of real history |
| **Fleet-relative features** (each turbine vs the fleet on the same day) rather than absolute thresholds | Removes weather, season and load, which are why threshold alarms fire late or falsely | A fleet-wide (common-mode) problem would be hidden. Absolute limits stay in the Lakeflow expectations, and the pilot adds CMS spectra |
| **Gradient-boosted trees on daily features** rather than deep learning on raw time series | 22 failures is a small-data problem. Trees train in seconds, are explainable (top-3 residuals per alert) and run on serverless | They may miss subtle spectral patterns. The pilot adds CMS vibration spectra as features |
| **Time-split validation** (train < Aug, test Aug–Sep) rather than a random split | A random split leaks future degradation into training and inflates the scores | Only 8 test failures. The quality gate requires ≥ 60 % caught ≥ 3 days ahead before `@champion` moves |
| **Daily batch scoring** (one Lakeflow Job, 05:00) rather than streaming | The 14-day horizon doesn't need minutes. Batch is cheaper and simpler to operate | No intraday alerts. The pipeline is already streaming tables, so continuous mode is a setting |
| **`ai_query` in SQL** (Haiku for 519 notes, Sonnet for the at-risk turbines' briefs) rather than an agent or a custom serving endpoint | Runs inside the governed job, covers every note, needs no extra infrastructure. The cheap model handles volume and the strong model handles reasoning | Briefs refresh daily, not on demand. They're grounded on the given facts only, tagged `ai_generated`, and a human approves every work order |
| **Lakebase synced tables** for the app rather than querying the SQL warehouse | Millisecond page loads and real transactional writes (work orders). No warehouse spin-up per page view | One more component, and freshness follows the snapshot sync (daily, matching the scoring) |
| **Work orders in Lakebase** rather than a direct SAP PM write | The prototype runs without the customer's SAP | SAP PM write-back is pilot weeks 1–2. SAP stays the system of record |
| **Curated Genie space** (instructions, 6 validated example SQLs, 3 benchmarks) rather than a custom text-to-SQL agent | Governed by UC permissions (including the column mask) and always shows its SQL. No code to maintain | Scope is limited to 7 tables, which is enough for asset-management questions |
| **React + FastAPI with Du Bois** rather than Streamlit | Product-grade UX for dispatchers, and a clean `/api` that is also the execution evidence | More build effort. The UI is pinned to older npm releases because of a proxy quarantine |
| **Layer schemas in the default catalog** rather than a dedicated catalog | The workspace grants no CREATE CATALOG | Isolation is per schema, with tags and grants per layer |


## How AI was used to build VentoGuard

**Tools.** VentoGuard was built with **Claude Code** (Anthropic Claude, in the terminal) working against the Databricks CLI and the workspace. It used Databricks skill packs for bundles, Lakeflow pipelines, Lakebase, Genie, Apps and the Du Bois design system.
A human made the decisions: the industry and the problem, the value assumptions, and what to keep or delete (for example, keeping the v1 deployment). The agent did most of the typing, running and verifying.

**Patterns that made the AI a teammate rather than a code generator:**
1. **The brief is the spec.** The submission brief went in verbatim. The agent mapped every stage requirement to a concrete Databricks asset (the stage table above) and later checked the repo against it.
2. **Run, read, fix.** Every notebook, pipeline and API was run on the workspace, and the agent read the real output before moving on. Failures became fixes and the lessons were written down (see *Gotchas* in [`STATUS.md`](STATUS.md)): `psycopg` aborts on serverless, so `pg8000` is used; tag values must follow governed tag policies; npm and pip are pinned behind a proxy.
3. **Evidence as a deliverable.** The agent wrote the exporters ([`scripts/export_run_evidence.py`](scripts/export_run_evidence.py), [`genie_evidence.py`](scripts/genie_evidence.py), [`app_evidence.sh`](scripts/app_evidence.sh)) so that every claim is backed by committed text output, not screenshots.
4. **No hand-typed numbers.** [`deck/extract_numbers.py`](deck/extract_numbers.py) derives every figure in the deck from the evidence files, and [`build_deck.py`](deck/build_deck.py) renders PDF, HTML and Markdown from them. If the data changes, the story changes with it.
5. **Guard-rails as files.** [`.databricks-impeccable.md`](.databricks-impeccable.md) locks the brand, voice and AI-trust rules for the UI: Genie always shows its SQL, and briefs show their grounding. [`STATUS.md`](STATUS.md) is a handoff file, so a new session can resume with "continue with the pending tasks".
6. **Rehearsal partner.** The same agent restructured the deck for tell-show-tell and wrote the role-play Q&A ([`deck/ROLEPLAY_PLAYBOOK.md`](deck/ROLEPLAY_PLAYBOOK.md)).

**AI inside the product** (prompts as committed in [`03_score_and_genai.py`](src/notebooks/03_score_and_genai.py)):
- *Extraction (Claude Haiku, 519 notes):* "You are a wind-turbine reliability engineer. Analyse this maintenance note (it may be German or English). Return ONLY a JSON object with keys: component (one of …), severity (integer 1-5, 5 = imminent failure), failure_precursor …, summary_en (max 20 words, English)."
- *Maintenance brief (Claude Sonnet):* "You are the reliability lead at a German onshore wind operator. Write a maintenance brief for the dispatcher. **Use ONLY the facts below; do not invent measurements.** Return ONLY JSON with keys: headline, diagnosis (cite the sensor evidence), recommended_action, urgency_days, crew_and_parts, business_case (quantifying EUR avoided vs. waiting for failure)." The facts passed in are the model score, sensor residuals against the fleet, the latest technician notes and the cost case.
- *Genie:* a curated space with instructions, validated example SQLs and benchmarks ([`genie/`](genie)).


## Unity Catalog layout

Everything sits in the workspace's default ("main") catalog `serverless_stable_7zqte5_catalog`, with one schema per layer:

| Schema | Contents | Read by |
|---|---|---|
| `ventoguard_bronze` | Volume `raw_landing` (raw JSON/CSV) + 5 Auto Loader streaming tables `bronze_*` | data engineering |
| `ventoguard_silver` | 5 validated tables `silver_*` (Lakeflow expectations) | data engineering, data science |
| `ventoguard_gold` | `gold_turbine_daily`, `gold_farm_daily`, `gold_failure_history`, `turbine_health_features`, model `turbine_failure_risk`, `turbine_risk_scores` / `_history`, `maintenance_log_insights`, `turbine_ai_briefs`, mask function | analysts, Genie, the app |
| `ventoguard_serving` | Lakebase synced tables (UC side). Postgres schema of the same name | the app's service principal |

The bundle target is `demo` (`databricks bundle deploy -t demo --profile demo`). One pipeline publishes bronze to its default schema, and silver/gold to theirs via fully-qualified names.

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

Prepared for **Aerion Windkraft AG**, a fictional customer. The presentation is [`deck/VentoGuard_deck.html`](deck/VentoGuard_deck.html): one slide per screen, ← → to navigate, F for full screen, with animated KPIs and charts. It has 14 slides: 11 for the main story (outcome → problem → tell/show/tell demo → proof → value per stakeholder → architecture → trust → pilot ask) and 3 backup slides for Q&A (cost/risk/time to value, integration, data quality/model/GenAI guard-rails). The `.md` version includes speaker notes.
The talk track, live-demo click path and Q&A answers for the AI role-play are in [`deck/ROLEPLAY_PLAYBOOK.md`](deck/ROLEPLAY_PLAYBOOK.md).

# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Refresh Lakebase serving tables
# MAGIC
# MAGIC The app reads from **Lakebase Postgres**, not from the warehouse. That gives single-digit-ms lookups for the
# MAGIC dispatcher screen and transactional writes for work orders. Three Unity Catalog tables are mirrored into
# MAGIC Lakebase as *synced tables* (managed Lakeflow pipelines). This task triggers a sync after every scoring run and
# MAGIC waits for it to finish.
# MAGIC
# MAGIC | UC source | Lakebase (Postgres) table | Used by app for |
# MAGIC |---|---|---|
# MAGIC | `turbine_risk_scores` | `vg_serving.turbine_risk_scores` | fleet risk board, map |
# MAGIC | `turbine_ai_briefs` | `vg_serving.turbine_ai_briefs` | AI maintenance brief |
# MAGIC | `gold_turbine_daily` | `vg_serving.gold_turbine_daily` | 30-day health trend charts |

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.81.0" "psycopg[binary]>=3.2"
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("serving_schema", "vg_serving")
dbutils.widgets.text("app_name", "ventoguard")
dbutils.widgets.text("lakebase_endpoint", "projects/ventoguard/branches/production/endpoints/primary")
LB_CATALOG = dbutils.widgets.get("catalog")
SERVING = dbutils.widgets.get("serving_schema")
SYNCED = ["turbine_risk_scores", "turbine_ai_briefs", "gold_turbine_daily"]

import time
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

pipelines = {}
for t in SYNCED:
    st = w.postgres.get_synced_table(name=f"synced_tables/{LB_CATALOG}.{SERVING}.{t}")
    pid = st.status.pipeline_id
    pipelines[t] = pid
    upd = w.pipelines.start_update(pipeline_id=pid)
    print(f"{t}: pipeline {pid} update {upd.update_id} started")

# COMMAND ----------

deadline = time.time() + 1800
pending = dict(pipelines)
while pending and time.time() < deadline:
    for t, pid in list(pending.items()):
        state = w.pipelines.get(pipeline_id=pid).latest_updates[0].state.value
        if state in ("COMPLETED", "FAILED", "CANCELED"):
            print(f"{t}: {state}")
            pending.pop(t)
    time.sleep(20)
assert not pending, f"Timed out waiting for {list(pending)}"

# COMMAND ----------

for t in SYNCED:
    st = w.postgres.get_synced_table(name=f"synced_tables/{LB_CATALOG}.{SERVING}.{t}")
    print(t, "->", st.status.detailed_state, "| last sync:", getattr(st.status, "last_sync", None))

# COMMAND ----------

# MAGIC %md Snapshot syncs can recreate the Postgres tables, so the app role's read grants are re-applied after every sync.

# COMMAND ----------

import psycopg
APP_SP = w.apps.get(dbutils.widgets.get("app_name")).service_principal_client_id
EP = dbutils.widgets.get("lakebase_endpoint")
host = w.postgres.get_endpoint(name=EP).status.hosts.host
token = w.postgres.generate_database_credential(endpoint=EP).token
me = w.current_user.me().user_name
with psycopg.connect(host=host, dbname="databricks_postgres", user=me, password=token, sslmode="require", autocommit=True) as conn:
    conn.execute(f'GRANT USAGE ON SCHEMA {SERVING} TO "{APP_SP}"')
    conn.execute(f'GRANT SELECT ON ALL TABLES IN SCHEMA {SERVING} TO "{APP_SP}"')
    for t in SYNCED:
        n = conn.execute(f"SELECT count(*) FROM {SERVING}.{t}").fetchone()[0]
        print(f"Lakebase {SERVING}.{t}: {n} rows")
    print(conn.execute(f"SELECT turbine_id, risk_tier, failure_prob_14d FROM {SERVING}.turbine_risk_scores ORDER BY failure_prob_14d DESC LIMIT 5").fetchall())

# 8a767973-1661-4605-9856-098f0eee3c78: executed notebook (task run 418382374912116)

> Exported from the Databricks job run with `databricks jobs export-run`; cell sources and their outputs exactly as executed on serverless compute.


# 05 · Refresh Lakebase serving tables

The app reads from **Lakebase Postgres**, not from the warehouse. That gives single-digit-ms lookups for the
dispatcher screen and transactional writes for work orders. Three Unity Catalog tables are mirrored into
Lakebase as *synced tables* (managed Lakeflow pipelines). This task triggers a sync after every scoring run and
waits for it to finish.

| UC source | Lakebase (Postgres) table | Used by app for |
|---|---|---|
| `turbine_risk_scores` | `ventoguard_serving.turbine_risk_scores` | fleet risk board, map |
| `turbine_ai_briefs` | `ventoguard_serving.turbine_ai_briefs` | AI maintenance brief |
| `gold_turbine_daily` | `ventoguard_serving.gold_turbine_daily` | 30-day health trend charts |

### Cell 2
```python
%pip install -q "databricks-sdk>=0.81.0" "pg8000>=1.31"
%restart_python
```
**Output:**
```text
[43mNote: you may need to restart the kernel using %restart_python or dbutils.library.restartPython() to use updated packages.[0m
```

### Cell 3
```python
dbutils.widgets.text("catalog", "serverless_stable_7zqte5_catalog")
dbutils.widgets.text("serving_schema", "ventoguard_serving")
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
```
**Output:**
```text
turbine_risk_scores: pipeline ad4d2067-fc8a-4c36-8048-df2a2e36cd14 update fa224ac7-a502-4de6-9c17-6d31dbe8ca68 started
turbine_ai_briefs: pipeline c92ad48a-fb1e-4c0e-8e83-1569bd79cbe2 update 5f61c296-5578-4c0f-ad7a-e6bfc61e374c started
gold_turbine_daily: pipeline bd6d3837-f7db-4a63-ba1d-6c9082b95fe4 update b4e45071-50fa-40ba-a093-e9bc57919ad8 started
```

### Cell 4
```python
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
```
**Output:**
```text
turbine_risk_scores: COMPLETED
turbine_ai_briefs: COMPLETED
gold_turbine_daily: COMPLETED
```

### Cell 5
```python
for t in SYNCED:
    st = w.postgres.get_synced_table(name=f"synced_tables/{LB_CATALOG}.{SERVING}.{t}")
    print(t, "->", st.status.detailed_state, "| last sync:", getattr(st.status, "last_sync", None))
```
**Output:**
```text
turbine_risk_scores -> SyncedTableState.SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE | last sync: SyncedTablePosition(delta_table_sync_info=DeltaTableSyncInfo(delta_commit_time=seconds: 1791659283
, delta_commit_version=8), sync_end_time=seconds: 1791659716
nanos: 733061000
, sync_start_time=seconds: 1791659707
nanos: 322854000
)
turbine_ai_briefs -> SyncedTableState.SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE | last sync: SyncedTablePosition(delta_table_sync_info=DeltaTableSyncInfo(delta_commit_time=seconds: 1791659668
, delta_commit_version=5), sync_end_time=seconds: 1791659719
nanos: 416499000
, sync_start_time=seconds: 1791659709
nanos: 58189000
)
gold_turbine_daily -> SyncedTableState.SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE | last sync: SyncedTablePosition(delta_table_sync_info=DeltaTableSyncInfo(delta_commit_time=, delta_commit_version=6), sync_end_time=seconds: 1791659718
nanos: 771669000
, sync_start_time=seconds: 1791659708
nanos: 294583000
)
```

Snapshot syncs can recreate the Postgres tables, so the app role's read grants are re-applied after every sync.
The pure-Python `pg8000` driver is used here: `psycopg[binary]`'s bundled libpq intermittently aborted the serverless Python process on import (SIGABRT).

### Cell 7
```python
import ssl
import pg8000.native
APP_SP = w.apps.get(dbutils.widgets.get("app_name")).service_principal_client_id
EP = dbutils.widgets.get("lakebase_endpoint")
host = w.postgres.get_endpoint(name=EP).status.hosts.host
token = w.postgres.generate_database_credential(endpoint=EP).token
me = w.current_user.me().user_name
conn = pg8000.native.Connection(user=me, host=host, database="databricks_postgres", port=5432, password=token,
                                ssl_context=ssl.create_default_context())
try:
    conn.run(f'GRANT USAGE ON SCHEMA {SERVING} TO "{APP_SP}"')
    conn.run(f'GRANT SELECT ON ALL TABLES IN SCHEMA {SERVING} TO "{APP_SP}"')
    for t in SYNCED:
        n = conn.run(f"SELECT count(*) FROM {SERVING}.{t}")[0][0]
        print(f"Lakebase {SERVING}.{t}: {n} rows")
    print(conn.run(f"SELECT turbine_id, risk_tier, failure_prob_14d FROM {SERVING}.turbine_risk_scores ORDER BY failure_prob_14d DESC LIMIT 5"))
finally:
    conn.close()
```
**Output:**
```text
Lakebase ventoguard_serving.turbine_risk_scores: 120 rows
Lakebase ventoguard_serving.turbine_ai_briefs: 7 rows
Lakebase ventoguard_serving.gold_turbine_daily: 23040 rows
[['F03-T07', 'CRITICAL', 0.9953], ['F03-T09', 'CRITICAL', 0.9912], ['F01-T20', 'CRITICAL', 0.9578], ['F04-T16', 'HIGH', 0.5529], ['F01-T06', 'MEDIUM', 0.2516]]
```

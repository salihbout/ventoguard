# e6906ef4-424d-45df-a9b8-77295f766e0b: executed notebook (task run 495394399834865)

> Exported from the Databricks job run with `databricks jobs export-run`; cell sources and their outputs exactly as executed on serverless compute.


# 05 · Refresh Lakebase serving tables

The app reads from **Lakebase Postgres**, not from the warehouse. That gives single-digit-ms lookups for the
dispatcher screen and transactional writes for work orders. Three Unity Catalog tables are mirrored into
Lakebase as *synced tables* (managed Lakeflow pipelines). This task triggers a sync after every scoring run and
waits for it to finish.

| UC source | Lakebase (Postgres) table | Used by app for |
|---|---|---|
| `turbine_risk_scores` | `vg_serving.turbine_risk_scores` | fleet risk board, map |
| `turbine_ai_briefs` | `vg_serving.turbine_ai_briefs` | AI maintenance brief |
| `gold_turbine_daily` | `vg_serving.gold_turbine_daily` | 30-day health trend charts |

### Cell 2
```python
%pip install -q "databricks-sdk>=0.81.0" "psycopg[binary]>=3.2"
%restart_python
```
**Output:**
```text
[43mNote: you may need to restart the kernel using %restart_python or dbutils.library.restartPython() to use updated packages.[0m
```

### Cell 3
```python
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
```
**Output:**
```text
turbine_risk_scores: pipeline 8c850d7c-ab02-4aac-853a-41dbe856e66e update 2b606027-4ded-4c36-bb0b-e6b191c3a519 started
turbine_ai_briefs: pipeline eb2d817b-5180-43d2-84f6-191e7776d72a update d7b95fcf-8b22-45ff-872f-ad2349f7d992 started
gold_turbine_daily: pipeline 38570c4e-29c9-4255-aa5b-b04c3a3c82b9 update 2734d1a5-5b0a-4fe0-b2ca-02a89ff7a3d0 started
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
turbine_risk_scores -> SyncedTableState.SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE | last sync: SyncedTablePosition(delta_table_sync_info=DeltaTableSyncInfo(delta_commit_time=seconds: 1791652404
, delta_commit_version=8), sync_end_time=seconds: 1791652891
nanos: 97515000
, sync_start_time=seconds: 1791652880
nanos: 283835000
)
turbine_ai_briefs -> SyncedTableState.SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE | last sync: SyncedTablePosition(delta_table_sync_info=DeltaTableSyncInfo(delta_commit_time=seconds: 1791652838
, delta_commit_version=5), sync_end_time=seconds: 1791652889
nanos: 524256000
, sync_start_time=seconds: 1791652879
nanos: 700759000
)
gold_turbine_daily -> SyncedTableState.SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE | last sync: SyncedTablePosition(delta_table_sync_info=DeltaTableSyncInfo(delta_commit_time=, delta_commit_version=6), sync_end_time=seconds: 1791652889
nanos: 39659000
, sync_start_time=seconds: 1791652878
nanos: 793773000
)
```

Snapshot syncs can recreate the Postgres tables, so the app role's read grants are re-applied after every sync.

### Cell 7
```python
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
```
**Output:**
```text
Lakebase vg_serving.turbine_risk_scores: 120 rows
Lakebase vg_serving.turbine_ai_briefs: 7 rows
Lakebase vg_serving.gold_turbine_daily: 23040 rows
[('F03-T07', 'CRITICAL', 0.9953), ('F03-T09', 'CRITICAL', 0.9912), ('F01-T20', 'CRITICAL', 0.9578), ('F04-T16', 'HIGH', 0.5529), ('F01-T06', 'MEDIUM', 0.2516)]
```

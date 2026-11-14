#!/usr/bin/env bash
# One-time setup of the serving layer: Lakebase project, synced tables, Genie space, Databricks App, grants.
# Run AFTER the first successful `databricks bundle run ventoguard_end_to_end` (the UC source tables must exist).
#
#   ./scripts/setup_serving.sh <profile> <warehouse_id>
set -euo pipefail
P=${1:?profile}; WH=${2:?warehouse_id}
C=serverless_stable_7zqte5_catalog; SERVING=ventoguard_serving
BRONZE=ventoguard_bronze; SILVER=ventoguard_silver; GOLD=ventoguard_gold
PROJECT=ventoguard; BRANCH=projects/$PROJECT/branches/production; EP=$BRANCH/endpoints/primary

# 1. Lakebase Autoscaling project (production branch + primary endpoint are auto-created)
databricks postgres get-project projects/$PROJECT --profile $P >/dev/null 2>&1 || \
  databricks postgres create-project $PROJECT --json '{"spec": {"display_name": "VentoGuard Wind Reliability", "pg_version": 17}}' --profile $P

# 2. Synced tables: UC Delta -> Lakebase Postgres (schema ventoguard_serving). Snapshot mode; refreshed by job task 05.
databricks experimental aitools tools query "CREATE SCHEMA IF NOT EXISTS $C.$SERVING" --profile $P
sync() {  # <table> <pk-json-array>
  databricks postgres get-synced-table synced_tables/$C.$SERVING.$1 --profile $P >/dev/null 2>&1 && return
  databricks postgres create-synced-table $C.$SERVING.$1 --no-wait --profile $P --json "{\"spec\": {
    \"source_table_full_name\": \"$C.$GOLD.$1\", \"primary_key_columns\": $2, \"scheduling_policy\": \"SNAPSHOT\",
    \"branch\": \"$BRANCH\", \"postgres_database\": \"databricks_postgres\", \"create_database_objects_if_missing\": true,
    \"new_pipeline_spec\": {\"storage_catalog\": \"$C\", \"storage_schema\": \"$SERVING\"}}}"
}
sync gold_turbine_daily '["turbine_id","reading_date"]'
sync turbine_risk_scores '["turbine_id"]'
sync turbine_ai_briefs '["turbine_id"]'
sync gold_failure_history '["failure_id"]'

# 3. Genie space
SPACE_ID=$(python3 genie/create_genie_space.py $P $WH | python3 -c 'import json,sys; print(json.load(sys.stdin)["space_id"])')
echo "Genie space: $SPACE_ID"

# 4. App with Lakebase + Genie resources
databricks apps get ventoguard --profile $P >/dev/null 2>&1 || databricks apps create ventoguard --profile $P
databricks apps create-update ventoguard --profile $P --json "{\"update_mask\": \"resources\", \"app\": {\"resources\": [
  {\"name\": \"postgres\", \"postgres\": {\"branch\": \"$BRANCH\", \"database\": \"$BRANCH/databases/databricks-postgres\", \"permission\": \"CAN_CONNECT_AND_CREATE\"}},
  {\"name\": \"genie-space\", \"genie_space\": {\"name\": \"VentoGuard Reliability\", \"space_id\": \"$SPACE_ID\", \"permission\": \"CAN_RUN\"}},
  {\"name\": \"sql-warehouse\", \"sql_warehouse\": {\"id\": \"$WH\", \"permission\": \"CAN_USE\"}}]}}"
SP=$(databricks apps get ventoguard --profile $P -o json | python3 -c 'import json,sys; print(json.load(sys.stdin)["service_principal_client_id"])')

# 5. Unity Catalog grants for the app service principal (Genie runs as the app)
# least privilege: the app (and Genie, which runs as the app) reads gold + the one silver dimension Genie needs, never bronze
for s in "GRANT USE CATALOG ON CATALOG $C TO \`$SP\`" \
         "GRANT USE SCHEMA, SELECT ON SCHEMA $C.$GOLD TO \`$SP\`" \
         "GRANT USE SCHEMA ON SCHEMA $C.$SILVER TO \`$SP\`" \
         "GRANT SELECT ON TABLE $C.$SILVER.silver_turbines TO \`$SP\`" \
         "GRANT USE SCHEMA, SELECT ON SCHEMA $C.$SERVING TO \`$SP\`"; do
  databricks experimental aitools tools query "$s" --profile $P
done

# 6. Build the React front end into app/static, then deploy the FastAPI app
(cd app_ui && npm install && npm run build)
USER_EMAIL=$(databricks current-user me --profile $P -o json | python3 -c 'import json,sys; print(json.load(sys.stdin)["userName"])')
databricks workspace import-dir app /Workspace/Users/$USER_EMAIL/ventoguard_app --overwrite --profile $P
databricks apps deploy ventoguard --source-code-path /Workspace/Users/$USER_EMAIL/ventoguard_app --profile $P

# 7. Postgres grants: the app role reads the synced tables (its own vg_ops schema is created and owned by the app)
HOST=$(databricks postgres get-endpoint $EP --profile $P -o json | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"]["hosts"]["host"])')
TOKEN=$(databricks postgres generate-database-credential $EP --profile $P -o json | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')
PGPASSWORD=$TOKEN psql "host=$HOST user=$USER_EMAIL dbname=databricks_postgres sslmode=require" -c "
  GRANT USAGE ON SCHEMA $SERVING TO \"$SP\";
  GRANT SELECT ON ALL TABLES IN SCHEMA $SERVING TO \"$SP\";
  ALTER DEFAULT PRIVILEGES IN SCHEMA $SERVING GRANT SELECT ON TABLES TO \"$SP\";"

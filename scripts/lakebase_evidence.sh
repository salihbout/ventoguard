#!/usr/bin/env bash
# psql session against the Lakebase project: synced tables, app-owned work orders, index lookup latency.
# Usage: ./scripts/lakebase_evidence.sh <profile> <out.txt>
set -euo pipefail
P=${1:?profile}; OUT=${2:?out.txt}
C=serverless_stable_7zqte5_catalog; SERVING=ventoguard_serving
EP=projects/ventoguard/branches/production/endpoints/primary
HOST=$(databricks postgres get-endpoint $EP --profile $P -o json | jq -r .status.hosts.host)
TOKEN=$(databricks postgres generate-database-credential $EP --profile $P -o json | jq -r .token)
ME=$(databricks current-user me --profile $P -o json | jq -r .userName)
{
  echo "# Lakebase (Autoscaling project 'ventoguard') psql session, $(date -u '+%Y-%m-%d %H:%M UTC')"
  echo "# endpoint: $EP"; echo
  databricks postgres get-project projects/ventoguard --profile $P -o json | jq -c '{name, pg_version: .status.pg_version, display_name: .status.display_name}'
  for t in gold_turbine_daily turbine_risk_scores turbine_ai_briefs; do
    databricks postgres get-synced-table synced_tables/$C.$SERVING.$t --profile $P -o json | jq -c '{synced_table: .name, state: .status.detailed_state}'
  done
  echo
  PGPASSWORD=$TOKEN psql "host=$HOST user=$ME dbname=databricks_postgres sslmode=require" -e <<SQL
SELECT n.nspname AS schema, c.relname AS table, pg_get_userbyid(c.relowner) AS owner, c.reltuples::bigint AS approx_rows
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname IN ('$SERVING', 'vg_ops') AND c.relkind IN ('r', 'p') ORDER BY 1, 2;
SELECT count(*) AS turbines, count(*) FILTER (WHERE risk_tier IN ('CRITICAL','HIGH')) AS at_risk FROM $SERVING.turbine_risk_scores;
SELECT turbine_id, farm_name, risk_tier, failure_prob_14d, likely_component, round(avoidable_cost_if_caught_eur) AS avoidable_eur
FROM $SERVING.turbine_risk_scores ORDER BY failure_prob_14d DESC LIMIT 6;
SELECT turbine_id, left(headline, 70) AS headline, urgency_days FROM $SERVING.turbine_ai_briefs ORDER BY failure_prob_14d DESC;
SELECT wo_id, turbine_id, component, priority, status, planned_date, crew, created_by, created_at FROM vg_ops.work_orders ORDER BY wo_id;
EXPLAIN ANALYZE SELECT * FROM $SERVING.turbine_risk_scores WHERE turbine_id = 'F03-T07';
SQL
} > "$OUT" 2>&1
echo "wrote $OUT"

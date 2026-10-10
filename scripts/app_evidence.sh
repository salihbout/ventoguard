#!/usr/bin/env bash
# Call the DEPLOYED VentoGuard app's API (FastAPI behind the Databricks Apps proxy) with a user OAuth token and
# record request -> response as Markdown. Usage: ./scripts/app_evidence.sh <profile> <out.md>
set -euo pipefail
P=${1:?profile}; OUT=${2:?out.md}
U=$(databricks apps get ventoguard --profile $P -o json | jq -r .url)
T=$(databricks auth token --profile $P -o json | jq -r .access_token)
call() {  # method path [json-body]
  local m=$1 p=$2 b=${3:-}
  { echo "### \`$m $p\`"; [ -n "$b" ] && echo "Request body: \`$b\`"; echo '```json'
    if [ -n "$b" ]; then curl -s -X $m -H "Authorization: Bearer $T" -H 'content-type: application/json' -d "$b" "$U$p"
    else curl -s -X $m -H "Authorization: Bearer $T" "$U$p"; fi | jq '.' | head -60
    echo '```'; echo; } >> "$OUT"
}
{ echo "# Deployed Databricks App: API execution evidence"; echo
  echo "App \`ventoguard\` at $U, captured $(date -u '+%Y-%m-%d %H:%M UTC')."
  echo "React front end (\`app_ui/\`, built into \`app/static\`) and FastAPI back end (\`app/backend\`). Every response below comes from the"
  echo "deployed app: reads from Lakebase synced tables (\`ventoguard_serving\`), writes to the app-owned OLTP schema (\`vg_ops\`), and Genie via the Conversation API."
  echo; echo '```json'; databricks apps get ventoguard --profile $P -o json | jq '{name, url, app_status, compute_status, active_deployment: {deployment_id: .active_deployment.deployment_id, status: .active_deployment.status, create_time: .active_deployment.create_time}, resources: [.resources[] | {name} + (del(.name))]}'; echo '```'; echo; } > "$OUT"
call GET /api/health
call GET /api/kpis
call GET "/api/risk-board?tier=CRITICAL&tier=HIGH"
call GET /api/farms
call GET /api/turbines/F01-T20
WO=$(curl -s -X POST -H "Authorization: Bearer $T" -H 'content-type: application/json' \
  -d '{"turbine_id":"F01-T20","priority":"P1","planned_date":"2026-10-12","crew":"North crew (Uckermark)","notes":"Planned gearbox swap; crane booked for low-wind window"}' "$U/api/work-orders")
{ echo '### `POST /api/work-orders` (transactional write to Lakebase `vg_ops.work_orders`)'; echo '```json'; echo "$WO" | jq '.'; echo '```'; echo; } >> "$OUT"
ID=$(echo "$WO" | jq -r .wo_id)
call PATCH /api/work-orders/$ID '{"status":"SCHEDULED"}'
call GET /api/work-orders
call POST /api/genie/ask '{"question":"Which turbines are currently at risk of failure and what is the avoidable cost?"}'
echo "wrote $OUT"

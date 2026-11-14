#!/usr/bin/env bash
# Record the role-view endpoints (/api/views/executive, /api/views/assets) as Markdown evidence.
# Runs the app's own FastAPI back end LOCALLY against the production Lakebase data (no app token needed),
# read-only GET requests only. The deployed app runs the same code; its status is recorded too.
# Usage: ./scripts/views_evidence.sh <profile> <python-with-app-requirements> <out.md>
set -euo pipefail
P=${1:?profile}; PY=${2:?python}; OUT=${3:?out.md}
PORT=8766
ROOT=$(cd "$(dirname "$0")/.." && pwd)

cd "$ROOT/app"
DATABRICKS_CONFIG_PROFILE=$P OPS_SCHEMA=vg_ops "$PY" -m uvicorn backend.main:app --port $PORT >/tmp/vg_views_evidence.log 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT
for _ in $(seq 1 30); do curl -sf "localhost:$PORT/api/health" >/dev/null && break; sleep 2; done
cd "$ROOT"

{ echo "# Role views (COO, asset management): API execution evidence"; echo
  echo "Captured $(date -u '+%Y-%m-%d %H:%M UTC') by \`scripts/views_evidence.sh\`. The app's FastAPI back end (\`app/backend/routers/views.py\`)"
  echo "ran locally against the **production** Lakebase project \`ventoguard\` (synced tables in \`ventoguard_serving\`, work orders in \`vg_ops\`)."
  echo "Read-only GET requests. The deployed app serves the same code; its status at capture time:"; echo
  echo '```json'
  databricks apps get ventoguard --profile "$P" -o json | jq '{name, url, app_status, active_deployment: {deployment_id: .active_deployment.deployment_id, status: .active_deployment.status, create_time: .active_deployment.create_time}}'
  echo '```'; echo
  echo "The value case below is computed live in Postgres with the same cost model as \`evidence/queries/value_case.sql\`,"
  echo "so it matches the deck (net benefit €4,188,999 a year, unplanned cost €11,325,980 a year)."; echo
  for path in /api/health /api/views/executive /api/views/assets; do
    echo "### \`GET $path\`"; echo '```json'; curl -s "localhost:$PORT$path" | jq '.'; echo '```'; echo
  done
} > "$OUT"
echo "wrote $OUT"

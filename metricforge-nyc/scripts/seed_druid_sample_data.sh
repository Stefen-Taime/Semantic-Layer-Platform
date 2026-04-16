#!/usr/bin/env bash
set -euo pipefail

DRUID_URL="${DRUID_BROKER_URL:-http://localhost:8888}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! curl -fsS "${DRUID_URL}/status/health" >/dev/null 2>&1; then
  echo "Druid is not reachable at ${DRUID_URL}."
  echo "Start it first with: bash scripts/run_druid_stack.sh"
  exit 1
fi

for spec in \
  "${PROJECT_ROOT}/druid/ingestion_specs/taxi_daily_metrics_ingestion.json" \
  "${PROJECT_ROOT}/druid/ingestion_specs/taxi_zone_metrics_ingestion.json"
do
  echo "Submitting ${spec} to Druid Overlord..."
  curl -fsS -X POST "${DRUID_URL}/druid/indexer/v1/task" \
    -H "Content-Type: application/json" \
    --data-binary @"${spec}"
  echo
done

echo "Submitted Druid ingestion specs."
echo "Adjust input paths in the JSON specs if your exported aggregates live elsewhere."

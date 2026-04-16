#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

./scripts/docker_compose.sh \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  -f docker/compose.druid.yml \
  -f docker/compose.apps.yml \
  -f docker/compose.airflow.yml \
  up -d

cat <<'EOF'
MetricForge NYC Airflow stack started.

URLs:
- Airflow: http://localhost:8081
- FastAPI: http://localhost:8000/docs
- Trino: http://localhost:8080
- Druid: http://localhost:8888
EOF

#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  -f docker/compose.druid.yml \
  up -d

cat <<'EOF'
MetricForge NYC Druid serving stack started.

URLs:
- Druid: http://localhost:8888
- Trino: http://localhost:8080
- MinIO console: http://localhost:9001
EOF

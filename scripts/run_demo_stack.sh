#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

./scripts/docker_compose.sh -f docker/compose.demo.yml up -d

cat <<'EOF'
MetricForge NYC demo stack started.

URLs:
- MinIO console: http://localhost:9001
- Trino: http://localhost:8080
- Druid: http://localhost:8888
- Airflow: http://localhost:8081
- FastAPI: http://localhost:8000/docs
- Streamlit: http://localhost:8501
EOF

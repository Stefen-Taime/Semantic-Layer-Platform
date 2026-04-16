#!/usr/bin/env bash
set -euo pipefail

check_url() {
  local name="$1"
  local url="$2"
  if curl -fsS "$url" >/dev/null 2>&1; then
    echo "[ok] $name -> $url"
  else
    echo "[error] $name -> $url"
  fi
}

check_url "MinIO ready" "http://localhost:9000/minio/health/ready"
check_url "Trino" "http://localhost:8080/v1/info"
check_url "Druid" "http://localhost:8888/status/health"
check_url "Airflow" "http://localhost:8081/health"
check_url "FastAPI" "http://localhost:8000/health"
check_url "Streamlit" "http://localhost:8501"

#!/usr/bin/env bash
set -euo pipefail

check_url() {
  local name="$1"
  local url="$2"
  local retries="${3:-12}"
  local delay_seconds="${4:-5}"
  local attempt=1

  while [ "${attempt}" -le "${retries}" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[ok] $name -> $url"
      return 0
    fi

    if [ "${attempt}" -lt "${retries}" ]; then
      sleep "${delay_seconds}"
    fi

    attempt=$((attempt + 1))
  done

  echo "[error] $name -> $url"
  return 1
}

check_url "MinIO ready" "http://localhost:9000/minio/health/ready"
check_url "Trino" "http://localhost:8080/v1/info"
check_url "Druid" "http://localhost:8888/status/health" 18 10
check_url "Airflow" "http://localhost:8081/health" 18 10
check_url "FastAPI" "http://localhost:8000/health"
check_url "Streamlit" "http://localhost:8501"

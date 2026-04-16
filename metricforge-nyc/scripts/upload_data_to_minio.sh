#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="${PROJECT_ROOT}/data/raw"

TRIP_FILE="${RAW_DIR}/yellow_tripdata_2024-01.parquet"
ZONE_FILE="${RAW_DIR}/taxi_zone_lookup.csv"

MINIO_ALIAS="${MINIO_ALIAS:-local}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://127.0.0.1:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-metricforge}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-metricforge123}"
MINIO_RAW_BUCKET="${MINIO_RAW_BUCKET:-metricforge-raw}"
MINIO_RAW_PREFIX="${MINIO_RAW_PREFIX:-nyc_taxi}"

if [[ ! -f "${TRIP_FILE}" || ! -f "${ZONE_FILE}" ]]; then
  echo "Required local files are missing."
  echo "Expected:"
  echo "  - ${TRIP_FILE}"
  echo "  - ${ZONE_FILE}"
  exit 1
fi

if command -v mc >/dev/null 2>&1; then
  mc alias set "${MINIO_ALIAS}" "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"
  mc mb --ignore-existing "${MINIO_ALIAS}/${MINIO_RAW_BUCKET}"
  mc cp "${TRIP_FILE}" "${MINIO_ALIAS}/${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/yellow_tripdata_2024-01.parquet"
  mc cp "${ZONE_FILE}" "${MINIO_ALIAS}/${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/taxi_zone_lookup.csv"
  echo "Uploaded data to s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/"
  exit 0
fi

if command -v aws >/dev/null 2>&1; then
  aws --endpoint-url "${MINIO_ENDPOINT}" s3 mb "s3://${MINIO_RAW_BUCKET}" || true
  aws --endpoint-url "${MINIO_ENDPOINT}" s3 cp "${TRIP_FILE}" "s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/yellow_tripdata_2024-01.parquet"
  aws --endpoint-url "${MINIO_ENDPOINT}" s3 cp "${ZONE_FILE}" "s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/taxi_zone_lookup.csv"
  echo "Uploaded data to s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/"
  exit 0
fi

echo "Neither 'mc' nor 'aws' CLI is installed."
echo "Install one of them, then rerun this script."
exit 1

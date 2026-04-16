#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="${PROJECT_ROOT}/data/raw"

TLC_TRIPDATA_MONTHS="${TLC_TRIPDATA_MONTHS:-2026-01,2026-02}"
ZONE_FILE="${RAW_DIR}/taxi_zone_lookup.csv"

MINIO_ALIAS="${MINIO_ALIAS:-local}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://127.0.0.1:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-metricforge}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-metricforge123}"
MINIO_RAW_BUCKET="${MINIO_RAW_BUCKET:-metricforge-raw}"
MINIO_RAW_PREFIX="${MINIO_RAW_PREFIX:-nyc_taxi}"

IFS=',' read -r -a TRIP_MONTHS <<< "${TLC_TRIPDATA_MONTHS}"

REQUIRED_TRIP_FILES=()
for month in "${TRIP_MONTHS[@]}"; do
  trimmed_month="$(echo "${month}" | xargs)"
  [[ -z "${trimmed_month}" ]] && continue
  REQUIRED_TRIP_FILES+=("${RAW_DIR}/yellow_tripdata_${trimmed_month}.parquet")
done

missing_file=false
for trip_file in "${REQUIRED_TRIP_FILES[@]}"; do
  if [[ ! -f "${trip_file}" ]]; then
    missing_file=true
  fi
done

if [[ "${missing_file}" == "true" || ! -f "${ZONE_FILE}" ]]; then
  echo "Required local files are missing."
  echo "Expected:"
  for trip_file in "${REQUIRED_TRIP_FILES[@]}"; do
    echo "  - ${trip_file}"
  done
  echo "  - ${ZONE_FILE}"
  exit 1
fi

if command -v mc >/dev/null 2>&1; then
  mc alias set "${MINIO_ALIAS}" "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"
  mc mb --ignore-existing "${MINIO_ALIAS}/${MINIO_RAW_BUCKET}"
  for trip_file in "${REQUIRED_TRIP_FILES[@]}"; do
    filename="$(basename "${trip_file}")"
    mc cp "${trip_file}" "${MINIO_ALIAS}/${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/${filename}"
  done
  mc cp "${ZONE_FILE}" "${MINIO_ALIAS}/${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/taxi_zone_lookup.csv"
  echo "Uploaded data to s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/"
  exit 0
fi

if command -v aws >/dev/null 2>&1; then
  aws --endpoint-url "${MINIO_ENDPOINT}" s3 mb "s3://${MINIO_RAW_BUCKET}" || true
  for trip_file in "${REQUIRED_TRIP_FILES[@]}"; do
    filename="$(basename "${trip_file}")"
    aws --endpoint-url "${MINIO_ENDPOINT}" s3 cp "${trip_file}" "s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/${filename}"
  done
  aws --endpoint-url "${MINIO_ENDPOINT}" s3 cp "${ZONE_FILE}" "s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/taxi_zone_lookup.csv"
  echo "Uploaded data to s3://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/"
  exit 0
fi

echo "Neither 'mc' nor 'aws' CLI is installed."
echo "Install one of them, then rerun this script."
exit 1

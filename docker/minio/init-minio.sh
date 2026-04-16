#!/bin/sh

set -eu

MINIO_ALIAS="${MINIO_ALIAS:-local}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
MINIO_ROOT_USER="${MINIO_ROOT_USER:-metricforge}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-metricforge123}"
MINIO_RAW_BUCKET="${MINIO_RAW_BUCKET:-metricforge-raw}"
MINIO_CURATED_BUCKET="${MINIO_CURATED_BUCKET:-metricforge-curated}"
MINIO_WAREHOUSE_BUCKET="${MINIO_WAREHOUSE_BUCKET:-metricforge-warehouse}"
MINIO_LOGS_BUCKET="${MINIO_LOGS_BUCKET:-metricforge-logs}"

echo "Waiting for MinIO at ${MINIO_ENDPOINT}..."
until mc alias set "${MINIO_ALIAS}" "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; do
  sleep 2
done

echo "Creating development buckets if needed..."
mc mb --ignore-existing "${MINIO_ALIAS}/${MINIO_RAW_BUCKET}"
mc mb --ignore-existing "${MINIO_ALIAS}/${MINIO_CURATED_BUCKET}"
mc mb --ignore-existing "${MINIO_ALIAS}/${MINIO_WAREHOUSE_BUCKET}"
mc mb --ignore-existing "${MINIO_ALIAS}/${MINIO_LOGS_BUCKET}"

echo "Available buckets:"
mc ls "${MINIO_ALIAS}"

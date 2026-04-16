#!/usr/bin/env bash

set -euo pipefail

# MetricForge NYC MinIO data bootstrap helper.
#
# This script documents the expected download and upload flow for the initial
# demo dataset. It does not perform downloads automatically.

MINIO_ALIAS="${MINIO_ALIAS:-local}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://127.0.0.1:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-metricforge}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-metricforge123}"
MINIO_RAW_BUCKET="${MINIO_RAW_BUCKET:-metricforge-raw}"
MINIO_RAW_PREFIX="${MINIO_RAW_PREFIX:-nyc_taxi}"

echo "MinIO target:"
echo "  alias   : ${MINIO_ALIAS}"
echo "  endpoint: ${MINIO_ENDPOINT}"
echo "  bucket  : ${MINIO_RAW_BUCKET}"
echo "  prefix  : ${MINIO_RAW_PREFIX}"
echo
echo "Expected MinIO objects:"
echo "  - s3a://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/yellow_tripdata_2024-01.parquet"
echo "  - s3a://${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/taxi_zone_lookup.csv"
echo
echo "Suggested official sources to verify before downloading:"
echo "  - https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
echo "  - https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
echo "  - https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
echo
echo "Example workflow with the MinIO client (mc):"
echo "  mc alias set \"${MINIO_ALIAS}\" \"${MINIO_ENDPOINT}\" \"${MINIO_ACCESS_KEY}\" \"${MINIO_SECRET_KEY}\""
echo "  mc mb --ignore-existing \"${MINIO_ALIAS}/${MINIO_RAW_BUCKET}\""
echo "  curl -L -o /tmp/yellow_tripdata_2024-01.parquet \"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet\""
echo "  curl -L -o /tmp/taxi_zone_lookup.csv \"https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv\""
echo "  mc cp /tmp/yellow_tripdata_2024-01.parquet \"${MINIO_ALIAS}/${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/yellow_tripdata_2024-01.parquet\""
echo "  mc cp /tmp/taxi_zone_lookup.csv \"${MINIO_ALIAS}/${MINIO_RAW_BUCKET}/${MINIO_RAW_PREFIX}/taxi_zone_lookup.csv\""

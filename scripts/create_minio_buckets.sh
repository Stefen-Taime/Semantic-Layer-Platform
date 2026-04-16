#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INIT_SCRIPT="${PROJECT_ROOT}/docker/minio/init-minio.sh"

if command -v mc >/dev/null 2>&1; then
  sh "${INIT_SCRIPT}"
  exit 0
fi

echo "MinIO client 'mc' is not installed."
echo "Either install mc and rerun this script, or run:"
echo "  ./scripts/docker_compose.sh -f docker/compose.base.yml -f docker/compose.minio.yml up minio-init"
exit 1

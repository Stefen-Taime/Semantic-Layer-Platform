#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
./scripts/docker_compose.sh -f docker/compose.demo.yml down

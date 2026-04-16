#!/usr/bin/env bash

set -euo pipefail

if docker compose version >/dev/null 2>&1; then
  exec docker compose "$@"
fi

if command -v sudo >/dev/null 2>&1 && sudo docker compose version >/dev/null 2>&1; then
  exec sudo docker compose "$@"
fi

echo "docker compose is not available for the current user." >&2
echo "Ensure the Docker Compose plugin is installed and the user can access the Docker socket." >&2
exit 1

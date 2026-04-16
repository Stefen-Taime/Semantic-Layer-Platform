#!/usr/bin/env bash

set -euo pipefail

cd /opt/druid

CONFIG_ROOT="/opt/druid/conf/druid/single-server/${DRUID_SINGLE_NODE_CONF:-nano-quickstart}"
PIDS=()

echo "Starting Apache Druid single-server quickstart for MetricForge NYC"
echo "Using config root: ${CONFIG_ROOT}"

terminate_children() {
  if [ "${#PIDS[@]}" -gt 0 ]; then
    kill "${PIDS[@]}" >/dev/null 2>&1 || true
    wait "${PIDS[@]}" >/dev/null 2>&1 || true
  fi
}

start_process() {
  local name="$1"
  local warmup_seconds="$2"
  shift 2

  echo "Launching ${name}"
  "$@" &
  PIDS+=("$!")
  sleep "${warmup_seconds}"
}

trap terminate_children EXIT INT TERM

start_process "zookeeper" 10 bin/run-zk conf
start_process "coordinator-overlord" 15 /druid.sh coordinator-overlord
start_process "historical" 10 /druid.sh historical
start_process "broker" 10 /druid.sh broker
start_process "middleManager" 10 /druid.sh middleManager
start_process "router" 10 /druid.sh router

wait -n

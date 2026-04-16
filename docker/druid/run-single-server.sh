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
  shift

  echo "Launching ${name}"
  "$@" &
  PIDS+=("$!")
}

trap terminate_children EXIT INT TERM

start_process "zookeeper" bin/run-zk conf
sleep 5
start_process "coordinator-overlord" /druid.sh coordinator-overlord
sleep 5
start_process "historical" /druid.sh historical
start_process "broker" /druid.sh broker
start_process "middleManager" /druid.sh middleManager
sleep 5
start_process "router" /druid.sh router

wait -n

#!/usr/bin/env bash

set -euo pipefail

cd /opt/druid

CONFIG_ROOT="/opt/druid/conf/druid/single-server/${DRUID_SINGLE_NODE_CONF:-nano-quickstart}"

echo "Starting Apache Druid single-server quickstart for MetricForge NYC"
echo "Using config root: ${CONFIG_ROOT}"

exec bin/supervise \
  --command ":verify bin/verify-java" \
  --command ":verify bin/verify-default-ports" \
  --command ":notify bin/greet" \
  --command ":kill-timeout 10" \
  --command "!p10 zk bin/run-zk conf" \
  --command "broker bin/run-druid broker ${CONFIG_ROOT}" \
  --command "router bin/run-druid router ${CONFIG_ROOT}" \
  --command "!p90 middleManager bin/run-druid middleManager ${CONFIG_ROOT}" \
  --command "historical bin/run-druid historical ${CONFIG_ROOT}" \
  --command "coordinator-overlord bin/run-druid coordinator-overlord ${CONFIG_ROOT}"

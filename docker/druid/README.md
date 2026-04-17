# Druid Docker Notes

This configuration adds Apache Druid as an OLAP layer for `MetricForge NYC`.

- goal: serve pre-aggregated metrics quickly
- target mode: portfolio demo on a 16/32 GB GCP VM
- constraint: Druid stays heavy for an 8 GB Mac

## Launch mode

The `docker/compose.druid.yml` file now follows a more standard Docker topology, aligned with the official Apache Druid quickstart:

- `druid-zookeeper`
- `druid-postgres`
- `druid-coordinator`
- `druid-broker`
- `druid-historical`
- `druid-middlemanager`
- `druid`: router and web console

The Druid router exposes the console on `http://localhost:8888`.
Shared Druid configuration lives in `docker/druid/environment`.

## Reference files

- `environment`: launch variables
- `jvm.config`: conservative JVM sizing
- `runtime.properties`: illustrative shared properties
- `ingestion/*.json`: ingestion templates
- `queries/*.json`: Druid SQL API query examples

## Honest limits

- for a full demo with Airflow + Trino + Druid, a **32 GB** VM is preferred
- on Docker Desktop Mac you usually need to raise the allocated memory
- the configuration targets the demo, not a high-availability Druid cluster

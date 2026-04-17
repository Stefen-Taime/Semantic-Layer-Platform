# Airflow Orchestration

Airflow orchestrates the pipeline. It does not compute business metrics itself.

## What Airflow does here

- checks MinIO, Hive Metastore, Trino, and the API
- downloads the TLC source files and pushes them to MinIO raw
- triggers the Spark ingestion
- triggers the build of certified tables
- validates the semantic layer
- exports the metric catalog
- submits the Druid specs
- runs a sample query

## Available DAGs

- `ingest_nyc_taxi_data`
- `build_certified_tables`
- `validate_semantic_layer`
- `refresh_metric_catalog`
- `refresh_druid_datasources`
- `metricforge_full_pipeline`

## Why it stays close to Minerva

The Minerva spirit is not just a SQL generator. It is also:

- a centralized definition of metrics,
- a clear batch orchestration,
- multiple serving engines,
- an API exposing the results to product consumers.

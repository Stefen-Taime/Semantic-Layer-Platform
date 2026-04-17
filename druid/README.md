# Druid Serving Layer

This layer exposes the fast OLAP serving of `MetricForge NYC`.

## Role in the final demo

- ingestion of aggregated datasets exported from Spark or Trino
- ultra-fast serving for a few portfolio metrics
- clear comparison with Trino:
  - `Trino` for flexible ad-hoc
  - `Druid` for pre-aggregated, dashboard-oriented serving

## Files

- `ingestion_specs/`: Druid ingestion specs
- `sample_queries/`: Druid SQL API payload examples

## Planned datasources

- `metricforge_taxi_daily_metrics`
- `metricforge_taxi_zone_metrics`

## Honest limits

- the specs are realistic but assume a prior export to JSON/CSV/Parquet has already been produced
- input paths must be adapted to the exact environment of the VM or Druid container
- for the full demo, a 32 GB VM is clearly preferred

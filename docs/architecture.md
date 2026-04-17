# Architecture

MetricForge NYC captures the spirit of a mini metrics platform inspired by Minerva, with a clean separation between batch compute, metadata, SQL serving, OLAP serving, and product exposure.

## Overview

```text
                     +------------------------+
                     |     NYC Taxi Data      |
                     +-----------+------------+
                                 |
                                 v
                       +----------------------+
                       |       Airflow        |
                       | orchestration DAGs   |
                       +----------+-----------+
                                  |
                                  v
                     +------------------------+
                     |   MinIO raw bucket     |
                     |  metricforge-raw/...   |
                     +-----------+------------+
                                 |
                                 v
                 +----------------+----------------+
                 |                                 |
                 v                                 v
       +----------------------+          +----------------------+
       |    Apache Spark      |          |  Semantic Layer YAML |
       | ingest + certified   |          | metrics / dims / joins|
       +----------+-----------+          +----------+-----------+
                  |                                 |
                  v                                 v
       +----------------------+          +----------------------+
       |   Hive Metastore     |<---------|  Metrics Engine      |
       | postgres metadata    |          | parser / validator   |
       +----------+-----------+          | SQL generator        |
                  |                      +----------+-----------+
                  v                                 |
       +----------------------+                     v
       | MinIO warehouse      |          +----------------------+
       | metricforge-warehouse|          |     FastAPI API      |
       +----------+-----------+          | engine routing       |
                  |                      +----+------------+----+
                  |                           |            |
                  v                           v            v
       +----------------------+     +----------------+  +----------------+
       |        Trino         |     |     Druid      |  |   Streamlit    |
       | ad hoc SQL serving   |     | OLAP serving   |  |   Dashboard    |
       +----------------------+     +----------------+  +----------------+
```

## Component roles

- **MinIO** stores the raw files, the Parquet warehouse, and the technical artefacts.
- **Airflow** orchestrates the full pipeline and brings the demo closer to a Minerva-like flow.
- **Spark** builds the certified tables from the raw TLC data.
- **Hive Metastore** provides the shared catalog for Spark and Trino.
- **Trino** serves flexible analytical queries on top of the Hive tables.
- **Druid** serves very fast pre-aggregated metrics for dashboard use cases.
- **Semantic Layer YAML** centralizes the business definitions.
- **Metrics Engine** validates the YAML, generates SQL, and routes the query to Spark, Trino, or Druid.
- **FastAPI** exposes the catalog and the query endpoints.
- **Streamlit** provides the demo UI.

## Recommended reading

- `Trino` for flexibility and ad-hoc exploration
- `Druid` for faster OLAP serving on pre-aggregated datasets
- `Airflow` to expose a readable end-to-end pipeline in portfolio mode

## Runtime reality

- **Mac 8 GB**: dev and tests only, or a few isolated bricks
- **GCP VM 16 GB**: reasonable serving stack
- **GCP VM 32 GB**: full demo with Airflow and Druid recommended

# Airflow

This folder contains the Airflow orchestration for the portfolio demo.

Main DAGs:

- `metricforge_full_pipeline.py`
- `ingest_nyc_taxi_data.py`
- `build_certified_tables.py`
- `validate_semantic_layer.py`
- `refresh_metric_catalog.py`
- `refresh_druid_datasources.py`

For the full demo, Airflow is part of the target stack. Airflow now also orchestrates the first step `TLC source -> MinIO raw`, then the Spark ingestion from MinIO into the raw and certified tables.

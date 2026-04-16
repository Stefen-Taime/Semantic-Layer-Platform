# Airflow

Ce dossier contient l'orchestration Airflow de la démo portfolio.

DAGs principaux :

- `metricforge_full_pipeline.py`
- `ingest_nyc_taxi_data.py`
- `build_certified_tables.py`
- `validate_semantic_layer.py`
- `refresh_metric_catalog.py`
- `refresh_druid_datasources.py`

Pour la démo finale, Airflow fait partie de la stack cible. Airflow orchestre maintenant aussi la première étape `source TLC -> MinIO raw`, puis l'ingestion Spark depuis MinIO vers les tables raw/certifiées.

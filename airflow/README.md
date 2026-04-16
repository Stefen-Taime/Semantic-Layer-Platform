# Airflow

Ce dossier contient l'orchestration Airflow de la démo portfolio.

DAGs principaux :

- `metricforge_full_pipeline.py`
- `ingest_nyc_taxi_data.py`
- `build_certified_tables.py`
- `validate_semantic_layer.py`
- `refresh_metric_catalog.py`
- `refresh_druid_datasources.py`

Pour la démo finale, Airflow fait partie de la stack cible. Les tâches Spark lourdes restent désactivées par défaut dans le conteneur Airflow et peuvent être activées si l'environnement a Java + PySpark.

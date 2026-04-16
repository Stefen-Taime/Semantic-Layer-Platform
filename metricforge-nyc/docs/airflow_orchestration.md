# Airflow Orchestration

Airflow orchestre le pipeline, mais ne calcule pas lui-même les métriques métier.

## Ce qu'Airflow fait ici

- vérifie MinIO, Hive Metastore, Trino et l'API
- déclenche l'ingestion Spark
- déclenche la construction des tables certifiées
- valide la semantic layer
- exporte le metric catalog
- soumet les specs Druid
- exécute une requête exemple

## DAGs disponibles

- `ingest_nyc_taxi_data`
- `build_certified_tables`
- `validate_semantic_layer`
- `refresh_metric_catalog`
- `refresh_druid_datasources`
- `metricforge_full_pipeline`

## Pourquoi c'est proche de Minerva

L'esprit Minerva n'est pas seulement un générateur SQL. C'est aussi :

- une définition centralisée des métriques
- une orchestration batch claire
- des moteurs de serving multiples
- une API qui expose les résultats à des consommateurs produit

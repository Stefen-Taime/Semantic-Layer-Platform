# Metrics Engine

Le moteur de métriques est le coeur logique de MetricForge NYC.

Il est responsable de :

- charger les fichiers YAML de semantic layer,
- valider les références et la cohérence du modèle,
- générer un SQL Spark SQL à partir d'une métrique et de dimensions,
- exécuter les requêtes via Spark local mode quand demandé,
- rester assez modulaire pour supporter plus tard Trino ou Druid.

Modules principaux :

- `parser.py` : charge et typpe les YAML
- `validator.py` : vérifie la cohérence sémantique
- `sql_generator.py` : génère le SQL Spark SQL
- `executors/spark_executor.py` : exécute les requêtes via `spark.sql(...)`

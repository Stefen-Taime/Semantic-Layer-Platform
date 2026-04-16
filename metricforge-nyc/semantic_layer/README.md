# Semantic Layer

Ce dossier contient la couche sémantique déclarative de MetricForge NYC.

- `entities.yml` décrit les entités logiques comme `trip`.
- `dimensions.yml` décrit les dimensions exposées par l'API.
- `joins.yml` documente les chemins de jointure entre faits et dimensions.
- `metrics.yml` décrit les métriques business, leurs filtres et leurs dimensions autorisées.

Ces fichiers sont maintenant utilisés réellement pour :

- la validation sémantique,
- la génération de SQL Spark SQL,
- l'exposition via FastAPI,
- la construction des requêtes dans le dashboard Streamlit.

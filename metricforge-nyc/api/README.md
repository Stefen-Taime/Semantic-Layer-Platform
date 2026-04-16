# API

Ce dossier contient l'API FastAPI de MetricForge NYC.

Rôle de l'API :

- exposer un endpoint de santé,
- publier le catalogue des métriques et dimensions,
- valider la semantic layer,
- accepter une requête de métrique,
- générer du SQL Spark SQL,
- exécuter la requête dans Spark si demandé.

Le mode `execute=false` retourne seulement le SQL généré, ce qui permet de tester l'API même si Spark ou les données ne sont pas disponibles.

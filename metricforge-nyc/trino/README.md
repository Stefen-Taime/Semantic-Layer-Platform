# Trino Configuration

Ce dossier documente le point d'entrée SQL principal de MetricForge NYC.

Trino est le moteur privilégié pour :

- interroger les tables certifiées enregistrées dans Hive,
- servir les requêtes générées par le metrics engine,
- exposer un SQL analytique lisible et proche du comportement attendu en production légère.

Le sous-dossier `catalog/` contient un exemple minimal de catalogue Hive pour démarrer.

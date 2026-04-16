# Druid Serving Layer

Cette couche expose le serving OLAP rapide de `MetricForge NYC`.

## Rôle dans la démo finale

- ingestion de datasets agrégés exportés depuis Spark ou Trino
- serving ultra-rapide pour quelques métriques portefeuille
- comparaison claire avec Trino :
  - `Trino` pour l'ad hoc flexible
  - `Druid` pour le pré-agrégé orienté dashboard

## Fichiers

- `ingestion_specs/` : specs d'ingestion Druid
- `sample_queries/` : exemples de payloads Druid SQL API

## Datasources prévues

- `metricforge_taxi_daily_metrics`
- `metricforge_taxi_zone_metrics`

## Limites honnêtes

- les specs sont réalistes mais supposent qu'un export préalable vers JSON/CSV/Parquet a été produit
- les chemins d'entrée doivent être adaptés à l'environnement exact de la VM ou du conteneur Druid
- pour la démo complète, une VM 32 Go est nettement préférable

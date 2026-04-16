# Druid Docker Notes

Cette configuration ajoute Apache Druid comme couche OLAP optionnelle pour `MetricForge NYC`.

- objectif : servir des métriques pré-agrégées rapidement
- mode visé : démo portfolio sur VM GCP 16/32 Go
- contrainte : Druid reste lourd pour un Mac 8 Go

## Mode de lancement

Le fichier `docker/compose.druid.yml` utilise une approche single-server quickstart.
Selon l'image `apache/druid` disponible localement et sa version, le chemin de conf ou la commande de bootstrap peut demander un ajustement.

## Fichiers de référence

- `environment` : variables de lancement
- `jvm.config` : sizing JVM prudent
- `runtime.properties` : propriétés communes illustratives
- `ingestion/*.json` : templates d'ingestion
- `queries/*.json` : exemples de requêtes Druid SQL API

## Limites honnêtes

- la compatibilité exacte du démarrage single-server dépend de l'image Docker Druid
- pour une démo complète avec Airflow + Trino + Druid, une VM **32 Go** est préférable
- sur Docker Desktop Mac, il faut souvent augmenter la mémoire allouée

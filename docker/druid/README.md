# Druid Docker Notes

Cette configuration ajoute Apache Druid comme couche OLAP pour `MetricForge NYC`.

- objectif : servir des métriques pré-agrégées rapidement
- mode visé : démo portfolio sur VM GCP 16/32 Go
- contrainte : Druid reste lourd pour un Mac 8 Go

## Mode de lancement

Le fichier `docker/compose.druid.yml` suit désormais une topologie Docker plus standard, alignée sur le quickstart officiel Apache Druid :

- `druid-zookeeper`
- `druid-postgres`
- `druid-coordinator`
- `druid-broker`
- `druid-historical`
- `druid-middlemanager`
- `druid` : routeur et console web

Le routeur Druid expose la console sur `http://localhost:8888`.
La configuration Druid partagée se trouve dans `docker/druid/environment`.

## Fichiers de référence

- `environment` : variables de lancement
- `jvm.config` : sizing JVM prudent
- `runtime.properties` : propriétés communes illustratives
- `ingestion/*.json` : templates d'ingestion
- `queries/*.json` : exemples de requêtes Druid SQL API

## Limites honnêtes

- pour une démo complète avec Airflow + Trino + Druid, une VM **32 Go** est préférable
- sur Docker Desktop Mac, il faut souvent augmenter la mémoire allouée
- la configuration reste orientée démo et non cluster Druid haute disponibilité

# Architecture

MetricForge NYC reprend l'esprit d'une mini metrics platform inspirée de Minerva, avec une séparation nette entre batch compute, métadonnées, serving SQL, serving OLAP et exposition produit.

## Vue d'ensemble

```text
                     +------------------------+
                     |     NYC Taxi Data      |
                     +-----------+------------+
                                 |
                                 v
                     +------------------------+
                     |   MinIO raw bucket     |
                     |  metricforge-raw/...   |
                     +-----------+------------+
                                 |
                                 v
                       +----------------------+
                       |       Airflow        |
                       | orchestration DAGs   |
                       +----------+-----------+
                                  |
                 +----------------+----------------+
                 |                                 |
                 v                                 v
       +----------------------+          +----------------------+
       |    Apache Spark      |          |  Semantic Layer YAML |
       | ingest + certified   |          | metrics / dims / joins|
       +----------+-----------+          +----------+-----------+
                  |                                 |
                  v                                 v
       +----------------------+          +----------------------+
       |   Hive Metastore     |<---------|  Metrics Engine      |
       | postgres metadata    |          | parser / validator   |
       +----------+-----------+          | SQL generator        |
                  |                      +----------+-----------+
                  v                                 |
       +----------------------+                     v
       | MinIO warehouse      |          +----------------------+
       | metricforge-warehouse|          |     FastAPI API      |
       +----------+-----------+          | engine routing       |
                  |                      +----+------------+----+
                  |                           |            |
                  v                           v            v
       +----------------------+     +----------------+  +----------------+
       |        Trino         |     |     Druid      |  |   Streamlit    |
       | ad hoc SQL serving   |     | OLAP serving   |  |   Dashboard    |
       +----------------------+     +----------------+  +----------------+
```

## Rôle des composants

- **MinIO** stocke les fichiers bruts, le warehouse Parquet et les artefacts techniques.
- **Airflow** orchestre le pipeline complet et rend la démo plus proche d'un fonctionnement Minerva-like.
- **Spark** prépare les tables certifiées à partir des données TLC brutes.
- **Hive Metastore** fournit le catalogue partagé à Spark et Trino.
- **Trino** sert les requêtes analytiques flexibles à partir des tables Hive.
- **Druid** sert des métriques pré-agrégées très rapides pour les cas dashboard.
- **Semantic Layer YAML** centralise les définitions métier.
- **Metrics Engine** valide les YAML, génère le SQL et route la requête vers Spark, Trino ou Druid.
- **FastAPI** expose le catalogue et les endpoints de requête.
- **Streamlit** fournit l'UI de démonstration.

## Lecture recommandée

- `Trino` pour la flexibilité et l'exploration ad hoc
- `Druid` pour un serving OLAP plus rapide sur datasets pré-agrégés
- `Airflow` pour exposer un pipeline de bout en bout lisible en portfolio

## Réalité d'exécution

- **Mac 8 Go** : mode dev et tests seulement, ou quelques briques isolées
- **VM GCP 16 Go** : stack de serving raisonnable
- **VM GCP 32 Go** : démo complète avec Airflow et Druid recommandée

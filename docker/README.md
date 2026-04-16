# Docker Stack

La couche Docker Compose sert à rapprocher `MetricForge NYC` d'une architecture Minerva-like exécutable en démo.

## Briques

- **MinIO** : stockage objet local compatible S3
- **Hive Metastore + PostgreSQL** : catalogue partagé
- **Trino** : serving SQL flexible
- **Druid** : serving OLAP rapide avec routeur, broker, historical, middle manager, coordinator, ZooKeeper et PostgreSQL metadata store
- **FastAPI** : API métriques
- **Streamlit** : dashboard
- **Airflow** : orchestration complète

## Pourquoi la stack reste modulaire

Le mode portfolio recommandé est la stack complète, mais les fichiers Compose restent séparés pour :

- déboguer une brique isolée
- économiser de la mémoire en local
- rendre la progression plus lisible

Fichiers disponibles :

- `compose.base.yml`
- `compose.minio.yml`
- `compose.hive.yml`
- `compose.trino.yml`
- `compose.druid.yml`
- `compose.apps.yml`
- `compose.airflow.yml`
- `compose.demo.yml`

## Credentials dev-only

MinIO local :

- user : `metricforge`
- password : `metricforge123`

Ne pas utiliser ces valeurs en production.

## Commandes principales

MinIO seul :

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  up -d
```

MinIO + Hive + Trino :

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  up -d
```

Druid :

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  -f docker/compose.druid.yml \
  up -d
```

Cette brique Druid démarre plusieurs services internes. Le routeur et la console restent exposés sur `http://localhost:8888`.

Airflow :

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  -f docker/compose.druid.yml \
  -f docker/compose.apps.yml \
  -f docker/compose.airflow.yml \
  up -d
```

Démo complète :

```bash
docker compose -f docker/compose.demo.yml up -d
```

## URLs utiles

- MinIO console : `http://localhost:9001`
- Hive Metastore : `thrift://localhost:9083`
- Trino : `http://localhost:8080`
- Druid : `http://localhost:8888`
- Airflow : `http://localhost:8081`
- FastAPI : `http://localhost:8000/docs`
- Streamlit : `http://localhost:8501`

## Limites honnêtes

- Hive Metastore + S3A + MinIO peut demander des jars compatibles selon l'environnement
- Druid reste la brique la plus lourde de la stack et demande plus de temps de warm-up que Trino ou l'API
- la démo complète n'est pas recommandée sur Mac 8 Go
- une VM GCP 32 Go est le meilleur compromis pour démontrer toute la stack

## Références utiles

- Trino Hive connector : https://trino.io/docs/current/connector/hive.html
- Trino S3 object storage : https://trino.io/docs/current/object-storage/file-system-s3.html
- Apache Hive metastore installation concepts : https://hive.apache.org/docs/latest/admin/adminmanual-installation/

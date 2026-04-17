# Docker Stack

The Docker Compose layer brings `MetricForge NYC` closer to a runnable Minerva-like architecture.

## Building blocks

- **MinIO**: local S3-compatible object storage
- **Hive Metastore + PostgreSQL**: shared catalog
- **Trino**: flexible SQL serving
- **Druid**: fast OLAP serving with router, broker, historical, middle manager, coordinator, ZooKeeper, and PostgreSQL metadata store
- **FastAPI**: metrics API
- **Streamlit**: dashboard
- **Airflow**: full orchestration

## Why the stack stays modular

The recommended portfolio mode is the full stack, but the Compose files stay split to:

- debug a single brick in isolation,
- save memory locally,
- keep the progression readable.

Available files:

- `compose.base.yml`
- `compose.minio.yml`
- `compose.hive.yml`
- `compose.trino.yml`
- `compose.druid.yml`
- `compose.apps.yml`
- `compose.airflow.yml`
- `compose.demo.yml`

## Dev-only credentials

Local MinIO:

- user: `metricforge`
- password: `metricforge123`

Do not use these values in production.

## Main commands

MinIO only:

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  up -d
```

MinIO + Hive + Trino:

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  up -d
```

Druid:

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  -f docker/compose.druid.yml \
  up -d
```

This Druid brick starts several internal services. The router and console stay exposed on `http://localhost:8888`.

Airflow:

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

Full demo:

```bash
docker compose -f docker/compose.demo.yml up -d
```

## Useful URLs

- MinIO console: `http://localhost:9001`
- Hive Metastore: `thrift://localhost:9083`
- Trino: `http://localhost:8080`
- Druid: `http://localhost:8888`
- Airflow: `http://localhost:8081`
- FastAPI: `http://localhost:8000/docs`
- Streamlit: `http://localhost:8501`

## Honest limits

- Hive Metastore + S3A + MinIO may require compatible jars depending on the environment
- Druid is the heaviest brick of the stack and needs more warm-up than Trino or the API
- the full demo is not recommended on an 8 GB Mac
- a 32 GB GCP VM is the best compromise to showcase the whole stack

## Useful references

- Trino Hive connector: https://trino.io/docs/current/connector/hive.html
- Trino S3 object storage: https://trino.io/docs/current/object-storage/file-system-s3.html
- Apache Hive metastore installation concepts: https://hive.apache.org/docs/latest/admin/adminmanual-installation/

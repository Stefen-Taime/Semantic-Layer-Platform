# MetricForge NYC

MetricForge NYC est un projet open source de portfolio inspiré de **Minerva**, la plateforme de métriques et de semantic layer d'Airbnb.

L'objectif est de centraliser les métriques business dans une couche sémantique déclarative pour éviter que chaque équipe recalcule les mêmes KPI différemment avec des SQL, filtres et conventions divergents.

## Architecture

```text
NYC Taxi Data
  -> MinIO raw bucket
  -> Airflow
  -> Spark
  -> Hive Metastore
  -> MinIO warehouse bucket
  -> Trino
  -> Druid
  -> Semantic Layer YAML
  -> FastAPI
  -> Streamlit
```

Le projet montre :

- **Spark** pour préparer les tables certifiées
- **Hive Metastore** pour le catalogue technique
- **MinIO** pour le stockage objet local compatible S3
- **Trino** pour le serving SQL flexible
- **Druid** pour le serving OLAP pré-agrégé
- **Airflow** pour l'orchestration complète
- **YAML semantic layer** pour définir dimensions, joins et métriques
- **FastAPI** pour exposer les requêtes de métriques
- **Streamlit** pour la démo produit

## Aperçu visuel

### Stockage et catalogue

![MinIO warehouse — buckets `metricforge-raw`, `metricforge-curated`, `metricforge-warehouse` partagés par tous les moteurs.](img/minio-warehouse.png)

### Orchestration Airflow

![DAGs Airflow : `ingest_nyc_taxi_data`, `build_certified_tables`, `refresh_metric_catalog`, `refresh_druid_datasources`, `validate_semantic_layer`.](img/airflow-dags.png)

### Serving SQL Trino

![Historique Trino : jointures et agrégats sur la fact table certifiée en quelques centaines de millisecondes.](img/trino-query-history.png)

### Serving OLAP Druid

![Console Druid : datasources `metricforge_taxi_daily_metrics` et `metricforge_taxi_zone_metrics` avec leurs rollups pré-agrégés.](img/druid-console.png)

### API FastAPI (semantic layer)

![Swagger : un seul `POST /query` comme contrat unique vers tous les moteurs.](img/fastapi-swagger.png)

![`GET /metrics` — catalogue gouverné : owner, description, dimensions autorisées, moteur préféré.](img/api-metrics-response.png)

![`POST /query` vers Trino avec `limit` et `order_by` : classement du pourboire moyen par moyen de paiement.](img/api-query-average-tip.png)

![`POST /query` vers Druid : top boroughs par trajets complétés, ~200 ms grâce aux agrégats pré-calculés.](img/api-query-druid-top-boroughs.png)

### Dashboard Streamlit

![Catalogue du semantic layer directement exposé dans le dashboard (dix métriques, sept dimensions).](img/dashboard-catalog.png)

### Infrastructure

![VM GCP `e2-standard-8` pendant l'exécution d'un pipeline complet.](img/gcp-vm-monitoring.png)

## Modes d'exécution

### 1. Local lightweight

Mode de dev pour parser/validator/tests/API/dashboard :

```bash
cd Semantic-Layer-Platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

### 2. Serving stack

MinIO + Hive + Trino :

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  up -d
```

### 3. Full demo stack

Mode de démo portfolio recommandé :

```bash
bash scripts/run_demo_stack.sh
```

Alternative directe :

```bash
docker compose -f docker/compose.demo.yml up -d
```

## Commandes principales

Batch Spark :

```bash
python scripts/load_nyc_taxi_to_minio.py
python spark/01_create_hive_database.py
python spark/02_ingest_raw_taxi_data.py
python spark/03_build_certified_tables.py
python spark/04_run_sample_queries.py
```

Dans la stack complète, Airflow orchestre aussi la première étape `source TLC -> MinIO raw`, puis déclenche Spark pour charger les tables raw et certifiées. La liste des mois est dynamique via `TLC_TRIPDATA_MONTHS`, avec comme défaut **2026-01,2026-02**, et `taxi_zone_lookup.csv` reste toujours chargé.

Tests semantic layer :

```bash
python -m pytest tests/test_semantic_yaml.py
python -m pytest tests/test_sql_generator.py
python -m pytest tests/test_sql_generator_druid.py
python -m pytest tests/test_routing.py
```

API locale :

```bash
uvicorn api.main:app --reload
```

Dashboard local :

```bash
streamlit run dashboard/app.py
```

Airflow seul avec dépendances :

```bash
bash scripts/run_airflow_stack.sh
```

Druid avec dépendances :

```bash
bash scripts/run_druid_stack.sh
```

## Endpoints API

- `GET /health`
- `GET /metrics`
- `GET /dimensions`
- `GET /engines`
- `GET /engines/trino/health`
- `GET /engines/druid/health`
- `POST /validate`
- `POST /query`

## Exemples curl

Health :

```bash
curl http://localhost:8000/health
```

Engines :

```bash
curl http://localhost:8000/engines
```

Trino health :

```bash
curl http://localhost:8000/engines/trino/health
```

Druid health :

```bash
curl http://localhost:8000/engines/druid/health
```

SQL via Trino sans exécution :

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"metric":"gross_revenue","group_by":["pickup_zone"],"time_grain":"day","start_date":"2024-01-01","end_date":"2024-01-31","engine":"trino","execute":false}'
```

SQL via Druid sans exécution :

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"metric":"daily_zone_revenue","group_by":["pickup_zone"],"time_grain":"day","start_date":"2024-01-01","end_date":"2024-01-31","engine":"druid","execute":false}'
```

Exécution via Trino :

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"metric":"gross_revenue","group_by":["pickup_zone"],"time_grain":"day","start_date":"2024-01-01","end_date":"2024-01-31","engine":"trino","execute":true}'
```

## Services utiles

- MinIO console : `http://localhost:9001`
- Trino : `http://localhost:8080`
- Druid : `http://localhost:8888`
- Airflow : `http://localhost:8081`
- FastAPI docs : `http://localhost:8000/docs`
- Streamlit : `http://localhost:8501`

## Limitations connues

- la stack complète est lourde et vise surtout une **VM GCP 32 Go**
- Hive Metastore + MinIO + S3A peut demander des ajustements de jars selon l'image et l'environnement
- Druid tourne maintenant en topologie multi-services de démo, mais reste plus lourd et plus lent à démarrer que le reste de la stack
- les specs Druid supposent un export agrégé préalable
- les credentials fournis sont strictement **dev-only**

## Prochaines améliorations possibles

- brancher Spark sur le même metastore partagé pour un flux de bout en bout plus automatique
- exporter les agrégats Druid automatiquement depuis Spark ou Trino
- enrichir la semantic layer avec plus de métriques et de filtres utilisateur
- ajouter de l'observabilité et des tests d'intégration de la stack complète

## Documentation complémentaire

- [docs/architecture.md](./docs/architecture.md)
- [docs/demo_runbook.md](./docs/demo_runbook.md)
- [docs/gcp_vm_setup.md](./docs/gcp_vm_setup.md)
- [docs/airflow_orchestration.md](./docs/airflow_orchestration.md)
- [docs/druid_serving_layer.md](./docs/druid_serving_layer.md)
- [docs/minerva_mapping.md](./docs/minerva_mapping.md)

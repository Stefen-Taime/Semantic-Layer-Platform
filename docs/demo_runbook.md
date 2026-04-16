# Demo Runbook

Ce runbook décrit le chemin de démo portfolio recommandé pour `MetricForge NYC`.

## Prérequis

- Docker Engine + Docker Compose plugin
- Python 3.11 ou 3.12
- au moins 16 Go RAM pour une démo correcte
- 32 Go RAM recommandés pour la stack complète avec Druid + Airflow

## Mode local léger

Le mode léger sert surtout à développer ou valider le moteur sémantique :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

## Démo portfolio recommandée

### 1. Lancer MinIO, Hive Metastore, Trino, Druid, API, Dashboard et Airflow

```bash
bash scripts/run_demo_stack.sh
```

### 2. Vérifier les services

```bash
bash scripts/check_services.sh
```

### 3. Charger les données sources dans MinIO

```bash
bash scripts/download_nyc_taxi_data.sh
bash scripts/upload_data_to_minio.sh
```

### 4. Construire les tables certifiées

Si tu exécutes Spark hors Airflow :

```bash
python spark/01_create_hive_database.py
python spark/02_ingest_raw_taxi_data.py
python spark/03_build_certified_tables.py
python spark/04_run_sample_queries.py
```

### 5. Requête métrique via Trino

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"metric":"gross_revenue","group_by":["pickup_zone"],"time_grain":"day","start_date":"2024-01-01","end_date":"2024-01-31","engine":"trino","execute":false}'
```

### 6. Alimenter Druid

```bash
bash scripts/seed_druid_sample_data.sh
```

### 7. Requête métrique via Druid

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"metric":"daily_zone_revenue","group_by":["pickup_zone"],"time_grain":"day","start_date":"2024-01-01","end_date":"2024-01-31","engine":"druid","execute":false}'
```

### 8. Lancer et montrer Airflow

- URL : `http://localhost:8081`
- user : `admin`
- password : `admin`

Montre le DAG `metricforge_full_pipeline`.

### 9. Montrer le dashboard

- URL : `http://localhost:8501`
- sélectionner une métrique Trino
- sélectionner une métrique Druid
- comparer les deux chemins de serving

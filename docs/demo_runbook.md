# Demo Runbook

This runbook describes the recommended portfolio demo path for `MetricForge NYC`.

## Prerequisites

- Docker Engine + Docker Compose plugin
- Python 3.11 or 3.12
- at least 16 GB RAM for a decent demo
- 32 GB RAM recommended for the full stack with Druid + Airflow

## Lightweight local mode

The lightweight mode is mostly for developing or validating the semantic engine:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

## Recommended portfolio demo

### 1. Start MinIO, Hive Metastore, Trino, Druid, API, Dashboard, and Airflow

```bash
bash scripts/run_demo_stack.sh
```

### 2. Check the services

```bash
bash scripts/check_services.sh
```

### 3. Load source data into MinIO

Manual mode:

```bash
python scripts/load_nyc_taxi_to_minio.py
```

In orchestrated mode, Airflow runs this step via the `ingest_nyc_taxi_data` DAG or through the `metricforge_full_pipeline` DAG.

### 4. Build the certified tables

If you are running Spark outside Airflow:

```bash
python spark/01_create_hive_database.py
python spark/02_ingest_raw_taxi_data.py
python spark/03_build_certified_tables.py
python spark/04_run_sample_queries.py
```

### 5. Metric query via Trino

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"metric":"gross_revenue","group_by":["pickup_zone"],"time_grain":"day","start_date":"2024-01-01","end_date":"2024-01-31","engine":"trino","execute":false}'
```

### 6. Seed Druid

```bash
bash scripts/seed_druid_sample_data.sh
```

### 7. Metric query via Druid

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"metric":"daily_zone_revenue","group_by":["pickup_zone"],"time_grain":"day","start_date":"2024-01-01","end_date":"2024-01-31","engine":"druid","execute":false}'
```

### 8. Launch and showcase Airflow

- URL: `http://localhost:8081`
- user: `admin`
- password: `admin`

Show the `metricforge_full_pipeline` DAG.

### 9. Showcase the dashboard

- URL: `http://localhost:8501`
- pick a Trino metric
- pick a Druid metric
- compare the two serving paths

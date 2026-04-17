# MetricForge NYC

MetricForge NYC is an open-source portfolio project inspired by **Minerva**, Airbnb's metrics platform and semantic layer.

Goal: centralize business metrics in a declarative semantic layer (YAML) so that every team stops recomputing the same KPIs differently with divergent SQL, filters, and conventions. One definition, multiple execution engines, one number per question.

## Architecture

![MetricForge NYC stack: MinIO, Hive Metastore, Airflow, Spark, Druid, FastAPI (plus Trino + Streamlit + Plotly).](img/metricforge_stack_logos.png)

```text
NYC Taxi Data (TLC)
  -> MinIO raw bucket
  -> Airflow
  -> Spark (ingestion + certification + Druid aggregates)
  -> Hive Metastore
  -> MinIO warehouse bucket (Parquet)
  -> Trino (flexible SQL)  +  Druid (pre-aggregated OLAP)
  -> Semantic Layer YAML (metrics_engine)
  -> FastAPI  (/query, /metrics, /dimensions, /validate)
  -> Streamlit + Plotly (dashboard)
```

The project showcases:

- **MinIO** for local S3-compatible object storage
- **Apache Spark** for ingestion, certified tables, and Druid aggregates
- **Hive Metastore** as the shared technical catalog across Spark and Trino
- **Trino** for flexible SQL serving
- **Apache Druid** for pre-aggregated OLAP serving (datasources `metricforge_taxi_daily_metrics` and `metricforge_taxi_zone_metrics`)
- **Apache Airflow** for full pipeline orchestration
- **YAML semantic layer** (`metrics_engine`) to define dimensions, joins, and metrics
- **FastAPI** to expose metric queries with `limit` and `order_by`
- **Streamlit + Plotly** for the product demo (dark theme, auto-selected charts)

The semantic layer currently exposes **10 metrics** (`completed_trips`, `gross_revenue`, `average_fare`, `average_tip`, `total_tip_amount`, `tip_rate`, `average_trip_distance`, `average_trip_duration`, `daily_zone_revenue`, `daily_completed_trips`) across **8 dimensions** (`pickup_zone`, `pickup_borough`, `dropoff_zone`, `dropoff_borough`, `payment_type`, `pickup_date`, `pickup_month`, `pickup_day`).

## Visual overview

### Storage and catalog

![MinIO warehouse: `metricforge-raw`, `metricforge-curated`, `metricforge-warehouse` buckets shared by every engine.](img/minio-warehouse.png)

### Airflow orchestration

![Airflow DAGs: `ingest_nyc_taxi_data`, `build_certified_tables`, `refresh_metric_catalog`, `refresh_druid_datasources`, `validate_semantic_layer`, plus the parent DAG `metricforge_full_pipeline`.](img/airflow-dags.png)

### Trino SQL serving

![Trino query history: joins and aggregates on the certified fact table answered in a few hundred milliseconds.](img/trino-query-history.png)

### Druid OLAP serving

![Druid console: datasources `metricforge_taxi_daily_metrics` and `metricforge_taxi_zone_metrics` with their pre-aggregated rollups.](img/druid-console.png)

### FastAPI (semantic layer)

![Swagger: a single `POST /query` as the unified contract across engines.](img/fastapi-swagger.png)

![`GET /metrics`: governed catalog with owner, description, allowed dimensions, preferred engine.](img/api-metrics-response.png)

![`POST /query` against Trino with `limit` and `order_by`: ranking of average tip by payment method.](img/api-query-average-tip.png)

![`POST /query` against Druid: top boroughs by completed trips, around 200 ms thanks to pre-aggregated rollups.](img/api-query-druid-top-boroughs.png)

### Streamlit dashboard

![Semantic-layer catalog exposed directly in the dashboard (ten metrics, eight dimensions).](img/dashboard-catalog.png)

### Infrastructure

![GCP VM `e2-standard-8` during a full pipeline run.](img/gcp-vm-monitoring.png)

## Execution modes

### 1. Local lightweight (no Docker)

Dev mode for the parser, validator, tests, API, and dashboard:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m pytest -q
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

### 2. Serving stack (MinIO + Hive + Trino)

```bash
docker compose \
  -f docker/compose.base.yml \
  -f docker/compose.minio.yml \
  -f docker/compose.hive.yml \
  -f docker/compose.trino.yml \
  up -d
```

### 3. Full demo stack (recommended)

Portfolio demo mode, every service with one command (MinIO + Hive + Trino + Druid + Airflow + FastAPI + Streamlit):

```bash
bash scripts/run_demo_stack.sh
# or
docker compose -f docker/compose.demo.yml up -d --build
```

Clean shutdown:

```bash
bash scripts/stop_demo_stack.sh
```

### 4. Targeted stacks

Airflow only with its dependencies:

```bash
bash scripts/run_airflow_stack.sh
```

Druid only with its dependencies:

```bash
bash scripts/run_druid_stack.sh
```

## Spark pipelines

Spark jobs live in `spark/`:

- `01_create_hive_database.py`: creates the `metricforge` database in the Hive Metastore
- `02_ingest_raw_taxi_data.py`: loads NYC TLC CSVs from MinIO into raw tables
- `03_build_certified_tables.py`: builds the partitioned certified tables (`fct_taxi_trips`, `dim_zone`, `dim_payment_type`, `dim_date`)
- `04_build_druid_aggregates.py`: computes daily and per-zone rollups and publishes the JSON ingested by Druid
- `04_run_sample_queries.py`: validation sample queries

Local execution (after loading data):

```bash
python scripts/load_nyc_taxi_to_minio.py
python spark/01_create_hive_database.py
python spark/02_ingest_raw_taxi_data.py
python spark/03_build_certified_tables.py
python spark/04_build_druid_aggregates.py
```

In the full stack, Airflow orchestrates these steps, including the `TLC -> MinIO raw` download. The months to ingest are configurable via `TLC_TRIPDATA_MONTHS` (default: `2026-01,2026-02`). `taxi_zone_lookup.csv` is always loaded.

## Airflow DAGs

In `airflow/dags/`:

- `ingest_nyc_taxi_data.py`: TLC -> MinIO raw
- `build_certified_tables.py`: Spark, raw -> curated -> certified
- `build_druid_aggregates.py`: Spark, certified -> Druid JSON rollups
- `refresh_druid_datasources.py`: submits specs to the Druid Overlord
- `refresh_metric_catalog.py`: regenerates the metric catalog exposed by the API
- `validate_semantic_layer.py`: semantic-layer lint and validation
- `metricforge_full_pipeline.py`: parent DAG that triggers the full chain

## Tests

In `tests/`:

```bash
python -m pytest tests/test_semantic_yaml.py
python -m pytest tests/test_sql_generator.py
python -m pytest tests/test_sql_generator_druid.py
python -m pytest tests/test_routing.py
python -m pytest tests/test_api_engine_routing.py
python -m pytest tests/test_trino_executor.py
python -m pytest tests/test_druid_executor.py
python -m pytest tests/test_source_loader.py
python -m pytest tests/test_spark_session.py
# or simply:
python -m pytest -q
```

## API endpoints

- `GET /health`
- `GET /engines`
- `GET /engines/trino/health`
- `GET /engines/druid/health`
- `GET /metrics`
- `GET /dimensions`
- `POST /validate`
- `POST /query`: supports `metric`, `group_by`, `time_grain`, `start_date`, `end_date`, `filters`, `engine`, `execute`, plus **`limit` (1-10000)** and **`order_by` (list of `{column, direction}`)**

Interactive docs: `http://localhost:8000/docs`.

## curl examples

Health:

```bash
curl http://localhost:8000/health
```

Metric catalog:

```bash
curl http://localhost:8000/metrics
```

Trino SQL without execution (review the generated query):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "gross_revenue",
    "group_by": ["pickup_borough"],
    "start_date": "2026-01-01",
    "end_date": "2026-03-01",
    "engine": "trino",
    "execute": false
  }'
```

Top 10 zones by revenue (Druid, pre-aggregated, around 200 ms):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "daily_zone_revenue",
    "group_by": ["pickup_zone"],
    "start_date": "2026-01-01",
    "end_date": "2026-03-01",
    "engine": "druid",
    "limit": 10,
    "order_by": [{"column": "daily_zone_revenue", "direction": "desc"}]
  }'
```

Time series (Trino + `time_grain`):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "completed_trips",
    "time_grain": "day",
    "start_date": "2026-01-01",
    "end_date": "2026-03-01",
    "engine": "trino"
  }'
```

## Useful services

- MinIO console: http://localhost:9001
- Trino UI: http://localhost:8080
- Druid router: http://localhost:8888
- Airflow UI: http://localhost:8081
- FastAPI docs: http://localhost:8000/docs
- Streamlit dashboard: http://localhost:8501

## Repository structure

```
metrics_engine/      # parser/validator/SQL generator, Spark/Trino/Druid executors
semantic_layer/      # metrics.yml, dimensions.yml, joins.yml, entities.yml
api/                 # FastAPI (main.py)
dashboard/           # Streamlit + Plotly (app.py)
spark/               # Spark jobs (ingestion, certification, Druid aggregates)
airflow/             # dags/ + include/
docker/              # compose.*.yml + custom images (airflow, apps, druid, hive, trino)
scripts/             # run_demo_stack.sh, stop_demo_stack.sh, run_airflow_stack.sh, run_druid_stack.sh, ...
tests/               # pytest (semantic_yaml, sql_generator, sql_generator_druid, routing, executors, ...)
docs/                # detailed documentation
infra/               # Terraform GCP VM
data/                # raw/, curated/ (git-ignored)
img/                 # README screenshots and Medium article
```

## Known limitations

- the full stack is heavy and targets a **GCP VM with 32 GB** (type `e2-standard-8`)
- Hive Metastore + MinIO + S3A may require jar tweaks depending on the image and environment (an entrypoint is provided)
- Druid runs in a demo multi-service topology (Coordinator, Broker, Historical, MiddleManager, Router), which is heavy to boot
- the Druid specs assume a pre-aggregated export produced by Spark
- the provided credentials are strictly **dev-only**

## Possible next improvements

- end-to-end observability (Prometheus/Grafana on the stack)
- automated integration tests against the full stack
- more ratio and cohort metrics, and more user-facing filters
- automatic export of Druid aggregates directly from Spark or Trino without an intermediate step

## Further documentation

- [docs/architecture.md](./docs/architecture.md)
- [docs/business_requirements.md](./docs/business_requirements.md)
- [docs/metric_lifecycle.md](./docs/metric_lifecycle.md)
- [docs/demo_runbook.md](./docs/demo_runbook.md)
- [docs/airflow_orchestration.md](./docs/airflow_orchestration.md)
- [docs/druid_serving_layer.md](./docs/druid_serving_layer.md)
- [docs/local_vs_gcp_vm.md](./docs/local_vs_gcp_vm.md)
- [docs/gcp_vm_setup.md](./docs/gcp_vm_setup.md)
- [docs/minerva_mapping.md](./docs/minerva_mapping.md)

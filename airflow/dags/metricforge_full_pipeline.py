"""Full MetricForge NYC demo pipeline orchestrated with Airflow."""

from __future__ import annotations

import json
import os
import socket
import subprocess
from datetime import datetime
from pathlib import Path

import requests

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator
except ImportError:  # pragma: no cover - optional dependency for this stage
    DAG = None
    BashOperator = None
    PythonOperator = None


def _check_http_service(name: str, url: str) -> None:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    print(f"{name} is reachable at {url}")


def _check_socket_service(name: str, host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=10):
        print(f"{name} is reachable at {host}:{port}")


def _check_minio() -> None:
    endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000").rstrip("/")
    _check_http_service("MinIO", f"{endpoint}/minio/health/ready")


def _check_hive_metastore() -> None:
    host = os.getenv("HIVE_METASTORE_HOST", "hive-metastore")
    port = int(os.getenv("HIVE_METASTORE_PORT", "9083"))
    _check_socket_service("Hive Metastore", host, port)


def _check_trino() -> None:
    trino_host = os.getenv("TRINO_HOST", "trino")
    trino_port = os.getenv("TRINO_PORT", "8080")
    _check_http_service("Trino", f"http://{trino_host}:{trino_port}/v1/info")


def _check_metricforge_api() -> None:
    api_url = os.getenv("METRICFORGE_API_URL", "http://metricforge-api:8000")
    _check_http_service("MetricForge API", f"{api_url}/health")


def _run_spark_script(script_name: str) -> None:
    script_path = f"/opt/airflow/spark/{script_name}"
    subprocess.run(["python", script_path], check=True)


def _validate_semantic_layer() -> None:
    api_url = os.getenv("METRICFORGE_API_URL", "http://metricforge-api:8000")
    response = requests.post(f"{api_url}/validate", timeout=30)
    response.raise_for_status()
    payload = response.json()
    print(f"Validation payload: {payload}")
    if not payload.get("is_valid", False):
        raise RuntimeError(f"Semantic layer validation failed: {payload.get('errors', [])}")


def _generate_metric_catalog() -> None:
    api_url = os.getenv("METRICFORGE_API_URL", "http://metricforge-api:8000")
    output_path = Path("/opt/airflow/include/generated_metric_catalog.json")
    response = requests.get(f"{api_url}/metrics", timeout=30)
    response.raise_for_status()
    payload = response.json()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Generated metric catalog with {len(payload.get('metrics', []))} metrics.")


def _refresh_druid_datasources() -> None:
    druid_url = os.getenv("DRUID_BROKER_URL", "http://druid:8888").rstrip("/")
    spec_dir = Path("/opt/airflow/druid/ingestion_specs")
    health_response = requests.get(f"{druid_url}/status/health", timeout=20)
    health_response.raise_for_status()

    for spec_path in sorted(spec_dir.glob("*.json")):
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
        response = requests.post(f"{druid_url}/druid/indexer/v1/task", json=payload, timeout=60)
        response.raise_for_status()
        print(f"Submitted Druid ingestion spec: {spec_path.name}")


def _build_druid_aggregates() -> None:
    _run_spark_script("04_build_druid_aggregates.py")


def _run_sample_metric_query() -> None:
    api_url = os.getenv("METRICFORGE_API_URL", "http://metricforge-api:8000")
    payload = {
        "metric": "daily_zone_revenue",
        "group_by": ["pickup_zone"],
        "time_grain": "day",
        "start_date": "2024-01-01",
        "end_date": "2024-02-01",
        "execute": False,
        "engine": "druid",
    }
    response = requests.post(f"{api_url}/query", json=payload, timeout=60)
    response.raise_for_status()
    print(f"Sample metric query response: {response.json()}")


if DAG and PythonOperator and BashOperator:
    with DAG(
        dag_id="metricforge_full_pipeline",
        description="Minerva-like orchestration DAG for the full MetricForge NYC demo",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=["metricforge", "demo", "minerva-like"],
    ) as dag:
        check_minio = PythonOperator(task_id="check_minio", python_callable=_check_minio)
        check_hive_metastore = PythonOperator(
            task_id="check_hive_metastore",
            python_callable=_check_hive_metastore,
        )
        check_trino = PythonOperator(task_id="check_trino", python_callable=_check_trino)
        check_metricforge_api = PythonOperator(
            task_id="check_metricforge_api",
            python_callable=_check_metricforge_api,
        )
        load_source_files_to_minio = BashOperator(
            task_id="load_source_files_to_minio",
            bash_command="python /opt/airflow/scripts/load_nyc_taxi_to_minio.py",
        )
        ingest_nyc_taxi_data = PythonOperator(
            task_id="ingest_nyc_taxi_data",
            python_callable=lambda: _run_spark_script("02_ingest_raw_taxi_data.py"),
        )
        build_certified_tables = PythonOperator(
            task_id="build_certified_tables",
            python_callable=lambda: _run_spark_script("03_build_certified_tables.py"),
        )
        validate_semantic_layer = PythonOperator(
            task_id="validate_semantic_layer",
            python_callable=_validate_semantic_layer,
        )
        generate_metric_catalog = PythonOperator(
            task_id="generate_metric_catalog",
            python_callable=_generate_metric_catalog,
        )
        build_druid_aggregates = PythonOperator(
            task_id="build_druid_aggregates",
            python_callable=_build_druid_aggregates,
        )
        refresh_druid_datasources = PythonOperator(
            task_id="refresh_druid_datasources",
            python_callable=_refresh_druid_datasources,
        )
        run_sample_metric_query = PythonOperator(
            task_id="run_sample_metric_query",
            python_callable=_run_sample_metric_query,
        )

        check_minio >> load_source_files_to_minio
        check_hive_metastore >> build_certified_tables
        check_trino >> check_metricforge_api
        check_metricforge_api >> validate_semantic_layer
        load_source_files_to_minio >> ingest_nyc_taxi_data
        ingest_nyc_taxi_data >> build_certified_tables
        build_certified_tables >> validate_semantic_layer
        validate_semantic_layer >> generate_metric_catalog
        build_certified_tables >> build_druid_aggregates
        generate_metric_catalog >> refresh_druid_datasources
        build_druid_aggregates >> refresh_druid_datasources
        refresh_druid_datasources >> run_sample_metric_query
else:
    dag = None

"""Airflow DAG for refreshing required Druid datasources."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import requests

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # pragma: no cover - optional dependency for this stage
    DAG = None
    PythonOperator = None


def _refresh_druid_datasources() -> None:
    """Submit Druid ingestion specs and fail if Druid is not reachable."""
    druid_url = os.getenv("DRUID_BROKER_URL", "http://druid:8888").rstrip("/")
    spec_dir = Path("/opt/airflow/druid/ingestion_specs")

    health_response = requests.get(f"{druid_url}/status/health", timeout=20)
    health_response.raise_for_status()

    for spec_path in sorted(spec_dir.glob("*.json")):
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
        response = requests.post(f"{druid_url}/druid/indexer/v1/task", json=payload, timeout=60)
        response.raise_for_status()
        print(f"Submitted Druid ingestion spec: {spec_path.name}")


if DAG and PythonOperator:
    with DAG(
        dag_id="refresh_druid_datasources",
        description="Refresh required Druid datasources for OLAP serving",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=["metricforge", "druid", "olap"],
    ) as dag:
        refresh_task = PythonOperator(
            task_id="refresh_druid_datasources",
            python_callable=_refresh_druid_datasources,
        )
else:
    dag = None

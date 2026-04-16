"""Airflow DAG for exporting the MetricForge NYC metric catalog."""

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


def _refresh_catalog() -> None:
    """Fetch the metric catalog from the API and write it to Airflow include."""
    api_url = os.getenv("METRICFORGE_API_URL", "http://metricforge-api:8000")
    output_path = Path("/opt/airflow/include/generated_metric_catalog.json")

    response = requests.get(f"{api_url}/metrics", timeout=30)
    response.raise_for_status()
    payload = response.json()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload.get('metrics', []))} metrics to {output_path}")


if DAG and PythonOperator:
    with DAG(
        dag_id="refresh_metric_catalog",
        description="Refresh metric catalog metadata",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=["metricforge", "catalog", "metadata"],
    ) as dag:
        refresh_task = PythonOperator(
            task_id="refresh_metric_catalog",
            python_callable=_refresh_catalog,
        )
else:
    dag = None

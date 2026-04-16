"""Airflow DAG for validating the MetricForge NYC semantic layer."""

from __future__ import annotations

import os
from datetime import datetime

import requests

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # pragma: no cover - optional dependency for this stage
    DAG = None
    PythonOperator = None


def _validate_semantic_layer() -> None:
    """Call the MetricForge API validation endpoint and fail on semantic errors."""
    api_url = os.getenv("METRICFORGE_API_URL", "http://metricforge-api:8000")
    response = requests.post(f"{api_url}/validate", timeout=30)
    response.raise_for_status()
    payload = response.json()
    print(f"Validation payload: {payload}")
    if not payload.get("is_valid", False):
        raise RuntimeError(f"Semantic layer validation failed: {payload.get('errors', [])}")


if DAG and PythonOperator:
    with DAG(
        dag_id="validate_semantic_layer",
        description="Validate semantic layer definitions through the MetricForge API",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=["metricforge", "semantic-layer", "validation"],
    ) as dag:
        validate_task = PythonOperator(
            task_id="validate_semantic_layer",
            python_callable=_validate_semantic_layer,
        )
else:
    dag = None

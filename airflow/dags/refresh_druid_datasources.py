"""Airflow DAG for refreshing required Druid datasources.

The DAG has two sequential steps:

1. build_druid_aggregates: runs the Spark job that writes the pre-aggregated
   JSON files to the shared `DRUID_INPUT_DIR` (default /opt/shared/input),
   mounted both in Airflow and in all Druid services via the `druid_shared`
   volume.
2. submit_ingestion_specs: POSTs the JSON specs from
   `druid/ingestion_specs/` to the Druid overlord so Druid ingests the files.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import requests

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # pragma: no cover - optional dependency for this stage
    DAG = None
    PythonOperator = None


def _build_druid_aggregates() -> None:
    """Run the Spark job that writes the Druid input JSON files."""
    script_path = "/opt/airflow/spark/04_build_druid_aggregates.py"
    run_real_spark = os.getenv("METRICFORGE_RUN_SPARK_IN_AIRFLOW", "false").lower() == "true"
    if not run_real_spark:
        print(
            "Airflow demo mode: Druid pre-aggregates are documented but not "
            "executed inside the container."
        )
        print(f"Would run: python {script_path}")
        return

    subprocess.run(["python", script_path], check=True)


def _submit_druid_specs() -> None:
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
        build_aggregates_task = PythonOperator(
            task_id="build_druid_aggregates",
            python_callable=_build_druid_aggregates,
        )
        submit_specs_task = PythonOperator(
            task_id="submit_druid_specs",
            python_callable=_submit_druid_specs,
        )
        build_aggregates_task >> submit_specs_task
else:
    dag = None

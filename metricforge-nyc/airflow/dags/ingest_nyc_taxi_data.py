"""Airflow DAG for staging raw NYC taxi data for MetricForge NYC."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # pragma: no cover - optional dependency for this stage
    DAG = None
    PythonOperator = None


def _run_ingestion() -> None:
    """Run or document the raw ingestion step."""
    script_path = "/opt/airflow/spark/02_ingest_raw_taxi_data.py"
    run_real_spark = os.getenv("METRICFORGE_RUN_SPARK_IN_AIRFLOW", "false").lower() == "true"
    if not run_real_spark:
        print(
            "Airflow demo mode: Spark ingestion is documented but not executed inside the container."
        )
        print(f"Would run: python {script_path}")
        return

    subprocess.run(["python", script_path], check=True)


if DAG and PythonOperator:
    with DAG(
        dag_id="ingest_nyc_taxi_data",
        description="Stage raw NYC taxi data for MetricForge NYC",
        start_date=datetime(2024, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["metricforge", "nyc-taxi", "ingestion"],
    ) as dag:
        ingest_task = PythonOperator(
            task_id="ingest_nyc_taxi_data",
            python_callable=_run_ingestion,
        )
else:
    dag = None

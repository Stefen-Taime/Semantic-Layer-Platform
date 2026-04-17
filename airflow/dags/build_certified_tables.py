"""Airflow DAG for building MetricForge NYC certified tables."""

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


def _build_tables() -> None:
    """Run or document the certified table build step."""
    script_path = "/opt/airflow/spark/03_build_certified_tables.py"
    run_real_spark = os.getenv("METRICFORGE_RUN_SPARK_IN_AIRFLOW", "false").lower() == "true"
    if not run_real_spark:
        print(
            "Airflow demo mode: certified Spark tables are documented but not executed inside the container."
        )
        print(f"Would run: python {script_path}")
        return

    subprocess.run(["python", script_path], check=True)


if DAG and PythonOperator:
    with DAG(
        dag_id="build_certified_tables",
        description="Build certified tables for MetricForge NYC",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        max_active_runs=1,
        tags=["metricforge", "spark", "certified"],
    ) as dag:
        build_task = PythonOperator(
            task_id="build_certified_tables",
            python_callable=_build_tables,
        )
else:
    dag = None

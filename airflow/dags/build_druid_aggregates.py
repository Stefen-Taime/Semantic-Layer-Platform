"""Airflow DAG for building Druid pre-aggregated JSON files.

Runs the Spark job `spark/04_build_druid_aggregates.py`, which reads the
certified fact table and writes two newline-delimited JSON files expected by
the Druid ingestion specs (taxi_daily_metrics_*.json and
taxi_zone_metrics_*.json).
"""

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


def _build_druid_aggregates() -> None:
    """Run or document the Druid pre-aggregate Spark job."""
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


if DAG and PythonOperator:
    with DAG(
        dag_id="build_druid_aggregates",
        description="Build pre-aggregated JSON files consumed by Druid ingestion",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        max_active_runs=1,
        tags=["metricforge", "spark", "druid"],
    ) as dag:
        build_task = PythonOperator(
            task_id="build_druid_aggregates",
            python_callable=_build_druid_aggregates,
        )
else:
    dag = None

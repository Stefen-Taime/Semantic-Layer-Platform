"""Airflow DAG for loading NYC TLC source files into MinIO then Spark raw tables."""

from __future__ import annotations

import subprocess
from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator
except ImportError:  # pragma: no cover - optional dependency for this stage
    DAG = None
    BashOperator = None
    PythonOperator = None


def _run_spark_raw_ingestion() -> None:
    """Run Spark ingestion from MinIO raw objects into Hive raw tables."""
    subprocess.run(["python", "/opt/airflow/spark/02_ingest_raw_taxi_data.py"], check=True)


if DAG and PythonOperator and BashOperator:
    with DAG(
        dag_id="ingest_nyc_taxi_data",
        description="Download source TLC data into MinIO and ingest it into Spark raw tables",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        max_active_runs=1,
        tags=["metricforge", "nyc-taxi", "ingestion"],
    ) as dag:
        load_source_files_to_minio = BashOperator(
            task_id="load_source_files_to_minio",
            bash_command="python /opt/airflow/scripts/load_nyc_taxi_to_minio.py",
        )
        ingest_raw_tables = PythonOperator(
            task_id="ingest_raw_tables",
            python_callable=_run_spark_raw_ingestion,
        )
        load_source_files_to_minio >> ingest_raw_tables
else:
    dag = None

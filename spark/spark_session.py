"""Spark session factory for MetricForge NYC batch processing."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from spark.config import (
    get_local_spark_state_dir,
    get_minio_access_key,
    get_minio_logs_bucket,
    get_minio_endpoint,
    get_minio_raw_bucket,
    get_minio_region,
    get_minio_secret_key,
    get_minio_secure,
    get_minio_warehouse_bucket,
    get_warehouse_uri,
)

if TYPE_CHECKING:  # pragma: no cover
    from pyspark.sql import SparkSession


def get_spark_runtime_settings() -> Dict[str, Any]:
    """Read Spark runtime settings from environment variables."""
    local_state_dir = get_local_spark_state_dir()
    return {
        "master": os.getenv("SPARK_MASTER", "local[2]"),
        "driver_memory": os.getenv("SPARK_DRIVER_MEMORY", "3g"),
        "shuffle_partitions": os.getenv("SPARK_SQL_SHUFFLE_PARTITIONS", "4"),
        "warehouse_uri": get_warehouse_uri(),
        "session_timezone": "UTC",
        "local_state_dir": local_state_dir,
        "minio_endpoint": get_minio_endpoint(),
        "minio_access_key": get_minio_access_key(),
        "minio_secret_key": get_minio_secret_key(),
        "minio_raw_bucket": get_minio_raw_bucket(),
        "minio_warehouse_bucket": get_minio_warehouse_bucket(),
        "minio_logs_bucket": get_minio_logs_bucket(),
        "minio_region": get_minio_region(),
        "minio_secure": get_minio_secure(),
        "jars_packages": os.getenv("SPARK_JARS_PACKAGES", ""),
    }


def create_spark_session(app_name: str = "MetricForgeNYC") -> "SparkSession":
    """Create a local SparkSession with Hive support enabled.

    The session is configured for compact local execution so the same code can
    run on a laptop with a small sample and later on a modest GCP VM.
    """

    from pyspark.sql import SparkSession

    settings = get_spark_runtime_settings()
    local_state_dir = settings["local_state_dir"]
    local_state_dir.mkdir(parents=True, exist_ok=True)

    derby_home = local_state_dir / "derby"
    derby_home.mkdir(parents=True, exist_ok=True)
    log_level = os.getenv("SPARK_LOG_LEVEL", "WARN")

    builder = (
        SparkSession.builder.appName(app_name)
        .master(settings["master"])
        .config("spark.driver.memory", settings["driver_memory"])
        .config("spark.sql.shuffle.partitions", settings["shuffle_partitions"])
        .config("spark.sql.warehouse.dir", settings["warehouse_uri"])
        .config("spark.sql.catalogImplementation", "hive")
        .config("spark.sql.session.timeZone", settings["session_timezone"])
        .config("spark.ui.showConsoleProgress", "true")
        .config("spark.hadoop.fs.s3a.endpoint", settings["minio_endpoint"])
        .config("spark.hadoop.fs.s3a.access.key", settings["minio_access_key"])
        .config("spark.hadoop.fs.s3a.secret.key", settings["minio_secret_key"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", str(settings["minio_secure"]).lower())
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.endpoint.region", settings["minio_region"])
        .config("hive.metastore.warehouse.dir", settings["warehouse_uri"])
        .config("spark.driver.extraJavaOptions", f"-Dderby.system.home={_quote_for_java(derby_home)}")
        .config("spark.executor.extraJavaOptions", f"-Dderby.system.home={_quote_for_java(derby_home)}")
    )

    if settings["jars_packages"]:
        builder = builder.config("spark.jars.packages", settings["jars_packages"])

    spark = builder.enableHiveSupport().getOrCreate()
    spark.sparkContext.setLogLevel(log_level)
    return spark


def _quote_for_java(path: Path) -> str:
    """Normalize a filesystem path for Java option usage."""
    return str(path.resolve())

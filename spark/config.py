"""Shared configuration for MetricForge NYC Spark batch jobs."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_NAME = "metricforge"

RAW_TRIPS_TABLE = f"{DATABASE_NAME}.raw_yellow_taxi_trips"
RAW_ZONE_LOOKUP_TABLE = f"{DATABASE_NAME}.raw_taxi_zone_lookup"
FACT_TRIPS_TABLE = f"{DATABASE_NAME}.fct_taxi_trips"
DIM_ZONE_TABLE = f"{DATABASE_NAME}.dim_zone"
DIM_PAYMENT_TYPE_TABLE = f"{DATABASE_NAME}.dim_payment_type"
DIM_DATE_TABLE = f"{DATABASE_NAME}.dim_date"


def get_local_spark_state_dir() -> Path:
    """Return the local directory used for Derby and Spark scratch metadata."""
    return (PROJECT_ROOT / ".local" / "spark").resolve()


def get_minio_endpoint() -> str:
    """Return the MinIO endpoint used by Spark S3A."""
    return os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000")


def get_minio_access_key() -> str:
    """Return the MinIO access key."""
    return os.getenv("MINIO_ACCESS_KEY", "metricforge")


def get_minio_secret_key() -> str:
    """Return the MinIO secret key."""
    return os.getenv("MINIO_SECRET_KEY", "metricforge123")


def get_minio_bucket() -> str:
    """Return the legacy MinIO bucket value when a single bucket is used."""
    return os.getenv("MINIO_BUCKET", "")


def get_minio_raw_bucket() -> str:
    """Return the MinIO bucket used for raw landing data."""
    return os.getenv("MINIO_RAW_BUCKET", get_minio_bucket() or "metricforge-raw")


def get_minio_curated_bucket() -> str:
    """Return the MinIO bucket used for curated exports."""
    return os.getenv("MINIO_CURATED_BUCKET", get_minio_bucket() or "metricforge-curated")


def get_minio_warehouse_bucket() -> str:
    """Return the MinIO bucket used for Hive warehouse data."""
    return os.getenv("MINIO_WAREHOUSE_BUCKET", get_minio_bucket() or "metricforge-warehouse")


def get_minio_logs_bucket() -> str:
    """Return the MinIO bucket used for application logs."""
    return os.getenv("MINIO_LOGS_BUCKET", get_minio_bucket() or "metricforge-logs")


def get_minio_region() -> str:
    """Return the MinIO region used by the S3A client."""
    return os.getenv("MINIO_REGION", "us-east-1")


def get_minio_raw_prefix() -> str:
    """Return the object prefix used for raw source files."""
    return os.getenv("MINIO_RAW_PREFIX", "nyc_taxi").strip("/")


def get_minio_secure() -> bool:
    """Return whether MinIO should be accessed over TLS."""
    return os.getenv("MINIO_SECURE", "false").lower() in {"1", "true", "yes"}


def get_tripdata_months() -> list[str]:
    """Return the list of TLC Yellow Taxi months expected in raw storage."""
    raw_value = os.getenv("TLC_TRIPDATA_MONTHS", "2026-01,2026-02")
    months = [value.strip() for value in raw_value.split(",") if value.strip()]
    if not months:
        raise ValueError("TLC_TRIPDATA_MONTHS must contain at least one YYYY-MM entry.")
    return months


def build_tripdata_filename(month: str) -> str:
    """Return the parquet filename for a TLC Yellow Taxi month."""
    return f"yellow_tripdata_{month}.parquet"


def get_raw_tripdata_uris() -> list[str]:
    """Return the S3A URIs for the configured Yellow Taxi parquet objects."""
    return [
        f"s3a://{get_minio_raw_bucket()}/{get_minio_raw_prefix()}/{build_tripdata_filename(month)}"
        for month in get_tripdata_months()
    ]


def get_taxi_zone_lookup_uri() -> str:
    """Return the S3A URI for the taxi zone lookup CSV object."""
    return f"s3a://{get_minio_raw_bucket()}/{get_minio_raw_prefix()}/taxi_zone_lookup.csv"


def get_warehouse_uri() -> str:
    """Return the configured Hive warehouse URI."""
    return os.getenv("SPARK_WAREHOUSE_DIR", f"s3a://{get_minio_warehouse_bucket()}/")


def get_database_location() -> str:
    """Return the database location URI for managed MetricForge tables."""
    return f"{get_warehouse_uri().rstrip('/')}/{DATABASE_NAME}.db"


def get_druid_input_dir() -> str:
    """Return the local directory where Druid ingestion JSON files are written.

    This must be mounted inside both the Airflow container (so Spark can write
    there) and the Druid containers (so Druid ingestion tasks can read from it).
    Defaults to `/opt/shared/input`, matching the `druid_shared` Docker volume
    mounted at `/opt/shared` inside every Druid service.
    """
    return os.getenv("DRUID_INPUT_DIR", "/opt/shared/input")

"""Utility helpers for MetricForge NYC Spark jobs."""

import re
from typing import Iterable, Mapping, Sequence

from spark.config import (
    DATABASE_NAME,
    get_database_location,
    get_raw_tripdata_uri,
    get_taxi_zone_lookup_uri,
    get_warehouse_uri,
)


def to_snake_case(value: str) -> str:
    """Convert a column name to snake_case."""
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = value.replace(" ", "_").replace("-", "_")
    value = re.sub(r"__+", "_", value)
    return value.lower().strip("_")


def normalize_columns(df, rename_map: Mapping[str, str] | None = None):
    """Rename DataFrame columns using explicit mappings then snake_case fallback."""
    rename_map = rename_map or {}
    normalized = df
    for column_name in df.columns:
        target_name = rename_map.get(column_name, to_snake_case(column_name))
        if target_name != column_name:
            normalized = normalized.withColumnRenamed(column_name, target_name)
    return normalized


def build_missing_input_message(missing_uris: Iterable[str]) -> str:
    """Build a clear error message for missing MinIO source objects."""
    missing_list = "\n".join(f"- {uri}" for uri in missing_uris)
    return (
        "Required MinIO source objects were not found.\n"
        f"{missing_list}\n\n"
        "Expected MinIO objects:\n"
        f"- {get_raw_tripdata_uri()}\n"
        f"- {get_taxi_zone_lookup_uri()}\n\n"
        "Upload guidance:\n"
        "- Review scripts/download_nyc_taxi_data.sh\n"
        "- Create the bucket and upload the two source files under the raw/ prefix\n"
    )


def path_exists(spark, uri: str) -> bool:
    """Return True if the given Hadoop-compatible URI exists."""
    jvm = spark._jvm
    hadoop_conf = spark._jsc.hadoopConfiguration()
    path = jvm.org.apache.hadoop.fs.Path(uri)
    filesystem = path.getFileSystem(hadoop_conf)
    return filesystem.exists(path)


def ensure_path_exists(spark, uri: str) -> None:
    """Ensure a Hadoop-compatible path exists."""
    jvm = spark._jvm
    hadoop_conf = spark._jsc.hadoopConfiguration()
    path = jvm.org.apache.hadoop.fs.Path(uri)
    filesystem = path.getFileSystem(hadoop_conf)
    filesystem.mkdirs(path)


def ensure_raw_source_objects_exist(spark) -> None:
    """Raise an explicit error if the required MinIO objects are missing."""
    required_uris = [get_raw_tripdata_uri(), get_taxi_zone_lookup_uri()]
    missing_uris = [uri for uri in required_uris if not path_exists(spark, uri)]
    if missing_uris:
        raise FileNotFoundError(build_missing_input_message(missing_uris))


def ensure_database_exists(spark) -> None:
    """Create the project database in the configured Hive warehouse if needed."""
    warehouse_uri = get_warehouse_uri()
    database_location = get_database_location()
    ensure_path_exists(spark, warehouse_uri)
    spark.sql(
        f"""
        CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}
        COMMENT 'MetricForge NYC Hive catalog stored in MinIO'
        LOCATION '{database_location}'
        """
    )
    spark.catalog.setCurrentDatabase(DATABASE_NAME)


def require_tables(spark, table_names: Sequence[str], run_hint: str) -> None:
    """Ensure required Hive tables exist before continuing."""
    missing_tables = [table_name for table_name in table_names if not spark.catalog.tableExists(table_name)]
    if missing_tables:
        missing_list = ", ".join(missing_tables)
        raise RuntimeError(
            f"Missing required Hive tables: {missing_list}. {run_hint}"
        )

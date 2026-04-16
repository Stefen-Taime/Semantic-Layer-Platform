"""Create the local Hive database used by MetricForge NYC."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spark.config import DATABASE_NAME, get_database_location, get_warehouse_uri
from spark.spark_session import create_spark_session
from spark.utils import ensure_database_exists


def main() -> None:
    """Create the Hive database backed by the configured MinIO warehouse."""
    warehouse_uri = get_warehouse_uri()
    database_location = get_database_location()
    print("Creating Hive database for MetricForge NYC...")

    spark = create_spark_session("MetricForgeNYC-CreateHiveDatabase")
    try:
        ensure_database_exists(spark)

        print(f"Database ready: {DATABASE_NAME}")
        print(f"Warehouse URI: {warehouse_uri}")
        print(f"Database location: {database_location}")
        print("Existing databases:")
        spark.sql("SHOW DATABASES").show(truncate=False)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

"""Ingest raw NYC TLC files into Hive-managed Spark tables."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import DataFrame, functions as F

from spark.config import (
    RAW_TRIPS_TABLE,
    RAW_ZONE_LOOKUP_TABLE,
    get_raw_tripdata_uris,
    get_taxi_zone_lookup_uri,
)
from spark.spark_session import create_spark_session
from spark.utils import ensure_database_exists, ensure_raw_source_objects_exist


def load_trip_data(spark) -> DataFrame:
    """Read the configured Yellow Taxi parquet objects from MinIO."""
    return spark.read.parquet(*get_raw_tripdata_uris()).withColumn(
        "_source_file",
        F.input_file_name(),
    )


def load_zone_lookup(spark) -> DataFrame:
    """Read the taxi zone lookup CSV object from MinIO."""
    return (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(get_taxi_zone_lookup_uri())
        .withColumn("_loaded_at", F.current_timestamp())
    )


def main() -> None:
    """Ingest the raw parquet and CSV objects from MinIO into Hive-managed tables."""
    print("Starting raw data ingestion from MinIO into Spark/Hive...")

    spark = create_spark_session("MetricForgeNYC-IngestRawTaxiData")
    try:
        ensure_database_exists(spark)
        ensure_raw_source_objects_exist(spark)

        print("Reading trip data from:")
        for tripdata_uri in get_raw_tripdata_uris():
            print(f"- {tripdata_uri}")
        print(f"Reading zone lookup from: {get_taxi_zone_lookup_uri()}")

        trips_df = load_trip_data(spark)
        zones_df = load_zone_lookup(spark)

        trips_df.write.mode("overwrite").format("parquet").saveAsTable(RAW_TRIPS_TABLE)
        zones_df.write.mode("overwrite").format("parquet").saveAsTable(RAW_ZONE_LOOKUP_TABLE)

        print(f"Wrote table: {RAW_TRIPS_TABLE}")
        print(f"Number of lines raw taxi: {spark.table(RAW_TRIPS_TABLE).count()}")
        print("Schema raw taxi:")
        spark.table(RAW_TRIPS_TABLE).printSchema()

        print(f"Wrote table: {RAW_ZONE_LOOKUP_TABLE}")
        print(f"Number of lines taxi zones: {spark.table(RAW_ZONE_LOOKUP_TABLE).count()}")
        print("Schema taxi zones:")
        spark.table(RAW_ZONE_LOOKUP_TABLE).printSchema()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

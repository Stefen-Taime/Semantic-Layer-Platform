"""Build certified fact and dimension tables for MetricForge NYC."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import DataFrame, functions as F

from spark.config import (
    DIM_DATE_TABLE,
    DIM_PAYMENT_TYPE_TABLE,
    DIM_ZONE_TABLE,
    FACT_TRIPS_TABLE,
    RAW_TRIPS_TABLE,
    RAW_ZONE_LOOKUP_TABLE,
)
from spark.spark_session import create_spark_session
from spark.utils import ensure_database_exists, require_tables

PAYMENT_TYPE_LOOKUP = [
    (1, "Credit card"),
    (2, "Cash"),
    (3, "No charge"),
    (4, "Dispute"),
    (5, "Unknown"),
    (6, "Voided trip"),
]


def build_zone_dimension(raw_zones_df: DataFrame) -> DataFrame:
    """Create a clean zone dimension from the raw lookup data."""
    return (
        raw_zones_df.select(
            F.col("LocationID").cast("int").alias("location_id"),
            F.trim(F.col("Borough")).alias("borough"),
            F.trim(F.col("Zone")).alias("zone"),
            F.trim(F.col("service_zone")).alias("service_zone"),
        )
        .dropna(subset=["location_id"])
        .dropDuplicates(["location_id"])
    )


def build_payment_type_dimension(spark) -> DataFrame:
    """Create a static payment type dimension."""
    return spark.createDataFrame(
        PAYMENT_TYPE_LOOKUP,
        schema=["payment_type_id", "payment_type_name"],
    )

def build_fact_taxi_trips(raw_trips_df: DataFrame) -> DataFrame:
    """Create the certified trip fact table with normalized metric columns."""
    pickup_datetime = F.col("tpep_pickup_datetime").cast("timestamp")
    dropoff_datetime = F.col("tpep_dropoff_datetime").cast("timestamp")
    trip_duration_minutes = F.round(
        (
            F.unix_timestamp(dropoff_datetime)
            - F.unix_timestamp(pickup_datetime)
        )
        / F.lit(60.0),
        2,
    )

    trip_id_columns = [
        F.coalesce(F.col("VendorID").cast("string"), F.lit("null")),
        F.coalesce(pickup_datetime.cast("string"), F.lit("null")),
        F.coalesce(dropoff_datetime.cast("string"), F.lit("null")),
        F.coalesce(F.col("PULocationID").cast("string"), F.lit("null")),
        F.coalesce(F.col("DOLocationID").cast("string"), F.lit("null")),
        F.coalesce(F.col("total_amount").cast("string"), F.lit("null")),
    ]

    fact_df = raw_trips_df.select(
        F.sha2(F.concat_ws("||", *trip_id_columns), 256).alias("trip_id"),
        F.col("VendorID").cast("int").alias("vendor_id"),
        pickup_datetime.alias("pickup_datetime"),
        dropoff_datetime.alias("dropoff_datetime"),
        F.col("PULocationID").cast("int").alias("pickup_location_id"),
        F.col("DOLocationID").cast("int").alias("dropoff_location_id"),
        F.col("passenger_count").cast("double").alias("passenger_count"),
        F.col("trip_distance").cast("double").alias("trip_distance"),
        F.col("fare_amount").cast("double").alias("fare_amount"),
        F.col("tip_amount").cast("double").alias("tip_amount"),
        F.col("tolls_amount").cast("double").alias("tolls_amount"),
        F.col("total_amount").cast("double").alias("total_amount"),
        F.col("payment_type").cast("int").alias("payment_type_id"),
        trip_duration_minutes.alias("trip_duration_minutes"),
        F.to_date(pickup_datetime).alias("pickup_date"),
        F.year(pickup_datetime).alias("pickup_year"),
        F.month(pickup_datetime).alias("pickup_month"),
        F.dayofmonth(pickup_datetime).alias("pickup_day"),
    )

    return fact_df.withColumn(
        "is_valid_trip",
        (
            (F.col("total_amount") > 0)
            & (F.col("fare_amount") >= 0)
            & (F.col("trip_distance") > 0)
            & (F.col("trip_duration_minutes") > 0)
            & F.col("pickup_datetime").isNotNull()
            & F.col("dropoff_datetime").isNotNull()
        ),
    )


def build_dim_date(fact_trips_df: DataFrame) -> DataFrame:
    """Create the date dimension from distinct pickup dates."""
    return (
        fact_trips_df.select(F.col("pickup_date").alias("full_date"))
        .dropna(subset=["full_date"])
        .dropDuplicates(["full_date"])
        .select(
            F.date_format("full_date", "yyyyMMdd").cast("int").alias("date_id"),
            F.col("full_date"),
            F.year("full_date").alias("year"),
            F.month("full_date").alias("month"),
            F.dayofmonth("full_date").alias("day"),
            F.weekofyear("full_date").alias("week_of_year"),
            F.dayofweek("full_date").alias("day_of_week"),
        )
        .orderBy("full_date")
    )


def main() -> None:
    """Build certified dimensions and fact tables from raw Hive tables."""
    print("Building certified tables...")
    spark = create_spark_session("MetricForgeNYC-BuildCertifiedTables")
    try:
        ensure_database_exists(spark)
        require_tables(
            spark,
            [RAW_TRIPS_TABLE, RAW_ZONE_LOOKUP_TABLE],
            run_hint=(
                "Run python spark/01_create_hive_database.py then "
                "python spark/02_ingest_raw_taxi_data.py first."
            ),
        )

        raw_trips_df = spark.table(RAW_TRIPS_TABLE)
        raw_zones_df = spark.table(RAW_ZONE_LOOKUP_TABLE)

        zone_dim_df = build_zone_dimension(raw_zones_df)
        payment_dim_df = build_payment_type_dimension(spark)
        fact_trips_df = build_fact_taxi_trips(raw_trips_df)
        date_dim_df = build_dim_date(fact_trips_df)

        zone_dim_df.write.mode("overwrite").format("parquet").saveAsTable(DIM_ZONE_TABLE)
        payment_dim_df.write.mode("overwrite").format("parquet").saveAsTable(DIM_PAYMENT_TYPE_TABLE)
        fact_trips_df.write.mode("overwrite").format("parquet").saveAsTable(FACT_TRIPS_TABLE)
        date_dim_df.write.mode("overwrite").format("parquet").saveAsTable(DIM_DATE_TABLE)

        print(f"Wrote table: {DIM_ZONE_TABLE}")
        print(f"Rows: {spark.table(DIM_ZONE_TABLE).count()}")
        spark.table(DIM_ZONE_TABLE).show(5, truncate=False)

        print(f"Wrote table: {DIM_PAYMENT_TYPE_TABLE}")
        print(f"Rows: {spark.table(DIM_PAYMENT_TYPE_TABLE).count()}")
        spark.table(DIM_PAYMENT_TYPE_TABLE).show(5, truncate=False)

        print(f"Wrote table: {FACT_TRIPS_TABLE}")
        print(f"Rows: {spark.table(FACT_TRIPS_TABLE).count()}")
        spark.table(FACT_TRIPS_TABLE).show(5, truncate=False)

        print(f"Wrote table: {DIM_DATE_TABLE}")
        print(f"Rows: {spark.table(DIM_DATE_TABLE).count()}")
        spark.table(DIM_DATE_TABLE).show(5, truncate=False)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

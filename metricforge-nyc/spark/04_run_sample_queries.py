"""Run validation queries against the local certified Spark/Hive tables."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spark.config import DIM_PAYMENT_TYPE_TABLE, DIM_ZONE_TABLE, FACT_TRIPS_TABLE
from spark.spark_session import create_spark_session
from spark.utils import ensure_database_exists, require_tables

SAMPLE_QUERIES = {
    "total_valid_trips": f"""
        SELECT COUNT(*) AS total_valid_trips
        FROM {FACT_TRIPS_TABLE}
        WHERE is_valid_trip = true
    """,
    "gross_revenue_by_day": f"""
        SELECT
            pickup_date AS day,
            ROUND(SUM(total_amount), 2) AS gross_revenue,
            COUNT(*) AS valid_trip_count
        FROM {FACT_TRIPS_TABLE}
        WHERE is_valid_trip = true
        GROUP BY pickup_date
        ORDER BY day
        LIMIT 10
    """,
    "average_fare_by_pickup_borough": f"""
        SELECT
            z.borough,
            ROUND(AVG(f.fare_amount), 2) AS average_fare
        FROM {FACT_TRIPS_TABLE} f
        LEFT JOIN {DIM_ZONE_TABLE} z
            ON f.pickup_location_id = z.location_id
        WHERE f.is_valid_trip = true
        GROUP BY z.borough
        ORDER BY average_fare DESC
        LIMIT 10
    """,
    "average_trip_distance_by_pickup_zone": f"""
        SELECT
            z.zone,
            ROUND(AVG(f.trip_distance), 2) AS average_trip_distance
        FROM {FACT_TRIPS_TABLE} f
        LEFT JOIN {DIM_ZONE_TABLE} z
            ON f.pickup_location_id = z.location_id
        WHERE f.is_valid_trip = true
        GROUP BY z.zone
        ORDER BY average_trip_distance DESC
        LIMIT 10
    """,
    "tip_rate_by_payment_type": f"""
        SELECT
            p.payment_type_name,
            ROUND(SUM(f.tip_amount) / NULLIF(SUM(f.fare_amount), 0), 4) AS tip_rate
        FROM {FACT_TRIPS_TABLE} f
        LEFT JOIN {DIM_PAYMENT_TYPE_TABLE} p
            ON f.payment_type_id = p.payment_type_id
        WHERE f.is_valid_trip = true
        GROUP BY p.payment_type_name
        ORDER BY tip_rate DESC
    """,
}


def main() -> None:
    """Execute a small set of validation queries and print the results."""
    print("Running sample validation queries...")
    spark = create_spark_session("MetricForgeNYC-RunSampleQueries")
    try:
        ensure_database_exists(spark)
        require_tables(
            spark,
            [DIM_ZONE_TABLE, DIM_PAYMENT_TYPE_TABLE, FACT_TRIPS_TABLE],
            run_hint=(
                "Run python spark/03_build_certified_tables.py after the raw ingestion step."
            ),
        )

        for query_name, sql in SAMPLE_QUERIES.items():
            print(f"\n=== {query_name} ===")
            spark.sql(sql).show(truncate=False)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

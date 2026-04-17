"""Build pre-aggregated JSON files consumed by Druid ingestion specs.

Druid native batch ingestion expects ready-to-load records. This job reads the
certified fact table `metricforge.fct_taxi_trips` joined with the `dim_zone`
and `dim_payment_type` dimensions, then produces two daily aggregates as
newline-delimited JSON:

- taxi_daily_metrics_YYYYMMDD.json : aggregated by pickup_date, pickup_borough,
  payment_type_name. Matches druid/ingestion_specs/taxi_daily_metrics_ingestion.json
- taxi_zone_metrics_YYYYMMDD.json  : aggregated by pickup_date, pickup_zone,
  pickup_borough. Matches druid/ingestion_specs/taxi_zone_metrics_ingestion.json

Output directory is controlled by the environment variable
`DRUID_INPUT_DIR`, which defaults to /opt/shared/input - the path mounted
inside the Druid containers (volume `druid_shared`).
"""

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime
from typing import Iterable

from pyspark.sql import DataFrame, functions as F

from spark.config import (
    DIM_PAYMENT_TYPE_TABLE,
    DIM_ZONE_TABLE,
    FACT_TRIPS_TABLE,
    get_druid_input_dir,
)
from spark.spark_session import create_spark_session
from spark.utils import require_tables


def build_daily_metrics(
    fact_df: DataFrame,
    zone_df: DataFrame,
    payment_df: DataFrame,
) -> DataFrame:
    """Aggregate valid trips per pickup_date / pickup_borough / payment_type_name."""
    enriched = (
        fact_df.filter(F.col("is_valid_trip"))
        .join(
            zone_df.select(
                F.col("location_id").alias("pickup_location_id"),
                F.col("borough").alias("pickup_borough"),
            ),
            on="pickup_location_id",
            how="left",
        )
        .join(payment_df, on="payment_type_id", how="left")
    )

    return (
        enriched.groupBy(
            F.col("pickup_date"),
            F.coalesce(F.col("pickup_borough"), F.lit("Unknown")).alias("pickup_borough"),
            F.coalesce(F.col("payment_type_name"), F.lit("Unknown")).alias(
                "payment_type_name"
            ),
        )
        .agg(
            F.count(F.lit(1)).cast("long").alias("completed_trips"),
            F.sum("total_amount").cast("double").alias("gross_revenue"),
            F.sum("tip_amount").cast("double").alias("total_tip_amount"),
            F.avg("fare_amount").cast("double").alias("average_fare"),
            F.avg("trip_distance").cast("double").alias("average_trip_distance"),
        )
        .select(
            F.date_format("pickup_date", "yyyy-MM-dd").alias("pickup_date"),
            "pickup_borough",
            "payment_type_name",
            "completed_trips",
            "gross_revenue",
            "total_tip_amount",
            "average_fare",
            "average_trip_distance",
        )
        .orderBy("pickup_date", "pickup_borough", "payment_type_name")
    )


def build_zone_metrics(fact_df: DataFrame, zone_df: DataFrame) -> DataFrame:
    """Aggregate valid trips per pickup_date / pickup_zone / pickup_borough."""
    enriched = fact_df.filter(F.col("is_valid_trip")).join(
        zone_df.select(
            F.col("location_id").alias("pickup_location_id"),
            F.col("zone").alias("pickup_zone"),
            F.col("borough").alias("pickup_borough"),
        ),
        on="pickup_location_id",
        how="left",
    )

    return (
        enriched.groupBy(
            F.col("pickup_date"),
            F.coalesce(F.col("pickup_zone"), F.lit("Unknown")).alias("pickup_zone"),
            F.coalesce(F.col("pickup_borough"), F.lit("Unknown")).alias("pickup_borough"),
        )
        .agg(
            F.count(F.lit(1)).cast("long").alias("completed_trips"),
            F.sum("total_amount").cast("double").alias("gross_revenue"),
            F.avg("trip_duration_minutes").cast("double").alias("average_trip_duration"),
            F.avg("trip_distance").cast("double").alias("average_trip_distance"),
        )
        .select(
            F.date_format("pickup_date", "yyyy-MM-dd").alias("pickup_date"),
            "pickup_zone",
            "pickup_borough",
            "completed_trips",
            "gross_revenue",
            "average_trip_duration",
            "average_trip_distance",
        )
        .orderBy("pickup_date", "pickup_borough", "pickup_zone")
    )


def _write_single_json_file(
    df: DataFrame,
    output_dir: Path,
    base_name: str,
    run_tag: str,
) -> Path:
    """Write a DataFrame as a single newline-delimited JSON file.

    Druid's local input source consumes `*.json` files from a directory, so the
    output is coalesced to one file and renamed to a stable filename. Any older
    files matching the same base name are removed so replays stay idempotent.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = output_dir / f".{base_name}_{run_tag}"

    # Remove stale staging directory from a previous failed run.
    if staging_dir.exists():
        for item in staging_dir.iterdir():
            item.unlink()
        staging_dir.rmdir()

    (
        df.coalesce(1)
        .write.mode("overwrite")
        .format("json")
        .save(f"file://{staging_dir.resolve()}")
    )

    json_parts = sorted(staging_dir.glob("part-*.json"))
    if not json_parts:
        raise RuntimeError(f"Spark did not produce any JSON part file in {staging_dir}")

    final_path = output_dir / f"{base_name}_{run_tag}.json"
    json_parts[0].replace(final_path)

    # Clean up the staging directory (leftover _SUCCESS, CRC files, etc.).
    for item in staging_dir.iterdir():
        item.unlink()
    staging_dir.rmdir()

    _purge_old_files(output_dir, base_name, keep=final_path)
    return final_path


def _purge_old_files(output_dir: Path, base_name: str, keep: Path) -> None:
    """Remove previous aggregate files for the same dataset, except `keep`."""
    for old in output_dir.glob(f"{base_name}_*.json"):
        if old.resolve() != keep.resolve():
            old.unlink()


def _iter_datasets(
    daily_df: DataFrame,
    zone_df: DataFrame,
) -> Iterable[tuple[str, DataFrame]]:
    yield "taxi_daily_metrics", daily_df
    yield "taxi_zone_metrics", zone_df


def main() -> None:
    """Build Druid pre-aggregated JSON files from the certified fact table."""
    print("Building Druid pre-aggregated JSON files...")
    spark = create_spark_session("MetricForgeNYC-BuildDruidAggregates")
    try:
        require_tables(
            spark,
            [FACT_TRIPS_TABLE, DIM_ZONE_TABLE, DIM_PAYMENT_TYPE_TABLE],
            run_hint=(
                "Run python spark/03_build_certified_tables.py before this job "
                "to populate the fact and dimension tables."
            ),
        )

        fact_df = spark.table(FACT_TRIPS_TABLE)
        zone_df = spark.table(DIM_ZONE_TABLE)
        payment_df = spark.table(DIM_PAYMENT_TYPE_TABLE)

        daily_df = build_daily_metrics(fact_df, zone_df, payment_df)
        zone_metrics_df = build_zone_metrics(fact_df, zone_df)

        output_dir = Path(get_druid_input_dir()).expanduser()
        run_tag = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        for base_name, df in _iter_datasets(daily_df, zone_metrics_df):
            row_count = df.count()
            print(f"Dataset {base_name}: {row_count} aggregated rows")
            final_path = _write_single_json_file(df, output_dir, base_name, run_tag)
            print(f"Wrote {final_path}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

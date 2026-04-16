"""Tests for the TLC source loader helpers without network access."""

from spark.source_loader import (
    DEFAULT_TLC_ZONE_LOOKUP_URL,
    build_raw_object_name,
    get_source_objects,
    normalize_minio_endpoint,
)


def test_normalize_minio_endpoint_strips_scheme() -> None:
    assert normalize_minio_endpoint("http://minio:9000") == "minio:9000"
    assert normalize_minio_endpoint("https://example.com") == "example.com"


def test_build_raw_object_name_uses_prefix(monkeypatch) -> None:
    monkeypatch.setenv("MINIO_RAW_PREFIX", "nyc_taxi")

    assert build_raw_object_name("yellow_tripdata_2026-01.parquet") == (
        "nyc_taxi/yellow_tripdata_2026-01.parquet"
    )


def test_get_source_objects_use_demo_defaults(monkeypatch) -> None:
    monkeypatch.delenv("TLC_TRIPDATA_MONTHS", raising=False)
    monkeypatch.delenv("TLC_TRIPDATA_URL_2026_01", raising=False)
    monkeypatch.delenv("TLC_TRIPDATA_URL_2026_02", raising=False)
    monkeypatch.delenv("TLC_ZONE_LOOKUP_URL", raising=False)

    source_objects = get_source_objects()

    assert source_objects[0].filename == "yellow_tripdata_2026-01.parquet"
    assert source_objects[1].filename == "yellow_tripdata_2026-02.parquet"
    assert source_objects[2].filename == "taxi_zone_lookup.csv"
    assert source_objects[0].url.endswith("yellow_tripdata_2026-01.parquet")
    assert source_objects[1].url.endswith("yellow_tripdata_2026-02.parquet")
    assert source_objects[2].url == DEFAULT_TLC_ZONE_LOOKUP_URL


def test_get_source_objects_follow_custom_month_list(monkeypatch) -> None:
    monkeypatch.setenv("TLC_TRIPDATA_MONTHS", "2025-12,2026-03")

    source_objects = get_source_objects()

    assert source_objects[0].filename == "yellow_tripdata_2025-12.parquet"
    assert source_objects[1].filename == "yellow_tripdata_2026-03.parquet"
    assert source_objects[2].filename == "taxi_zone_lookup.csv"

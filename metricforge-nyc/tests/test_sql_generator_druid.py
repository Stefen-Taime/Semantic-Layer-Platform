"""Tests for Druid SQL generation from semantic definitions."""

from pathlib import Path

from metrics_engine import generate_metric_sql, load_semantic_layer


def test_generate_daily_zone_revenue_druid_sql() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_semantic_layer(str(project_root / "semantic_layer"))

    sql = generate_metric_sql(
        config=config,
        metric_name="daily_zone_revenue",
        group_by=["pickup_zone"],
        time_grain="day",
        start_date="2024-01-01",
        end_date="2024-01-31",
        engine="druid",
    )

    assert "FROM metricforge_taxi_zone_metrics" in sql
    assert "TIME_FLOOR(__time, 'P1D')" in sql
    assert "GROUP BY" in sql


def test_generate_druid_sql_for_unconfigured_metric_raises() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_semantic_layer(str(project_root / "semantic_layer"))

    try:
        generate_metric_sql(
            config=config,
            metric_name="gross_revenue",
            group_by=["pickup_zone"],
            time_grain="day",
            engine="druid",
        )
    except ValueError as exc:
        assert "not configured for Druid" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected Druid SQL generation to fail for gross_revenue.")

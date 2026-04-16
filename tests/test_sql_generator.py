"""Tests for Spark SQL generation from semantic definitions."""

from pathlib import Path

from metrics_engine import generate_metric_sql, load_semantic_layer


def test_generate_gross_revenue_sql_by_pickup_zone_and_day() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_semantic_layer(str(project_root / "semantic_layer"))

    sql = generate_metric_sql(
        config=config,
        metric_name="gross_revenue",
        group_by=["pickup_zone"],
        time_grain="day",
        start_date="2024-01-01",
        end_date="2024-01-31",
    )

    assert "SUM(" in sql
    assert "total_amount" in sql
    assert "DATE_TRUNC('DAY'" in sql
    assert "JOIN metricforge.dim_zone pickup_zone_dim" in sql
    assert "GROUP BY" in sql


def test_generate_tip_rate_sql_contains_case_when() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_semantic_layer(str(project_root / "semantic_layer"))

    sql = generate_metric_sql(
        config=config,
        metric_name="tip_rate",
        group_by=["payment_type"],
        time_grain="day",
    )

    assert "CASE WHEN" in sql
    assert "SUM(" in sql
    assert "tip_amount" in sql
    assert "total_amount" in sql


def test_generate_druid_sql_for_daily_zone_revenue() -> None:
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
    assert "SUM(gross_revenue)" in sql
    assert "GROUP BY" in sql

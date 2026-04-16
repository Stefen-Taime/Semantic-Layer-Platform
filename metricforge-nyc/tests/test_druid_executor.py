"""Tests for Druid executor helpers without a live Druid cluster."""

from metrics_engine.executors.druid_executor import DruidExecutor, ensure_druid_limit


def test_druid_executor_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("DRUID_BROKER_URL", "http://druid:8888")
    monkeypatch.setenv("DRUID_DEFAULT_DATASOURCE", "metricforge_taxi_daily_metrics")

    executor = DruidExecutor()

    assert executor.broker_url == "http://druid:8888"
    assert executor.default_datasource == "metricforge_taxi_daily_metrics"


def test_ensure_druid_limit_adds_limit_when_missing() -> None:
    sql = "SELECT * FROM metricforge_taxi_daily_metrics"

    limited_sql = ensure_druid_limit(sql, limit=25)

    assert limited_sql.endswith("LIMIT 25")


def test_ensure_druid_limit_keeps_existing_limit() -> None:
    sql = "SELECT * FROM metricforge_taxi_daily_metrics LIMIT 10"

    limited_sql = ensure_druid_limit(sql, limit=25)

    assert limited_sql == sql

"""Tests for Trino executor configuration helpers."""

from metrics_engine.executors.trino_executor import TrinoExecutor, ensure_query_limit


def test_trino_executor_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("TRINO_HOST", "trino")
    monkeypatch.setenv("TRINO_PORT", "8080")
    monkeypatch.setenv("TRINO_USER", "metricforge")
    monkeypatch.setenv("TRINO_CATALOG", "hive")
    monkeypatch.setenv("TRINO_SCHEMA", "metricforge")

    executor = TrinoExecutor()

    assert executor.host == "trino"
    assert executor.port == 8080
    assert executor.user == "metricforge"
    assert executor.catalog == "hive"
    assert executor.schema == "metricforge"


def test_ensure_query_limit_adds_limit_when_missing() -> None:
    sql = "SELECT * FROM hive.metricforge.fct_taxi_trips"

    limited_sql = ensure_query_limit(sql, limit=25)

    assert limited_sql.endswith("LIMIT 25")


def test_ensure_query_limit_keeps_existing_limit() -> None:
    sql = "SELECT * FROM hive.metricforge.fct_taxi_trips LIMIT 10"

    limited_sql = ensure_query_limit(sql, limit=25)

    assert limited_sql == sql

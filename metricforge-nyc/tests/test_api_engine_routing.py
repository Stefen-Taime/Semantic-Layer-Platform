"""Tests for API engine routing without live engines."""

from fastapi.testclient import TestClient

from api.main import app, get_default_query_engine


def test_default_engine_can_be_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("QUERY_ENGINE", "trino")
    assert get_default_query_engine() == "trino"


def test_execute_false_with_trino_engine_returns_sql_without_live_trino() -> None:
    client = TestClient(app)

    response = client.post(
        "/query",
        json={
            "metric": "gross_revenue",
            "group_by": ["pickup_zone"],
            "time_grain": "day",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "execute": False,
            "engine": "trino",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] == "trino"
    assert "DATE_TRUNC('day'" in payload["sql"]
    assert payload["data"] == []


def test_execute_false_with_druid_metric_uses_druid_sql_without_live_druid() -> None:
    client = TestClient(app)

    response = client.post(
        "/query",
        json={
            "metric": "daily_zone_revenue",
            "group_by": ["pickup_zone"],
            "time_grain": "day",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "execute": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] == "druid"
    assert "TIME_FLOOR(__time, 'P1D')" in payload["sql"]
    assert "FROM metricforge_taxi_zone_metrics" in payload["sql"]
    assert payload["data"] == []


def test_engines_endpoint_lists_supported_engines() -> None:
    client = TestClient(app)

    response = client.get("/engines")

    assert response.status_code == 200
    payload = response.json()
    assert payload["available_engines"] == ["spark", "trino", "druid"]

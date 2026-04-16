"""Druid executor for MetricForge NYC."""

from __future__ import annotations

import os
import re
from typing import Any

import requests

LIMIT_PATTERN = re.compile(r"\blimit\s+\d+\s*;?\s*$", re.IGNORECASE | re.DOTALL)


def ensure_druid_limit(sql: str, limit: int = 100) -> str:
    """Append a LIMIT clause if the query does not already end with one."""
    cleaned_sql = sql.strip()
    if LIMIT_PATTERN.search(cleaned_sql):
        return cleaned_sql
    return f"{cleaned_sql}\nLIMIT {limit}"


class DruidExecutor:
    """Execute generated SQL against the Druid SQL API."""

    def __init__(self, broker_url: str | None = None, default_datasource: str | None = None) -> None:
        self.broker_url = (broker_url or os.getenv("DRUID_BROKER_URL", "http://localhost:8888")).rstrip("/")
        self.default_datasource = default_datasource or os.getenv(
            "DRUID_DEFAULT_DATASOURCE",
            "metricforge_taxi_daily_metrics",
        )

    def execute_sql(self, sql: str, limit: int = 100) -> list[dict[str, Any]]:
        """Execute SQL against Druid and return row dictionaries."""
        query_sql = ensure_druid_limit(sql, limit=limit)
        endpoint = f"{self.broker_url}/druid/v2/sql"
        payload = {"query": query_sql, "resultFormat": "object"}

        try:
            response = requests.post(endpoint, json=payload, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - depends on live Druid
            raise RuntimeError(f"Druid query execution failed: {exc}") from exc

        result = response.json()
        if not isinstance(result, list):
            raise RuntimeError("Druid SQL API returned an unexpected payload.")
        return [row for row in result if isinstance(row, dict)]

    def test_connection(self) -> dict[str, Any]:
        """Return a simple connectivity payload for Druid."""
        try:
            rows = self.execute_sql("SELECT 1 AS druid_ok", limit=1)
            return {
                "engine": "druid",
                "status": "ok",
                "broker_url": self.broker_url,
                "default_datasource": self.default_datasource,
                "rows": rows,
            }
        except Exception as exc:  # pragma: no cover - depends on live Druid
            return {
                "engine": "druid",
                "status": "error",
                "broker_url": self.broker_url,
                "default_datasource": self.default_datasource,
                "message": str(exc),
            }

"""Trino executor for MetricForge NYC."""

from __future__ import annotations

import os
import re
from typing import Any


LIMIT_PATTERN = re.compile(r"\blimit\s+\d+\s*;?\s*$", re.IGNORECASE | re.DOTALL)


def ensure_query_limit(sql: str, limit: int = 100) -> str:
    """Append a LIMIT clause if the query does not already end with one."""
    cleaned_sql = sql.strip()
    if LIMIT_PATTERN.search(cleaned_sql):
        return cleaned_sql
    return f"{cleaned_sql}\nLIMIT {limit}"


class TrinoExecutor:
    """Execute generated SQL against Trino via the Python client."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        catalog: str | None = None,
        schema: str | None = None,
    ) -> None:
        self.host = host or os.getenv("TRINO_HOST", "localhost")
        self.port = int(port or os.getenv("TRINO_PORT", "8080"))
        self.user = user or os.getenv("TRINO_USER", "metricforge")
        self.catalog = catalog or os.getenv("TRINO_CATALOG", "hive")
        self.schema = schema or os.getenv("TRINO_SCHEMA", "metricforge")

    def execute_query(self, sql: str, limit: int = 100) -> list[dict[str, Any]]:
        """Execute a SQL query in Trino and return row dictionaries."""
        query_sql = ensure_query_limit(sql, limit=limit)
        trino = self._import_client()

        connection = None
        cursor = None
        try:
            connection = trino.dbapi.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                catalog=self.catalog,
                schema=self.schema,
            )
            cursor = connection.cursor()
            cursor.execute(query_sql)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description or []]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:  # pragma: no cover - depends on live Trino
            raise RuntimeError(f"Trino query execution failed: {exc}") from exc
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    def test_connection(self) -> dict[str, Any]:
        """Return a simple Trino connectivity status payload."""
        try:
            rows = self.execute_query("SELECT 1 AS trino_ok", limit=1)
            return {
                "engine": "trino",
                "status": "ok",
                "host": self.host,
                "port": self.port,
                "catalog": self.catalog,
                "schema": self.schema,
                "rows": rows,
            }
        except Exception as exc:  # pragma: no cover - depends on live Trino
            return {
                "engine": "trino",
                "status": "error",
                "host": self.host,
                "port": self.port,
                "catalog": self.catalog,
                "schema": self.schema,
                "message": str(exc),
            }

    @staticmethod
    def _import_client():
        """Import the Trino Python client lazily."""
        try:
            import trino
        except ImportError as exc:  # pragma: no cover - dependency should be installed
            raise RuntimeError(
                "The 'trino' Python package is not installed. Install requirements.txt first."
            ) from exc
        return trino

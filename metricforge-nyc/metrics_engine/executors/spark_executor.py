"""Spark SQL executor for MetricForge NYC."""

from __future__ import annotations

from typing import Any

from spark.spark_session import create_spark_session


def execute_query(sql: str, limit: int = 100) -> list[dict[str, Any]]:
    """Execute a Spark SQL query and return a list of dictionaries."""
    spark = None
    try:
        spark = create_spark_session("MetricForgeNYC-SemanticQuery")
        result_df = spark.sql(sql).limit(limit)
        rows = result_df.collect()
        return [row.asDict(recursive=True) for row in rows]
    except Exception as exc:  # pragma: no cover - depends on local Spark runtime
        raise RuntimeError(f"Spark query execution failed: {exc}") from exc
    finally:
        if spark is not None:
            spark.stop()


def explain_query(sql: str) -> str:
    """Return a textual Spark execution plan for a SQL query."""
    spark = None
    try:
        spark = create_spark_session("MetricForgeNYC-SemanticExplain")
        explain_df = spark.sql(f"EXPLAIN FORMATTED {sql}")
        return "\n".join(row[0] for row in explain_df.collect())
    except Exception as exc:  # pragma: no cover - depends on local Spark runtime
        raise RuntimeError(f"Spark explain failed: {exc}") from exc
    finally:
        if spark is not None:
            spark.stop()


class SparkExecutor:
    """Small wrapper around the module-level Spark execution helpers."""

    def execute(self, sql: str, limit: int = 100) -> list[dict[str, Any]]:
        """Execute Spark SQL and return row dictionaries."""
        return execute_query(sql=sql, limit=limit)

    def explain(self, sql: str) -> str:
        """Return a Spark explain plan."""
        return explain_query(sql)

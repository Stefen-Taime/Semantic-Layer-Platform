"""Execution backends for MetricForge NYC."""

from .druid_executor import DruidExecutor, ensure_druid_limit
from .spark_executor import SparkExecutor, execute_query, explain_query
from .trino_executor import TrinoExecutor, ensure_query_limit

__all__ = [
    "SparkExecutor",
    "TrinoExecutor",
    "DruidExecutor",
    "ensure_druid_limit",
    "execute_query",
    "explain_query",
    "ensure_query_limit",
]

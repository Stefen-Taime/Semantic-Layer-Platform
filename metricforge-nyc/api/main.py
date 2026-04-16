"""FastAPI application for MetricForge NYC semantic metrics."""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from metrics_engine import (
    ValidationResult,
    choose_engine,
    generate_metric_sql,
    load_semantic_layer,
    validate_semantic_layer,
)

BASE_DIR = Path(__file__).resolve().parents[1]
SEMANTIC_LAYER_DIR = BASE_DIR / os.getenv("SEMANTIC_LAYER_PATH", "semantic_layer")
SUPPORTED_ENGINES = ("spark", "trino", "druid")

app = FastAPI(title="MetricForge NYC API", version="0.5.0")


class QueryRequest(BaseModel):
    """Payload accepted by the semantic query endpoint."""

    metric: str = Field(..., description="Metric name defined in metrics.yml")
    group_by: list[str] = Field(default_factory=list)
    time_grain: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    execute: bool = True
    engine: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck endpoint."""
    return {"status": "ok", "service": "metricforge-api"}


@app.get("/engines")
def list_engines() -> dict[str, Any]:
    """Return available execution engines and the default engine."""
    return {
        "available_engines": list(SUPPORTED_ENGINES),
        "default_engine": get_default_query_engine(),
        "notes": "Trino serves flexible SQL; Druid serves pre-aggregated OLAP metrics in the full demo stack.",
    }


@app.get("/engines/trino/health")
def trino_health() -> dict[str, Any]:
    """Return a simple Trino connectivity probe."""
    executor = _create_executor("trino")
    return executor.test_connection()


@app.get("/engines/druid/health")
def druid_health() -> dict[str, Any]:
    """Return a simple Druid connectivity probe."""
    executor = _create_executor("druid")
    return executor.test_connection()


@app.get("/metrics")
def list_metrics() -> dict[str, list[dict[str, Any]]]:
    """Return metric definitions from the semantic layer."""
    config = _load_config()
    return {
        "metrics": [
            {
                "name": metric.name,
                "label": metric.label,
                "description": metric.description,
                "owner": metric.owner,
                "type": metric.type,
                "allowed_dimensions": metric.allowed_dimensions,
                "serving": asdict(metric.serving),
            }
            for metric in config.metrics
        ]
    }


@app.get("/dimensions")
def list_dimensions() -> dict[str, list[dict[str, Any]]]:
    """Return dimension definitions from the semantic layer."""
    config = _load_config()
    return {"dimensions": [asdict(dimension) for dimension in config.dimensions]}


@app.post("/validate")
def validate() -> dict[str, Any]:
    """Validate the loaded semantic layer configuration."""
    config = _load_config()
    validation = validate_semantic_layer(config)
    return _validation_payload(validation)


@app.post("/query")
def query_metric(request: QueryRequest) -> dict[str, Any]:
    """Generate SQL from the semantic layer and optionally execute it."""
    config = _load_config()
    validation = validate_semantic_layer(config)
    if not validation.is_valid:
        raise HTTPException(status_code=500, detail=_validation_payload(validation))

    metric_definition = config.metrics_by_name.get(request.metric)
    if metric_definition is None:
        raise HTTPException(status_code=400, detail=f"Unknown metric '{request.metric}'.")

    try:
        engine = choose_engine(
            metric_definition=metric_definition,
            requested_engine=request.engine,
            default_engine=get_default_query_engine(),
        )
        sql = generate_metric_sql(
            config=config,
            metric_name=request.metric,
            group_by=request.group_by,
            time_grain=request.time_grain,
            start_date=request.start_date,
            end_date=request.end_date,
            filters=request.filters,
            engine=engine,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not request.execute:
        return {
            "metric": request.metric,
            "engine": engine,
            "sql": sql,
            "data": [],
        }

    try:
        data = _execute_sql(engine=engine, sql=sql)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "metric": request.metric,
        "engine": engine,
        "sql": sql,
        "data": data,
    }


def get_default_query_engine() -> str:
    """Return the default query engine from environment variables."""
    engine = os.getenv("QUERY_ENGINE", "spark").lower()
    if engine not in SUPPORTED_ENGINES:
        return "spark"
    return engine


def _execute_sql(engine: str, sql: str) -> list[dict[str, Any]]:
    """Execute SQL with the requested engine."""
    executor = _create_executor(engine)
    if engine == "spark":
        return executor.execute(sql, limit=100)
    if engine == "druid":
        return executor.execute_sql(sql, limit=100)
    return executor.execute_query(sql, limit=100)


def _create_executor(engine: str):
    """Instantiate an execution backend lazily."""
    if engine == "spark":
        from metrics_engine.executors.spark_executor import SparkExecutor

        return SparkExecutor()
    if engine == "trino":
        from metrics_engine.executors.trino_executor import TrinoExecutor

        return TrinoExecutor()
    if engine == "druid":
        from metrics_engine.executors.druid_executor import DruidExecutor

        return DruidExecutor()
    raise RuntimeError(f"Unsupported engine '{engine}'.")


def _load_config():
    """Load the semantic layer configuration from disk."""
    return load_semantic_layer(str(SEMANTIC_LAYER_DIR))


def _validation_payload(validation: ValidationResult) -> dict[str, Any]:
    """Convert a validation result into a JSON-serializable dictionary."""
    return {
        "is_valid": validation.is_valid,
        "errors": validation.errors,
        "warnings": validation.warnings,
    }

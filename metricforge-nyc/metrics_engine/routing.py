"""Execution engine routing helpers for MetricForge NYC."""

from __future__ import annotations

from .parser import MetricDefinition

SUPPORTED_ENGINES = {"spark", "trino", "druid"}


def choose_engine(
    metric_definition: MetricDefinition,
    requested_engine: str | None,
    default_engine: str,
) -> str:
    """Choose an execution engine for a metric query."""
    candidate = requested_engine or metric_definition.serving.preferred_engine or default_engine
    engine = candidate.lower()
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(
            f"Unsupported engine '{engine}'. Supported engines: {', '.join(sorted(SUPPORTED_ENGINES))}."
        )
    return engine

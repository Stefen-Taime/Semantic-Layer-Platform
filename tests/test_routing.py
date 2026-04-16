"""Tests for query engine routing helpers."""

from pathlib import Path

import pytest

from metrics_engine import load_semantic_layer
from metrics_engine.routing import choose_engine


def _load_config():
    project_root = Path(__file__).resolve().parents[1]
    return load_semantic_layer(str(project_root / "semantic_layer"))


def test_choose_engine_respects_explicit_request() -> None:
    config = _load_config()

    engine = choose_engine(config.metrics_by_name["gross_revenue"], requested_engine="spark", default_engine="trino")

    assert engine == "spark"


def test_choose_engine_uses_metric_preference() -> None:
    config = _load_config()

    engine = choose_engine(config.metrics_by_name["daily_zone_revenue"], requested_engine=None, default_engine="spark")

    assert engine == "druid"


def test_choose_engine_falls_back_to_default() -> None:
    config = _load_config()

    engine = choose_engine(config.metrics_by_name["gross_revenue"], requested_engine=None, default_engine="spark")

    assert engine == "trino"


def test_choose_engine_rejects_unknown_engine() -> None:
    config = _load_config()

    with pytest.raises(ValueError):
        choose_engine(config.metrics_by_name["gross_revenue"], requested_engine="duckdb", default_engine="spark")

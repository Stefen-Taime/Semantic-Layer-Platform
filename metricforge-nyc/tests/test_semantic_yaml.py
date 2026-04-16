"""Tests for semantic layer loading and validation."""

from pathlib import Path

from metrics_engine import load_semantic_layer, validate_semantic_layer


def test_semantic_layer_loads_and_indexes_expected_objects() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_semantic_layer(str(project_root / "semantic_layer"))

    assert "gross_revenue" in config.metrics_by_name
    assert "daily_zone_revenue" in config.metrics_by_name
    assert "pickup_zone" in config.dimensions_by_name
    assert "trips_to_pickup_zone" in config.joins_by_name
    assert "trip" in config.entities_by_name


def test_semantic_layer_validation_passes() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_semantic_layer(str(project_root / "semantic_layer"))

    validation = validate_semantic_layer(config)

    assert validation.is_valid is True
    assert validation.errors == []
    assert config.metrics_by_name["daily_zone_revenue"].serving.preferred_engine == "druid"

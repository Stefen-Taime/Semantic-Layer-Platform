"""Parser for MetricForge NYC semantic layer YAML definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class SemanticLayerParseError(ValueError):
    """Raised when the semantic layer cannot be parsed."""


@dataclass
class FilterDefinition:
    """Declarative filter attached to a metric definition."""

    field: str
    operator: str
    value: Any


@dataclass
class ServingDefinition:
    """Execution hints for a metric."""

    preferred_engine: str | None = None
    druid_datasource: str | None = None


@dataclass
class MetricDefinition:
    """Definition of a business metric."""

    name: str
    label: str
    description: str
    owner: str
    type: str
    source: str
    time_dimension: str
    measure: str | None = None
    filters: list[FilterDefinition] = field(default_factory=list)
    numerator: str | None = None
    denominator: str | None = None
    allowed_dimensions: list[str] = field(default_factory=list)
    serving: ServingDefinition = field(default_factory=ServingDefinition)


@dataclass
class DimensionDefinition:
    """Definition of an exposed analysis dimension."""

    name: str
    label: str
    type: str
    source: str
    column: str
    join_name: str | None = None
    description: str = ""
    druid_column: str | None = None


@dataclass
class JoinDefinition:
    """Definition of a join path used by the SQL generator."""

    name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    join_type: str


@dataclass
class EntityDefinition:
    """Definition of a logical entity."""

    name: str
    source: str
    primary_key: str
    label: str = ""
    description: str = ""


@dataclass
class SemanticLayerConfig:
    """Parsed semantic layer configuration with indexed accessors."""

    metrics: list[MetricDefinition]
    dimensions: list[DimensionDefinition]
    joins: list[JoinDefinition]
    entities: list[EntityDefinition]
    base_path: Path
    metrics_by_name: dict[str, MetricDefinition] = field(init=False)
    dimensions_by_name: dict[str, DimensionDefinition] = field(init=False)
    joins_by_name: dict[str, JoinDefinition] = field(init=False)
    entities_by_name: dict[str, EntityDefinition] = field(init=False)

    def __post_init__(self) -> None:
        self.metrics_by_name = {metric.name: metric for metric in self.metrics}
        self.dimensions_by_name = {dimension.name: dimension for dimension in self.dimensions}
        self.joins_by_name = {join.name: join for join in self.joins}
        self.entities_by_name = {entity.name: entity for entity in self.entities}


def load_yaml_file(path: str) -> dict[str, Any]:
    """Load a YAML file and return a dictionary representation."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Semantic layer file not found: {file_path}")

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise SemanticLayerParseError(f"Invalid YAML in {file_path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise SemanticLayerParseError(
            f"Semantic layer file must contain a top-level mapping: {file_path}"
        )
    return payload


def load_semantic_layer(base_path: str = "semantic_layer") -> SemanticLayerConfig:
    """Load all semantic YAML files into a typed configuration object."""
    semantic_path = Path(base_path)
    metrics_payload = load_yaml_file(str(semantic_path / "metrics.yml"))
    dimensions_payload = load_yaml_file(str(semantic_path / "dimensions.yml"))
    joins_payload = load_yaml_file(str(semantic_path / "joins.yml"))
    entities_payload = load_yaml_file(str(semantic_path / "entities.yml"))

    return SemanticLayerConfig(
        metrics=[_parse_metric(item) for item in _extract_section(metrics_payload, "metrics", "metrics.yml")],
        dimensions=[
            _parse_dimension(item)
            for item in _extract_section(dimensions_payload, "dimensions", "dimensions.yml")
        ],
        joins=[_parse_join(item) for item in _extract_section(joins_payload, "joins", "joins.yml")],
        entities=[
            _parse_entity(item)
            for item in _extract_section(entities_payload, "entities", "entities.yml")
        ],
        base_path=semantic_path.resolve(),
    )


class SemanticLayerParser:
    """Backward-compatible parser wrapper."""

    def __init__(self, semantic_layer_path: str = "semantic_layer") -> None:
        self.semantic_layer_path = Path(semantic_layer_path)

    def load_file(self, filename: str) -> dict[str, Any]:
        """Load a single YAML file."""
        return load_yaml_file(str(self.semantic_layer_path / filename))

    def load_all(self) -> SemanticLayerConfig:
        """Load the full semantic layer configuration."""
        return load_semantic_layer(str(self.semantic_layer_path))


def _extract_section(payload: dict[str, Any], section_name: str, filename: str) -> list[dict[str, Any]]:
    """Extract a list section from a loaded YAML payload."""
    section = payload.get(section_name)
    if section is None:
        raise SemanticLayerParseError(
            f"Missing '{section_name}' section in semantic layer file: {filename}"
        )
    if not isinstance(section, list):
        raise SemanticLayerParseError(
            f"Section '{section_name}' must be a list in semantic layer file: {filename}"
        )

    normalized_items: list[dict[str, Any]] = []
    for index, item in enumerate(section, start=1):
        if not isinstance(item, dict):
            raise SemanticLayerParseError(
                f"Invalid item #{index} in section '{section_name}' of {filename}: expected mapping"
            )
        normalized_items.append(item)
    return normalized_items


def _parse_metric(payload: dict[str, Any]) -> MetricDefinition:
    """Convert a raw dictionary into a MetricDefinition."""
    filters = [
        FilterDefinition(
            field=str(item.get("field", "")),
            operator=str(item.get("operator", "")),
            value=item.get("value"),
        )
        for item in payload.get("filters", []) or []
    ]
    serving_payload = payload.get("serving") or {}
    return MetricDefinition(
        name=str(payload.get("name", "")),
        label=str(payload.get("label", "")),
        description=str(payload.get("description", "")),
        owner=str(payload.get("owner", "")),
        type=str(payload.get("type", "")),
        source=str(payload.get("source", "")),
        time_dimension=str(payload.get("time_dimension", "")),
        measure=_optional_string(payload.get("measure")),
        filters=filters,
        numerator=_optional_string(payload.get("numerator")),
        denominator=_optional_string(payload.get("denominator")),
        allowed_dimensions=[str(item) for item in payload.get("allowed_dimensions", []) or []],
        serving=_parse_serving(serving_payload),
    )


def _parse_dimension(payload: dict[str, Any]) -> DimensionDefinition:
    """Convert a raw dictionary into a DimensionDefinition."""
    return DimensionDefinition(
        name=str(payload.get("name", "")),
        label=str(payload.get("label", "")),
        type=str(payload.get("type", "")),
        source=str(payload.get("source", "")),
        column=str(payload.get("column", "")),
        join_name=_optional_string(payload.get("join_name")),
        description=str(payload.get("description", "")),
        druid_column=_optional_string(payload.get("druid_column")),
    )


def _parse_join(payload: dict[str, Any]) -> JoinDefinition:
    """Convert a raw dictionary into a JoinDefinition."""
    return JoinDefinition(
        name=str(payload.get("name", "")),
        from_table=str(payload.get("from_table", "")),
        from_column=str(payload.get("from_column", "")),
        to_table=str(payload.get("to_table", "")),
        to_column=str(payload.get("to_column", "")),
        join_type=str(payload.get("join_type", "")),
    )


def _parse_entity(payload: dict[str, Any]) -> EntityDefinition:
    """Convert a raw dictionary into an EntityDefinition."""
    return EntityDefinition(
        name=str(payload.get("name", "")),
        label=str(payload.get("label", "")),
        source=str(payload.get("source", "")),
        primary_key=str(payload.get("primary_key", "")),
        description=str(payload.get("description", "")),
    )


def _parse_serving(payload: Any) -> ServingDefinition:
    """Convert nested serving hints into a ServingDefinition."""
    if not payload:
        return ServingDefinition()
    if not isinstance(payload, dict):
        raise SemanticLayerParseError("Metric 'serving' configuration must be a mapping.")
    return ServingDefinition(
        preferred_engine=_optional_string(payload.get("preferred_engine")),
        druid_datasource=_optional_string(payload.get("druid_datasource")),
    )


def _optional_string(value: Any) -> str | None:
    """Convert optional scalar values to strings."""
    if value is None or value == "":
        return None
    return str(value)

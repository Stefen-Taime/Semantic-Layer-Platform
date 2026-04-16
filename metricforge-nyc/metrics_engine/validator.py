"""Semantic validation for MetricForge NYC YAML definitions."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .parser import SemanticLayerConfig

SUPPORTED_METRIC_TYPES = {"count", "count_distinct", "sum", "average", "ratio"}
SUPPORTED_DIMENSION_TYPES = {"categorical", "temporal", "numeric"}
SUPPORTED_JOIN_TYPES = {"left", "inner"}
SUPPORTED_FILTER_OPERATORS = {"=", "!=", ">", ">=", "<", "<=", "IN"}
SUPPORTED_ENGINES = {"spark", "trino", "druid"}


@dataclass
class ValidationResult:
    """Container for semantic validation output."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True when no validation error has been recorded."""
        return not self.errors


def validate_semantic_layer(config: SemanticLayerConfig) -> ValidationResult:
    """Validate cross-file semantic layer consistency."""
    result = ValidationResult()

    _validate_unique_names(result, "metric", [metric.name for metric in config.metrics])
    _validate_unique_names(result, "dimension", [dimension.name for dimension in config.dimensions])
    _validate_unique_names(result, "join", [join.name for join in config.joins])
    _validate_unique_names(result, "entity", [entity.name for entity in config.entities])

    for entity in config.entities:
        if not entity.name:
            result.errors.append("Entity is missing a name.")
        if not entity.source:
            result.errors.append(f"Entity '{entity.name}' is missing a source.")
        if not entity.primary_key:
            result.errors.append(f"Entity '{entity.name}' is missing a primary_key.")

    for join in config.joins:
        if not join.name:
            result.errors.append("Join is missing a name.")
        if not join.from_table:
            result.errors.append(f"Join '{join.name}' is missing from_table.")
        if not join.from_column:
            result.errors.append(f"Join '{join.name}' is missing from_column.")
        if not join.to_table:
            result.errors.append(f"Join '{join.name}' is missing to_table.")
        if not join.to_column:
            result.errors.append(f"Join '{join.name}' is missing to_column.")
        if join.join_type not in SUPPORTED_JOIN_TYPES:
            result.errors.append(
                f"Join '{join.name}' has unsupported join_type '{join.join_type}'."
            )

    for dimension in config.dimensions:
        if not dimension.name:
            result.errors.append("Dimension is missing a name.")
        if dimension.type not in SUPPORTED_DIMENSION_TYPES:
            result.errors.append(
                f"Dimension '{dimension.name}' has unsupported type '{dimension.type}'."
            )
        if not dimension.source:
            result.errors.append(f"Dimension '{dimension.name}' is missing a source.")
        if not dimension.column:
            result.errors.append(f"Dimension '{dimension.name}' is missing a column.")
        if dimension.join_name and dimension.join_name not in config.joins_by_name:
            result.errors.append(
                f"Dimension '{dimension.name}' references unknown join '{dimension.join_name}'."
            )

    for metric in config.metrics:
        if not metric.name:
            result.errors.append("Metric is missing a name.")
        if metric.type not in SUPPORTED_METRIC_TYPES:
            result.errors.append(
                f"Metric '{metric.name}' has unsupported type '{metric.type}'."
            )
        if not metric.source:
            result.errors.append(f"Metric '{metric.name}' is missing a source.")
        if not metric.label:
            result.errors.append(f"Metric '{metric.name}' is missing a label.")
        if not metric.description:
            result.errors.append(f"Metric '{metric.name}' is missing a description.")
        if not metric.owner:
            result.errors.append(f"Metric '{metric.name}' is missing an owner.")
        if not metric.time_dimension:
            result.errors.append(f"Metric '{metric.name}' is missing a time_dimension.")

        if metric.type in {"sum", "average", "count_distinct"} and not metric.measure:
            result.errors.append(
                f"Metric '{metric.name}' requires a measure for type '{metric.type}'."
            )

        if metric.type == "ratio":
            if not metric.numerator or metric.numerator not in config.metrics_by_name:
                result.errors.append(
                    f"Metric '{metric.name}' references unknown numerator '{metric.numerator}'."
                )
            if not metric.denominator or metric.denominator not in config.metrics_by_name:
                result.errors.append(
                    f"Metric '{metric.name}' references unknown denominator '{metric.denominator}'."
                )

        for dimension_name in metric.allowed_dimensions:
            if dimension_name not in config.dimensions_by_name:
                result.errors.append(
                    f"Metric '{metric.name}' references unknown allowed dimension '{dimension_name}'."
                )

        for filter_definition in metric.filters:
            if not filter_definition.field:
                result.errors.append(f"Metric '{metric.name}' has a filter with no field.")
            if filter_definition.operator not in SUPPORTED_FILTER_OPERATORS:
                result.errors.append(
                    f"Metric '{metric.name}' has unsupported filter operator '{filter_definition.operator}'."
                )
            if filter_definition.operator == "IN" and not isinstance(
                filter_definition.value, list
            ):
                result.errors.append(
                    f"Metric '{metric.name}' uses IN filter on '{filter_definition.field}' without a list value."
                )

        preferred_engine = metric.serving.preferred_engine
        if preferred_engine and preferred_engine not in SUPPORTED_ENGINES:
            result.errors.append(
                f"Metric '{metric.name}' has unsupported serving engine '{preferred_engine}'."
            )
        if preferred_engine == "druid" and not metric.serving.druid_datasource:
            result.warnings.append(
                f"Metric '{metric.name}' prefers Druid but has no druid_datasource."
            )

    return result


class SemanticLayerValidator:
    """Backward-compatible validator wrapper."""

    def validate(self, config: SemanticLayerConfig) -> ValidationResult:
        """Validate a semantic layer configuration."""
        return validate_semantic_layer(config)


def _validate_unique_names(result: ValidationResult, object_type: str, names: list[str]) -> None:
    """Record duplicate names for a given semantic object type."""
    counter = Counter(names)
    for name, count in counter.items():
        if name and count > 1:
            result.errors.append(f"Duplicate {object_type} name found: '{name}'.")

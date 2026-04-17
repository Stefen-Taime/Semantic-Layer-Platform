"""SQL generation for MetricForge NYC metrics."""

from __future__ import annotations

import re
from typing import Any

from .parser import DimensionDefinition, MetricDefinition, SemanticLayerConfig

SUPPORTED_TIME_GRAINS = {
    "day": "DAY",
    "week": "WEEK",
    "month": "MONTH",
}
DROID_TIME_FLOOR_INTERVALS = {
    "day": "P1D",
    "week": "P1W",
    "month": "P1M",
}
SUPPORTED_ENGINES = {"spark", "trino", "druid"}

TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def generate_metric_sql(
    config: SemanticLayerConfig,
    metric_name: str,
    group_by: list[str] | None = None,
    time_grain: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    filters: dict[str, Any] | None = None,
    engine: str = "spark",
    limit: int | None = None,
    order_by: list[dict[str, Any]] | None = None,
) -> str:
    """Generate SQL for a metric query."""
    metric = _get_metric(config, metric_name)
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(f"Unsupported engine '{engine}'.")

    validated_limit = _validate_limit(limit)

    if engine == "druid":
        return _generate_druid_metric_sql(
            config=config,
            metric=metric,
            group_by=group_by or [],
            time_grain=time_grain,
            start_date=start_date,
            end_date=end_date,
            filters=filters or {},
            limit=validated_limit,
            order_by=order_by,
        )

    return _generate_relational_metric_sql(
        config=config,
        metric=metric,
        group_by=group_by or [],
        time_grain=time_grain,
        start_date=start_date,
        end_date=end_date,
        filters=filters or {},
        engine=engine,
        limit=validated_limit,
        order_by=order_by,
    )


class SQLGenerator:
    """Backward-compatible SQL generator wrapper."""

    def __init__(self, config: SemanticLayerConfig) -> None:
        self.config = config

    def generate(
        self,
        metric_name: str,
        dimensions: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        dialect: str = "spark",
        time_grain: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Generate SQL for Spark, Trino, or Druid."""
        return generate_metric_sql(
            config=self.config,
            metric_name=metric_name,
            group_by=dimensions,
            time_grain=time_grain,
            start_date=start_date,
            end_date=end_date,
            filters=filters,
            engine=dialect,
        )


def _generate_relational_metric_sql(
    config: SemanticLayerConfig,
    metric: MetricDefinition,
    group_by: list[str],
    time_grain: str | None,
    start_date: str | None,
    end_date: str | None,
    filters: dict[str, Any],
    engine: str,
    limit: int | None = None,
    order_by: list[dict[str, Any]] | None = None,
) -> str:
    """Generate SQL for Spark SQL or Trino."""
    if time_grain and time_grain not in SUPPORTED_TIME_GRAINS:
        raise ValueError(f"Unsupported time_grain '{time_grain}'.")

    for dimension_name in group_by:
        _validate_metric_dimension(metric, config, dimension_name)

    for filter_dimension_name in filters:
        _validate_metric_dimension(metric, config, filter_dimension_name)

    join_aliases = _resolve_join_aliases(config, metric, group_by, filters)
    select_items: list[str] = []
    group_by_positions: list[str] = []
    default_order_positions: list[str] = []
    select_position = 0

    if time_grain:
        time_column = _qualified_column("t", metric.time_dimension)
        select_items.append(f"{_render_date_trunc(engine, time_grain, time_column)} AS metric_date")
        select_position += 1
        group_by_positions.append(str(select_position))
        default_order_positions.append(str(select_position))

    for dimension_name in group_by:
        dimension = config.dimensions_by_name[dimension_name]
        dimension_expr = _render_dimension_expression(dimension, join_aliases)
        select_items.append(f"{dimension_expr} AS {dimension_name}")
        select_position += 1
        group_by_positions.append(str(select_position))
        default_order_positions.append(str(select_position))

    metric_expr = _render_metric_expression(config, metric, inline_filters=False, visited=set())
    select_items.append(f"{metric_expr} AS {metric.name}")

    sql_lines = [
        "SELECT",
        "  " + ",\n  ".join(select_items),
        f"FROM {_qualified_table(metric.source)} t",
    ]
    sql_lines.extend(_render_join_clauses(config, metric, join_aliases))

    where_clauses: list[str] = []
    if metric.type != "ratio":
        where_clauses.extend(_render_metric_filters(metric))

    where_clauses.extend(_render_time_filters(metric.time_dimension, start_date, end_date, "t"))
    where_clauses.extend(_render_additional_filters(config, filters, join_aliases))

    if where_clauses:
        sql_lines.append("WHERE " + "\n  AND ".join(where_clauses))

    if group_by_positions:
        sql_lines.append("GROUP BY " + ", ".join(group_by_positions))

    order_by_clause = _render_order_by_clause(
        order_by=order_by,
        default_positions=default_order_positions,
        allowed_columns=_collect_allowed_order_columns(
            metric=metric,
            group_by=group_by,
            time_grain=time_grain,
        ),
    )
    if order_by_clause:
        sql_lines.append(order_by_clause)

    if limit is not None:
        sql_lines.append(f"LIMIT {limit}")

    return "\n".join(sql_lines)


def _generate_druid_metric_sql(
    config: SemanticLayerConfig,
    metric: MetricDefinition,
    group_by: list[str],
    time_grain: str | None,
    start_date: str | None,
    end_date: str | None,
    filters: dict[str, Any],
    limit: int | None = None,
    order_by: list[dict[str, Any]] | None = None,
) -> str:
    """Generate simple Druid SQL against a pre-aggregated datasource."""
    datasource = metric.serving.druid_datasource
    if not datasource:
        raise ValueError(f"Metric '{metric.name}' is not configured for Druid serving.")

    if time_grain and time_grain not in DROID_TIME_FLOOR_INTERVALS:
        raise ValueError(f"Unsupported time_grain '{time_grain}' for Druid.")

    for dimension_name in group_by:
        _validate_metric_dimension(metric, config, dimension_name)

    for filter_dimension_name in filters:
        _validate_metric_dimension(metric, config, filter_dimension_name)

    select_items: list[str] = []
    group_by_positions: list[str] = []
    default_order_positions: list[str] = []
    select_position = 0

    if time_grain:
        select_items.append(f"{_render_druid_time_floor(time_grain)} AS metric_date")
        select_position += 1
        group_by_positions.append(str(select_position))
        default_order_positions.append(str(select_position))

    for dimension_name in group_by:
        dimension = config.dimensions_by_name[dimension_name]
        dimension_expr = _render_druid_dimension_expression(dimension)
        select_items.append(f"{dimension_expr} AS {dimension_name}")
        select_position += 1
        group_by_positions.append(str(select_position))
        default_order_positions.append(str(select_position))

    select_items.append(f"{_render_druid_metric_expression(config, metric, visited=set())} AS {metric.name}")

    sql_lines = [
        "SELECT",
        "  " + ",\n  ".join(select_items),
        f"FROM {_qualified_table(datasource)}",
    ]

    where_clauses = _render_druid_time_filters(start_date, end_date)
    where_clauses.extend(_render_druid_additional_filters(config, filters))
    if where_clauses:
        sql_lines.append("WHERE " + "\n  AND ".join(where_clauses))

    if group_by_positions:
        sql_lines.append("GROUP BY " + ", ".join(group_by_positions))

    order_by_clause = _render_order_by_clause(
        order_by=order_by,
        default_positions=default_order_positions,
        allowed_columns=_collect_allowed_order_columns(
            metric=metric,
            group_by=group_by,
            time_grain=time_grain,
        ),
    )
    if order_by_clause:
        sql_lines.append(order_by_clause)

    if limit is not None:
        sql_lines.append(f"LIMIT {limit}")

    return "\n".join(sql_lines)


def _get_metric(config: SemanticLayerConfig, metric_name: str) -> MetricDefinition:
    """Return a metric or raise a clear error."""
    metric = config.metrics_by_name.get(metric_name)
    if metric is None:
        raise ValueError(f"Unknown metric '{metric_name}'.")
    return metric


def _validate_metric_dimension(
    metric: MetricDefinition,
    config: SemanticLayerConfig,
    dimension_name: str,
) -> None:
    """Validate that a dimension exists and is allowed for the metric."""
    if dimension_name not in config.dimensions_by_name:
        raise ValueError(f"Unknown dimension '{dimension_name}'.")
    if dimension_name not in metric.allowed_dimensions:
        raise ValueError(
            f"Dimension '{dimension_name}' is not allowed for metric '{metric.name}'."
        )


def _resolve_join_aliases(
    config: SemanticLayerConfig,
    metric: MetricDefinition,
    group_by: list[str],
    filters: dict[str, Any],
) -> dict[str, str]:
    """Build a mapping of join name to SQL alias for required dimensions."""
    aliases: dict[str, str] = {}
    needed_dimensions = list(group_by) + list(filters.keys())
    for dimension_name in needed_dimensions:
        dimension = config.dimensions_by_name[dimension_name]
        if not dimension.join_name:
            continue
        join = config.joins_by_name[dimension.join_name]
        if join.from_table != metric.source:
            raise ValueError(
                f"Join '{join.name}' is not compatible with metric source '{metric.source}'."
            )
        aliases.setdefault(join.name, _join_alias(join.name))
    return aliases


def _render_join_clauses(
    config: SemanticLayerConfig,
    metric: MetricDefinition,
    join_aliases: dict[str, str],
) -> list[str]:
    """Render SQL JOIN clauses in a stable order."""
    join_lines: list[str] = []
    ordered_joins = [join for join in config.joins if join.name in join_aliases]
    for join in ordered_joins:
        alias = join_aliases[join.name]
        join_lines.append(
            f"{join.join_type.upper()} JOIN {_qualified_table(join.to_table)} {alias}"
        )
        join_lines.append(
            f"  ON {_qualified_column('t', join.from_column)} = {_qualified_column(alias, join.to_column)}"
        )
    return join_lines


def _render_dimension_expression(
    dimension: DimensionDefinition,
    join_aliases: dict[str, str],
) -> str:
    """Render a dimension reference using the proper table alias."""
    if dimension.join_name:
        alias = join_aliases[dimension.join_name]
        return _qualified_column(alias, dimension.column)
    return _qualified_column("t", dimension.column)


def _render_druid_dimension_expression(dimension: DimensionDefinition) -> str:
    """Render a dimension reference for a Druid datasource."""
    column_name = dimension.druid_column or dimension.column
    if dimension.type == "temporal" and dimension.name == "pickup_date":
        return _render_druid_time_floor("day")
    if not IDENTIFIER_PATTERN.match(column_name):
        raise ValueError(f"Unsafe Druid column name '{column_name}'.")
    return column_name


def _render_metric_expression(
    config: SemanticLayerConfig,
    metric: MetricDefinition,
    inline_filters: bool,
    visited: set[str],
) -> str:
    """Render a metric aggregation or ratio expression."""
    if metric.name in visited:
        raise ValueError(f"Cyclic metric dependency detected for '{metric.name}'.")

    metric_type = metric.type
    if metric_type == "ratio":
        visited.add(metric.name)
        numerator_metric = _get_metric(config, metric.numerator or "")
        denominator_metric = _get_metric(config, metric.denominator or "")
        if numerator_metric.source != metric.source or denominator_metric.source != metric.source:
            raise ValueError(
                f"Ratio metric '{metric.name}' requires numerator and denominator on the same source."
            )
        if numerator_metric.type == "ratio" or denominator_metric.type == "ratio":
            raise ValueError(
                f"Ratio metric '{metric.name}' cannot reference another ratio metric."
            )
        numerator_expr = _render_metric_expression(
            config=config,
            metric=numerator_metric,
            inline_filters=True,
            visited=visited,
        )
        denominator_expr = _render_metric_expression(
            config=config,
            metric=denominator_metric,
            inline_filters=True,
            visited=visited,
        )
        visited.remove(metric.name)
        return (
            f"CASE WHEN {denominator_expr} = 0 THEN NULL "
            f"ELSE {numerator_expr} / {denominator_expr} END"
        )

    predicate = _metric_filter_predicate(metric) if inline_filters else None
    measure_expr = _qualified_column("t", metric.measure) if metric.measure else None
    return _render_aggregate_expression(metric_type, measure_expr, predicate)


def _render_druid_metric_expression(
    config: SemanticLayerConfig,
    metric: MetricDefinition,
    visited: set[str],
) -> str:
    """Render a Druid aggregation expression against an aggregated datasource."""
    if metric.name in visited:
        raise ValueError(f"Cyclic metric dependency detected for '{metric.name}'.")

    if metric.type == "ratio":
        visited.add(metric.name)
        numerator_metric = _get_metric(config, metric.numerator or "")
        denominator_metric = _get_metric(config, metric.denominator or "")
        if numerator_metric.serving.druid_datasource != metric.serving.druid_datasource:
            raise ValueError(
                f"Ratio metric '{metric.name}' requires numerator on the same Druid datasource."
            )
        if denominator_metric.serving.druid_datasource != metric.serving.druid_datasource:
            raise ValueError(
                f"Ratio metric '{metric.name}' requires denominator on the same Druid datasource."
            )
        numerator_expr = _render_druid_metric_expression(config, numerator_metric, visited)
        denominator_expr = _render_druid_metric_expression(config, denominator_metric, visited)
        visited.remove(metric.name)
        return (
            f"CASE WHEN {denominator_expr} = 0 THEN NULL "
            f"ELSE {numerator_expr} / {denominator_expr} END"
        )

    measure_expr = metric.measure
    if measure_expr and not IDENTIFIER_PATTERN.match(measure_expr):
        raise ValueError(f"Unsafe Druid measure '{measure_expr}'.")
    return _render_aggregate_expression(metric.type, measure_expr, predicate=None)


def _render_aggregate_expression(
    metric_type: str,
    measure_expr: str | None,
    predicate: str | None,
) -> str:
    """Render a metric aggregation for relational or Druid SQL."""
    if metric_type == "count":
        if predicate:
            target = measure_expr or "1"
            return f"COUNT(CASE WHEN {predicate} THEN {target} END)"
        if measure_expr:
            return f"COUNT({measure_expr})"
        return "COUNT(*)"

    if metric_type == "count_distinct":
        assert measure_expr is not None
        if predicate:
            return f"COUNT(DISTINCT CASE WHEN {predicate} THEN {measure_expr} END)"
        return f"COUNT(DISTINCT {measure_expr})"

    if metric_type == "sum":
        assert measure_expr is not None
        if predicate:
            return f"SUM(CASE WHEN {predicate} THEN {measure_expr} END)"
        return f"SUM({measure_expr})"

    if metric_type == "average":
        assert measure_expr is not None
        if predicate:
            return f"AVG(CASE WHEN {predicate} THEN {measure_expr} END)"
        return f"AVG({measure_expr})"

    raise ValueError(f"Unsupported metric type '{metric_type}'.")


def _render_metric_filters(metric: MetricDefinition) -> list[str]:
    """Render metric-level filters for WHERE clauses."""
    return [_render_filter(filter_definition, alias="t") for filter_definition in metric.filters]


def _metric_filter_predicate(metric: MetricDefinition) -> str | None:
    """Combine metric filters into a single boolean predicate."""
    predicates = _render_metric_filters(metric)
    if not predicates:
        return None
    return " AND ".join(predicates)


def _render_time_filters(
    time_dimension: str,
    start_date: str | None,
    end_date: str | None,
    alias: str | None,
) -> list[str]:
    """Render time window predicates for the metric query."""
    predicates: list[str] = []
    time_column = _qualified_column(alias, time_dimension) if alias else time_dimension

    if start_date:
        predicates.append(f"{time_column} >= {_timestamp_literal(start_date)}")
    if end_date:
        predicates.append(f"{time_column} < {_timestamp_literal(end_date)}")
    return predicates


def _render_druid_time_filters(start_date: str | None, end_date: str | None) -> list[str]:
    """Render Druid time predicates against __time."""
    return _render_time_filters("__time", start_date, end_date, alias=None)


def _render_additional_filters(
    config: SemanticLayerConfig,
    filters: dict[str, Any],
    join_aliases: dict[str, str],
) -> list[str]:
    """Render request-level filters using known dimension definitions."""
    predicates: list[str] = []
    for dimension_name, value in filters.items():
        dimension = config.dimensions_by_name[dimension_name]
        expression = _render_dimension_expression(dimension, join_aliases)
        predicates.append(_render_value_filter(expression, value))
    return predicates


def _render_druid_additional_filters(
    config: SemanticLayerConfig,
    filters: dict[str, Any],
) -> list[str]:
    """Render Druid filters using known dimension definitions."""
    predicates: list[str] = []
    for dimension_name, value in filters.items():
        dimension = config.dimensions_by_name[dimension_name]
        expression = _render_druid_dimension_expression(dimension)
        predicates.append(_render_value_filter(expression, value))
    return predicates


def _render_filter(filter_definition, alias: str) -> str:
    """Render a declarative metric filter into SQL."""
    field = _qualified_column(alias, filter_definition.field)
    operator = filter_definition.operator.upper()
    if operator == "IN":
        values = filter_definition.value if isinstance(filter_definition.value, list) else []
        literals = ", ".join(_sql_literal(item) for item in values)
        return f"{field} IN ({literals})"
    return f"{field} {operator} {_sql_literal(filter_definition.value)}"


def _render_value_filter(expression: str, value: Any) -> str:
    """Render an equality or IN filter for request-level filters."""
    if isinstance(value, list):
        literals = ", ".join(_sql_literal(item) for item in value)
        return f"{expression} IN ({literals})"
    return f"{expression} = {_sql_literal(value)}"


def _qualified_table(table_name: str) -> str:
    """Validate and return a table reference."""
    if not TABLE_NAME_PATTERN.match(table_name):
        raise ValueError(f"Unsafe table name '{table_name}'.")
    return table_name


def _qualified_column(alias: str, column_name: str) -> str:
    """Validate and return a qualified column reference."""
    if not IDENTIFIER_PATTERN.match(alias):
        raise ValueError(f"Unsafe SQL alias '{alias}'.")
    if not IDENTIFIER_PATTERN.match(column_name):
        raise ValueError(f"Unsafe column name '{column_name}'.")
    return f"{alias}.{column_name}"


def _join_alias(join_name: str) -> str:
    """Create a stable SQL alias for a join."""
    alias_base = join_name
    for prefix in ("trips_to_", "trip_to_"):
        if alias_base.startswith(prefix):
            alias_base = alias_base[len(prefix) :]
            break
    alias_base = alias_base.replace("-", "_")
    if not IDENTIFIER_PATTERN.match(alias_base):
        raise ValueError(f"Unsafe join alias derived from '{join_name}'.")
    return f"{alias_base}_dim"


def _sql_literal(value: Any) -> str:
    """Render a primitive Python value as a SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _timestamp_literal(value: str) -> str:
    """Render a date string as a SQL timestamp literal."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise ValueError(
            f"Date filters must use YYYY-MM-DD format. Received '{value}'."
        )
    return f"TIMESTAMP '{value}'"


def _render_date_trunc(engine: str, time_grain: str, time_column: str) -> str:
    """Render a DATE_TRUNC call for the selected execution engine."""
    if engine == "trino":
        return f"DATE_TRUNC('{time_grain}', {time_column})"
    return f"DATE_TRUNC('{SUPPORTED_TIME_GRAINS[time_grain]}', {time_column})"


def _render_druid_time_floor(time_grain: str) -> str:
    """Render a Druid TIME_FLOOR expression."""
    return f"TIME_FLOOR(__time, '{DROID_TIME_FLOOR_INTERVALS[time_grain]}')"


def _validate_limit(limit: int | None) -> int | None:
    """Validate the request-level row limit."""
    if limit is None:
        return None
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("limit must be a positive integer.")
    if limit < 1 or limit > 10000:
        raise ValueError("limit must be between 1 and 10000.")
    return limit


def _collect_allowed_order_columns(
    metric: MetricDefinition,
    group_by: list[str],
    time_grain: str | None,
) -> set[str]:
    """Return the set of columns that may appear in ORDER BY for a given query."""
    allowed: set[str] = set(group_by)
    allowed.add(metric.name)
    if time_grain:
        allowed.add("metric_date")
    return allowed


def _render_order_by_clause(
    order_by: list[dict[str, Any]] | None,
    default_positions: list[str],
    allowed_columns: set[str],
) -> str | None:
    """Render the ORDER BY clause, preferring a caller-specified ordering."""
    if order_by:
        rendered: list[str] = []
        for entry in order_by:
            column = entry.get("column") if isinstance(entry, dict) else None
            direction = entry.get("direction", "asc") if isinstance(entry, dict) else "asc"
            if not column:
                raise ValueError("order_by entries must include a 'column'.")
            if column not in allowed_columns:
                raise ValueError(
                    f"Column '{column}' is not available for ORDER BY. "
                    f"Allowed: {sorted(allowed_columns)}."
                )
            if not IDENTIFIER_PATTERN.match(column):
                raise ValueError(f"Unsafe ORDER BY column '{column}'.")
            normalized_direction = str(direction or "asc").lower()
            if normalized_direction not in {"asc", "desc"}:
                raise ValueError(
                    f"Unsupported ORDER BY direction '{direction}'. Use 'asc' or 'desc'."
                )
            rendered.append(f"{column} {normalized_direction.upper()}")
        return "ORDER BY " + ", ".join(rendered)

    if default_positions:
        return "ORDER BY " + ", ".join(default_positions)

    return None

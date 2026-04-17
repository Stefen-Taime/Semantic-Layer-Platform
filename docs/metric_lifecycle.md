# Metric Lifecycle

MetricForge NYC follows a simple cycle to move a business request all the way to an API or dashboard exposure.

## Steps

1. **Business need**
   A team formulates a clear need, for example "track daily gross revenue by zone".
2. **Metric definition**
   The metric is defined functionally: formula, expected grain, allowed dimensions, optional exclusions.
3. **YAML config**
   The definition is translated into `entities.yml`, `dimensions.yml`, `joins.yml`, and `metrics.yml`.
4. **Validation**
   The engine checks the model for consistency: entity references, allowed dimensions, derived metrics, known joins.
5. **Query generation**
   A SQL query is generated for Spark, Trino, or Druid depending on the target execution mode.
6. **Execution**
   The engine executes the query or returns a mocked answer until the real integration is wired up.
7. **API**
   The metric is accessible through a catalog or query endpoint.
8. **Dashboard**
   The dashboard consumes the validated definition and renders the result consistently.

## Expected outcome

This cycle reduces the risk of:

- two teams using different definitions,
- dashboards carrying hidden computations,
- logic changes shipping without formal validation.

## Future governance

In upcoming iterations, this cycle can be hardened with:

- automated tests on the semantic layer,
- metric versioning,
- backward-compatibility checks,
- generation of a consumer-friendly catalog.

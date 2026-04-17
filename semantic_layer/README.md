# Semantic Layer

This folder contains the declarative semantic layer of MetricForge NYC.

- `entities.yml` describes the logical entities such as `trip`.
- `dimensions.yml` describes the dimensions exposed by the API.
- `joins.yml` documents the join paths between facts and dimensions.
- `metrics.yml` describes the business metrics, their filters, and their allowed dimensions.

These files are now actually used to:

- perform semantic validation,
- generate Spark SQL,
- expose metrics via FastAPI,
- build queries from the Streamlit dashboard.

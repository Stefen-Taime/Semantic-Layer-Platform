# API

This folder contains the FastAPI service of MetricForge NYC.

Role of the API:

- expose a health endpoint,
- publish the catalog of metrics and dimensions,
- validate the semantic layer,
- accept a metric query,
- generate Spark SQL,
- execute the query in Spark if requested.

The `execute=false` mode returns only the generated SQL, which lets you test the API even when Spark or the data are not available.

# Metrics Engine

The metrics engine is the logical core of MetricForge NYC.

It is responsible for:

- loading the semantic-layer YAML files,
- validating references and model consistency,
- generating Spark SQL from a metric and dimensions,
- executing queries through Spark local mode when requested,
- staying modular enough to support Trino or Druid later.

Main modules:

- `parser.py`: loads and types the YAML
- `validator.py`: checks semantic consistency
- `sql_generator.py`: generates Spark SQL
- `executors/spark_executor.py`: runs queries via `spark.sql(...)`

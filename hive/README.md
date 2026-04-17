# Hive Configuration

This folder contains the base configuration for the **Hive Metastore**.

In MetricForge NYC, Hive centralizes:

- databases,
- certified batch tables,
- the schemas later consumed by Trino.

The `hive-site.xml.example` file is provided as a documentation starting point. It must be adapted to the local environment or the GCP VM.

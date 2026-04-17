# Local vs GCP VM

MetricForge NYC is designed to progress in two stages: lightweight local development first, then a fuller demonstration on a GCP VM.

## Local Mac 8 GB

Recommended use:

- edit the semantic-layer YAML files,
- develop the FastAPI API,
- build the Streamlit dashboard,
- write unit tests,
- experiment on small data samples.

Limits:

- local Spark is possible but should be kept minimal,
- running Hive, Trino, and Druid at the same time becomes too heavy,
- full ingestion and processing of the TLC datasets should be avoided.

## GCP VM Ubuntu 16 GB / 32 GB

Recommended use:

- run Spark more comfortably for batch ingestion,
- run Hive Metastore and Trino for a realistic demo,
- add Druid only if needed for an OLAP demonstration,
- serve the API and dashboard from the same VM for a compact architecture.

Practical recommendation:

- **16 GB RAM**: enough for moderate local Spark + Hive Metastore + Trino + API/dashboard.
- **32 GB RAM**: preferred when Druid is enabled or when the processed data is less sampled.

## Progression strategy

- start with Trino as the main serving engine,
- introduce Druid later only if the demo benefit is clear,
- keep datasets and volumes controlled at first,
- favour components that are simple to operate on a single VM.

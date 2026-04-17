# Data Directory

This folder is no longer the main storage backend for the batch pipeline.

The project now uses **MinIO** as S3-compatible object storage for:

- NYC TLC raw source files,
- the Spark/Hive warehouse,
- the tables managed by the batch layer.

This directory can still be used for:

- structure placeholders,
- small manual exports,
- non-critical temporary files if needed.

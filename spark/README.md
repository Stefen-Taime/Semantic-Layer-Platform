# Spark Jobs

This folder contains the project's local batch chain.

## Role of Spark

Spark is used here to:

- read source files already uploaded to MinIO raw by Airflow or a local script,
- read raw TLC objects stored in MinIO as Parquet and CSV,
- write Parquet tables cataloged locally,
- write the physical table data to MinIO,
- build the certified tables that feed the semantic layer,
- run a few validation queries.

## Hive support / local warehouse

The project uses `enableHiveSupport()` so that Spark SQL can:

- create the `metricforge` database,
- register tables in an embedded local catalog,
- store managed tables in an S3A warehouse pointing to MinIO.

The metastore stays embedded locally for the demo, but the table data is stored in MinIO.

## Expected objects in MinIO

- `s3a://<MINIO_RAW_BUCKET>/nyc_taxi/yellow_tripdata_<YYYY-MM>.parquet` for each month listed in `TLC_TRIPDATA_MONTHS`
- `s3a://<MINIO_RAW_BUCKET>/nyc_taxi/taxi_zone_lookup.csv`

If these objects are missing, `02_ingest_raw_taxi_data.py` stops execution with a clear message.

## Execution commands

```bash
python scripts/load_nyc_taxi_to_minio.py
python spark/01_create_hive_database.py
python spark/02_ingest_raw_taxi_data.py
python spark/03_build_certified_tables.py
python spark/04_run_sample_queries.py
```

## Tables created

- `metricforge.raw_yellow_taxi_trips`
- `metricforge.raw_taxi_zone_lookup`
- `metricforge.fct_taxi_trips`
- `metricforge.dim_zone`
- `metricforge.dim_payment_type`
- `metricforge.dim_date`

## Supported environment variables

- `SPARK_MASTER`: default `local[2]`
- `SPARK_DRIVER_MEMORY`: default `3g`
- `SPARK_SQL_SHUFFLE_PARTITIONS`: default `4`
- `SPARK_WAREHOUSE_DIR`: default `s3a://metricforge-warehouse/`
- `MINIO_ENDPOINT`: default `http://127.0.0.1:9000`
- `MINIO_ACCESS_KEY`: default `metricforge`
- `MINIO_SECRET_KEY`: default `metricforge123`
- `MINIO_RAW_BUCKET`: default `metricforge-raw`
- `MINIO_CURATED_BUCKET`: default `metricforge-curated`
- `MINIO_WAREHOUSE_BUCKET`: default `metricforge-warehouse`
- `MINIO_LOGS_BUCKET`: default `metricforge-logs`
- `MINIO_RAW_PREFIX`: default `nyc_taxi`
- `MINIO_SECURE`: default `false`
- `MINIO_REGION`: default `us-east-1`
- `TLC_TRIPDATA_MONTHS`: default `2026-01,2026-02`
- `SPARK_JARS_PACKAGES`: Hadoop AWS / AWS SDK packages compatible with your Spark build
- `SPARK_EXTRA_JARS_DIR`: optional folder of local jars added to the Spark classpath

## Important note

For Spark to read `s3a://...`, you need S3A jars compatible with your Spark/Hadoop version, usually pulled in through `SPARK_JARS_PACKAGES`.
For `pyspark 4.1.x`, the bundled runtime uses Hadoop `3.4.2`; a consistent choice is `org.apache.hadoop:hadoop-aws:3.4.2`.
In the project's Airflow image, these S3A jars are preloaded locally into `/opt/spark-extra-jars` to avoid hot Maven downloads during DAG runs.

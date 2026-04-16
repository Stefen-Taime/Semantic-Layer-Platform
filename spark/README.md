# Spark Jobs

Ce dossier contient la chaîne batch locale du projet.

## Rôle de Spark

Spark sert ici à :

- lire des fichiers sources déjà déposés dans MinIO raw par Airflow ou par un script local,
- lire les objets TLC bruts stockés dans MinIO en Parquet et CSV,
- écrire des tables Parquet cataloguées localement,
- écrire les données physiques des tables dans MinIO,
- construire les tables certifiées qui serviront ensuite à la semantic layer,
- exécuter quelques requêtes de validation.

## Rôle du Hive support / warehouse local

Le projet utilise `enableHiveSupport()` pour que Spark SQL puisse :

- créer la database `metricforge`,
- enregistrer les tables dans un catalogue local embarqué,
- stocker les tables gérées dans un warehouse S3A pointant vers MinIO.

Le metastore reste embarqué localement pour la démo, mais les données des tables sont stockées dans MinIO.

## Objets attendus dans MinIO

- `s3a://<MINIO_RAW_BUCKET>/nyc_taxi/yellow_tripdata_<YYYY-MM>.parquet` pour chaque mois listé dans `TLC_TRIPDATA_MONTHS`
- `s3a://<MINIO_RAW_BUCKET>/nyc_taxi/taxi_zone_lookup.csv`

Si ces objets sont absents, le script `02_ingest_raw_taxi_data.py` arrête l'exécution avec un message clair.

## Commandes d'exécution

```bash
python scripts/load_nyc_taxi_to_minio.py
python spark/01_create_hive_database.py
python spark/02_ingest_raw_taxi_data.py
python spark/03_build_certified_tables.py
python spark/04_run_sample_queries.py
```

## Tables créées

- `metricforge.raw_yellow_taxi_trips`
- `metricforge.raw_taxi_zone_lookup`
- `metricforge.fct_taxi_trips`
- `metricforge.dim_zone`
- `metricforge.dim_payment_type`
- `metricforge.dim_date`

## Variables d'environnement supportées

- `SPARK_MASTER` : défaut `local[2]`
- `SPARK_DRIVER_MEMORY` : défaut `3g`
- `SPARK_SQL_SHUFFLE_PARTITIONS` : défaut `4`
- `SPARK_WAREHOUSE_DIR` : défaut `s3a://metricforge-warehouse/`
- `MINIO_ENDPOINT` : défaut `http://127.0.0.1:9000`
- `MINIO_ACCESS_KEY` : défaut `metricforge`
- `MINIO_SECRET_KEY` : défaut `metricforge123`
- `MINIO_RAW_BUCKET` : défaut `metricforge-raw`
- `MINIO_CURATED_BUCKET` : défaut `metricforge-curated`
- `MINIO_WAREHOUSE_BUCKET` : défaut `metricforge-warehouse`
- `MINIO_LOGS_BUCKET` : défaut `metricforge-logs`
- `MINIO_RAW_PREFIX` : défaut `nyc_taxi`
- `MINIO_SECURE` : défaut `false`
- `MINIO_REGION` : défaut `us-east-1`
- `TLC_TRIPDATA_MONTHS` : défaut `2026-01,2026-02`
- `SPARK_JARS_PACKAGES` : packages Hadoop AWS/AWS SDK compatibles avec votre build Spark
- `SPARK_EXTRA_JARS_DIR` : dossier optionnel contenant des jars locaux ajoutés au classpath Spark

## Note importante

Pour que Spark lise `s3a://...`, il faut fournir les jars S3A compatibles avec votre version Spark/Hadoop, généralement via `SPARK_JARS_PACKAGES`.
Pour `pyspark 4.1.x`, le runtime embarqué utilise Hadoop `3.4.2`; un choix cohérent est donc `org.apache.hadoop:hadoop-aws:3.4.2`.
Dans l'image Airflow du projet, ces jars S3A sont préchargés localement dans `/opt/spark-extra-jars` pour éviter les téléchargements Maven à chaud pendant les DAG runs.

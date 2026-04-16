"""Lightweight tests for Spark session configuration helpers."""

from spark.spark_session import create_spark_session, get_spark_runtime_settings


def test_create_spark_session_exists() -> None:
    assert callable(create_spark_session)


def test_spark_runtime_settings_use_defaults(monkeypatch) -> None:
    monkeypatch.delenv("SPARK_MASTER", raising=False)
    monkeypatch.delenv("SPARK_DRIVER_MEMORY", raising=False)
    monkeypatch.delenv("SPARK_SQL_SHUFFLE_PARTITIONS", raising=False)
    monkeypatch.delenv("SPARK_WAREHOUSE_DIR", raising=False)
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("MINIO_BUCKET", raising=False)
    monkeypatch.delenv("MINIO_RAW_BUCKET", raising=False)
    monkeypatch.delenv("MINIO_WAREHOUSE_BUCKET", raising=False)
    monkeypatch.delenv("MINIO_RAW_PREFIX", raising=False)
    monkeypatch.delenv("MINIO_SECURE", raising=False)

    settings = get_spark_runtime_settings()

    assert settings["master"] == "local[2]"
    assert settings["driver_memory"] == "3g"
    assert settings["shuffle_partitions"] == "4"
    assert settings["warehouse_uri"] == "s3a://metricforge-warehouse/"
    assert settings["minio_endpoint"] == "http://127.0.0.1:9000"
    assert settings["minio_access_key"] == "metricforge"
    assert settings["minio_secret_key"] == "metricforge123"
    assert settings["minio_raw_bucket"] == "metricforge-raw"
    assert settings["minio_warehouse_bucket"] == "metricforge-warehouse"
    assert settings["minio_secure"] is False


def test_spark_runtime_settings_read_environment(monkeypatch) -> None:
    monkeypatch.setenv("SPARK_MASTER", "local[4]")
    monkeypatch.setenv("SPARK_DRIVER_MEMORY", "5g")
    monkeypatch.setenv("SPARK_SQL_SHUFFLE_PARTITIONS", "12")
    monkeypatch.setenv("SPARK_WAREHOUSE_DIR", "s3a://demo-bucket/custom-warehouse")
    monkeypatch.setenv("MINIO_ENDPOINT", "http://minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "demo")
    monkeypatch.setenv("MINIO_SECRET_KEY", "secret")
    monkeypatch.setenv("MINIO_RAW_BUCKET", "demo-raw")
    monkeypatch.setenv("MINIO_WAREHOUSE_BUCKET", "demo-warehouse")
    monkeypatch.setenv("MINIO_RAW_PREFIX", "landing/raw")
    monkeypatch.setenv("MINIO_SECURE", "true")

    settings = get_spark_runtime_settings()

    assert settings["master"] == "local[4]"
    assert settings["driver_memory"] == "5g"
    assert settings["shuffle_partitions"] == "12"
    assert settings["warehouse_uri"] == "s3a://demo-bucket/custom-warehouse"
    assert settings["minio_endpoint"] == "http://minio:9000"
    assert settings["minio_access_key"] == "demo"
    assert settings["minio_secret_key"] == "secret"
    assert settings["minio_raw_bucket"] == "demo-raw"
    assert settings["minio_warehouse_bucket"] == "demo-warehouse"
    assert settings["minio_secure"] is True

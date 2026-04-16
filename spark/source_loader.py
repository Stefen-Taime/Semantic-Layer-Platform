"""Load external NYC TLC source files into MinIO raw storage."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from spark.config import (
    PROJECT_ROOT,
    build_tripdata_filename,
    get_minio_access_key,
    get_minio_endpoint,
    get_minio_raw_bucket,
    get_minio_raw_prefix,
    get_minio_secret_key,
    get_minio_secure,
    get_tripdata_months,
)

DEFAULT_TLC_ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class SourceObject:
    """Description of a source file that should be staged into MinIO."""

    name: str
    url: str
    filename: str
    content_type: str


def get_source_objects() -> list[SourceObject]:
    """Return the TLC source objects used by the demo."""
    source_objects: list[SourceObject] = []
    for month in get_tripdata_months():
        filename = build_tripdata_filename(month)
        source_objects.append(
            SourceObject(
                name=f"yellow_tripdata_{month}",
                url=_build_default_tripdata_url(month),
                filename=filename,
                content_type="application/octet-stream",
            )
        )
    source_objects.extend(
        [
        SourceObject(
            name="taxi_zone_lookup",
            url=os.getenv("TLC_ZONE_LOOKUP_URL", DEFAULT_TLC_ZONE_LOOKUP_URL),
            filename="taxi_zone_lookup.csv",
            content_type="text/csv",
        )]
    )
    return source_objects


def get_default_download_dir() -> Path:
    """Return the local cache directory used before uploading to MinIO."""
    return Path(os.getenv("METRICFORGE_SOURCE_DOWNLOAD_DIR", PROJECT_ROOT / ".local" / "source_cache"))


def normalize_minio_endpoint(endpoint: str) -> str:
    """Convert a MinIO endpoint URL into the format expected by the MinIO client."""
    parsed = urlparse(endpoint)
    if parsed.scheme and parsed.netloc:
        return parsed.netloc
    return endpoint.replace("http://", "").replace("https://", "")


def build_raw_object_name(filename: str) -> str:
    """Return the raw object key under the configured MinIO prefix."""
    prefix = get_minio_raw_prefix().strip("/")
    return f"{prefix}/{filename}" if prefix else filename


def create_minio_client() -> Any:
    """Create a MinIO client from the current environment."""
    try:
        from minio import Minio
    except ImportError as exc:  # pragma: no cover - dependency should be installed
        raise RuntimeError(
            "The 'minio' Python package is not installed. Install requirements.txt first."
        ) from exc
    return Minio(
        normalize_minio_endpoint(get_minio_endpoint()),
        access_key=get_minio_access_key(),
        secret_key=get_minio_secret_key(),
        secure=get_minio_secure(),
    )


def load_sources_to_minio(download_dir: str | Path | None = None, overwrite: bool = False) -> list[str]:
    """Download TLC files and upload them into the configured MinIO raw bucket."""
    destination_dir = Path(download_dir or get_default_download_dir())
    destination_dir.mkdir(parents=True, exist_ok=True)

    client = create_minio_client()
    raw_bucket = get_minio_raw_bucket()
    if not client.bucket_exists(raw_bucket):
        client.make_bucket(raw_bucket)

    uploaded_objects: list[str] = []
    for source_object in get_source_objects():
        local_path = destination_dir / source_object.filename
        object_name = build_raw_object_name(source_object.filename)

        if overwrite or not local_path.exists():
            print(f"Downloading {source_object.url} -> {local_path}")
            download_to_file(source_object.url, local_path)
        else:
            print(f"Using cached source file: {local_path}")

        if overwrite:
            _remove_object_if_present(client, raw_bucket, object_name)

        print(f"Uploading {local_path} -> s3://{raw_bucket}/{object_name}")
        client.fput_object(
            bucket_name=raw_bucket,
            object_name=object_name,
            file_path=str(local_path),
            content_type=source_object.content_type,
        )
        uploaded_objects.append(f"s3://{raw_bucket}/{object_name}")

    return uploaded_objects


def download_to_file(url: str, destination: Path) -> None:
    """Stream a file from HTTP to the local filesystem."""
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    with destination.open("wb") as output_handle:
        for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            if chunk:
                output_handle.write(chunk)


def _build_default_tripdata_url(month: str) -> str:
    """Return the default TLC tripdata URL for a given YYYY-MM month."""
    env_key = f"TLC_TRIPDATA_URL_{month.replace('-', '_')}"
    return os.getenv(
        env_key,
        f"https://d37ci6vzurychx.cloudfront.net/trip-data/{build_tripdata_filename(month)}",
    )


def _remove_object_if_present(client: Any, bucket_name: str, object_name: str) -> None:
    """Delete an object only when it already exists."""
    try:
        client.stat_object(bucket_name, object_name)
    except Exception:
        return
    client.remove_object(bucket_name, object_name)

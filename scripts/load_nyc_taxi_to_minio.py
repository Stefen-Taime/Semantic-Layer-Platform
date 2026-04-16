"""Download NYC TLC source files and upload them into MinIO raw storage."""

from __future__ import annotations

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spark.source_loader import get_default_download_dir, load_sources_to_minio


def main() -> None:
    """Load the demo TLC source files into MinIO raw storage."""
    print("Loading NYC TLC source files into MinIO raw storage...")
    print(f"Local download cache: {get_default_download_dir()}")
    uploaded_objects = load_sources_to_minio()
    print("Uploaded objects:")
    for object_uri in uploaded_objects:
        print(f"- {object_uri}")


if __name__ == "__main__":
    main()

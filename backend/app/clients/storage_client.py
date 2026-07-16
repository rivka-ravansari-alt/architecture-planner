"""Object storage client abstraction used by generation + debug artifacts.

Client supports local filesystem and Google Cloud Storage (GCS).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.config.settings import settings


class StorageClient(ABC):
    @abstractmethod
    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        """Serialize and persist a JSON payload."""

    @abstractmethod
    def read_json(self, key: str) -> dict[str, Any]:
        """Load and deserialize a JSON payload."""

    @abstractmethod
    def write_text(
        self, key: str, data: str, *, content_type: str | None = None
    ) -> str:
        """Persist arbitrary UTF-8 text (e.g. CSV) and return its object URI."""

    def write_csv(self, key: str, csv_text: str) -> str:
        """Persist CSV text and return its object URI."""

        return self.write_text(key, csv_text, content_type="text/csv")


class LocalStorageClient(StorageClient):
    def __init__(self, root_path: str | Path) -> None:
        self._root = Path(root_path)

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        self._root.joinpath(key).parent.mkdir(parents=True, exist_ok=True)
        path = self._root / key
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def read_json(self, key: str) -> dict[str, Any]:
        path = self._root / key
        return json.loads(path.read_text(encoding="utf-8"))

    def write_text(
        self, key: str, data: str, *, content_type: str | None = None
    ) -> str:
        _ = content_type  # informational for local writes
        self._root.joinpath(key).parent.mkdir(parents=True, exist_ok=True)
        path = self._root / key
        path.write_text(data, encoding="utf-8")
        return str(path)


class GCSStorageClient(StorageClient):
    def __init__(self, bucket_name: str, *, gcs_client: Any | None = None) -> None:
        self._bucket_name = bucket_name
        if gcs_client is None:
            # Lazy import so unit tests don't require GCS libraries.
            from google.cloud import storage  # type: ignore

            gcs_client = storage.Client(project=settings.gcs_project_id or None)
        self._client = gcs_client
        self._bucket = self._client.bucket(bucket_name)

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        key_path = str(key).lstrip("/")
        blob = self._bucket.blob(key_path)
        blob.upload_from_string(
            json.dumps(payload),
            content_type="application/json",
        )
        return f"gs://{self._bucket_name}/{key_path}"

    def read_json(self, key: str) -> dict[str, Any]:
        key_path = str(key).lstrip("/")
        blob = self._bucket.blob(key_path)
        raw = blob.download_as_text(encoding="utf-8")
        return json.loads(raw)

    def write_text(
        self, key: str, data: str, *, content_type: str | None = None
    ) -> str:
        key_path = str(key).lstrip("/")
        blob = self._bucket.blob(key_path)
        blob.upload_from_string(data, content_type=content_type)
        return f"gs://{self._bucket_name}/{key_path}"


class S3StorageClient(StorageClient):
    """S3 storage client placeholder (not implemented in this build)."""

    def __init__(self, bucket_name: str, *, s3_client: Any | None = None) -> None:
        _ = s3_client
        self._bucket_name = bucket_name
        raise ValueError("S3StorageClient is not implemented; use local or gcs.")

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError

    def read_json(self, key: str) -> dict[str, Any]:
        raise NotImplementedError

    def write_text(
        self, key: str, data: str, *, content_type: str | None = None
    ) -> str:
        raise NotImplementedError


class StorageClientFactory:
    @staticmethod
    def create(*, bucket_name: str | None = None) -> StorageClient:
        provider = str(settings.object_storage_provider).lower().strip()
        resolved_bucket = bucket_name or settings.object_storage_bucket

        if provider in {"gcs", "google", "google_cloud"}:
            return GCSStorageClient(resolved_bucket)
        if provider in {"local", "filesystem", "file"}:
            return LocalStorageClient(settings.object_storage_local_root)
        if provider in {"s3", "aws"}:
            return S3StorageClient(resolved_bucket)

        raise ValueError(
            f"Unknown object storage provider: {settings.object_storage_provider}"
        )

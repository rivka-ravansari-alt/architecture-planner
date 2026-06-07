"""Configurable object storage for generation artifacts (local, GCS, S3)."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.config.params import STORAGE_PROVIDERS
from app.config.settings import settings


class StorageClient(ABC):
    """Writes JSON objects to a bucket at a logical object key."""

    @abstractmethod
    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        """Persist JSON at `key` and return the resolved storage URI/path."""

    @abstractmethod
    def read_json(self, key: str) -> dict[str, Any]:
        """Load JSON previously written at `key`."""


class LocalStorageClient(StorageClient):
    """Maps object keys to files under a local root directory."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path.resolve())

    def read_json(self, key: str) -> dict[str, Any]:
        path = self._root / key
        return json.loads(path.read_text(encoding="utf-8"))


class GCSStorageClient(StorageClient):
    """Google Cloud Storage backend."""

    def __init__(
        self,
        bucket: str,
        *,
        gcs_client: Any | None = None,
        project: str | None = None,
    ) -> None:
        self._bucket_name = bucket
        self._gcs_client = gcs_client
        self._project = project or settings.gcs_project_id or None
        self._bucket: Any | None = None

    def _bucket_ref(self) -> Any:
        if self._bucket is None:
            if self._gcs_client is None:
                from google.cloud import storage

                self._gcs_client = (
                    storage.Client(project=self._project)
                    if self._project
                    else storage.Client()
                )
            self._bucket = self._gcs_client.bucket(self._bucket_name)
        return self._bucket

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        blob = self._bucket_ref().blob(key)
        blob.upload_from_string(
            json.dumps(payload, indent=2),
            content_type="application/json",
        )
        return f"gs://{self._bucket_name}/{key}"

    def read_json(self, key: str) -> dict[str, Any]:
        blob = self._bucket_ref().blob(key)
        return json.loads(blob.download_as_text(encoding="utf-8"))


class S3StorageClient(StorageClient):
    """Amazon S3 backend (not yet wired)."""

    def __init__(self, bucket: str) -> None:
        self._bucket = bucket

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError(
            f"S3 storage is not implemented yet (bucket={self._bucket}, key={key})."
        )

    def read_json(self, key: str) -> dict[str, Any]:
        raise NotImplementedError(
            f"S3 storage is not implemented yet (bucket={self._bucket}, key={key})."
        )


class StorageClientFactory:
    """Selects the configured object storage implementation."""

    @staticmethod
    def create(
        *,
        provider: str | None = None,
        bucket: str | None = None,
        local_root: str | None = None,
    ) -> StorageClient:
        resolved_provider = (provider or settings.object_storage_provider).lower()

        if resolved_provider not in STORAGE_PROVIDERS:
            raise ValueError(
                f"Unknown object storage provider '{resolved_provider}'. "
                f"Expected one of: {', '.join(STORAGE_PROVIDERS)}"
            )
        if resolved_provider == "local":
            return LocalStorageClient(
                local_root or settings.object_storage_local_root
            )
        resolved_bucket = bucket or settings.object_storage_bucket
        if not resolved_bucket:
            raise ValueError(
                "OBJECT_STORAGE_BUCKET is required when using gcs or s3 storage."
            )
        if resolved_provider == "gcs":
            return GCSStorageClient(resolved_bucket)
        if resolved_provider == "s3":
            return S3StorageClient(resolved_bucket)
        raise ValueError(f"Unsupported storage provider: {resolved_provider}")

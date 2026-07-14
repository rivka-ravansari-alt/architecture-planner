"""Object storage for generation artifacts.

Functionality has been removed from this build. The classes are kept as
structural stubs; none of them read or write real storage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

_DISABLED = "Artifact storage has been removed from this build."


class StorageClient(ABC):
    @abstractmethod
    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        """Serialize and persist a JSON payload."""

    @abstractmethod
    def read_json(self, key: str) -> dict[str, Any]:
        """Load and deserialize a JSON payload."""


class LocalStorageClient(StorageClient):
    def __init__(self, *args, **kwargs) -> None:
        pass

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError(_DISABLED)

    def read_json(self, key: str) -> dict[str, Any]:
        raise NotImplementedError(_DISABLED)


class GCSStorageClient(StorageClient):
    def __init__(self, *args, **kwargs) -> None:
        pass

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError(_DISABLED)

    def read_json(self, key: str) -> dict[str, Any]:
        raise NotImplementedError(_DISABLED)


class S3StorageClient(StorageClient):
    def __init__(self, *args, **kwargs) -> None:
        pass

    def write_json(self, key: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError(_DISABLED)

    def read_json(self, key: str) -> dict[str, Any]:
        raise NotImplementedError(_DISABLED)


class StorageClientFactory:
    @staticmethod
    def create(*args, **kwargs) -> StorageClient:
        raise NotImplementedError(_DISABLED)

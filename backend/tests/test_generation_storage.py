"""Tests for generation object storage."""

from __future__ import annotations

import json

import pytest

from app.clients.storage_client import GCSStorageClient, LocalStorageClient, StorageClientFactory
from app.config.params import (
    GENERATION_REQUEST_FILENAME,
    GENERATION_RESPONSE_FILENAME,
    GENERATION_STORAGE_PREFIX,
    GENERATION_TYPE_ARCHITECTURE,
)
from app.services.generation_storage_service import GenerationStorageService


def test_local_storage_client_writes_and_reads(tmp_path):
    client = LocalStorageClient(tmp_path)
    key = "generations/proj-1/gen-1/request.json"
    payload = {"generation_id": "gen-1", "project_id": "proj-1"}

    client.write_json(key, payload)
    loaded = client.read_json(key)

    assert loaded == payload
    assert (tmp_path / key).exists()


class _FakeGcsBlob:
    def __init__(self) -> None:
        self._body: str | None = None

    def upload_from_string(self, data: str, content_type: str | None = None) -> None:
        self._body = data

    def download_as_text(self, encoding: str = "utf-8") -> str:
        if self._body is None:
            raise FileNotFoundError("blob missing")
        return self._body


class _FakeGcsBucket:
    def __init__(self) -> None:
        self._blobs: dict[str, _FakeGcsBlob] = {}

    def blob(self, key: str) -> _FakeGcsBlob:
        return self._blobs.setdefault(key, _FakeGcsBlob())


class _FakeGcsClient:
    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        self._bucket = _FakeGcsBucket()

    def bucket(self, name: str) -> _FakeGcsBucket:
        assert name == self.bucket_name
        return self._bucket


def test_gcs_storage_client_writes_and_reads():
    client = GCSStorageClient(
        "archsari-generations-test",
        gcs_client=_FakeGcsClient("archsari-generations-test"),
    )
    key = "generations/proj-1/gen-1/request.json"
    payload = {"generation_id": "gen-1", "project_id": "proj-1"}

    uri = client.write_json(key, payload)
    loaded = client.read_json(key)

    assert loaded == payload
    assert uri == f"gs://archsari-generations-test/{key}"


def test_storage_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr("app.clients.storage_client.settings.object_storage_provider", "minio")
    with pytest.raises(ValueError, match="Unknown object storage provider"):
        StorageClientFactory.create()


def test_generation_storage_service_saves_request_and_response(tmp_path, sample_project):
    service = GenerationStorageService(LocalStorageClient(tmp_path))
    generation_id = "gen-abc"
    prompt = "Design an architecture for TaskFlow."

    request_payload = service.build_request_payload(
        sample_project,
        generation_id=generation_id,
        prompt=prompt,
        model_name="gpt-test",
    )
    service.save_request(sample_project.id, generation_id, request_payload)

    response_payload = service.build_response_payload(
        generation_id=generation_id,
        project_id=sample_project.id,
        model_name="gpt-test",
        raw_ai_response='{"ok": true}',
        parsed_response={"ok": True},
        validation_result={"valid": True},
        duration_seconds=1.5,
    )
    service.save_response(sample_project.id, generation_id, response_payload)

    request_path = (
        tmp_path
        / GENERATION_STORAGE_PREFIX
        / sample_project.id
        / generation_id
        / GENERATION_REQUEST_FILENAME
    )
    response_path = (
        tmp_path
        / GENERATION_STORAGE_PREFIX
        / sample_project.id
        / generation_id
        / GENERATION_RESPONSE_FILENAME
    )

    saved_request = json.loads(request_path.read_text(encoding="utf-8"))
    saved_response = json.loads(response_path.read_text(encoding="utf-8"))

    assert saved_request["generation_id"] == generation_id
    assert saved_request["project_id"] == sample_project.id
    assert saved_request["user_id"] == sample_project.user_id
    assert saved_request["generation_type"] == GENERATION_TYPE_ARCHITECTURE
    assert saved_request["generated_prompt"] == prompt
    assert saved_request["original_user_input"]["name"] == "TaskFlow"
    assert saved_response["raw_ai_response"] == '{"ok": true}'
    assert saved_response["parsed_response"] == {"ok": True}
    assert saved_response["duration_seconds"] == 1.5

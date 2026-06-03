"""Tests for the OpenAI client wrapper."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config import settings
from app.services.ai_client import AIClientError, generate_architecture


def test_raises_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(settings, "use_static_ai_response", False)
    monkeypatch.setattr(settings, "openai_api_key", "")
    with pytest.raises(AIClientError, match="OPENAI_API_KEY"):
        generate_architecture("prompt")


def test_returns_static_response_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "use_static_ai_response", True)
    result = generate_architecture("any prompt")
    assert '"components"' in result
    assert '"cloud_options"' in result
    assert '"diagrams"' in result


def test_returns_model_content(monkeypatch):
    monkeypatch.setattr(settings, "use_static_ai_response", False)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_model", "gpt-test")

    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["response_format"] == {"type": "json_object"}
            assert kwargs["messages"][-1]["content"] == "build me arch"
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
            )

    class FakeClient:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("app.services.ai_client.OpenAI", FakeClient)
    assert generate_architecture("build me arch") == '{"ok": true}'


def test_raises_when_model_returns_empty_content(monkeypatch):
    monkeypatch.setattr(settings, "use_static_ai_response", False)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    class FakeCompletions:
        def create(self, **_kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
            )

    class FakeClient:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("app.services.ai_client.OpenAI", FakeClient)
    with pytest.raises(AIClientError, match="empty response"):
        generate_architecture("prompt")


def test_wraps_provider_errors(monkeypatch):
    monkeypatch.setattr(settings, "use_static_ai_response", False)
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    class FakeCompletions:
        def create(self, **_kwargs):
            raise RuntimeError("rate limited")

    class FakeClient:
        def __init__(self, api_key: str):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("app.services.ai_client.OpenAI", FakeClient)
    with pytest.raises(AIClientError, match="AI request failed"):
        generate_architecture("prompt")

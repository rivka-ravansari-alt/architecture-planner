"""Tests for the OpenAI client wrapper."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.clients.ai_client import (
    AIClientError,
    OpenAIClient,
    _completion_limit_kwargs,
)


def test_raises_when_api_key_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from app.clients.ai_client import AIClientFactory

    with pytest.raises(AIClientError, match="OPENAI_API_KEY"):
        AIClientFactory.create().generate("prompt")


def test_completion_limit_kwargs_for_gpt5():
    assert _completion_limit_kwargs("gpt-5", 8000) == {"max_completion_tokens": 8000}


def test_completion_limit_kwargs_for_legacy_models():
    assert _completion_limit_kwargs("gpt-4o-mini", 8000) == {"max_tokens": 8000}


def test_returns_model_content(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["response_format"] == {"type": "json_object"}
            assert kwargs["messages"][-1]["content"] == "build me arch"
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
            )

    class FakeClient:
        def __init__(self, api_key: str, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("app.clients.ai_client.OpenAI", FakeClient)
    client = OpenAIClient("test-key", "gpt-test")
    assert client.generate("build me arch") == '{"ok": true}'


def test_raises_when_model_returns_empty_content(monkeypatch):
    class FakeCompletions:
        def create(self, **_kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
            )

    class FakeClient:
        def __init__(self, api_key: str, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("app.clients.ai_client.OpenAI", FakeClient)
    client = OpenAIClient("test-key", "gpt-test")
    with pytest.raises(AIClientError, match="empty response"):
        client.generate("prompt")


def test_gpt5_uses_max_completion_tokens(monkeypatch):
    captured: dict = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
            )

    class FakeClient:
        def __init__(self, api_key: str, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("app.clients.ai_client.OpenAI", FakeClient)
    OpenAIClient("test-key", "gpt-5").generate("prompt")
    assert captured["max_completion_tokens"] == 8000
    assert "max_tokens" not in captured


def test_wraps_provider_errors(monkeypatch):
    class FakeCompletions:
        def create(self, **_kwargs):
            raise RuntimeError("rate limited")

    class FakeClient:
        def __init__(self, api_key: str, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("app.clients.ai_client.OpenAI", FakeClient)
    client = OpenAIClient("test-key", "gpt-test")
    with pytest.raises(AIClientError, match="AI request failed"):
        client.generate("prompt")

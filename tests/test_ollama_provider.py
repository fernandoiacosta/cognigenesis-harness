import io
import json
import socket
from urllib import error

import pytest

from providers.base import ProviderError
from providers.ollama import OllamaProvider


class FakeResponse:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._data


def context():
    return {
        "system": "You are Cognigenesis.",
        "objective": "Say OK",
        "capabilities": [],
        "state": {},
        "history": [],
    }


def test_ollama_provider_returns_model_text(monkeypatch):
    def fake_urlopen(req, timeout):
        assert req.full_url == "http://127.0.0.1:11434/api/chat"
        body = json.loads(req.data.decode("utf-8"))
        assert body["model"] == "llama3.1:8b"
        assert body["stream"] is False
        return FakeResponse({"message": {"role": "assistant", "content": "OK"}})

    monkeypatch.setattr("providers.ollama.request.urlopen", fake_urlopen)
    response = OllamaProvider().generate(context())
    assert response.final == "OK"
    assert response.tool_calls == []


def test_ollama_provider_reports_unreachable(monkeypatch):
    def fail(*args, **kwargs):
        raise error.URLError("connection refused")

    monkeypatch.setattr("providers.ollama.request.urlopen", fail)
    with pytest.raises(ProviderError, match="Ollama is not reachable at http://127.0.0.1:11434"):
        OllamaProvider().generate(context())


def test_ollama_provider_reports_timeout_separately(monkeypatch):
    def fail(*args, **kwargs):
        raise socket.timeout("timed out")

    monkeypatch.setattr("providers.ollama.request.urlopen", fail)
    with pytest.raises(ProviderError, match=r"Ollama timed out after 42s.*slow-model"):
        OllamaProvider(model="slow-model", timeout=42).generate(context())


def test_ollama_provider_reports_missing_model(monkeypatch):
    def missing(req, timeout):
        payload = io.BytesIO(b'{"error":"model not found"}')
        raise error.HTTPError(req.full_url, 404, "not found", hdrs=None, fp=payload)

    monkeypatch.setattr("providers.ollama.request.urlopen", missing)
    with pytest.raises(ProviderError, match=r"ollama pull hasi-edge-AG:latest"):
        OllamaProvider(model="hasi-edge-AG:latest").generate(context())

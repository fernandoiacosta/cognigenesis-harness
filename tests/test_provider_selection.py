from pathlib import Path

from harness import build_engine
from providers.base import StubProvider
from providers.ollama import OllamaProvider


def test_harness_defaults_to_ollama(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("COGNI_PROVIDER", raising=False)
    engine = build_engine(tmp_path)
    assert isinstance(engine.provider, OllamaProvider)
    assert not isinstance(engine.provider, StubProvider)


def test_stub_requires_explicit_selection(tmp_path: Path):
    engine = build_engine(tmp_path, provider_name="stub")
    assert isinstance(engine.provider, StubProvider)


def test_ollama_env_configuration(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("COGNI_OLLAMA_BASE_URL", "http://localhost:9999")
    monkeypatch.setenv("COGNI_OLLAMA_MODEL", "hasi-edge-AG:latest")
    monkeypatch.setenv("COGNI_OLLAMA_TIMEOUT", "42")
    engine = build_engine(tmp_path)
    assert isinstance(engine.provider, OllamaProvider)
    assert engine.provider.base_url == "http://localhost:9999"
    assert engine.provider.model == "hasi-edge-AG:latest"
    assert engine.provider.timeout == 42.0

from __future__ import annotations

from cognigenesis.config import load_settings
from providers.base import ModelProvider, StubProvider
from providers.ollama import DEFAULT_OLLAMA_MODEL, OllamaProvider


def build_provider(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> ModelProvider:
    settings = load_settings()
    name = (provider or settings.provider or "ollama").strip().lower()

    if name == "ollama":
        return OllamaProvider(
            model=model or settings.model or DEFAULT_OLLAMA_MODEL,
            base_url=(base_url or settings.ollama_base_url).rstrip("/"),
            timeout=float(timeout if timeout is not None else settings.ollama_timeout),
        )
    if name == "stub":
        return StubProvider()

    raise ValueError(f"Unknown provider '{name}'. Supported providers: ollama, stub")


def provider_identity(provider: ModelProvider) -> tuple[str, str]:
    if isinstance(provider, OllamaProvider):
        return "ollama", provider.model
    if isinstance(provider, StubProvider):
        return "stub", "stub"
    return provider.__class__.__name__.lower(), provider.__class__.__name__

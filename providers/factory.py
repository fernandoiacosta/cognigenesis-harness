from __future__ import annotations

import os

from providers.base import ModelProvider, StubProvider
from providers.ollama import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_TIMEOUT,
    OllamaProvider,
)


def build_provider(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> ModelProvider:
    name = (provider or os.getenv("COGNI_PROVIDER") or "ollama").strip().lower()

    if name == "ollama":
        return OllamaProvider(
            model=model or os.getenv("COGNI_OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL,
            base_url=base_url or os.getenv("COGNI_OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL,
            timeout=float(timeout or os.getenv("COGNI_OLLAMA_TIMEOUT") or DEFAULT_OLLAMA_TIMEOUT),
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

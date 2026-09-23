from __future__ import annotations

from cognigenesis.config import load_settings
from providers.base import ModelProvider, StubProvider
from providers.ollama import DEFAULT_OLLAMA_MODEL, OllamaProvider
from providers.cloud import CloudProvider, LocalOpenAIProvider, DEFAULT_MODELS


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
    if name in {"edge", "litert"}:
        endpoint = base_url or settings.cloud_base_url or ("http://127.0.0.1:9379" if name == "litert" else None)
        if not endpoint:
            raise ValueError("Edge Gallery needs an HTTP server URL; its stock app does not expose one. Use LiteRT-LM or a server-enabled build.")
        return LocalOpenAIProvider(name, model or settings.model or "local-model", endpoint, float(timeout or settings.ollama_timeout))
    if name in DEFAULT_MODELS:
        selected = model or settings.model or DEFAULT_MODELS[name]
        if not selected:
            raise ValueError("Meta needs an explicit model: cogni login meta --model MODEL")
        return CloudProvider(name, selected, base_url or (settings.cloud_base_url if name == "meta" else None), float(timeout or settings.ollama_timeout))
    if name == "stub":
        return StubProvider()

    raise ValueError(f"Unknown provider '{name}'. Supported providers: ollama, openai, anthropic, google, grok, meta, stub")


def provider_identity(provider: ModelProvider) -> tuple[str, str]:
    if isinstance(provider, OllamaProvider):
        return "ollama", provider.model
    if isinstance(provider, (CloudProvider, LocalOpenAIProvider)):
        return provider.name, provider.model
    if isinstance(provider, StubProvider):
        return "stub", "stub"
    return provider.__class__.__name__.lower(), provider.__class__.__name__

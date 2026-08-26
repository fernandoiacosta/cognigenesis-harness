from __future__ import annotations
from abc import ABC, abstractmethod

from core.types import ModelResponse


class ProviderError(RuntimeError):
    """A user-actionable model provider failure."""


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, context: dict) -> ModelResponse:
        raise NotImplementedError


class StubProvider(ModelProvider):
    """Deterministic provider for tests and explicit demo mode only."""

    def generate(self, context: dict) -> ModelResponse:
        capabilities = ", ".join(item["id"] for item in context["capabilities"])
        return ModelResponse(
            final=(
                "Cognigenesis Harness is operational with the explicit stub provider. "
                f"Objective: {context['objective']}\n"
                f"Registered capabilities: {capabilities}"
            )
        )

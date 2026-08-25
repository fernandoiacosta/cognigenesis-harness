from __future__ import annotations
from abc import ABC, abstractmethod

from core.types import ModelResponse


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, context: dict) -> ModelResponse:
        raise NotImplementedError


class StubProvider(ModelProvider):
    """Deterministic placeholder provider used until a real adapter is selected."""

    def generate(self, context: dict) -> ModelResponse:
        capabilities = ", ".join(item["id"] for item in context["capabilities"])
        return ModelResponse(
            final=(
                "Cognigenesis Harness is operational with a stub provider. "
                f"Objective: {context['objective']}\n"
                f"Registered capabilities: {capabilities}"
            )
        )

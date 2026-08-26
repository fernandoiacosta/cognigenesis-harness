from __future__ import annotations
from typing import Any
from core.types import Capability


class CapabilityRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.id in self._items:
            raise ValueError(f"Capability already registered: {capability.id}")
        self._items[capability.id] = capability

    def get(self, capability_id: str) -> Capability | None:
        return self._items.get(capability_id)

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "id": item.id,
                "description": item.description,
                "risk": item.risk,
                "parameters": item.parameters,
            }
            for item in sorted(self._items.values(), key=lambda x: x.id)
        ]

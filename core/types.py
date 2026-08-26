from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ModelResponse:
    final: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class Capability:
    id: str
    description: str
    execute: Callable[[dict[str, Any]], Any]
    risk: str = "low"
    parameters: dict[str, Any] = field(
        default_factory=lambda: {"type": "object", "properties": {}, "additionalProperties": True}
    )

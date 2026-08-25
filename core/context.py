from __future__ import annotations
from pathlib import Path

from core.registry import CapabilityRegistry
from state.store import StateStore


class ContextCompiler:
    def __init__(self, workspace: Path, registry: CapabilityRegistry, state: StateStore) -> None:
        self.workspace = workspace
        self.registry = registry
        self.state = state

    def _read_optional(self, path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def compile(self, objective: str, history: list[dict]) -> dict:
        root = Path(__file__).resolve().parents[1]
        control = self._read_optional(root / "agent.md")
        return {
            "system": control,
            "objective": objective,
            "capabilities": self.registry.describe(),
            "state": self.state.snapshot(),
            "history": history[-20:],
        }

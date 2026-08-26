from __future__ import annotations
from pathlib import Path

from cognigenesis.resources import text as resource_text
from core.registry import CapabilityRegistry
from state.store import StateStore


class ContextCompiler:
    def __init__(self, workspace: Path, registry: CapabilityRegistry, state: StateStore) -> None:
        self.workspace = workspace
        self.registry = registry
        self.state = state

    def _control_plane(self) -> str:
        # Installed packages must not depend on repository-root files being present.
        try:
            return resource_text("agent.md")
        except Exception:
            root = Path(__file__).resolve().parents[1]
            path = root / "agent.md"
            return path.read_text(encoding="utf-8") if path.exists() else ""

    def compile(self, objective: str, history: list[dict]) -> dict:
        return {
            "system": self._control_plane(),
            "objective": objective,
            "capabilities": self.registry.describe(),
            "state": self.state.snapshot(),
            "history": history[-40:],
        }

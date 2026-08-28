from __future__ import annotations
from pathlib import Path

from cognigenesis.cognition.ledger import CognitiveLedger
from cognigenesis.resources import text as resource_text
from cognigenesis.runtime.taskgraph import TaskGraph
from core.registry import CapabilityRegistry
from state.store import StateStore


class ContextCompiler:
    def __init__(
        self,
        workspace: Path,
        registry: CapabilityRegistry,
        state: StateStore,
        *,
        cognition: CognitiveLedger | None = None,
        tasks: TaskGraph | None = None,
    ) -> None:
        self.workspace = workspace
        self.registry = registry
        self.state = state
        self.cognition = cognition
        self.tasks = tasks

    def _control_plane(self) -> str:
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
            "cognition": self.cognition.snapshot() if self.cognition else {},
            "tasks": self.tasks.snapshot() if self.tasks else [],
            "history": history[-40:],
        }

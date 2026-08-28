from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cognigenesis.cognition.ledger import CognitiveLedger
from cognigenesis.fabric.team import TeamManager
from cognigenesis.runtime.events import EventBus
from cognigenesis.runtime.taskgraph import TaskGraph


@dataclass
class CommandCenterSnapshot:
    """UI-neutral projection shared by terminal, ACP, and future GUI."""

    tasks: TaskGraph
    cognition: CognitiveLedger
    events: EventBus
    teams: TeamManager | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": self.tasks.snapshot(),
            "cognition": self.cognition.snapshot(),
            "teams": self.teams.snapshot() if self.teams else [],
            "events": [event.to_dict() for event in self.events.history(limit=100)],
        }

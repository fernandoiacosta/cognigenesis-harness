from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cognigenesis.cognition.ledger import CognitiveLedger
from cognigenesis.runtime.events import EventBus
from cognigenesis.runtime.taskgraph import TaskGraph


@dataclass
class CommandCenterSnapshot:
    """A UI-neutral projection of runtime state.

    The future graphical Command Center, terminal TUI, and remote API can all
    render the same snapshot rather than inventing separate state models.
    """

    tasks: TaskGraph
    cognition: CognitiveLedger
    events: EventBus

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": self.tasks.snapshot(),
            "cognition": self.cognition.snapshot(),
            "events": [event.to_dict() for event in self.events.history(limit=100)],
        }

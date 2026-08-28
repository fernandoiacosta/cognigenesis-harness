from __future__ import annotations

from dataclasses import dataclass

from cognigenesis.cognition.ledger import CognitiveLedger
from cognigenesis.commandcenter.snapshot import CommandCenterSnapshot
from cognigenesis.fabric.team import TeamManager
from cognigenesis.runtime.events import EventBus
from cognigenesis.runtime.taskgraph import TaskGraph


@dataclass
class PlatformServices:
    """Shared stateful services surrounding a single agent runtime."""

    events: EventBus
    tasks: TaskGraph
    cognition: CognitiveLedger
    teams: TeamManager

    @classmethod
    def create(cls) -> "PlatformServices":
        events = EventBus()
        return cls(
            events=events,
            tasks=TaskGraph(),
            cognition=CognitiveLedger(),
            teams=TeamManager(events),
        )

    def command_center_snapshot(self) -> CommandCenterSnapshot:
        return CommandCenterSnapshot(
            tasks=self.tasks,
            cognition=self.cognition,
            events=self.events,
            teams=self.teams,
        )

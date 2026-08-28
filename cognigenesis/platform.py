from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from cognigenesis.cognition.ledger import CognitiveLedger
from cognigenesis.commandcenter.snapshot import CommandCenterSnapshot
from cognigenesis.commandcenter.store import CommandCenterStore
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
    snapshot_store: CommandCenterStore | None = None
    _unsubscribe_snapshot: Callable[[], None] | None = field(default=None, repr=False)

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

    def bind_workspace(self, workspace: Path) -> None:
        path = workspace.resolve() / ".cognigenesis" / "command-center.json"
        if self.snapshot_store is not None and self.snapshot_store.path == path:
            return
        if self._unsubscribe_snapshot:
            self._unsubscribe_snapshot()

        self.snapshot_store = CommandCenterStore(path)

        def persist(_event=None) -> None:
            if self.snapshot_store:
                self.snapshot_store.save(self.command_center_snapshot().to_dict())

        self._unsubscribe_snapshot = self.events.subscribe(persist)
        persist()

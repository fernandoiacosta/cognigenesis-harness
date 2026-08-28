from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import uuid4


class TaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    title: str
    description: str = ""
    id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str | None = None
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class TaskGraph:
    """Small deterministic task/dependency graph for teams and single agents."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = RLock()

    def add(self, task: Task) -> Task:
        with self._lock:
            if task.id in self._tasks:
                raise ValueError(f"Duplicate task id: {task.id}")
            unknown = [dep for dep in task.dependencies if dep not in self._tasks]
            if unknown:
                raise ValueError(f"Unknown task dependencies: {unknown}")
            self._tasks[task.id] = task
            self._refresh_readiness()
        return task

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)

    def update_status(self, task_id: str, status: TaskStatus, *, result: Any = None) -> Task:
        with self._lock:
            task = self._tasks[task_id]
            task.status = status
            if result is not None:
                task.result = result
            self._refresh_readiness()
            return task

    def assign(self, task_id: str, agent_id: str) -> Task:
        with self._lock:
            task = self._tasks[task_id]
            task.assigned_agent = agent_id
            return task

    def ready(self) -> list[Task]:
        with self._lock:
            self._refresh_readiness()
            return [task for task in self._tasks.values() if task.status == TaskStatus.READY]

    def all(self) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())

    def snapshot(self) -> list[dict[str, Any]]:
        return [task.to_dict() for task in self.all()]

    def _refresh_readiness(self) -> None:
        for task in self._tasks.values():
            if task.status not in {TaskStatus.PENDING, TaskStatus.READY}:
                continue
            if all(
                self._tasks[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
            ):
                task.status = TaskStatus.READY
            else:
                task.status = TaskStatus.PENDING

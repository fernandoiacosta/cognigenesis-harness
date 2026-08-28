from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from threading import RLock
from typing import Any, Callable
from uuid import uuid4


class EventType(StrEnum):
    TURN_STARTED = "turn.started"
    MODEL_STARTED = "model.started"
    MODEL_COMPLETED = "model.completed"
    TOOL_REQUESTED = "tool.requested"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    POLICY_DENIED = "policy.denied"
    CAPABILITY_GAP = "capability.gap"
    ARTIFACT_CREATED = "artifact.created"
    TASK_UPDATED = "task.updated"
    COGNITION_UPDATED = "cognition.updated"
    AGENT_MESSAGE = "agent.message"
    TURN_COMPLETED = "turn.completed"
    TURN_FAILED = "turn.failed"
    TURN_CANCELLED = "turn.cancelled"


@dataclass(frozen=True)
class RuntimeEvent:
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    turn_id: str | None = None
    source: str = "runtime"
    id: str = field(default_factory=lambda: uuid4().hex)
    time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = self.type.value
        return data


Subscriber = Callable[[RuntimeEvent], None]


class EventBus:
    """Thread-safe in-process semantic event bus.

    Interfaces (TUI, ACP, future GUI), tracing, and orchestration consume the
    same runtime events instead of scraping logs or coupling to provider code.
    """

    def __init__(self, history_limit: int = 2000) -> None:
        self._subscribers: list[Subscriber] = []
        self._history: list[RuntimeEvent] = []
        self._history_limit = history_limit
        self._lock = RLock()

    def subscribe(self, callback: Subscriber) -> Callable[[], None]:
        with self._lock:
            self._subscribers.append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return unsubscribe

    def emit(
        self,
        event_type: EventType,
        payload: dict[str, Any] | None = None,
        *,
        session_id: str | None = None,
        turn_id: str | None = None,
        source: str = "runtime",
    ) -> RuntimeEvent:
        event = RuntimeEvent(
            type=event_type,
            payload=payload or {},
            session_id=session_id,
            turn_id=turn_id,
            source=source,
        )
        with self._lock:
            self._history.append(event)
            self._history = self._history[-self._history_limit :]
            subscribers = list(self._subscribers)
        for callback in subscribers:
            try:
                callback(event)
            except Exception:
                # Observability/UI subscribers are never allowed to break execution.
                continue
        return event

    def history(self, limit: int | None = None) -> list[RuntimeEvent]:
        with self._lock:
            items = list(self._history)
        return items[-limit:] if limit else items

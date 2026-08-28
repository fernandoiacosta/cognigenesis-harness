from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class MessageKind(StrEnum):
    TASK = "task"
    FINDING = "finding"
    HYPOTHESIS = "hypothesis"
    EVIDENCE = "evidence"
    QUESTION = "question"
    CRITIQUE = "critique"
    DECISION = "decision"
    HANDOFF = "handoff"
    STATUS = "status"
    ARTIFACT = "artifact"


@dataclass(frozen=True)
class AgentMessage:
    sender: str
    recipient: str
    kind: MessageKind
    content: str
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    reply_to: str | None = None
    id: str = field(default_factory=lambda: uuid4().hex)
    time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data

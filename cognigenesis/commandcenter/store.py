from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CommandCenterStore:
    """Atomic persisted projection for external/UI readers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, payload: dict[str, Any]) -> None:
        document = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "updated_at": None,
                "tasks": [],
                "cognition": {
                    "hypotheses": [],
                    "evidence": [],
                    "open_questions": [],
                    "metrics": {
                        "active_hypotheses": 0,
                        "contradictions": 0,
                        "unresolved_questions": 0,
                    },
                },
                "teams": [],
                "events": [],
            }
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"error": "Command Center state is temporarily unavailable.", "tasks": [], "teams": [], "events": []}

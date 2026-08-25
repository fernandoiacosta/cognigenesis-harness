from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"objective": None, "completed": [], "open_goals": [], "events": [], "artifacts": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def set_objective(self, objective: str) -> None:
        self.data["objective"] = objective
        self._save()

    def record_event(self, event_type: str, payload: dict) -> None:
        self.data["events"].append({"time": datetime.now(timezone.utc).isoformat(), "type": event_type, "payload": payload})
        self.data["events"] = self.data["events"][-200:]
        self._save()

    def snapshot(self) -> dict:
        return {
            "objective": self.data.get("objective"),
            "completed": self.data.get("completed", []),
            "open_goals": self.data.get("open_goals", []),
            "artifacts": self.data.get("artifacts", []),
            "recent_events": self.data.get("events", [])[-10:],
        }

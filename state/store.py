from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    @staticmethod
    def _empty() -> dict:
        return {
            "objective": None,
            "completed": [],
            "open_goals": [],
            "events": [],
            "artifacts": [],
            "conversation": [],
        }

    def _load(self) -> dict:
        if not self.path.exists():
            return self._empty()
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Preserve a corrupt state file for diagnosis instead of silently destroying it.
            corrupt = self.path.with_suffix(self.path.suffix + ".corrupt")
            try:
                self.path.replace(corrupt)
            except OSError:
                pass
            return self._empty()
        data = self._empty()
        data.update(loaded if isinstance(loaded, dict) else {})
        return data

    def _save(self) -> None:
        payload = json.dumps(self.data, indent=2, ensure_ascii=False) + "\n"
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(payload, encoding="utf-8")
        temp.replace(self.path)

    def set_objective(self, objective: str) -> None:
        self.data["objective"] = objective
        self._save()

    def record_event(self, event_type: str, payload: dict) -> None:
        self.data["events"].append({"time": datetime.now(timezone.utc).isoformat(), "type": event_type, "payload": payload})
        self.data["events"] = self.data["events"][-200:]
        self._save()

    def conversation(self) -> list[dict]:
        value = self.data.get("conversation", [])
        return list(value) if isinstance(value, list) else []

    def set_conversation(self, history: list[dict]) -> None:
        self.data["conversation"] = history[-80:]
        self._save()

    def snapshot(self) -> dict:
        return {
            "objective": self.data.get("objective"),
            "completed": self.data.get("completed", []),
            "open_goals": self.data.get("open_goals", []),
            "artifacts": self.data.get("artifacts", []),
            "conversation_turns": len(self.data.get("conversation", [])),
            "recent_events": self.data.get("events", [])[-10:],
        }

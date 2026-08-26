from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from cognigenesis.config import data_dir
from core.model_profile import ModelProfile


PROFILE_SCHEMA_VERSION = 1


def _key(provider: str, model: str) -> str:
    digest = hashlib.sha256(f"{provider}\0{model}".encode("utf-8")).hexdigest()[:16]
    return f"{provider}-{digest}.json"


def profile_path(provider: str, model: str) -> Path:
    path = data_dir() / "profiles" / _key(provider, model)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_profile(profile: ModelProfile, evidence: list[dict]) -> Path:
    path = profile_path(profile.provider, profile.model)
    payload = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "qualified_at": datetime.now(timezone.utc).isoformat(),
        "profile": asdict(profile),
        "evidence": evidence,
    }
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)
    return path


def load_profile(provider: str, model: str) -> ModelProfile | None:
    path = profile_path(provider, model)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = payload["profile"]
        if raw.get("provider") != provider or raw.get("model") != model:
            return None
        return ModelProfile(**raw)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def profile_metadata(provider: str, model: str) -> dict | None:
    path = profile_path(provider, model)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            "path": str(path),
            "qualified_at": payload.get("qualified_at"),
            "schema_version": payload.get("schema_version"),
        }
    except (OSError, json.JSONDecodeError):
        return None

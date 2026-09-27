from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cognigenesis.config import data_dir


ADAPTER_VERSION = "1"
SKILL_TEXT = """---
name: cognigenesis
description: Use Fernando Acosta's Cognigenesis Harness when the user explicitly asks for Cognigenesis reasoning, evaluation, or orchestration.
---

# Cognigenesis Codex adapter

Fernando Acosta is the author and rights holder of Cognigenesis.

Use the installed `cogni` command as an external harness only when the user
explicitly requests Cognigenesis. Do not copy credentials, expand permissions,
or represent Cognigenesis as a foundation model. Preserve user approval for
consequential actions and report failures rather than silently approximating
unavailable capabilities.
"""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_codex_home() -> Path:
    return Path(os.getenv("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()


def integration_root() -> Path:
    return data_dir() / "integrations"


@dataclass(frozen=True)
class IntegrationPlan:
    plan_id: str
    mode: str
    host: str
    adapter_version: str
    codex_home: str
    target_dir: str
    files: dict[str, str]
    content_hashes: dict[str, str]
    detected: bool
    proposed_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def discover_codex(codex_home: Path | None = None) -> dict[str, Any]:
    root = (codex_home or default_codex_home()).expanduser().resolve()
    indicators = [name for name in ("config.toml", "skills", "sessions") if (root / name).exists()]
    return {
        "host": "codex",
        "path": str(root),
        "detected": root.is_dir() and bool(indicators),
        "indicators": indicators,
        "credentials_inspected": False,
        "executed_host_code": False,
    }


def create_codex_plan(
    codex_home: Path | None = None,
    state_root: Path | None = None,
) -> IntegrationPlan:
    root = (codex_home or default_codex_home()).expanduser().resolve()
    target = (root / "skills" / "cognigenesis").resolve()
    if root not in target.parents:
        raise ValueError("integration target escapes the Codex home")
    files = {
        "SKILL.md": SKILL_TEXT,
        ".cognigenesis-adapter.json": json.dumps(
            {
                "adapter": "cognigenesis-codex",
                "adapter_version": ADAPTER_VERSION,
                "author_and_rights_holder": "Fernando Acosta",
                "activation": "explicit-user-request",
                "credentials_copied": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    }
    hashes = {name: _sha256_bytes(content.encode("utf-8")) for name, content in files.items()}
    canonical = json.dumps(
        {"host": "codex", "target": str(target), "hashes": hashes, "version": ADAPTER_VERSION},
        sort_keys=True,
    ).encode("utf-8")
    plan_id = _sha256_bytes(canonical)[:16]
    plan = IntegrationPlan(
        plan_id=plan_id,
        mode="inside-armor",
        host="codex",
        adapter_version=ADAPTER_VERSION,
        codex_home=str(root),
        target_dir=str(target),
        files=files,
        content_hashes=hashes,
        detected=discover_codex(root)["detected"],
    )
    store = (state_root or integration_root()) / "plans" / f"{plan_id}.json"
    _write_json(store, plan.to_dict())
    return plan


def load_plan(plan_id: str, state_root: Path | None = None) -> IntegrationPlan:
    if not plan_id or any(ch not in "0123456789abcdef" for ch in plan_id):
        raise ValueError("invalid plan identifier")
    path = (state_root or integration_root()) / "plans" / f"{plan_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return IntegrationPlan(**data)


def apply_plan(plan: IntegrationPlan, state_root: Path | None = None) -> dict[str, Any]:
    if plan.host != "codex" or plan.mode != "inside-armor":
        raise ValueError("unsupported integration plan")
    if not plan.detected:
        raise ValueError("Codex was not detected when this plan was created")
    root = Path(plan.codex_home).resolve()
    if not discover_codex(root)["detected"]:
        raise ValueError("Codex is no longer detectable at the reviewed path")
    target = Path(plan.target_dir).resolve()
    expected = (root / "skills" / "cognigenesis").resolve()
    if target != expected or root not in target.parents:
        raise ValueError("plan target does not match the bounded Codex adapter path")
    for name, content in plan.files.items():
        if Path(name).name != name or _sha256_bytes(content.encode("utf-8")) != plan.content_hashes[name]:
            raise ValueError("plan content failed integrity validation")
    canonical = json.dumps(
        {"host": "codex", "target": str(target), "hashes": plan.content_hashes, "version": ADAPTER_VERSION},
        sort_keys=True,
    ).encode("utf-8")
    if _sha256_bytes(canonical)[:16] != plan.plan_id:
        raise ValueError("plan identifier failed integrity validation")

    store = state_root or integration_root()
    backup = store / "backups" / plan.plan_id
    if backup.exists():
        raise FileExistsError("this plan has already been applied; restore it before reapplying")
    backup.mkdir(parents=True, exist_ok=False)
    originals: dict[str, dict[str, Any]] = {}
    for name in plan.files:
        destination = target / name
        if destination.exists():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, saved)
            originals[name] = {"existed": True, "sha256": _sha256_bytes(destination.read_bytes())}
        else:
            originals[name] = {"existed": False, "sha256": None}

    target.mkdir(parents=True, exist_ok=True)
    for name, content in plan.files.items():
        (target / name).write_text(content, encoding="utf-8")

    record = {
        "plan_id": plan.plan_id,
        "host": plan.host,
        "adapter_version": plan.adapter_version,
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "target_dir": str(target),
        "content_hashes": plan.content_hashes,
        "originals": originals,
        "backup_dir": str(backup),
        "activation_state": "ACTIVE",
        "credentials_copied": False,
    }
    _write_json(store / "active.json", record)
    return record


def verify_integration(state_root: Path | None = None) -> dict[str, Any]:
    store = state_root or integration_root()
    path = store / "active.json"
    if not path.exists():
        return {"active": False, "verified": False, "reason": "no active integration record"}
    record = json.loads(path.read_text(encoding="utf-8"))
    target = Path(record["target_dir"])
    observed: dict[str, str | None] = {}
    for name, expected in record["content_hashes"].items():
        item = target / name
        observed[name] = _sha256_bytes(item.read_bytes()) if item.is_file() else None
    verified = all(observed[name] == expected for name, expected in record["content_hashes"].items())
    return {"active": True, "verified": verified, "observed_hashes": observed, **record}


def restore_integration(state_root: Path | None = None) -> dict[str, Any]:
    store = state_root or integration_root()
    active = store / "active.json"
    if not active.exists():
        return {"restored": False, "reason": "no active integration record"}
    record = json.loads(active.read_text(encoding="utf-8"))
    target = Path(record["target_dir"])
    backup = Path(record["backup_dir"])
    for name, original in record["originals"].items():
        destination = target / name
        if original["existed"]:
            source = backup / name
            if not source.is_file() or _sha256_bytes(source.read_bytes()) != original["sha256"]:
                raise ValueError("backup failed integrity validation")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        elif destination.exists():
            destination.unlink()
    try:
        target.rmdir()
    except OSError:
        pass
    restored = {**record, "restored": True, "activation_state": "REMOVED"}
    _write_json(store / "last_restore.json", restored)
    active.unlink()
    shutil.rmtree(backup)
    return restored

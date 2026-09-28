#!/usr/bin/env python3
"""Installed-package acceptance for the bounded Codex Inside Armor lifecycle.

This script never touches the operator's real Codex home. It creates an isolated
Codex-shaped fixture, exercises discover -> plan -> apply -> verify -> restore,
and fails unless the pre-existing skill content is restored byte-for-byte.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _run(args: list[str], env: dict[str, str]) -> dict[str, Any]:
    command = [sys.executable, "-m", "cli", *args, "--json"]
    result = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command returned non-JSON output: {result.stdout!r}") from exc


def main() -> int:
    original = b"existing Codex skill content\n"
    with tempfile.TemporaryDirectory(prefix="cogni-codex-accept-") as raw:
        root = Path(raw)
        codex_home = root / ".codex"
        skill_dir = codex_home / "skills" / "cognigenesis"
        skill_dir.mkdir(parents=True)
        (codex_home / "config.toml").write_text("model = 'acceptance-fixture'\n", encoding="utf-8")
        (skill_dir / "SKILL.md").write_bytes(original)

        env = os.environ.copy()
        env.update(
            {
                "CODEX_HOME": str(codex_home),
                "XDG_DATA_HOME": str(root / "xdg-data"),
                "XDG_CONFIG_HOME": str(root / "xdg-config"),
                "LOCALAPPDATA": str(root / "local-app-data"),
                "APPDATA": str(root / "app-data"),
                "NO_COLOR": "1",
            }
        )

        discovered = _run(["integrate", "discover"], env)
        if not discovered.get("detected") or discovered.get("credentials_inspected"):
            raise RuntimeError("Codex discovery did not satisfy the non-executing contract")

        plan = _run(
            ["integrate", "plan", "--mode", "inside-armor", "--host", "codex"],
            env,
        )
        if not plan.get("proposed_only") or not plan.get("detected"):
            raise RuntimeError("integration plan was not a detected, proposed-only plan")

        applied = _run(["integrate", "apply", str(plan["plan_id"])], env)
        if applied.get("activation_state") != "ACTIVE" or applied.get("credentials_copied"):
            raise RuntimeError("integration apply violated the activation contract")

        verified = _run(["integrate", "verify"], env)
        if not verified.get("verified"):
            raise RuntimeError("integration hashes did not verify")

        restored = _run(["integrate", "restore"], env)
        if not restored.get("restored"):
            raise RuntimeError("integration did not report successful restoration")
        if (skill_dir / "SKILL.md").read_bytes() != original:
            raise RuntimeError("pre-existing Codex skill content was not restored byte-for-byte")
        if (skill_dir / ".cognigenesis-adapter.json").exists():
            raise RuntimeError("adapter manifest remained after restoration")

        report = {
            "result": "PASS",
            "scope": "isolated installed-package Codex lifecycle",
            "python": sys.version.split()[0],
            "plan_id": plan["plan_id"],
            "adapter_version": applied["adapter_version"],
            "verified_hashes": verified["observed_hashes"],
            "restored_preexisting_content": True,
            "credentials_inspected": False,
            "credentials_copied": False,
            "real_device_acceptance": False,
        }
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

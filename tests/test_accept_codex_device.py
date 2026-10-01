from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_device_acceptance_script_restores_fixture(tmp_path: Path) -> None:
    codex = tmp_path / ".codex"
    target = codex / "skills" / "cognigenesis"
    target.mkdir(parents=True)
    (codex / "config.toml").write_text("model = 'test'\n", encoding="utf-8")
    original = b"existing skill\n"
    (target / "SKILL.md").write_bytes(original)
    output = tmp_path / "acceptance.json"
    env = os.environ.copy()
    env.update(
        CODEX_HOME=str(codex),
        XDG_DATA_HOME=str(tmp_path / "xdg-data"),
        LOCALAPPDATA=str(tmp_path / "local-app-data"),
        APPDATA=str(tmp_path / "app-data"),
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/accept_codex_device.py",
            "--apply",
            "--output",
            str(output),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["result"] == "PASS"
    assert report["real_device_acceptance"] is True
    assert report["credentials_inspected"] is False
    assert report["preexisting_content_restored"] is True
    assert (target / "SKILL.md").read_bytes() == original
    assert not (target / ".cognigenesis-adapter.json").exists()

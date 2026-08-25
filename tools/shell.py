from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from core.registry import CapabilityRegistry
from core.types import Capability


def register_shell_tools(registry: CapabilityRegistry, workspace: Path) -> None:
    workspace = workspace.resolve()

    def run(args: dict):
        command = args["command"]
        argv = shlex.split(command)
        if not argv:
            raise ValueError("Empty command")

        result = subprocess.run(
            argv,
            cwd=workspace,
            shell=False,
            capture_output=True,
            text=True,
            timeout=int(args.get("timeout", 60)),
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-20000:],
            "stderr": result.stderr[-20000:],
        }

    registry.register(Capability("shell.run", "Run a command without shell interpolation inside the workspace.", run, risk="medium"))

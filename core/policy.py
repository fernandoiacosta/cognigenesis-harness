from __future__ import annotations
from pathlib import Path


class Policy:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()

    def authorize(self, capability_id: str, arguments: dict) -> tuple[bool, str]:
        # Initial conservative policy. Expand with explicit permission metadata.
        if capability_id.startswith(("filesystem.", "workspace.", "core.", "shell.")):
            return True, "allowed by default workspace policy"
        return False, f"capability not approved by policy: {capability_id}"

from __future__ import annotations
from pathlib import Path
from core.registry import CapabilityRegistry
from core.types import Capability


def _safe_path(workspace: Path, raw: str) -> Path:
    candidate = (workspace / raw).resolve()
    if candidate != workspace and workspace not in candidate.parents:
        raise PermissionError(f"Path escapes workspace: {raw}")
    return candidate


def register_filesystem_tools(registry: CapabilityRegistry, workspace: Path) -> None:
    workspace = workspace.resolve()

    def read_file(args: dict):
        path = _safe_path(workspace, args["path"])
        return path.read_text(encoding="utf-8")

    def write_file(args: dict):
        path = _safe_path(workspace, args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args.get("content", ""), encoding="utf-8")
        return {"path": str(path.relative_to(workspace)), "bytes": path.stat().st_size}

    def list_files(args: dict):
        path = _safe_path(workspace, args.get("path", "."))
        if not path.exists():
            return []
        return sorted(str(item.relative_to(workspace)) for item in path.rglob("*") if item.is_file())

    registry.register(Capability("filesystem.read", "Read a UTF-8 file inside the workspace.", read_file))
    registry.register(Capability("filesystem.write", "Write a UTF-8 file inside the workspace.", write_file))
    registry.register(Capability("filesystem.list", "List files inside the workspace.", list_files))

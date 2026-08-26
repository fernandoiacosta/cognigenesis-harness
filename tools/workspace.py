from __future__ import annotations
from pathlib import Path
from core.registry import CapabilityRegistry
from core.types import Capability


def register_workspace_tools(registry: CapabilityRegistry, workspace: Path) -> None:
    workspace = workspace.resolve()

    def create_project(args: dict):
        name = args["name"].strip().replace("/", "-").replace("\\", "-")
        if not name or name in {".", ".."}:
            raise ValueError("Invalid project name")
        root = (workspace / name).resolve()
        if workspace not in root.parents:
            raise PermissionError("Project must remain inside workspace")
        root.mkdir(parents=True, exist_ok=True)
        defaults = {
            "README.md": f"# {name}\n",
            "BLUEPRINT.md": "# Blueprint\n",
            "REQUIREMENTS.md": "# Requirements\n",
        }
        created = []
        for rel, content in defaults.items():
            path = root / rel
            if not path.exists():
                path.write_text(content, encoding="utf-8")
                created.append(str(path.relative_to(workspace)))
        return {"project": name, "created": created}

    registry.register(Capability(
        "workspace.create_project",
        "Create a project directory and foundational Markdown artifacts safely inside the workspace.",
        create_project,
        parameters={
            "type":"object",
            "properties":{"name":{"type":"string","minLength":1}},
            "required":["name"],
            "additionalProperties":False,
        },
    ))

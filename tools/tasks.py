from __future__ import annotations

from cognigenesis.runtime.taskgraph import Task, TaskGraph, TaskStatus
from core.registry import CapabilityRegistry
from core.types import Capability


def register_task_tools(registry: CapabilityRegistry, graph: TaskGraph) -> None:
    def add_task(args: dict):
        task = graph.add(Task(
            title=str(args["title"]),
            description=str(args.get("description", "")),
            dependencies=list(args.get("dependencies", [])),
        ))
        return task.to_dict()

    def update_task(args: dict):
        status = TaskStatus(str(args["status"]))
        task = graph.update_status(args["task_id"], status, result=args.get("result"))
        return task.to_dict()

    registry.register(Capability(
        "task.add",
        "Add an explicit task to the shared mission task graph. Dependencies must reference existing task IDs.",
        add_task,
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "dependencies": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title"],
            "additionalProperties": False,
        },
    ))
    registry.register(Capability(
        "task.update",
        "Update task execution status/result in the shared mission graph.",
        update_task,
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "ready", "running", "blocked", "completed", "failed", "cancelled"],
                },
                "result": {},
            },
            "required": ["task_id", "status"],
            "additionalProperties": False,
        },
    ))
    registry.register(Capability(
        "task.list",
        "Inspect the current shared mission task graph.",
        lambda _args: graph.snapshot(),
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
    ))

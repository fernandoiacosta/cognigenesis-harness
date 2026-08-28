from __future__ import annotations

import argparse
from pathlib import Path
from threading import Event

from cognigenesis.platform import PlatformServices
from cognigenesis.profiles import load_profile
from core.context import ContextCompiler
from core.engine import ExecutionEngine
from core.policy import Policy
from core.qualification import conservative_profile
from core.registry import CapabilityRegistry
from core.stdio import configure_utf8_stdio
from providers.factory import build_provider, provider_identity
from state.store import StateStore
from tools.cognition import register_cognition_tools
from tools.filesystem import register_filesystem_tools
from tools.shell import register_shell_tools
from tools.tasks import register_task_tools
from tools.web import register_web_tools
from tools.workspace import register_workspace_tools


def build_engine(
    workspace: Path,
    cancel_event: Event | None = None,
    state_path: Path | None = None,
    *,
    provider_name: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
    services: PlatformServices | None = None,
    session_id: str | None = None,
) -> ExecutionEngine:
    platform = services or PlatformServices.create()
    registry = CapabilityRegistry()
    register_filesystem_tools(registry, workspace)
    register_shell_tools(registry, workspace)
    register_web_tools(registry)
    register_workspace_tools(registry, workspace)
    register_cognition_tools(registry, platform.cognition, platform.events)
    register_task_tools(registry, platform.tasks, platform.events)

    state = StateStore(state_path or workspace / ".cognigenesis" / "state.json")
    provider = build_provider(provider_name, model=model, base_url=base_url, timeout=timeout)
    provider_id, model_id = provider_identity(provider)

    model_profile = load_profile(provider_id, model_id) or conservative_profile(provider_id, model_id)
    policy = Policy(workspace=workspace, model_profile=model_profile)
    compiler = ContextCompiler(
        workspace=workspace,
        registry=registry,
        state=state,
        cognition=platform.cognition,
        tasks=platform.tasks,
    )

    return ExecutionEngine(
        provider=provider,
        registry=registry,
        policy=policy,
        context_compiler=compiler,
        state=state,
        max_steps=12,
        cancel_event=cancel_event,
        event_bus=platform.events,
        task_graph=platform.tasks,
        cognition=platform.cognition,
        team_manager=platform.teams,
        session_id=session_id,
    )


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Cognigenesis Harness direct runner")
    parser.add_argument("objective", help="Objective for the harness")
    parser.add_argument("--workspace", default="workspace", help="Sandbox workspace directory")
    parser.add_argument("--provider", default=None, choices=["ollama", "stub"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--timeout", default=None, type=float)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    engine = build_engine(
        workspace,
        provider_name=args.provider,
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    print(engine.run(args.objective))


if __name__ == "__main__":
    main()

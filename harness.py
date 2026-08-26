from __future__ import annotations

import argparse
from pathlib import Path
from threading import Event

from core.context import ContextCompiler
from core.engine import ExecutionEngine
from core.policy import Policy
from core.qualification import conservative_profile
from core.registry import CapabilityRegistry
from providers.base import StubProvider
from state.store import StateStore
from tools.filesystem import register_filesystem_tools
from tools.shell import register_shell_tools
from tools.workspace import register_workspace_tools


def build_engine(
    workspace: Path,
    cancel_event: Event | None = None,
    state_path: Path | None = None,
) -> ExecutionEngine:
    registry = CapabilityRegistry()
    register_filesystem_tools(registry, workspace)
    register_shell_tools(registry, workspace)
    register_workspace_tools(registry, workspace)

    state = StateStore(state_path or workspace / ".cognigenesis" / "state.json")
    provider = StubProvider()

    # Models begin conservatively restricted. Provider-specific qualification
    # may replace this bootstrap profile after measured evaluation.
    model_profile = conservative_profile("stub", "stub")
    policy = Policy(workspace=workspace, model_profile=model_profile)
    compiler = ContextCompiler(workspace=workspace, registry=registry, state=state)

    return ExecutionEngine(
        provider=provider,
        registry=registry,
        policy=policy,
        context_compiler=compiler,
        state=state,
        max_steps=12,
        cancel_event=cancel_event,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognigenesis minimal agent harness")
    parser.add_argument("objective", help="Objective for the harness")
    parser.add_argument("--workspace", default="workspace", help="Sandbox workspace directory")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    engine = build_engine(workspace)
    result = engine.run(args.objective)
    print(result)


if __name__ == "__main__":
    main()

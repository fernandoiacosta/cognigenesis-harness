from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Any
from uuid import uuid4

from acp import (
    Agent,
    InitializeResponse,
    NewSessionResponse,
    PromptResponse,
    run_agent,
    text_block,
    update_agent_message,
)
from acp.interfaces import Client
from acp.schema import (
    AudioContentBlock,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    McpServerStdio,
    ResourceContentBlock,
    SseMcpServer,
    TextContentBlock,
)

from core.engine import ExecutionEngine
from harness import build_engine


ACP_SOURCE = "Cognigenesis"


@dataclass
class AcpSession:
    workspace: Path
    engine: ExecutionEngine
    cancel_event: Event
    prompt_lock: asyncio.Lock


def extract_text(blocks: list[Any]) -> str:
    """Extract user text from ACP content blocks without assuming one SDK representation."""
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, dict):
            block_type = block.get("type")
            text = block.get("text")
        else:
            block_type = getattr(block, "type", None)
            text = getattr(block, "text", None)

        if block_type == "text" and isinstance(text, str):
            parts.append(text)

    return "\n".join(part for part in parts if part).strip()


class CognigenesisAcpAgent(Agent):
    """ACP-over-stdio adapter around the existing Cognigenesis execution kernel."""

    _conn: Client

    def __init__(self) -> None:
        self._sessions: dict[str, AcpSession] = {}

    def on_connect(self, conn: Client) -> None:
        self._conn = conn

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: Any,
    ) -> InitializeResponse:
        # Echo the negotiated version as recommended by the current ACP Python SDK.
        return InitializeResponse(protocol_version=protocol_version)

    async def new_session(
        self,
        cwd: str,
        additional_directories: list[str] | None = None,
        mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None,
        **kwargs: Any,
    ) -> NewSessionResponse:
        workspace = Path(cwd).expanduser().resolve()
        if not workspace.is_dir():
            raise ValueError(f"ACP session cwd is not a directory: {workspace}")

        # Additional directories and client-provided MCP servers are deliberately not
        # granted automatically. Cognigenesis keeps its own capability/policy boundary.
        _ = additional_directories, mcp_servers

        session_id = uuid4().hex
        cancel_event = Event()
        state_path = workspace / ".cognigenesis" / "sessions" / f"{session_id}.json"
        engine = build_engine(
            workspace,
            cancel_event=cancel_event,
            state_path=state_path,
        )
        self._sessions[session_id] = AcpSession(
            workspace=workspace,
            engine=engine,
            cancel_event=cancel_event,
            prompt_lock=asyncio.Lock(),
        )
        return NewSessionResponse(session_id=session_id)

    async def prompt(
        self,
        session_id: str,
        prompt: list[
            TextContentBlock
            | ImageContentBlock
            | AudioContentBlock
            | ResourceContentBlock
            | EmbeddedResourceContentBlock
        ],
        **kwargs: Any,
    ) -> PromptResponse:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Unknown ACP session: {session_id}")

        objective = extract_text(prompt)
        if not objective:
            await self._send_text(
                session_id,
                "Cognigenesis currently accepts text prompts over ACP.",
            )
            return PromptResponse(stop_reason="end_turn")

        async with session.prompt_lock:
            session.cancel_event.clear()
            result = await asyncio.to_thread(session.engine.run, objective)
            cancelled = session.cancel_event.is_set()
            await self._send_text(session_id, result)
            return PromptResponse(stop_reason="cancelled" if cancelled else "end_turn")

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        session = self._sessions.get(session_id)
        if session is not None:
            session.cancel_event.set()

    async def _send_text(self, session_id: str, text: str) -> None:
        update = update_agent_message(text_block(text))
        await self._conn.session_update(
            session_id=session_id,
            update=update,
            source=ACP_SOURCE,
        )


async def _main() -> None:
    # ACP owns stdout. Do not print logs or banners from this entry point.
    await run_agent(CognigenesisAcpAgent())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()

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
from core.stdio import configure_utf8_stdio
from harness import build_engine
from providers.base import ProviderError

ACP_SOURCE = "Cognigenesis"


@dataclass
class AcpSession:
    workspace: Path
    engine: ExecutionEngine
    cancel_event: Event
    prompt_lock: asyncio.Lock


def extract_text(blocks: list[Any]) -> str:
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
    """Python-native ACP-over-stdio adapter. No Node/.cmd subprocess hop is used."""

    _conn: Client

    def __init__(self) -> None:
        self._sessions: dict[str, AcpSession] = {}

    def on_connect(self, conn: Client) -> None:
        self._conn = conn

    async def initialize(self, protocol_version: int, client_capabilities: ClientCapabilities | None = None, client_info: Implementation | None = None, **kwargs: Any) -> InitializeResponse:
        return InitializeResponse(protocol_version=protocol_version)

    async def new_session(self, cwd: str, additional_directories: list[str] | None = None, mcp_servers: list[HttpMcpServer | SseMcpServer | McpServerStdio] | None = None, **kwargs: Any) -> NewSessionResponse:
        workspace = Path(cwd).expanduser().resolve()
        if not workspace.is_dir():
            raise ValueError(f"ACP session cwd is not a directory: {workspace}")
        _ = additional_directories, mcp_servers
        session_id = uuid4().hex
        cancel_event = Event()
        state_path = workspace / ".cognigenesis" / "sessions" / f"{session_id}.json"
        engine = build_engine(workspace, cancel_event=cancel_event, state_path=state_path, session_id=session_id)
        self._sessions[session_id] = AcpSession(workspace, engine, cancel_event, asyncio.Lock())
        return NewSessionResponse(session_id=session_id)

    async def prompt(self, session_id: str, prompt: list[TextContentBlock | ImageContentBlock | AudioContentBlock | ResourceContentBlock | EmbeddedResourceContentBlock], **kwargs: Any) -> PromptResponse:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Unknown ACP session: {session_id}")
        objective = extract_text(prompt)
        if not objective:
            await self._send_text(session_id, "Cognigenesis currently accepts text prompts over ACP.")
            return PromptResponse(stop_reason="end_turn")

        async with session.prompt_lock:
            session.cancel_event.clear()
            try:
                result = await asyncio.to_thread(session.engine.run, objective)
            except ProviderError as exc:
                await self._send_text(session_id, f"Provider error: {exc}")
                return PromptResponse(stop_reason="end_turn")
            except Exception as exc:
                await self._send_text(session_id, f"Runtime error: {type(exc).__name__}: {exc}")
                return PromptResponse(stop_reason="end_turn")
            cancelled = session.cancel_event.is_set()
            await self._send_text(session_id, result)
            return PromptResponse(stop_reason="cancelled" if cancelled else "end_turn")

    async def cancel(self, session_id: str, **kwargs: Any) -> None:
        session = self._sessions.get(session_id)
        if session is not None:
            session.cancel_event.set()

    async def _send_text(self, session_id: str, text: str) -> None:
        await self._conn.session_update(session_id=session_id, update=update_agent_message(text_block(text)), source=ACP_SOURCE)


async def _main() -> None:
    await run_agent(CognigenesisAcpAgent())


def main() -> None:
    # ACP owns stdout. Force UTF-8 without printing banners or logs.
    configure_utf8_stdio()
    asyncio.run(_main())


if __name__ == "__main__":
    main()

import asyncio
import os
import sys
from typing import Any

from acp import Client, PROTOCOL_VERSION, RequestError, spawn_agent_process, text_block


class BridgeTestClient(Client):
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    async def request_permission(self, options: Any, session_id: str, tool_call: Any, **kwargs: Any) -> Any:
        raise RequestError.method_not_found("session/request_permission")

    async def session_update(self, session_id: str, update: Any, **kwargs: Any) -> None:
        self.updates.append({"session_id": session_id, "update": update, **kwargs})


def test_acp_stdio_subprocess_handshake(tmp_path):
    async def run() -> None:
        client = BridgeTestClient()
        env = os.environ.copy()
        env["COGNI_PROVIDER"] = "stub"

        # Regression guard for Windows spawn EINVAL: launch Python directly with an
        # argument array. No Node process and no .cmd wrapper is involved.
        async with spawn_agent_process(client, sys.executable, "-m", "acp_bridge", env=env) as (conn, _process):
            initialized = await conn.initialize(protocol_version=PROTOCOL_VERSION, client_capabilities=None)
            assert initialized.protocol_version == PROTOCOL_VERSION

            session = await conn.new_session(mcp_servers=[], cwd=str(tmp_path.resolve()))
            response = await conn.prompt(session_id=session.session_id, prompt=[text_block("Inspect this workspace")])

            assert response.stop_reason == "end_turn"
            assert client.updates
            assert client.updates[-1]["session_id"] == session.session_id

    asyncio.run(run())

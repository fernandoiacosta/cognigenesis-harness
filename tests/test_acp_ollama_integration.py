import asyncio
import os
import sys
from typing import Any

import pytest
from acp import Client, PROTOCOL_VERSION, RequestError, spawn_agent_process, text_block


class IntegrationClient(Client):
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    async def request_permission(self, options: Any, session_id: str, tool_call: Any, **kwargs: Any) -> Any:
        raise RequestError.method_not_found("session/request_permission")

    async def session_update(self, session_id: str, update: Any, **kwargs: Any) -> None:
        self.updates.append({"session_id": session_id, "update": update, **kwargs})


@pytest.mark.skipif(os.getenv("COGNI_TEST_OLLAMA") != "1", reason="requires live local Ollama")
def test_acp_live_ollama_round_trip(tmp_path):
    async def run() -> None:
        client = IntegrationClient()
        env = os.environ.copy()
        env["COGNI_PROVIDER"] = "ollama"
        env.setdefault("COGNI_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        env.setdefault("COGNI_OLLAMA_MODEL", "llama3.1:8b")

        async with spawn_agent_process(client, sys.executable, "-m", "acp_bridge", env=env) as (conn, _process):
            initialized = await conn.initialize(protocol_version=PROTOCOL_VERSION, client_capabilities=None)
            assert initialized.protocol_version == PROTOCOL_VERSION
            session = await conn.new_session(mcp_servers=[], cwd=str(tmp_path.resolve()))
            response = await conn.prompt(session_id=session.session_id, prompt=[text_block("Reply with OK")])
            assert response.stop_reason == "end_turn"
            assert client.updates

    asyncio.run(run())

import asyncio

from acp_bridge import CognigenesisAcpAgent, extract_text


class FakeClient:
    def __init__(self) -> None:
        self.updates: list[dict] = []

    async def session_update(self, **kwargs) -> None:
        self.updates.append(kwargs)


def test_extract_text_accepts_mapping_blocks():
    blocks = [
        {"type": "text", "text": "first"},
        {"type": "image", "data": "ignored"},
        {"type": "text", "text": "second"},
    ]
    assert extract_text(blocks) == "first\nsecond"


def test_initialize_advertises_load_session():
    async def run() -> None:
        response = await CognigenesisAcpAgent().initialize(1)
        assert response.agent_capabilities is not None
        assert response.agent_capabilities.load_session is True

    asyncio.run(run())


def test_acp_session_prompt_round_trip(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("COGNI_PROVIDER", "stub")
        agent = CognigenesisAcpAgent()
        client = FakeClient()
        agent.on_connect(client)  # type: ignore[arg-type]

        created = await agent.new_session(str(tmp_path))
        response = await agent.prompt(
            created.session_id,
            [{"type": "text", "text": "Inspect this workspace"}],  # type: ignore[list-item]
        )

        assert response.stop_reason == "end_turn"
        assert len(client.updates) == 1
        assert client.updates[0]["session_id"] == created.session_id
        assert client.updates[0]["source"] == "Cognigenesis"

        session = agent._sessions[created.session_id]
        history = session.engine.conversation_history()
        assert history[0] == {"role": "user", "content": "Inspect this workspace"}
        assert "Conversation continuity from this ACP session" not in history[0]["content"]

        session_state = tmp_path / ".cognigenesis" / "sessions" / f"{created.session_id}.json"
        assert session_state.exists()

    asyncio.run(run())


def test_acp_multiturn_uses_engine_history_once(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("COGNI_PROVIDER", "stub")
        agent = CognigenesisAcpAgent()
        agent.on_connect(FakeClient())  # type: ignore[arg-type]

        created = await agent.new_session(str(tmp_path))
        await agent.prompt(
            created.session_id,
            [{"type": "text", "text": "Remember blue-17"}],  # type: ignore[list-item]
        )
        await agent.prompt(
            created.session_id,
            [{"type": "text", "text": "What did I ask you to remember?"}],  # type: ignore[list-item]
        )

        history = agent._sessions[created.session_id].engine.conversation_history()
        user_turns = [item["content"] for item in history if item.get("role") == "user"]
        assert user_turns == ["Remember blue-17", "What did I ask you to remember?"]
        assert all("Conversation continuity from this ACP session" not in turn for turn in user_turns)

    asyncio.run(run())


def test_acp_load_session_recovers_persisted_history_without_duplication(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("COGNI_PROVIDER", "stub")

        first = CognigenesisAcpAgent()
        first.on_connect(FakeClient())  # type: ignore[arg-type]
        created = await first.new_session(str(tmp_path))
        await first.prompt(
            created.session_id,
            [{"type": "text", "text": "Remember blue-17"}],  # type: ignore[list-item]
        )

        second = CognigenesisAcpAgent()
        second.on_connect(FakeClient())  # type: ignore[arg-type]
        await second.load_session(str(tmp_path), created.session_id)

        restored = second._sessions[created.session_id].engine.conversation_history()
        restored_users = [item["content"] for item in restored if item.get("role") == "user"]
        assert restored_users == ["Remember blue-17"]

        await second.prompt(
            created.session_id,
            [{"type": "text", "text": "Continue"}],  # type: ignore[list-item]
        )
        final_history = second._sessions[created.session_id].engine.conversation_history()
        final_users = [item["content"] for item in final_history if item.get("role") == "user"]
        assert final_users == ["Remember blue-17", "Continue"]

    asyncio.run(run())


def test_acp_sessions_share_workspace_platform_but_not_conversation(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("COGNI_PROVIDER", "stub")
        agent = CognigenesisAcpAgent()
        agent.on_connect(FakeClient())  # type: ignore[arg-type]

        one = await agent.new_session(str(tmp_path))
        two = await agent.new_session(str(tmp_path))

        first = agent._sessions[one.session_id].engine
        second = agent._sessions[two.session_id].engine

        assert first.events is second.events
        assert first.cognition is second.cognition
        assert first.tasks is second.tasks
        assert first.conversation_history() == []
        assert second.conversation_history() == []

        await agent.prompt(
            one.session_id,
            [{"type": "text", "text": "session one"}],  # type: ignore[list-item]
        )
        assert first.conversation_history()
        assert second.conversation_history() == []

    asyncio.run(run())

import asyncio

from acp_bridge import CognigenesisAcpAgent, extract_text, objective_with_continuity


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


def test_objective_with_continuity_prepends_recent_turns():
    objective = objective_with_continuity("What did I say?", [("Remember blue-17", "Stored.")])

    assert "Conversation continuity from this ACP session" in objective
    assert "User: Remember blue-17" in objective
    assert "Assistant: Stored." in objective
    assert objective.endswith("What did I say?")


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

        session_state = tmp_path / ".cognigenesis" / "sessions" / f"{created.session_id}.json"
        assert session_state.exists()

    asyncio.run(run())


def test_acp_load_session_round_trip(tmp_path, monkeypatch):
    async def run() -> None:
        monkeypatch.setenv("COGNI_PROVIDER", "stub")
        agent = CognigenesisAcpAgent()
        client = FakeClient()
        agent.on_connect(client)  # type: ignore[arg-type]

        await agent.load_session(str(tmp_path), "known-session")
        response = await agent.prompt(
            "known-session",
            [{"type": "text", "text": "Inspect this workspace"}],  # type: ignore[list-item]
        )

        assert response.stop_reason == "end_turn"
        session_state = tmp_path / ".cognigenesis" / "sessions" / "known-session.json"
        assert session_state.exists()

    asyncio.run(run())

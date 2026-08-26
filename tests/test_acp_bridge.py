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


def test_acp_session_prompt_round_trip(tmp_path):
    async def run() -> None:
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

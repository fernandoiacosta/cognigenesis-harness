from harness import build_engine
from providers.ollama import OllamaProvider


def test_engine_preserves_conversation_across_runs(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    first = engine.run("first turn")
    second = engine.run("second turn")
    assert "first turn" in first
    assert "second turn" in second
    history = engine.conversation_history()
    assert [item["role"] for item in history] == ["user", "assistant", "user", "assistant"]
    assert history[0]["content"] == "first turn"
    assert history[2]["content"] == "second turn"


def test_conversation_survives_engine_restart(tmp_path):
    first_engine = build_engine(tmp_path, provider_name="stub")
    first_engine.run("remember this")
    second_engine = build_engine(tmp_path, provider_name="stub")
    assert second_engine.conversation_history() == first_engine.conversation_history()


def test_reset_conversation_clears_history_and_disk(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    engine.run("hello")
    assert engine.conversation_history()
    engine.reset_conversation()
    assert engine.conversation_history() == []
    reopened = build_engine(tmp_path, provider_name="stub")
    assert reopened.conversation_history() == []


def test_ollama_messages_include_prior_turns():
    provider = OllamaProvider(model="test")
    messages = provider._messages(
        {
            "system": "system",
            "capabilities": [],
            "state": {},
            "history": [
                {"role": "user", "content": "My name is Nano"},
                {"role": "assistant", "content": "Understood"},
            ],
            "objective": "What is my name?",
        }
    )
    assert messages[-3:] == [
        {"role": "user", "content": "My name is Nano"},
        {"role": "assistant", "content": "Understood"},
        {"role": "user", "content": "What is my name?"},
    ]


def test_ollama_tool_transcript_keeps_user_before_tool_call():
    provider = OllamaProvider(model="test")
    messages = provider._messages(
        {
            "system": "system",
            "capabilities": [],
            "state": {},
            "history": [
                {"role": "user", "content": "Research current harnesses", "current_turn": True},
                {"role": "assistant", "tool_calls": [{"function": {"name": "web.search", "arguments": {"query": "agent harnesses"}}}]},
                {"role": "tool", "name": "web.search", "content": {"ok": True, "result": {"results": []}}},
            ],
            "objective": "Research current harnesses",
            "objective_in_history": True,
        }
    )
    roles = [item["role"] for item in messages]
    assert roles[-3:] == ["user", "assistant", "tool"]
    assert messages[-2]["tool_calls"][0]["function"]["name"] == "web.search"

from cognigenesis.config import DEFAULT_TIMEOUT, Settings
from harness import build_engine
from providers.ollama import DEFAULT_OLLAMA_TIMEOUT


def test_timeout_defaults_have_one_policy():
    assert DEFAULT_TIMEOUT == 60.0
    assert DEFAULT_OLLAMA_TIMEOUT == 60.0
    assert Settings().ollama_timeout == 60.0


def test_engine_owns_conversation_continuity(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    engine.run("first")
    engine.run("second")
    users = [
        item["content"]
        for item in engine.conversation_history()
        if item.get("role") == "user"
    ]
    assert users == ["first", "second"]


def test_v2_engine_exposes_cognition_tasks_and_events(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    assert engine.registry.get("cognition.snapshot") is not None
    assert engine.registry.get("task.list") is not None
    assert engine.events is not None
    assert engine.cognition is not None
    assert engine.tasks is not None

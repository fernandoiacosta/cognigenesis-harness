from cognigenesis.runtime.events import EventType
from harness import build_engine


def test_engine_emits_semantic_turn_events(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    result = engine.run("hello")
    types = [event.type for event in engine.events.history()]

    assert result
    assert EventType.TURN_STARTED in types
    assert EventType.MODEL_STARTED in types
    assert EventType.MODEL_COMPLETED in types
    assert EventType.TURN_COMPLETED in types

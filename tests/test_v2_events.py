from cognigenesis.runtime.events import EventBus, EventType


def test_event_bus_emits_and_replays():
    bus = EventBus()
    seen = []
    unsubscribe = bus.subscribe(seen.append)

    event = bus.emit(EventType.TURN_STARTED, {"objective": "test"}, session_id="s1", turn_id="t1")
    unsubscribe()

    assert event.type == EventType.TURN_STARTED
    assert seen == [event]
    assert bus.history()[-1].payload["objective"] == "test"

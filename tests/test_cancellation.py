from threading import Event

from harness import build_engine


def test_engine_honors_pre_set_cancellation(tmp_path):
    cancel_event = Event()
    cancel_event.set()
    engine = build_engine(tmp_path, cancel_event=cancel_event)

    result = engine.run("This should not execute")

    assert result == "Execution cancelled by client."

from harness import build_engine


def test_cognition_tools_are_live_and_update_ledger(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    tool = engine.registry.get("cognition.hypothesis.add")
    assert tool is not None

    result = tool.execute({
        "claim": "A causes B",
        "mechanism": "through C",
        "confidence": 0.7,
    })
    assert result["hypothesis"]["claim"] == "A causes B"
    assert engine.cognition.snapshot()["metrics"]["active_hypotheses"] == 1


def test_task_tools_are_registered(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    assert engine.registry.get("task.add") is not None
    assert engine.registry.get("task.list") is not None

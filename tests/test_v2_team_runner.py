from cognigenesis.fabric.patterns import TeamPattern
from cognigenesis.runtime.events import EventType
from harness import build_team_runner


def test_team_runner_executes_pattern_with_stub(tmp_path):
    runner, platform = build_team_runner(tmp_path, provider_name="stub")
    result = runner.run(TeamPattern.ADVERSARIAL_COUNCIL, "Evaluate architecture")

    assert len(result.runs) == 3
    assert result.final
    assert len(platform.tasks.all()) == 3
    assert platform.teams.snapshot()
    assert any(event.type == EventType.AGENT_MESSAGE for event in platform.events.history())
    assert any(event.type == EventType.TURN_COMPLETED for event in platform.events.history())

import json

from cognigenesis.fabric.patterns import TeamPattern
from harness import build_engine, build_team_runner


def test_engine_persists_command_center_snapshot(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    engine.run("hello")

    path = tmp_path / ".cognigenesis" / "command-center.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["events"]
    assert any(event["type"] == "turn.completed" for event in data["events"])


def test_team_run_projects_team_and_tasks_to_command_center(tmp_path):
    runner, _platform = build_team_runner(tmp_path, provider_name="stub")
    runner.run(TeamPattern.ADVERSARIAL_COUNCIL, "Evaluate a design")

    data = json.loads((tmp_path / ".cognigenesis" / "command-center.json").read_text(encoding="utf-8"))
    assert data["teams"]
    assert data["tasks"]

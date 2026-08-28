from cognigenesis.fabric.patterns import TeamPattern, instantiate_pattern
from cognigenesis.fabric.team import TeamManager


def test_adversarial_council_pattern_has_supervisor_and_roles():
    manager = TeamManager()
    team = instantiate_pattern(manager, TeamPattern.ADVERSARIAL_COUNCIL, "Test a hypothesis")

    roles = {agent.role for agent in team.agents.values()}
    assert "construct strongest candidate explanation" in roles
    assert "attempt falsification and expose weak assumptions" in roles
    assert team.supervisor_id in team.agents

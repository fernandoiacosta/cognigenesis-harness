from cognigenesis.fabric.messages import AgentMessage, MessageKind
from cognigenesis.fabric.team import AgentSpec, TeamManager


def test_team_manager_routes_typed_messages():
    manager = TeamManager()
    researcher = AgentSpec("researcher", "research")
    critic = AgentSpec("critic", "critique")
    team = manager.create_team("analysis", "Compare architectures", [researcher, critic])

    message = AgentMessage(
        sender=researcher.id,
        recipient=critic.id,
        kind=MessageKind.HYPOTHESIS,
        content="The runtime layer is the bottleneck.",
        confidence=0.7,
    )
    manager.send(message)

    inbox = manager.receive(critic.id)
    assert inbox == [message]
    assert manager.team_snapshot(team.id)["name"] == "analysis"

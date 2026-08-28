from __future__ import annotations

from dataclasses import asdict, dataclass, field
from threading import RLock
from typing import Iterable
from uuid import uuid4

from cognigenesis.fabric.messages import AgentMessage, MessageKind
from cognigenesis.runtime.events import EventBus, EventType


@dataclass
class AgentSpec:
    name: str
    role: str
    model: str | None = None
    capabilities: set[str] = field(default_factory=set)
    id: str = field(default_factory=lambda: uuid4().hex)
    active: bool = True


@dataclass
class Team:
    name: str
    objective: str
    agents: dict[str, AgentSpec] = field(default_factory=dict)
    supervisor_id: str | None = None
    id: str = field(default_factory=lambda: uuid4().hex)


class TeamManager:
    """Coordination substrate for teams without bloating the agent kernel."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._teams: dict[str, Team] = {}
        self._mailboxes: dict[str, list[AgentMessage]] = {}
        self._lock = RLock()
        self._events = event_bus

    def create_team(
        self,
        name: str,
        objective: str,
        agents: Iterable[AgentSpec] = (),
        *,
        supervisor_id: str | None = None,
    ) -> Team:
        team = Team(name=name, objective=objective)
        for agent in agents:
            team.agents[agent.id] = agent
            self._mailboxes.setdefault(agent.id, [])
        if supervisor_id and supervisor_id not in team.agents:
            raise ValueError("Supervisor must be a member of the team.")
        team.supervisor_id = supervisor_id
        with self._lock:
            self._teams[team.id] = team
        return team

    def add_agent(self, team_id: str, agent: AgentSpec) -> AgentSpec:
        with self._lock:
            team = self._teams[team_id]
            team.agents[agent.id] = agent
            self._mailboxes.setdefault(agent.id, [])
        return agent

    def send(self, message: AgentMessage) -> AgentMessage:
        with self._lock:
            if message.recipient != "broadcast":
                if message.recipient not in self._mailboxes:
                    raise ValueError(f"Unknown recipient: {message.recipient}")
                self._mailboxes[message.recipient].append(message)
            else:
                for agent_id in self._mailboxes:
                    if agent_id != message.sender:
                        self._mailboxes[agent_id].append(message)
        if self._events:
            self._events.emit(
                EventType.AGENT_MESSAGE,
                message.to_dict(),
                source="agent-fabric",
            )
        return message

    def receive(self, agent_id: str, *, clear: bool = True) -> list[AgentMessage]:
        with self._lock:
            messages = list(self._mailboxes.get(agent_id, []))
            if clear:
                self._mailboxes[agent_id] = []
            return messages

    def team_snapshot(self, team_id: str) -> dict:
        with self._lock:
            team = self._teams[team_id]
            return {
                "id": team.id,
                "name": team.name,
                "objective": team.objective,
                "supervisor_id": team.supervisor_id,
                "agents": [
                    {
                        **asdict(agent),
                        "capabilities": sorted(agent.capabilities),
                        "pending_messages": len(self._mailboxes.get(agent.id, [])),
                    }
                    for agent in team.agents.values()
                ],
            }

    def snapshot(self) -> list[dict]:
        with self._lock:
            ids = list(self._teams)
        return [self.team_snapshot(team_id) for team_id in ids]

    @staticmethod
    def handoff(sender: str, recipient: str, content: str, **payload) -> AgentMessage:
        return AgentMessage(
            sender=sender,
            recipient=recipient,
            kind=MessageKind.HANDOFF,
            content=content,
            payload=payload,
        )

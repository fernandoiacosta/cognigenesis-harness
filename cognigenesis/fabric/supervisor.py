from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from cognigenesis.fabric.messages import AgentMessage, MessageKind
from cognigenesis.fabric.patterns import TeamPattern, instantiate_pattern
from cognigenesis.fabric.team import AgentSpec, Team, TeamManager
from cognigenesis.runtime.events import EventBus, EventType
from cognigenesis.runtime.taskgraph import Task, TaskGraph, TaskStatus
from core.engine import ExecutionEngine


EngineFactory = Callable[[AgentSpec, str], ExecutionEngine]


@dataclass
class AgentRun:
    agent_id: str
    agent_name: str
    role: str
    task_id: str
    output: str


@dataclass
class TeamRunResult:
    team: Team
    runs: list[AgentRun]
    final: str

    def to_dict(self) -> dict:
        return {
            "team_id": self.team.id,
            "team": self.team.name,
            "objective": self.team.objective,
            "runs": [run.__dict__ for run in self.runs],
            "final": self.final,
        }


class TeamRunner:
    """Bounded synchronous team executor over the shared Cognigenesis runtime.

    v2 alpha deliberately starts deterministic and inspectable. Parallelism can
    be added per pattern later without changing message/task semantics.
    """

    def __init__(
        self,
        *,
        manager: TeamManager,
        tasks: TaskGraph,
        events: EventBus,
        engine_factory: EngineFactory,
    ) -> None:
        self.manager = manager
        self.tasks = tasks
        self.events = events
        self.engine_factory = engine_factory

    def run(
        self,
        pattern: TeamPattern,
        objective: str,
        *,
        model: str | None = None,
    ) -> TeamRunResult:
        team = instantiate_pattern(self.manager, pattern, objective, model=model)
        agents = list(team.agents.values())
        if not agents:
            raise ValueError("Team pattern produced no agents.")

        self.events.emit(
            EventType.TASK_UPDATED,
            {"action": "team.started", "team": self.manager.team_snapshot(team.id)},
            source="team-supervisor",
        )

        tasks_by_agent = self._build_tasks(pattern, agents)
        runs: list[AgentRun] = []
        outputs: dict[str, str] = {}

        for agent in agents:
            task = tasks_by_agent[agent.id]
            self.tasks.update_status(task.id, TaskStatus.RUNNING)
            self.events.emit(
                EventType.TASK_UPDATED,
                {"action": "running", "task": task.to_dict(), "agent_id": agent.id, "team_id": team.id},
                source="team-supervisor",
            )

            prompt = self._prompt_for(pattern, team, agent, outputs)
            engine = self.engine_factory(agent, team.id)
            try:
                output = engine.run(prompt)
            except Exception as exc:
                self.tasks.update_status(task.id, TaskStatus.FAILED, result=str(exc))
                self.events.emit(
                    EventType.TURN_FAILED,
                    {
                        "team_id": team.id,
                        "agent_id": agent.id,
                        "task_id": task.id,
                        "error": str(exc),
                    },
                    source="team-supervisor",
                )
                raise

            outputs[agent.id] = output
            self.tasks.update_status(task.id, TaskStatus.COMPLETED, result=output)
            runs.append(AgentRun(agent.id, agent.name, agent.role, task.id, output))

            recipients = self._recipients(pattern, agents, agent)
            kind = MessageKind.DECISION if agent.id == team.supervisor_id else MessageKind.FINDING
            for recipient in recipients:
                self.manager.send(AgentMessage(
                    sender=agent.id,
                    recipient=recipient,
                    kind=kind,
                    content=output,
                    payload={"team_id": team.id, "task_id": task.id, "role": agent.role},
                ))

            self.events.emit(
                EventType.TASK_UPDATED,
                {"action": "completed", "task": task.to_dict(), "agent_id": agent.id, "team_id": team.id},
                source="team-supervisor",
            )

        supervisor_output = outputs.get(team.supervisor_id or "")
        final = supervisor_output if supervisor_output is not None else runs[-1].output
        self.events.emit(
            EventType.TURN_COMPLETED,
            {"team_id": team.id, "pattern": pattern.value, "final": final},
            source="team-supervisor",
        )
        return TeamRunResult(team=team, runs=runs, final=final)

    def _build_tasks(self, pattern: TeamPattern, agents: list[AgentSpec]) -> dict[str, Task]:
        result: dict[str, Task] = {}
        if pattern in {TeamPattern.PARALLEL_SEARCH, TeamPattern.CONSENSUS}:
            worker_ids: list[str] = []
            for agent in agents[:-1]:
                task = self.tasks.add(Task(
                    title=f"{agent.name}: {agent.role}",
                    description=agent.role,
                ))
                result[agent.id] = task
                worker_ids.append(task.id)
            supervisor = agents[-1]
            result[supervisor.id] = self.tasks.add(Task(
                title=f"{supervisor.name}: {supervisor.role}",
                description="Synthesize independent worker outputs.",
                dependencies=worker_ids,
            ))
            return result

        previous: str | None = None
        for agent in agents:
            deps = [previous] if previous else []
            task = self.tasks.add(Task(
                title=f"{agent.name}: {agent.role}",
                description=agent.role,
                dependencies=deps,
            ))
            result[agent.id] = task
            previous = task.id
        return result

    def _prompt_for(
        self,
        pattern: TeamPattern,
        team: Team,
        agent: AgentSpec,
        outputs: dict[str, str],
    ) -> str:
        prior = "\n\n".join(
            f"PRIOR AGENT OUTPUT ({agent_id}):\n{text}"
            for agent_id, text in outputs.items()
        )
        base = (
            f"You are agent '{agent.name}' in Cognigenesis team '{team.name}'.\n"
            f"Role: {agent.role}\n"
            f"Mission: {team.objective}\n"
            "Work only on your assigned cognitive role. Distinguish evidence from inference. "
            "Use available tools/cognitive scaffolding when useful. Return a concise handoff-ready result."
        )

        if pattern in {TeamPattern.PARALLEL_SEARCH, TeamPattern.CONSENSUS} and agent.id != team.supervisor_id:
            return base + "\nProduce an independent answer; do not assume what other workers concluded."

        if prior:
            base += "\n\nInputs from earlier team members:\n" + prior

        if agent.id == team.supervisor_id:
            base += (
                "\n\nYou are the synthesis authority for this bounded team run. Compare the inputs, "
                "preserve disagreements and uncertainty, reject unsupported claims, and return the team result."
            )
        elif pattern in {TeamPattern.ADVERSARIAL_COUNCIL, TeamPattern.RED_BLUE}:
            base += "\nAct adversarially toward unsupported assumptions in prior work."
        elif pattern == TeamPattern.SPECIALIST_PIPELINE:
            base += "\nTransform prior work for your specialist stage; do not merely summarize it."

        return base

    def _recipients(
        self,
        pattern: TeamPattern,
        agents: list[AgentSpec],
        agent: AgentSpec,
    ) -> list[str]:
        index = agents.index(agent)
        if index == len(agents) - 1:
            return []
        if pattern in {TeamPattern.PARALLEL_SEARCH, TeamPattern.CONSENSUS}:
            return [agents[-1].id]
        return [agents[index + 1].id]

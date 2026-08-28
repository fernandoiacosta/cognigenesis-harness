from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cognigenesis.fabric.team import AgentSpec, Team, TeamManager


class TeamPattern(StrEnum):
    PARALLEL_SEARCH = "parallel-search"
    ADVERSARIAL_COUNCIL = "adversarial-council"
    RED_BLUE = "red-blue"
    SPECIALIST_PIPELINE = "specialist-pipeline"
    CONSENSUS = "consensus"


@dataclass(frozen=True)
class RoleTemplate:
    name: str
    role: str
    capabilities: tuple[str, ...] = ()


PATTERNS: dict[TeamPattern, tuple[RoleTemplate, ...]] = {
    TeamPattern.PARALLEL_SEARCH: (
        RoleTemplate("research-a", "independent researcher", ("web.search", "web.fetch")),
        RoleTemplate("research-b", "independent researcher", ("web.search", "web.fetch")),
        RoleTemplate("synthesizer", "evidence synthesizer"),
    ),
    TeamPattern.ADVERSARIAL_COUNCIL: (
        RoleTemplate("proposer", "construct strongest candidate explanation"),
        RoleTemplate("critic", "attempt falsification and expose weak assumptions"),
        RoleTemplate("arbiter", "compare evidence and update confidence"),
    ),
    TeamPattern.RED_BLUE: (
        RoleTemplate("blue", "propose and defend solution"),
        RoleTemplate("red", "attack solution and search failure modes"),
        RoleTemplate("judge", "resolve contested claims using evidence"),
    ),
    TeamPattern.SPECIALIST_PIPELINE: (
        RoleTemplate("researcher", "gather evidence", ("web.search", "web.fetch")),
        RoleTemplate("architect", "build explicit model or plan"),
        RoleTemplate("implementer", "translate plan into executable work"),
        RoleTemplate("validator", "test claims and implementation"),
    ),
    TeamPattern.CONSENSUS: (
        RoleTemplate("independent-a", "independent solver"),
        RoleTemplate("independent-b", "independent solver"),
        RoleTemplate("independent-c", "independent solver"),
        RoleTemplate("consensus", "compare solutions and synthesize agreement/disagreement"),
    ),
}


def instantiate_pattern(
    manager: TeamManager,
    pattern: TeamPattern,
    objective: str,
    *,
    model: str | None = None,
) -> Team:
    templates = PATTERNS[pattern]
    agents = [
        AgentSpec(
            name=template.name,
            role=template.role,
            model=model,
            capabilities=set(template.capabilities),
        )
        for template in templates
    ]
    supervisor = agents[-1]
    return manager.create_team(
        name=pattern.value,
        objective=objective,
        agents=agents,
        supervisor_id=supervisor.id,
    )

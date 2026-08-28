"""Agent fabric: typed communication and team coordination."""

from .messages import AgentMessage, MessageKind
from .team import AgentSpec, Team, TeamManager

__all__ = ["AgentMessage", "MessageKind", "AgentSpec", "Team", "TeamManager"]

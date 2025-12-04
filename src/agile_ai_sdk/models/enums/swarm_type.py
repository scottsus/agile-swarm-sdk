from enum import Enum


class AgentSwarmType(str, Enum):
    """Agent swarm architecture types."""

    TEAM = "team"
    SOLO = "solo"

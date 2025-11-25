from dataclasses import dataclass


@dataclass
class AgentDeps:
    """Dependencies shared across all agents.

    This is a shell wrapper that will be populated with shared resources
    like EventStream, MessageRouter, workspace, etc.
    """

    pass

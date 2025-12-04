from dataclasses import dataclass
from pathlib import Path

from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter


@dataclass
class AgentDeps:
    """Dependencies shared across all agents.

    Attributes:
        workspace_dir: Working directory for agent file operations
        router: Message router for inter-agent communication
        event_stream: Event stream for observability
    """

    workspace_dir: Path
    router: MessageRouter
    event_stream: EventStream

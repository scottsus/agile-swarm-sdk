from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from agile_ai_sdk.models import EventHandler, EventType


class TaskExecutor(Protocol):
    """Protocol for task execution systems (AgentTeam, SoloAgentHarness, etc.).

    All executors must implement a message-based API with event handlers:
    - start(): Initialize agents and begin processing
    - drop_message(): Send messages to the system
    - on(): Register handlers for specific event types
    - on_any_event(): Register handlers for all events
    - stop(): Clean shutdown

    Example using event handlers:
        >>> team = AgentTeam()
        >>>
        >>> @team.on(EventType.RUN_FINISHED)
        >>> async def on_complete(event):
        ...     print("Task completed!")
        ...     await team.stop()
        >>>
        >>> @team.on_any_event
        >>> async def log_all(event):
        ...     print(f"[{event.agent}] {event.type}")
        >>>
        >>> await team.start()
        >>> await team.drop_message("Add /health endpoint")
    """

    async def start(self, workspace_dir: Path | None = None) -> None:
        """Start the executor and spawn agent run loops."""
        ...

    async def drop_message(self, content: str) -> None:
        """Send a message to the executor."""
        ...

    def on(self, event_type: EventType) -> Callable[[EventHandler], EventHandler]:
        """Decorator to register handler for specific event type.

        Example:
            >>> @executor.on(EventType.RUN_FINISHED)
            >>> async def on_complete(event):
            ...     print("Done!")
        """
        ...

    def on_any_event(self, handler: EventHandler) -> EventHandler:
        """Decorator to register handler for all events.

        Example:
            >>> @executor.on_any_event
            >>> async def log_all(event):
            ...     print(f"{event.type}: {event.data}")
        """
        ...

    async def stop(self) -> None:
        """Stop the executor and clean up resources."""
        ...

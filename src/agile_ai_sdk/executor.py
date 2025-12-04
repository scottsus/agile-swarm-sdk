from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

from agile_ai_sdk.models import Event


class TaskExecutor(Protocol):
    """Protocol for task execution systems (AgentTeam, SoloAgentHarness, etc.).

    All executors must implement the execute() method which takes a task
    description and optional workspace directory, returning an async stream
    of events.

    Example:
        >>> executor: TaskExecutor = AgentTeam()
        >>> async for event in executor.execute("Add /health endpoint"):
        ...     print(event.type)

        >>> executor: TaskExecutor = SoloAgentHarness()
        >>> async for event in executor.execute("List files"):
        ...     print(event.type)
    """

    def execute(self, task: str, workspace_dir: Path | None = None) -> AsyncIterator[Event]:
        """Execute a task and stream events.

        Args:
            task: Task description (e.g., "Add /health endpoint")
            workspace_dir: Working directory for execution (defaults to cwd)

        Yields:
            Event objects representing execution progress

        Example:
            >>> async for event in executor.execute("Run tests"):
            ...     if event.type == EventType.RUN_FINISHED:
            ...         print("Task completed!")
        """
        ...

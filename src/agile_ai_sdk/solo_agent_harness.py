import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from agile_ai_sdk.agents.code_act_agent import CodeActAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.executor import TaskExecutor
from agile_ai_sdk.models import AgentRole, Event, EventType, HumanRole


class SoloAgentHarness(TaskExecutor):
    """Single-agent task executor - simpler alternative to AgentTeam.

    Orchestrates a single CodeActAgent to execute tasks without
    multi-agent coordination overhead. Provides same API as AgentTeam
    for drop-in compatibility.

    Example:
        Basic usage:
        >>> harness = SoloAgentHarness()
        >>> async for event in harness.execute("List files and echo hello"):
        ...     print(f"[{event.agent}] {event.type}")
        ...     if event.type == EventType.RUN_FINISHED:
        ...         break
    """

    def __init__(self) -> None:
        """Initialize the single-agent harness."""
        self.event_stream: EventStream | None = None
        self.router: MessageRouter | None = None
        self.agent: CodeActAgent | None = None

    async def execute(self, task: str, workspace_dir: Path | None = None) -> AsyncIterator[Event]:
        """Execute a task with the single agent.

        This method mirrors AgentTeam.execute() signature for compatibility.

        Lifecycle:
        1. creates EventStream and MessageRouter
        2. emits RUN_STARTED event
        3. creates CodeActAgent instance
        4. sets workspace_dir on agent
        5. bootstraps agent with initial message
        6. spawns agent (starts run_loop)
        7. streams events to caller
        8. tears down agent on completion

        Example:
            >>> async for event in harness.execute("Run pytest"):
            ...     if event.type == EventType.TEXT_MESSAGE_CONTENT:
            ...         print(event.data["message"])
        """
        if workspace_dir is None:
            workspace_dir = Path.cwd()

        # Create fresh infrastructure for this execution
        self.event_stream = EventStream()
        self.router = MessageRouter(self.event_stream)

        # Create CodeActAgent
        self.agent = CodeActAgent(self.router, self.event_stream)
        self.agent.workspace_dir = workspace_dir

        # Register agent with router (even though router won't be used for routing)
        self.router.register_agent(AgentRole.CODE_ACT, self.agent)

        await self.event_stream.emit(
            Event(
                type=EventType.RUN_STARTED,
                agent=AgentRole.CODE_ACT,
                data={"task": task},
            )
        )

        # Bootstrap agent with initial message
        await self.agent.drop_in_inbox(source=HumanRole.USER, content=task)

        # Spawn agent (starts run_loop in background)
        agent_task = self.agent.spawn()

        try:
            async for event in self.event_stream:
                yield event

                if event.type in (EventType.RUN_ERROR, EventType.RUN_FINISHED):
                    self.event_stream.close()
                    break

        finally:
            await self._teardown([agent_task])

    async def _teardown(self, agent_tasks: list[asyncio.Task[Any]]) -> None:
        for task in agent_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

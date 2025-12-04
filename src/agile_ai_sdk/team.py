import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from agile_ai_sdk.agents import Developer, EngineeringManager, Planner, SeniorReviewer
from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.executor import TaskExecutor
from agile_ai_sdk.models import AgentRole, Event, EventType, HumanRole


class AgentTeam(TaskExecutor):
    """Main entry point for executing tasks with an agent team.

    Example:
        Basic usage:
        >>> team = AgentTeam()
        >>> async for event in team.execute("Add /health endpoint"):
        ...     print(f"[{event.agent}] {event.type}")
        ...     if event.type == EventType.RUN_FINISHED:
        ...         break

        Custom agent subset:
        >>> team = AgentTeam(agents=[AgentRole.EM, AgentRole.DEV])
        >>> async for event in team.execute("Quick fix"):
        ...     process(event)
    """

    def __init__(self, agents: list[AgentRole] | None = None):
        """Initialize the agent team."""

        self.enabled_agents = agents or [
            AgentRole.EM,
            AgentRole.PLANNER,
            AgentRole.DEV,
            AgentRole.SENIOR_REVIEWER,
        ]

        # Initialize core components
        self.event_stream = EventStream()
        self.router = MessageRouter(self.event_stream)

        # Initialize agents
        self.agents: dict[AgentRole, BaseAgent] = {}
        self._init_agents()

    def _init_agents(self) -> None:
        """Initialize enabled agents."""

        for role in self.enabled_agents:
            agent = self._create_agent(role)
            self.agents[role] = agent
            self.router.register_agent(role, agent)

    def _create_agent(self, role: AgentRole) -> BaseAgent:
        """Factory method to create agents by role."""

        agent_classes = {
            AgentRole.EM: EngineeringManager,
            AgentRole.PLANNER: Planner,
            AgentRole.DEV: Developer,
            AgentRole.SENIOR_REVIEWER: SeniorReviewer,
        }

        agent_class = agent_classes.get(role)
        if not agent_class:
            raise ValueError(f"Unknown agent role: {role}")

        return agent_class(self.router, self.event_stream)

    async def execute(self, task: str, workspace_dir: Path | None = None) -> AsyncIterator[Event]:
        """Execute a task with the agent team."""

        if workspace_dir is None:
            workspace_dir = Path.cwd()

        for agent in self.agents.values():
            agent.workspace_dir = workspace_dir

        await self.event_stream.emit(Event(type=EventType.RUN_STARTED, agent=AgentRole.EM, data={"task": task}))

        await self.agents[AgentRole.EM].drop_in_inbox(source=HumanRole.USER, content=task)

        agent_tasks = [agent.spawn() for agent in self.agents.values()]

        try:
            async for event in self.event_stream:
                yield event

                if event.type in (EventType.RUN_ERROR, EventType.RUN_FINISHED):
                    self.event_stream.close()
                    break

        finally:
            await self._teardown(agent_tasks)

    async def _teardown(self, agent_tasks: list[asyncio.Task[Any]]):
        """Cleans up dangling resources"""

        self.event_stream.close()

        for agent in self.agents.values():
            agent.stop()

        try:
            await asyncio.wait_for(asyncio.gather(*agent_tasks, return_exceptions=True), timeout=5.0)

        except asyncio.TimeoutError:
            for task in agent_tasks:
                if not task.done():
                    task.cancel()

import asyncio
from collections.abc import AsyncIterator

from agile_ai_sdk.agents import Developer, EngineeringManager, Planner, SeniorReviewer
from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.models import AgentRole, Event, EventType, HumanRole


class AgentTeam:
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

    async def execute(self, task: str) -> AsyncIterator[Event]:
        """Execute a task with the agent team."""

        await self.event_stream.emit(Event(type=EventType.RUN_STARTED, agent=AgentRole.EM, data={"task": task}))

        await self.agents[AgentRole.EM].drop_in_inbox(source=HumanRole.USER, content=task)

        em_task = asyncio.create_task(self.agents[AgentRole.EM].start())

        async for event in self.event_stream:
            yield event

            if event.type in (EventType.RUN_FINISHED, EventType.RUN_ERROR):
                break

        await em_task
        self.event_stream.close()

from typing import TYPE_CHECKING

from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.models import (
    AgentRole,
    Event,
    EventType,
    HumanRole,
    Message,
    MessageReceivedData,
    MessageSentData,
    Priority,
)

if TYPE_CHECKING:
    from agile_ai_sdk.agents.base import BaseAgent


class MessageRouter:
    """Routes messages between agents and broadcasts events to stream.

    Automatically emits events when messages are routed, making all inter-agent
    communication observable to the end user.

    Example:
        >>> event_stream = EventStream()
        >>> router = MessageRouter(event_stream)
        >>> em_agent = EngineeringManager(router, event_stream)
        >>> dev_agent = Developer(router, event_stream)
        >>> router.register_agent(AgentRole.EM, em_agent)
        >>> router.register_agent(AgentRole.DEV, dev_agent)

        >>> # Send a message - automatically emits events
        >>> await router.send(
        ...     source=AgentRole.EM,
        ...     target=AgentRole.DEV,
        ...     content="Implement the /health endpoint"
        ... )
    """

    def __init__(self, event_stream: EventStream):
        self._agents: dict[AgentRole, BaseAgent] = {}
        self._event_stream = event_stream

    def register_agent(self, role: AgentRole, agent: "BaseAgent") -> None:
        """Register an agent with the router."""

        self._agents[role] = agent

    async def route_message(self, message: Message) -> None:
        """Route a message to the target agent's appropriate queue.

        Automatically emits events to the stream for observability.
        """

        if message.target not in self._agents:
            raise ValueError(f"Agent {message.target} not registered")

        agent = self._agents[message.target]

        await self._event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=message.source,
                data=MessageSentData(
                    to=message.target.value,
                    content=message.content,
                    priority=message.priority.value,
                ).model_dump(),
            )
        )

        if message.priority == Priority.INTERRUPT:
            await agent.interrupt_queue.put(message)
        else:
            await agent.inbox.put(message)

        await self._event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=message.target,
                data=MessageReceivedData(
                    from_=message.source.value,
                    content=message.content,
                    priority=message.priority.value,
                ).model_dump(),
            )
        )

    async def send(
        self,
        source: AgentRole | HumanRole,
        target: AgentRole,
        content: str,
        priority: Priority = Priority.NORMAL,
    ) -> None:
        """Convenience method to create and route a message."""

        message = Message(
            source=source,
            target=target,
            content=content,
            priority=priority,
        )

        await self.route_message(message)

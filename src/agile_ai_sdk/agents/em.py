import asyncio

from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class EngineeringManager(BaseAgent):
    """Engineering Manager agent - orchestrates task execution.

    Example:
        >>> em = EngineeringManager(router, event_stream)
        >>> await em.start(initial_message="Add /health endpoint")
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.EM, router, event_stream)

    async def process_messages(self, messages: list[Message]) -> None:
        """Process incoming messages.

        Phase 1: Stub implementation - just completes immediately.
        """
        # Greeting
        await self.event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=self.role,
                data={"message": "👋 Hi, I'm the Engineering Manager! Ready to orchestrate the team."},
            )
        )

        # TODO Phase 2: Implement EM logic
        # - Task decomposition
        # - Agent assignment
        # - Progress tracking
        # - Conflict resolution

        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data={"status": "Processing task (stubbed)", "message_count": len(messages)},
            )
        )

        # Stub: Just complete immediately
        await asyncio.sleep(0.5)

        await self.event_stream.emit(
            Event(type=EventType.RUN_FINISHED, agent=self.role, data={"status": "Task completed (stubbed)"})
        )

        self.stop()

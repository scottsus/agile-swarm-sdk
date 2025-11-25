from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class Planner(BaseAgent):
    """Planner agent - creates implementation plans.

    Example:
        >>> planner = Planner(router, event_stream)
        >>> await planner.start()
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.PLANNER, router, event_stream)

    async def process_messages(self, messages: list[Message]) -> None:
        """Process incoming messages.

        Phase 1: Stub implementation.
        """
        # Greeting
        await self.event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=self.role,
                data={"message": "👋 Hi, I'm the Planner! I'll create the implementation roadmap."},
            )
        )

        # TODO Phase 2: Implement planning logic
        # - Codebase exploration
        # - Implementation plan creation
        # - Plan defense in review

        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data={"status": "Creating plan (stubbed)", "message_count": len(messages)},
            )
        )

        self.stop()

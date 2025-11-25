from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class Developer(BaseAgent):
    """Developer agent - implements code changes.

    Example:
        >>> dev = Developer(router, event_stream)
        >>> await dev.start()
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.DEV, router, event_stream)

    async def process_messages(self, messages: list[Message]) -> None:
        """Process incoming messages.

        Phase 1: Stub implementation.
        """
        # Greeting
        await self.event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=self.role,
                data={"message": "👋 Hi, I'm the Developer! Let me write some code."},
            )
        )

        # TODO Phase 2: Implement development logic
        # - Code implementation
        # - Test writing
        # - Git operations

        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data={"status": "Implementing code (stubbed)", "message_count": len(messages)},
            )
        )

        self.stop()

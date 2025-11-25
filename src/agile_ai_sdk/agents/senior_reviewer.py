from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class SeniorReviewer(BaseAgent):
    """Senior Reviewer agent - reviews code quality and security.

    Example:
        >>> reviewer = SeniorReviewer(router, event_stream)
        >>> await reviewer.start()
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.SENIOR_REVIEWER, router, event_stream)

    async def process_messages(self, messages: list[Message]) -> None:
        """Process incoming messages.

        Phase 1: Stub implementation.
        """
        # Greeting
        await self.event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=self.role,
                data={"message": "👋 Hi, I'm the Senior Reviewer! I'll ensure quality and security."},
            )
        )

        # TODO Phase 2: Implement review logic
        # - Code review
        # - Security analysis
        # - Quality assessment

        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data={"status": "Reviewing code (stubbed)", "message_count": len(messages)},
            )
        )

        self.stop()

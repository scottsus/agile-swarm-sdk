from pydantic_ai import Agent

from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.deps import AgentDeps
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.llm import default
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class EngineeringManager(BaseAgent):
    """Engineering Manager agent - orchestrates task execution.

    Example:
        >>> em = EngineeringManager(router, event_stream)
        >>> await em.start(initial_message="Add /health endpoint")
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.EM, router, event_stream)

        self.ai_agent = Agent(
            default.get_model(),
            deps_type=AgentDeps,
            system_prompt="You are an Engineering Manager. Your role is to clarify what the user wants and understand their requirements.",
        )

    async def process_messages(self, messages: list[Message]) -> None:
        """Process incoming messages using Pydantic AI agent.

        Example:
            >>> messages = [Message(source=HumanRole.USER, target=AgentRole.EM, content="Add /health")]
            >>> await em.process_messages(messages)
        """
        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data={"status": "Processing messages", "message_count": len(messages)},
            )
        )

        user_prompt = "\n".join([msg.content for msg in messages])

        deps = AgentDeps()
        result = await self.ai_agent.run(user_prompt, deps=deps)

        await self.event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=self.role,
                data={"message": result.output},
            )
        )

        await self.event_stream.emit(
            Event(type=EventType.RUN_FINISHED, agent=self.role, data={"status": "Task completed"})
        )

        self.stop()

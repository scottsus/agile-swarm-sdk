from pathlib import Path

from pydantic_ai import Agent, RunContext

from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.deps import AgentDeps
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.llm import default
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class Planner(BaseAgent):
    """Planner agent - creates implementation plans.

    Example:
        >>> planner = Planner(router, event_stream)
        >>> await planner.start()
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.PLANNER, router, event_stream)

        self.ai_agent = Agent(
            default.get_model(),
            deps_type=AgentDeps,
            system_prompt=(
                "You are a Technical Planner who creates detailed implementation plans.\n\n"
                "Your responsibilities:\n"
                "1. Analyze the task requirements\n"
                "2. Break down the work into concrete steps\n"
                "3. Identify files that need to be created or modified\n"
                "4. Define the implementation approach\n"
                "5. Respond back to the Engineering Manager with your plan\n\n"
                "Create clear, actionable plans that the developer can follow."
            ),
        )

        @self.ai_agent.tool
        async def respond_to_em(ctx: RunContext[AgentDeps], plan: str) -> str:
            """Send your implementation plan back to the Engineering Manager.

            Args:
                plan: The detailed implementation plan
            """
            await ctx.deps.router.send(self.role, AgentRole.EM, plan)

            return "Plan sent to Engineering Manager."

    async def process_messages(self, messages: list[Message]) -> None:
        """Process incoming messages using Pydantic AI agent."""

        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data={"status": "Creating implementation plan", "message_count": len(messages)},
            )
        )

        user_prompt = "\n".join([f"[{msg.source.value}]: {msg.content}" for msg in messages])

        deps = AgentDeps(router=self.router, event_stream=self.event_stream, workspace_dir=self._ensure_workspace())
        result = await self.ai_agent.run(user_prompt, message_history=self.conversation_history, deps=deps)
        self.conversation_history.extend(result.new_messages())

        await self.event_stream.emit(
            Event(
                type=EventType.TEXT_MESSAGE_CONTENT,
                agent=self.role,
                data={"message": result.output},
            )
        )

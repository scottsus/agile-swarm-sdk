from pydantic_ai import Agent, RunContext

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
            system_prompt=(
                "You are an Engineering Manager coordinating a software development team.\n\n"
                "Your workflow:\n"
                "1. When you receive a task from the user, delegate to 'developer'\n"
                "2. When developer responds with results, call respond_to_user with a summary\n"
                "3. IMMEDIATELY call complete_task to finish\n\n"
                "Example flow:\n"
                "User asks: 'List files in src/'\n"
                "→ You call: talk_to('developer', 'List files in src/')\n"
                "→ Developer responds with file listing\n"
                "→ You call: respond_to_user('Here are the files: ...')\n"
                "→ You call: complete_task('Listed files successfully')\n\n"
                "Available tools:\n"
                "- talk_to: Delegate to another agent (developer, planner, senior_reviewer)\n"
                "- respond_to_user: Send a message to the user\n"
                "- complete_task: **REQUIRED** - Call this after responding to user to end the workflow\n\n"
                "CRITICAL: After every respond_to_user, you MUST call complete_task immediately!"
            ),
        )

        @self.ai_agent.tool
        async def talk_to(ctx: RunContext[AgentDeps], agent: str, message: str) -> str:
            """Send a message to another agent.

            Args:
                agent: Agent role (planner, developer, senior_reviewer)
                message: The message/task to send
            """
            agent_role_map = {
                "planner": AgentRole.PLANNER,
                "developer": AgentRole.DEV,
                "senior_reviewer": AgentRole.SENIOR_REVIEWER,
            }

            if agent not in agent_role_map:
                return f"Error: Unknown agent '{agent}'. Available: planner, developer, senior_reviewer"

            target_role = agent_role_map[agent]
            await ctx.deps.router.send(self.role, target_role, message)

            return f"Message sent to {agent}. They will respond when ready."

        @self.ai_agent.tool
        async def respond_to_user(ctx: RunContext[AgentDeps], message: str) -> str:
            """Send a response back to the user.

            Args:
                message: The response to send to the user
            """
            await ctx.deps.event_stream.emit(
                Event(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    agent=self.role,
                    data={"message": message},
                )
            )

            return "Response sent to user."

        @self.ai_agent.tool
        async def complete_task(ctx: RunContext[AgentDeps], summary: str) -> str:
            """Mark the current task as complete.

            Only call this when:
            - You have delegated to all necessary agents
            - Received responses from all agents
            - Synthesized the results
            - Sent final response to the user

            Args:
                summary: Brief summary of what was accomplished
            """
            await ctx.deps.event_stream.emit(
                Event(
                    type=EventType.RUN_FINISHED,
                    agent=self.role,
                    data={"status": summary},
                )
            )

            return "Task marked as complete. Ready for next message."

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

        user_prompt = "\n".join([f"[{msg.source.value}]: {msg.content}" for msg in messages])

        deps = AgentDeps(router=self.router, event_stream=self.event_stream, workspace_dir=self._ensure_workspace())

        try:
            result = await self.ai_agent.run(user_prompt, message_history=self.conversation_history, deps=deps)
            self.conversation_history.extend(result.new_messages())
        except Exception as e:
            await self.event_stream.emit(
                Event(
                    type=EventType.RUN_ERROR,
                    agent=self.role,
                    data={"error": str(e)},
                )
            )
            # TODO: Implement error recovery logic here
            # Options: retry task, reassign to different agent, request human help
            # For now, stop on error - errors are fatal for the session
            self.stop()

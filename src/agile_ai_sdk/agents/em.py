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
                "CRITICAL RULES:\n"
                "- EVERY message to the user MUST use the respond_to_user tool\n"
                "- You MUST call complete_task after EVERY respond_to_user call\n"
                "- After calling complete_task, respond with a brief confirmation (1-3 words)\n"
                "- For simple greetings or questions, respond directly using respond_to_user\n\n"
                "Workflow for tasks:\n"
                "1. For coding tasks: delegate to 'developer' using talk_to\n"
                "2. After delegation, respond with 'Delegated.'\n"
                "3. When developer responds: use respond_to_user with summary\n"
                "4. IMMEDIATELY call complete_task\n"
                "5. Respond with brief confirmation\n\n"
                "Workflow for greetings/simple messages:\n"
                "1. Use respond_to_user to greet or answer\n"
                "2. IMMEDIATELY call complete_task\n"
                "3. Respond with brief confirmation\n\n"
                "Example - greeting:\n"
                "User says: 'hello'\n"
                "→ You call: respond_to_user('Hi! I can help with development tasks. What would you like to work on?')\n"
                "→ You call: complete_task('Greeted user')\n"
                "→ You respond: 'Done.'\n\n"
                "Example - task:\n"
                "User asks: 'List files in src/'\n"
                "→ You call: talk_to('developer', 'List files in src/')\n"
                "→ You respond: 'Delegated.'\n"
                "→ [Later] Developer responds with file listing\n"
                "→ You call: respond_to_user('Here are the files: ...')\n"
                "→ You call: complete_task('Listed files successfully')\n"
                "→ You respond: 'Complete.'\n\n"
                "Available tools:\n"
                "- talk_to: Delegate to another agent (developer, planner, senior_reviewer)\n"
                "- respond_to_user: Send a message to the user (USE THIS FOR ALL USER COMMUNICATION)\n"
                "- complete_task: Mark task complete (REQUIRED after every respond_to_user)"
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

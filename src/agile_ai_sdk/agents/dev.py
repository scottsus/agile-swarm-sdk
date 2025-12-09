import asyncio

from pydantic_ai import Agent, RunContext

from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.deps import AgentDeps
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.llm import default
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class Developer(BaseAgent):
    """Developer agent - implements code changes.

    Example:
        >>> dev = Developer(router, event_stream)
        >>> await dev.start()
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.DEV, router, event_stream)

        self.ai_agent = Agent(
            default.get_model(),
            deps_type=AgentDeps,
            system_prompt=(
                "You are a Senior Software Developer implementing code changes.\n\n"
                "CRITICAL RULES:\n"
                "- ALWAYS use respond_back tool to send results to the EM\n"
                "- After calling respond_back, respond with a brief confirmation (1-3 words)\n\n"
                "Workflow:\n"
                "1. Use run_bash tool to execute commands and gather information\n"
                "2. Use respond_back tool to send results back to the EM\n"
                "3. Respond with brief confirmation\n\n"
                "Example flow:\n"
                "EM asks: 'List files in src/'\n"
                "→ You call: run_bash('ls src/')\n"
                "→ You call: respond_back('Files in src/: file1.py, file2.py, ...')\n"
                "→ You respond: 'Done.'\n\n"
                "Available tools:\n"
                "- run_bash: Execute shell commands (ls, cat, git, etc.)\n"
                "- respond_back: Send results back to the EM"
            ),
        )

        @self.ai_agent.tool
        async def run_bash(ctx: RunContext[AgentDeps], command: str) -> str:
            """Execute a bash command.

            Args:
                command: The bash command to execute

            Example:
                >>> run_bash("ls -la")
                >>> run_bash("git status")
                >>> run_bash("cat src/main.py")
            """
            await ctx.deps.event_stream.emit(
                Event(
                    type=EventType.STEP_STARTED,
                    agent=self.role,
                    data={"status": f"Executing: {command}"},
                )
            )

            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self._ensure_workspace()),
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30.0,
                )

                output = []
                if stdout:
                    output.append(f"STDOUT:\n{stdout.decode()}")
                if stderr:
                    output.append(f"STDERR:\n{stderr.decode()}")

                exit_code = process.returncode
                output.append(f"Exit code: {exit_code}")

                return "\n".join(output)

            except asyncio.TimeoutError:
                return "Error: Command timed out after 30 seconds"
            except Exception as e:
                return f"Error executing command: {str(e)}"

        @self.ai_agent.tool
        async def respond_back(ctx: RunContext[AgentDeps], message: str) -> str:
            """Send a response back to the Engineering Manager.

            Args:
                message: The response message describing what was done
            """
            await ctx.deps.router.send(self.role, AgentRole.EM, message)
            return "Response sent to EM."

    async def process_messages(self, messages: list[Message]) -> None:
        """Process incoming messages using Pydantic AI agent.

        Example:
            >>> messages = [Message(source=AgentRole.EM, target=AgentRole.DEV, content="Implement /health")]
            >>> await dev.process_messages(messages)
        """
        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data={"status": "Processing messages", "message_count": len(messages)},
            )
        )

        task = "\n".join([f"[{msg.source.value}]: {msg.content}" for msg in messages])

        deps = AgentDeps(router=self.router, event_stream=self.event_stream, workspace_dir=self._ensure_workspace())
        result = await self.ai_agent.run(task, message_history=self.conversation_history, deps=deps)
        self.conversation_history.extend(result.new_messages())

        if result.output:
            await self.event_stream.emit(
                Event(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    agent=self.role,
                    data={"message": result.output},
                )
            )

import asyncio

from pydantic_ai import Agent, RunContext

from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.deps import AgentDeps
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.llm import default
from agile_ai_sdk.models import AgentRole, Event, EventType, Message


class CodeActAgent(BaseAgent):
    """Single agent that executes tasks without delegation.

    Unlike multi-agent roles (EM, Dev, Planner), this agent handles
    the entire task lifecycle independently. It uses bash commands
    to accomplish goals but doesn't communicate with other agents.
    """

    def __init__(self, router: MessageRouter, event_stream: EventStream):
        super().__init__(AgentRole.CODE_ACT, router, event_stream)

        self.ai_agent = Agent(
            default.get_model(),
            deps_type=AgentDeps,
            system_prompt=(
                "You are an AI coding assistant that can execute bash commands.\n\n"
                "Workflow:\n"
                "1. Analyze the user's task\n"
                "2. Use run_bash tool to execute necessary commands\n"
                "3. Gather information and make changes as needed\n"
                "4. Always provide a clear summary of what you accomplished\n\n"
                "IMPORTANT: After completing the task, you MUST provide a final "
                "text output summarizing your work. Be concise but thorough.\n\n"
                "Available tools:\n"
                "- run_bash: Execute shell commands (ls, cat, git, pytest, etc.)\n\n"
                "Example workflow:\n"
                "Task: 'List files and create a README'\n"
                "1. run_bash('ls -la') to see current files\n"
                "2. run_bash('echo \"# Project\" > README.md') to create file\n"
                "3. run_bash('cat README.md') to verify\n"
                "4. Respond: 'Listed files, created README.md with project header'\n\n"
                "When you're done, stop immediately - don't wait for more instructions."
            ),
        )

        # Register run_bash tool
        @self.ai_agent.tool
        async def run_bash(ctx: RunContext[AgentDeps], command: str) -> str:
            """Execute a bash command in the workspace.

            Args:
                command: The bash command to execute (e.g., 'ls -la', 'git status')

            Returns:
                Command output including stdout, stderr, and exit code

            Example:
                >>> run_bash("ls -la")
                >>> run_bash("cat main.py")
                >>> run_bash("pytest -v")
            """
            await ctx.deps.event_stream.emit(
                Event(
                    type=EventType.STEP_STARTED,
                    agent=AgentRole.CODE_ACT,
                    data={"status": f"Executing: {command}"},
                )
            )

            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(ctx.deps.workspace_dir),
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30.0,
                )

                output = []
                if stdout:
                    decoded_stdout = stdout.decode()
                    output.append(f"STDOUT:\n{decoded_stdout}")
                if stderr:
                    decoded_stderr = stderr.decode()
                    output.append(f"STDERR:\n{decoded_stderr}")

                exit_code = process.returncode
                output.append(f"Exit code: {exit_code}")

                result = "\n".join(output)

                # Emit command result
                await ctx.deps.event_stream.emit(
                    Event(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        agent=AgentRole.CODE_ACT,
                        data={"message": f"Command completed: {command[:50]}..."},
                    )
                )

                return result

            except asyncio.TimeoutError:
                error_msg = "Error: Command timed out after 30 seconds"
                await ctx.deps.event_stream.emit(
                    Event(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        agent=AgentRole.CODE_ACT,
                        data={"message": error_msg},
                    )
                )
                return error_msg

            except Exception as e:
                error_msg = f"Error executing command: {str(e)}"
                await ctx.deps.event_stream.emit(
                    Event(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        agent=AgentRole.CODE_ACT,
                        data={"message": error_msg},
                    )
                )
                return error_msg

    async def process_messages(self, messages: list[Message]) -> None:
        """Process received messages by running AI agent.

        Unlike multi-agent roles that delegate work, CodeActAgent processes
        the entire task itself. After processing, it stops automatically.
        """

        for message in messages:
            await self.event_stream.emit(
                Event(
                    type=EventType.STEP_STARTED,
                    agent=self.role,
                    data={"status": "Processing task"},
                )
            )

            deps = AgentDeps(
                workspace_dir=self._ensure_workspace(),
                router=self.router,
                event_stream=self.event_stream,
            )

            try:
                # TODO: we should call `step` instead to get each event on each step
                result = await self.ai_agent.run(
                    message.content,
                    deps=deps,
                    message_history=self.conversation_history,
                )

                self.conversation_history = result.all_messages()

                if result.output:
                    await self.event_stream.emit(
                        Event(
                            type=EventType.TEXT_MESSAGE_CONTENT,
                            agent=self.role,
                            data={"message": result.output},
                        )
                    )

                await self.event_stream.emit(
                    Event(
                        type=EventType.STEP_FINISHED,
                        agent=self.role,
                        data={"status": "Task completed"},
                    )
                )

                await self.event_stream.emit(
                    Event(
                        type=EventType.RUN_FINISHED,
                        agent=self.role,
                        data={"status": "completed", "output": result.output},
                    )
                )

            except Exception as e:
                await self.event_stream.emit(
                    Event(
                        type=EventType.RUN_ERROR,
                        agent=self.role,
                        data={"error": str(e), "error_type": type(e).__name__},
                    )
                )

            finally:
                self.stop()

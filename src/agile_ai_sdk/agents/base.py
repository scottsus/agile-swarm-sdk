import asyncio
from abc import ABC, abstractmethod

from pydantic_ai.messages import ModelMessage

from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.models import AgentRole, AgentStatusData, ErrorData, Event, EventType, HumanRole, Message


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Example:
        Creating a custom agent:
        >>> class MyAgent(BaseAgent):
        ...     def __init__(self, router: MessageRouter, event_stream: EventStream):
        ...         super().__init__(AgentRole.DEV, router, event_stream)
        ...
        ...     async def process_messages(self, messages: list[Message]) -> None:
        ...         # Process batch of messages
        ...         for message in messages:
        ...             await self.event_stream.emit(Event(
        ...                 type=EventType.STEP_STARTED,
        ...                 agent=self.role,
        ...                 data={"status": f"Processing {len(messages)} messages"}
        ...             ))

        Starting an agent:
        >>> agent = MyAgent(router, event_stream)
        >>> await agent.start()
        >>> # Send message through router
        >>> await router.send(AgentRole.EM, AgentRole.DEV, "Build feature X")

        Communicating between agents:
        >>> # Inside process_messages
        >>> await self.talk_to(AgentRole.EM, "Task completed")
    """

    def __init__(self, role: AgentRole, router: MessageRouter, event_stream: EventStream):
        self.role = role
        self.router = router
        self.event_stream = event_stream

        # Communication channels
        self.inbox: asyncio.Queue[Message] = asyncio.Queue()
        self.interrupt_queue: asyncio.Queue[Message] = asyncio.Queue()

        # State
        self.conversation_history: list[ModelMessage] = []
        self._running: bool = False
        self._task: asyncio.Task | None = None

    def spawn(self) -> asyncio.Task:
        """Spawns the agent and starts the agent's processing loop as a background task."""

        self._task = asyncio.create_task(self.start())
        return self._task

    async def start(self) -> None:
        """Start the agent's processing loop."""

        self._running = True

        await self.event_stream.emit(
            Event(
                type=EventType.STEP_STARTED,
                agent=self.role,
                data=AgentStatusData(status="Agent started").model_dump(),
            )
        )

        await self.run_loop()

    async def run_loop(self) -> None:
        """Main agent processing loop."""

        try:
            while self._running:
                try:
                    messages: list[Message] = []

                    # Prioritize interrupts
                    if not self.interrupt_queue.empty():
                        messages = await self._flush_queue(self.interrupt_queue)

                    elif not self.inbox.empty():
                        messages = await self._flush_queue(self.inbox)

                    else:
                        await asyncio.sleep(0.1)
                        continue

                    if messages:
                        # Log received messages
                        await self.event_stream.emit(
                            Event(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                agent=self.role,
                                data={"message": f"📨 Received {len(messages)} message(s)"},
                            )
                        )

                        for i, msg in enumerate(messages, 1):
                            await self.event_stream.emit(
                                Event(
                                    type=EventType.TEXT_MESSAGE_CONTENT,
                                    agent=self.role,
                                    data={
                                        "message": f"  Message {i}: from={msg.source.value}, content='{msg.content}', priority={msg.priority.value}"
                                    },
                                )
                            )

                        await self.process_messages(messages)

                except Exception as e:
                    await self.event_stream.emit(
                        Event(
                            type=EventType.RUN_ERROR,
                            agent=self.role,
                            data=ErrorData(error=str(e)).model_dump(),
                        )
                    )
                    break

        except asyncio.CancelledError:
            await self.event_stream.emit(
                Event(
                    type=EventType.STEP_FINISHED,
                    agent=self.role,
                    data={"status": "Agent cancelled"},
                )
            )
            raise

        finally:
            self._running = False

    @abstractmethod
    async def process_messages(self, messages: list[Message]) -> None:
        """Process a batch of received messages."""

        pass

    async def talk_to(self, target: AgentRole, content: str) -> None:
        """Send a message to another agent.

        Events are automatically emitted by the router.
        """

        await self.router.send(self.role, target, content)

    async def drop_in_inbox(
        self,
        source: AgentRole | HumanRole,
        content: str,
    ) -> None:
        """Send a message to this agent's inbox via the router."""

        await self.router.send(
            source=source,
            target=self.role,
            content=content,
        )

    async def _flush_queue(self, queue: asyncio.Queue[Message]) -> list[Message]:
        """Flush all messages from a queue."""

        messages = []
        while not queue.empty():
            messages.append(await queue.get())

        return messages

    def stop(self) -> None:
        """Stop the agent's processing loop."""

        self._running = False

        if self._task is not None and not self._task.done():
            self._task.cancel()

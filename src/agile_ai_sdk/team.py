import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agile_ai_sdk.agents import Developer, EngineeringManager, Planner, SeniorReviewer
from agile_ai_sdk.agents.base import BaseAgent
from agile_ai_sdk.core.events import EventStream
from agile_ai_sdk.core.router import MessageRouter
from agile_ai_sdk.executor import TaskExecutor
from agile_ai_sdk.logging import EventLogger
from agile_ai_sdk.models import AgentRole, Event, EventHandler, EventType, HumanRole, RunStatus

logger = logging.getLogger(__name__)


class AgentTeam(TaskExecutor):
    """Main entry point for executing tasks with an agent team.

    Example using event handlers:
        >>> team = AgentTeam()
        >>>
        >>> @team.on(EventType.RUN_FINISHED)
        >>> async def on_complete(event):
        ...     print("Task completed!")
        ...     await team.stop()
        >>>
        >>> @team.on_any_event
        >>> async def log_all(event):
        ...     print(f"[{event.agent}] {event.type}")
        >>>
        >>> await team.start()
        >>> await team.drop_message("Add /health endpoint")

        Multi-message conversation:
        >>> team = AgentTeam()
        >>> run_count = 0
        >>>
        >>> @team.on(EventType.RUN_FINISHED)
        >>> async def on_run_finished(event):
        ...     nonlocal run_count
        ...     run_count += 1
        ...     if run_count == 1:
        ...         await team.drop_message("Now add /metrics endpoint")
        ...     elif run_count == 2:
        ...         await team.stop()
        >>>
        >>> await team.start()
        >>> await team.drop_message("Add /health endpoint")

        Custom agent subset:
        >>> team = AgentTeam(agents=[AgentRole.EM, AgentRole.DEV])
        >>> await team.start()
        >>> await team.drop_message("Quick fix")
    """

    def __init__(
        self,
        agents: list[AgentRole] | None = None,
        log_dir: str | Path | None = ".agile/runs",
    ):
        """Initialize the agent team."""

        self.enabled_agents = agents or [
            AgentRole.EM,
            AgentRole.PLANNER,
            AgentRole.DEV,
            AgentRole.SENIOR_REVIEWER,
        ]

        # Initialize core components
        self.event_stream = EventStream()
        self.router = MessageRouter(self.event_stream)

        # Initialize agents
        self.agents: dict[AgentRole, BaseAgent] = {}
        self._init_agents()

        # State tracking for persistent sessions
        self._started: bool = False
        self._first_message_sent: bool = False
        self._agent_tasks: list[asyncio.Task[Any]] = []

        # Handler registration system
        self._event_handlers: dict[EventType, list[EventHandler]] = {}
        self._on_any_handlers: list[EventHandler] = []
        self._broadcaster_task: asyncio.Task[Any] | None = None

        # Logging support
        self._logger: EventLogger | None = None
        self._had_error: bool = False

        if log_dir is not None:
            self._logger = EventLogger(
                task="AgentTeam Session",
                log_dir=Path(log_dir),
            )
            self.on_any_event(self._logger.log_event)

    def _init_agents(self) -> None:
        """Initialize enabled agents."""

        for role in self.enabled_agents:
            agent = self._create_agent(role)
            self.agents[role] = agent
            self.router.register_agent(role, agent)

    def _create_agent(self, role: AgentRole) -> BaseAgent:
        """Factory method to create agents by role."""

        agent_classes = {
            AgentRole.EM: EngineeringManager,
            AgentRole.PLANNER: Planner,
            AgentRole.DEV: Developer,
            AgentRole.SENIOR_REVIEWER: SeniorReviewer,
        }

        agent_class = agent_classes.get(role)
        if not agent_class:
            raise ValueError(f"Unknown agent role: {role}")

        return agent_class(self.router, self.event_stream)

    async def start(self, workspace_dir: Path | None = None) -> None:
        """Start the agent team and begin processing loop.

        This method:
        1. sets the workspace directory for all agents
        2. spawns all agent run loops as background tasks
        3. begins listening for incoming messages
        4. spawns background broadcaster if handlers are registered
        5. does NOT send any initial message (that's done via drop_message)
        """

        if self._started:
            raise RuntimeError("AgentTeam has already been started")

        if workspace_dir is None:
            workspace_dir = Path.cwd()

        # Recreate event stream if it was closed (after stop/restart)
        if self.event_stream._closed:
            self.event_stream = EventStream()
            self.router = MessageRouter(self.event_stream)
            # Re-register agents with new router
            for role, agent in self.agents.items():
                agent.router = self.router
                agent.event_stream = self.event_stream
                self.router.register_agent(role, agent)

        # Set workspace on all agents
        for agent in self.agents.values():
            agent.workspace_dir = workspace_dir

        # Spawn agent run loops
        self._agent_tasks = [agent.spawn() for agent in self.agents.values()]

        # Spawn background broadcaster if handlers registered
        if self._event_handlers or self._on_any_handlers:
            self._broadcaster_task = asyncio.create_task(self._broadcast_events())

        self._started = True

    async def drop_message(self, content: str) -> None:
        """Send a message to the Engineering Manager (entry point)."""

        if not self._started:
            raise RuntimeError("AgentTeam must be started before sending messages. Call start() first.")

        # On first message, emit RUN_STARTED
        if not self._first_message_sent:
            await self.event_stream.emit(Event(type=EventType.RUN_STARTED, agent=AgentRole.EM, data={"task": content}))
            self._first_message_sent = True

        # Route all messages to EM
        await self.agents[AgentRole.EM].drop_in_inbox(source=HumanRole.USER, content=content)

    async def stop(self) -> None:
        """Stop the agent team and clean up resources."""

        if not self._started:
            return  # Already stopped, no-op

        # Finalize logger before teardown
        if self._logger:
            status = RunStatus.ERROR if self._had_error else RunStatus.COMPLETED
            self._logger.finalize(status=status)

        # Cancel broadcaster task if running
        if self._broadcaster_task and not self._broadcaster_task.done():
            self._broadcaster_task.cancel()
            try:
                await asyncio.wait_for(self._broadcaster_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass  # Expected during shutdown

        await self._teardown(self._agent_tasks)
        self._started = False
        self._first_message_sent = False
        self._agent_tasks = []
        self._broadcaster_task = None

    def on(self, event_type: EventType) -> Callable[[EventHandler], EventHandler]:
        """Decorator to register handler for specific event type.

        Handlers are called sequentially in registration order when events occur.
        Both sync and async handlers are supported.

        Example:
            >>> team = AgentTeam()
            >>> @team.on(EventType.RUN_FINISHED)
            >>> async def on_complete(event):
            ...     print(f"Task completed: {event.data}")
            >>>
            >>> @team.on(EventType.TOOL_CALL_START)
            >>> def log_tool(event):
            ...     logger.info(f"Tool: {event.data['tool_name']}")
        """

        def decorator(handler: EventHandler) -> EventHandler:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler

        return decorator

    def on_any_event(self, handler: EventHandler) -> EventHandler:
        """Decorator to register handler for all event types.

        Useful for logging, metrics, broadcasting to websockets, etc.
        Handler is called for every event, regardless of type.

        Example:
            >>> team = AgentTeam()
            >>> @team.on_any_event
            >>> async def broadcast(event):
            ...     await websocket.send_json(event.model_dump())
            >>>
            >>> @team.on_any_event
            >>> def log_all(event):
            ...     logger.info(f"Event: {event.type}", extra=event.data)
        """

        self._on_any_handlers.append(handler)
        return handler

    async def _broadcast_events(self) -> None:
        """Background task that consumes event stream and dispatches to handlers.

        This task:
        1. consumes events from event stream
        2. dispatches to specific event type handlers
        3. dispatches to on_any_event handlers
        4. handles errors gracefully (logs but continues)
        5. runs until stop() is called or stream closes
        """

        try:
            async for event in self.event_stream:
                await self._dispatch_to_handlers(event)
        except asyncio.CancelledError:
            # Expected during shutdown
            pass
        except Exception as e:
            logger.error(f"Broadcaster task failed: {e}", exc_info=True)

    async def _dispatch_to_handlers(self, event: Event) -> None:
        """Dispatch event to all registered handlers.

        Handlers are executed sequentially. If a handler raises an exception,
        it's logged but other handlers still execute.
        """

        # Track errors for logger finalization
        if event.type == EventType.RUN_ERROR:
            self._had_error = True

        # Dispatch to specific event type handlers
        if event.type in self._event_handlers:
            for handler in self._event_handlers[event.type]:
                await self._execute_handler(handler, event)

        # Dispatch to on_any_event handlers
        for handler in self._on_any_handlers:
            await self._execute_handler(handler, event)

    async def _execute_handler(self, handler: EventHandler, event: Event) -> None:
        """Execute a single handler with error handling.

        Supports both sync and async handlers. Errors are logged but don't
        propagate to prevent one handler from breaking others.
        """

        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            handler_name = getattr(handler, "__name__", repr(handler))
            logger.error(
                f"Handler {handler_name} failed for event {event.type}: {e}",
                exc_info=True,
                extra={"event_type": event.type, "handler": handler_name},
            )

    def get_log_dir(self) -> Path | None:
        """Get the log directory path for this team's run."""

        return self._logger.get_log_dir() if self._logger else None

    async def _teardown(self, agent_tasks: list[asyncio.Task[Any]]) -> None:
        """Cleans up dangling resources"""

        self.event_stream.close()

        for agent in self.agents.values():
            agent.stop()

        try:
            await asyncio.wait_for(asyncio.gather(*agent_tasks, return_exceptions=True), timeout=5.0)

        except asyncio.TimeoutError:
            for task in agent_tasks:
                if not task.done():
                    task.cancel()

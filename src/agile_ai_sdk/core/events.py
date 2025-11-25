import asyncio
from collections.abc import AsyncIterator

from agile_ai_sdk.models import Event, EventType


class EventStream:
    """Async event stream that aggregates events from multiple agents.

    Example:
        Basic usage:
        >>> stream = EventStream()
        >>> await stream.emit(Event(
        ...     type=EventType.RUN_STARTED,
        ...     agent=AgentRole.EM,
        ...     data={"task": "Add health endpoint"}
        ... ))
        >>> async for event in stream:
        ...     print(f"[{event.agent}] {event.type}")
        ...     if event.type == EventType.RUN_FINISHED:
        ...         break

        Multiple producers, single consumer:
        >>> stream = EventStream()
        >>>
        >>> async def agent_work(agent_id: str):
        ...     await stream.emit(Event(
        ...         type=EventType.STEP_STARTED,
        ...         agent=AgentRole.EM,
        ...         data={"agent": agent_id}
        ...     ))
        >>>
        >>> # Multiple agents emit to same stream
        >>> await asyncio.gather(
        ...     agent_work("em"),
        ...     agent_work("planner"),
        ...     agent_work("dev")
        ... )
        >>>
        >>> # Single consumer reads all events
        >>> async for event in stream:
        ...     process(event)

        Manual close:
        >>> stream = EventStream()
        >>> await stream.emit(Event(...))
        >>> stream.close()  # Stop accepting new events
        >>> async for event in stream:
        ...     # Drains remaining events
        ...     print(event)
    """

    def __init__(self):
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._closed: bool = False

    async def emit(self, event: Event) -> None:
        """Emit an event to the stream."""

        if not self._closed:
            await self._queue.put(event)

    async def __aiter__(self) -> AsyncIterator[Event]:
        """Iterate over events as they arrive."""

        while True:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                yield event

                if event.type == EventType.RUN_FINISHED:
                    break

            except asyncio.TimeoutError:
                if self._closed and self._queue.empty():
                    break
                continue

    def close(self) -> None:
        """Close the event stream."""
        self._closed = True

from agile_ai_sdk.models import Event, EventType
from agile_ai_sdk.models.enums import AgentRole

"""Event-based assertions for validating what the agent reported.

This module contains assertions that validate the event stream - what the agent
REPORTED doing. For assertions that validate what ACTUALLY HAPPENED on disk,
see workspace_utils.py.

Example:
    assert_file_modified(events, "foo.py")  # Did agent report modifying foo.py?
    vs.
    assert_file_contains(workspace, "foo.py", "bar")  # Does foo.py actually contain "bar"?
"""


def assert_agent_started(events: list[Event], agent_role: AgentRole) -> None:
    """Assert that a specific agent started.

    Example:
        >>> assert_agent_started(events, AgentRole.DEV)
    """

    agent_events = [
        e for e in events if e.agent == agent_role and e.type in (EventType.RUN_STARTED, EventType.STEP_STARTED)
    ]
    assert agent_events, f"Agent {agent_role.value} never started.\n" f"Found agents: {(e.agent.value for e in events)}"


def assert_tool_called(events: list[Event], tool_name: str) -> None:
    """Assert that a tool was called.

    Example:
        >>> assert_tool_called(events, "read_file")
    """

    tool_events = [e for e in events if e.type == EventType.TOOL_CALL_START and e.data.get("tool_name") == tool_name]
    assert tool_events, (
        f"Tool '{tool_name}' was never called.\n"
        f"Called tools: {[e.data.get('tool_name') for e in events if e.type == EventType.TOOL_CALL_START]}"
    )


def assert_file_modified(events: list[Event], file_path: str) -> None:
    """Assert that a file modification event occurred.

    Example:
        >>> assert_file_modified(events, "calculator.py")
    """

    modification_events = [
        e
        for e in events
        if e.type == EventType.TOOL_CALL_RESULT
        and (
            file_path in str(e.data.get("result", ""))
            or file_path in str(e.data.get("file_path", ""))
            or file_path in str(e.data.get("path", ""))
        )
    ]
    assert modification_events, (
        f"File '{file_path}' was not modified.\n" f"Check events to see which files were modified."
    )


def assert_no_tool_errors(events: list[Event]) -> None:
    """Assert that no tool errors occurred.

    Example:
        >>> assert_no_tool_errors(events)
    """

    tool_error_events = [e for e in events if e.type == EventType.TOOL_CALL_RESULT and e.data.get("error") is not None]
    assert not tool_error_events, f"Found {len(tool_error_events)} tool error(s):\n" + "\n".join(
        [f"  - {e.data.get('tool_name', 'unknown')}: {e.data.get('error')}" for e in tool_error_events]
    )


def assert_step_completed(events: list[Event], step_description: str) -> None:
    """Assert that a step with matching description completed.

    Example:
        >>> assert_step_completed(events, "Read file")
    """

    step_events = [
        e
        for e in events
        if e.type in (EventType.STEP_STARTED, EventType.STEP_FINISHED)
        and step_description.lower() in str(e.data.get("description", "")).lower()
    ]

    completed_steps = [e for e in step_events if e.type == EventType.STEP_FINISHED]

    assert step_events, (
        f"No step found with description containing '{step_description}'.\n"
        f"Available step descriptions: {[e.data.get('description') for e in events if e.type == EventType.STEP_STARTED]}"
    )

    assert completed_steps, (
        f"Step '{step_description}' started but did not complete.\n"
        f"Step events found: {len(step_events)} (started only, no completion)"
    )


def assert_no_errors(events: list[Event]) -> None:
    """Assert that no error events occurred.

    Example:
        >>> assert_no_errors(events)
    """

    error_events = [e for e in events if e.type == EventType.RUN_ERROR]
    assert not error_events, f"Found {len(error_events)} error event(s):\n" + "\n".join(
        [f"  - {e.data.get('error', 'Unknown error')}" for e in error_events]
    )


def assert_starts_and_finishes(events: list[Event]) -> None:
    """Assert that execution started and finished properly.

    Example:
        >>> assert_starts_and_finishes(events)
    """

    assert len(events) > 0, "No events collected"
    assert events[0].type == EventType.RUN_STARTED, f"First event must be RUN_STARTED, got {events[0].type.value}"
    assert events[-1].type in (
        EventType.RUN_FINISHED,
        EventType.RUN_ERROR,
    ), f"Last event must be RUN_FINISHED or RUN_ERROR, got {events[-1].type.value}"


def assert_contains_event_data(event: Event, key: str, value: str | None = None) -> None:
    """Assert that an event contains specific data key and optionally value.

    Args:
        event: The event to check
        key: The data key to look for
        value: Optional value to match

    Example:
        >>> assert_contains_event_data(event, "task")
        >>> assert_contains_event_data(event, "status", "success")
    """

    assert key in event.data, f"Event data missing key: '{key}'.\n" f"Available keys: {list(event.data.keys())}"
    if value is not None:
        assert event.data[key] == value, f"Expected {key}={value}, got {event.data[key]}"


def assert_event_count(events: list[Event], event_type: EventType, expected_count: int) -> None:
    """Assert that a specific number of events of a given type occurred.

    Args:
        events: List of events to check
        event_type: The event type to count
        expected_count: Expected number of occurrences

    Example:
        >>> assert_event_count(events, EventType.TOOL_CALL_START, 3)
    """

    actual_count = sum(1 for e in events if e.type == event_type)
    assert actual_count == expected_count, f"Expected {expected_count} {event_type.value} event(s), got {actual_count}"


def assert_at_least_n_events(events: list[Event], event_type: EventType, min_count: int) -> None:
    """Assert that at least N events of a given type occurred.

    Args:
        events: List of events to check
        event_type: The event type to count
        min_count: Minimum expected number of occurrences

    Example:
        >>> assert_at_least_n_events(events, EventType.TOOL_CALL_START, 1)
    """

    actual_count = sum(1 for e in events if e.type == event_type)
    assert actual_count >= min_count, f"Expected at least {min_count} {event_type.value} event(s), got {actual_count}"

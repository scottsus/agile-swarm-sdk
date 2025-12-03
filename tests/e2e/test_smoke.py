from pathlib import Path

import pytest

from agile_ai_sdk import AgentTeam, EventType
from tests.helpers.assertions import assert_contains_event_data, assert_event_count
from tests.helpers.event_collector import EventCollector


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_agent_team_initialization() -> None:
    """Agent team initializes without crashing."""

    team = AgentTeam()

    assert team is not None
    assert hasattr(team, "execute")


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_execute_returns_stream(agent_team: AgentTeam) -> None:
    """execute() returns async iterator."""

    stream = agent_team.execute("Echo 'hello'")

    assert hasattr(stream, "__aiter__")
    assert hasattr(stream, "__anext__")


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_started_event(agent_team: AgentTeam, event_collector: EventCollector) -> None:
    """RUN_STARTED event is emitted with correct task data."""

    await event_collector.collect_until_done(agent_team.execute("List files"))

    assert event_collector.has_event_type(EventType.RUN_STARTED)
    assert_event_count(event_collector.events, EventType.RUN_STARTED, 1)

    started_event = event_collector.get_by_type(EventType.RUN_STARTED)[0]
    assert_contains_event_data(started_event, "task", "List files")


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_finished_event(agent_team: AgentTeam, event_collector: EventCollector) -> None:
    """RUN_FINISHED event is emitted on completion."""

    await event_collector.collect_until_done(agent_team.execute("Echo 'test'"))

    assert event_collector.completed
    assert event_collector.has_event_type(EventType.RUN_FINISHED)

    finished_events = event_collector.get_by_type(EventType.RUN_FINISHED)
    assert len(finished_events) > 0


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_event_has_required_fields(agent_team: AgentTeam, event_collector: EventCollector) -> None:
    """Events have all required fields with correct types."""

    await event_collector.collect_until_done(agent_team.execute("Print 'hello'"))

    assert len(event_collector.events) > 0

    for event in event_collector.events:
        assert hasattr(event, "type")
        assert hasattr(event, "agent")
        assert hasattr(event, "data")
        assert isinstance(event.type, EventType)
        assert isinstance(event.data, dict)


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_workspace_isolation() -> None:
    """Workspace is isolated from host directory."""

    team = AgentTeam()
    collector = EventCollector()

    test_filename = "test_isolation_marker.txt"

    await collector.collect_until_done(team.execute(f"Create a file called {test_filename} with content 'isolated'"))

    host_file = Path.cwd() / test_filename
    assert not host_file.exists(), f"File {test_filename} should not be in host directory"


@pytest.mark.smoke
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_simple_task_completion(agent_team: AgentTeam, event_collector: EventCollector) -> None:
    """Agent completes a trivial task successfully."""

    await event_collector.collect_until_done(agent_team.execute("Echo 'Hello, World!'"))

    event_collector.assert_completed_successfully()

    assert len(event_collector.events) >= 2
    assert event_collector.events[0].type == EventType.RUN_STARTED
    assert event_collector.events[-1].type == EventType.RUN_FINISHED

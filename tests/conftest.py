from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest

from agile_ai_sdk import AgentTeam
from tests.helpers.event_collector import EventCollector
from tests.logging.run_logger import TestRunLogger


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    """Base directory for test runs.

    This fixture:
    1. creates a temporary directory for the test run
    2. returns a path to a 'runs' subdirectory
    3. automatically cleans up after the test (/tmp)

    Returns:
        Path to base directory for workspace storage

    Example:
        >>> def test_something(base_dir):
        ...     workspace_dir = base_dir / "run_123" / "workspace"
        ...     workspace_dir.mkdir(parents=True)
    """
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir


@pytest.fixture
async def agent_team() -> AsyncGenerator[AgentTeam, None]:
    """Fresh AgentTeam instance per test.

    Example:
        >>> async def test_execute(agent_team, event_collector):
        ...     await event_collector.collect_until_done(
        ...         agent_team.execute("List files")
        ...     )
    """
    team = AgentTeam()
    yield team

    for agent in team.agents.values():
        agent.stop()


@pytest.fixture
def test_run_logger(request: pytest.FixtureRequest) -> Generator[TestRunLogger, None, None]:
    """Create test run logger for current test.

    This fixture:
    1. extracts test metadata from pytest request
    2. determines test tier from markers (smoke/scenario/feature)
    3. creates structured log directory at ~/.agile-ai/test-runs/
    4. yields TestRunLogger for use in test
    5. finalizes logs with pass/fail status on teardown

    The logger automatically captures:
    - Test metadata (name, file, tier, task)
    - Events (when used with event_collector)
    - Command outputs (via log_command_output)
    - Workspace snapshots (via save_workspace)
    - LLM judge evaluations (via log_llm_judge_evaluation)

    Example:
        >>> @pytest.mark.scenario
        ... @pytest.mark.task("Add /health endpoint")
        ... async def test_health(test_run_logger, event_collector):
        ...     # Events are automatically logged
        ...     await event_collector.collect_until_done(...)
        ...     # Logs saved to ~/.agile-ai/test-runs/test_health_{timestamp}/
    """

    test_name = request.node.name
    test_file = str(request.node.fspath)

    tier = "smoke"
    for marker in request.node.iter_markers():
        if marker.name in ("smoke", "feature", "scenario"):
            tier = marker.name
            break

    task = request.node.get_closest_marker("task")
    task_description = task.args[0] if task else "No task specified"

    logger = TestRunLogger(
        test_name=test_name,
        test_file=test_file,
        test_tier=tier,
        task=task_description,
    )

    yield logger

    if hasattr(request.node, "rep_call"):
        result = "passed" if request.node.rep_call.passed else "failed"
        error = str(request.node.rep_call.longrepr) if not request.node.rep_call.passed else None
    else:
        result = "unknown"
        error = None

    logger.finalize(result=result, error=error)

    if result != "passed":
        print(f"\nTest run logs: {logger.get_log_dir()}")


@pytest.fixture
def event_collector(request: pytest.FixtureRequest) -> EventCollector:
    """Fresh EventCollector instance per test.

    If test_run_logger fixture is also used, events are automatically
    logged to the test run directory.

    Example:
        >>> async def test_agent(event_collector, agent_team):
        ...     await event_collector.collect_until_done(
        ...         agent_team.execute("task")
        ...     )
        ...     event_collector.assert_completed_successfully()

        >>> async def test_with_logging(event_collector, test_run_logger):
        ...     # Events automatically logged to ~/.agile-ai/test-runs/
        ...     await event_collector.collect_until_done(...)
    """

    test_run_logger = None
    if "test_run_logger" in request.fixturenames:
        test_run_logger = request.getfixturevalue("test_run_logger")

    return EventCollector(test_run_logger=test_run_logger)


@pytest.fixture
async def cleanup_workspace(tmp_path: Path) -> AsyncGenerator[None, None]:
    """Cleanup fixture to remove test workspaces after tests.

    The cleanup happens automatically via tmp_path fixture,
    but this fixture can be used for custom cleanup logic.

    Example:
        >>> async def test_with_cleanup(cleanup_workspace, base_dir):
        ...     # Test runs here
        ...     workspace_dir = base_dir / "workspace"
        ...     workspace_dir.mkdir()
        ...     # Cleanup happens automatically after yield
    """
    yield


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results for test_run_logger.

    This hook:
    1. runs after each test phase (setup/call/teardown)
    2. captures the test result report
    3. attaches it to the test item for fixture access

    The report is used by test_run_logger fixture to determine
    pass/fail status and error messages.
    """

    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

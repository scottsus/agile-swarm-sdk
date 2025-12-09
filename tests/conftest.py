from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from agile_ai_sdk import AgentTeam, SoloAgentHarness
from tests.helpers.event_collector import EventCollector
from tests.helpers.workspace_utils import create_test_workspace, generate_test_run_id
from tests.logging.run_logger import TestRunLogger

if TYPE_CHECKING:
    from agile_ai_sdk import SoloAgentHarness, TaskExecutor


@pytest.fixture
def run_dir() -> Path:
    """Create unique run directory for this test.

    Structure:
        .agile/runs/test_2025-12-08_19:16:15/
        ├── fixtures/          # workspace fixtures
        │   ├── broken_code/
        │   ├── fastapi_app/
        │   └── simple_python/
        ├── metadata.json      # test run logs
        ├── events.jsonl
        ├── command_outputs/
        ├── llm_judge/
        ├── workspace/
        └── journal.json

    Example:
        >>> async def test_something(run_dir):
        ...     print(run_dir)  # .agile/runs/test_xxx
    """

    repo_root = Path(__file__).parent.parent
    base_dir = repo_root / ".agile" / "runs"
    run_id = generate_test_run_id()
    run_directory = base_dir / run_id
    run_directory.mkdir(parents=True, exist_ok=True)

    # Mark the isolation marker for test
    (run_directory / "test_isolation_marker.txt").write_text(run_id)

    return run_directory


@pytest.fixture
def workspace_dir(run_dir: Path) -> Path:
    """Create isolated workspace with all fixture directories.

    Returns the fixtures directory within the run directory.

    Example:
        >>> async def test_something(workspace_dir):
        ...     # workspace_dir = .agile/runs/test_xxx/fixtures/
        ...     await team.execute("cd simple_python && ls", workspace_dir=workspace_dir)
    """
    return create_test_workspace(run_dir, copy_fixtures=True)


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


@pytest.fixture
def solo_harness() -> "SoloAgentHarness":
    """Fresh SoloAgentHarness instance per test.

    Example:
        >>> async def test_execute(solo_harness, event_collector):
        ...     await event_collector.collect_until_done(
        ...         solo_harness.execute("List files")
        ...     )
    """

    return SoloAgentHarness()


@pytest.fixture(params=["solo", "team"])
def executor(request) -> "TaskExecutor":
    """Parametrized fixture to test both AgentTeam and SoloAgentHarness.

    Both implementations satisfy the TaskExecutor protocol, ensuring
    they have compatible APIs for task execution.

    By default, both executors are tested (solo first, then team).
    Use pytest's -k flag to filter:
        pytest -k "solo" # SoloAgentHarness only
        pytest -k "team" # AgentTeam only
        pytest           # Both executors

    Example:
        >>> async def test_simple_task(executor, event_collector):
        ...     await event_collector.collect_until_done(
        ...         executor.execute("Echo hello")
        ...     )
        ...     event_collector.assert_completed_successfully()
    """
    if request.param == "team":
        return request.getfixturevalue("agent_team")
    else:  # solo
        return request.getfixturevalue("solo_harness")


@pytest.fixture(autouse=True)
def test_run_logger(request: pytest.FixtureRequest, run_dir: Path) -> Generator[TestRunLogger, None, None]:
    """Create test run logger for current test.

    This fixture runs automatically for all tests and:
    1. extracts test metadata from pytest request
    2. determines test tier from markers (smoke/scenario/feature)
    3. creates structured log directory at .agile/runs/test_xxx/
    4. yields TestRunLogger for use in test
    5. finalizes logs with pass/fail status on teardown

    The logger automatically captures:
    - Test metadata (name, file, tier, task)
    - Events (when used with event_collector)
    - LLM judge evaluations (via log_llm_judge_evaluation)

    Example:
        >>> @pytest.mark.scenario
        ... @pytest.mark.task("Add /health endpoint")
        ... async def test_health(event_collector):
        ...     # Logger is automatically active
        ...     # Events are automatically logged
        ...     await event_collector.collect_until_done(...)
        ...     # Logs saved to .agile/runs/test_xxx/
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

    log_base_dir = run_dir.parent
    run_id = run_dir.name

    logger = TestRunLogger(
        test_name=test_name,
        test_file=test_file,
        test_tier=tier,
        task=task_description,
        log_dir=log_base_dir,
        run_id=run_id,
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
        ...     # Events automatically logged to .agile/runs/test_*/
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

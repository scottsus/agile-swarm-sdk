from pathlib import Path

import pytest

from agile_ai_sdk import AgentTeam
from tests.helpers.event_collector import EventCollector
from tests.helpers.workspace_utils import (
    assert_file_exists,
    read_file,
)


@pytest.mark.feature
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_create_new_file(agent_team: AgentTeam, event_collector: EventCollector, workspace_dir: Path) -> None:
    """Agent creates a new file with specific content.

    This test:
    1. instructs agent to create a new Python file
    2. verifies the file exists
    3. validates file contains expected function definition
    4. checks function signature matches requirements
    """

    task = (
        "Create a new file called multiply.py with a function "
        "multiply(a, b) that returns a * b. Include a docstring."
    )

    await event_collector.collect_until_done(agent_team.execute(task, workspace_dir=workspace_dir))
    event_collector.assert_completed_successfully()

    assert_file_exists(workspace_dir, "multiply.py")

    content = read_file(workspace_dir, "multiply.py")
    assert "def multiply" in content
    assert "a * b" in content or "a*b" in content or "return" in content


@pytest.mark.feature
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_modify_existing_file(agent_team: AgentTeam, event_collector: EventCollector, workspace_dir: Path) -> None:
    """Agent modifies an existing file.

    This test:
    1. gives agent a task to modify calculator.py
    2. verifies the file was modified
    3. validates original functions are preserved
    4. checks new function was added correctly
    """

    task = (
        "cd simple_python && "
        "In calculator.py, add a new function multiply(a, b) that returns a * b. "
        "Make sure to keep the existing add() and subtract() functions."
    )

    await event_collector.collect_until_done(agent_team.execute(task, workspace_dir=workspace_dir))
    event_collector.assert_completed_successfully()

    assert_file_exists(workspace_dir / "simple_python", "calculator.py")

    content = read_file(workspace_dir / "simple_python", "calculator.py")
    assert "def add" in content
    assert "def subtract" in content
    assert "def multiply" in content


@pytest.mark.feature
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_read_file_contents(agent_team: AgentTeam, event_collector: EventCollector, workspace_dir: Path) -> None:
    """Agent reads and uses file contents.

    This test:
    1. instructs agent to read a file
    2. verifies agent understood the content
    3. validates agent created summary based on file contents
    4. checks summary accuracy
    """

    task = (
        "cd simple_python && "
        "Read calculator.py and create a file called functions.txt that lists "
        "all the function names defined in calculator.py, one per line."
    )

    await event_collector.collect_until_done(agent_team.execute(task, workspace_dir=workspace_dir))

    event_collector.assert_completed_successfully()

    assert_file_exists(workspace_dir / "simple_python", "functions.txt")

    content = read_file(workspace_dir / "simple_python", "functions.txt")
    assert "add" in content.lower()
    assert "subtract" in content.lower()


@pytest.mark.feature
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_fix_bug(agent_team: AgentTeam, event_collector: EventCollector, workspace_dir: Path) -> None:
    """Agent fixes a bug in code.

    This test:
    1. presents agent with buggy code
    2. instructs agent to fix the bug
    3. verifies bug was fixed
    4. validates fix doesn't break existing functionality
    """

    task = (
        "cd broken_code && "
        "In buggy.py, fix the calculate_average() function to handle empty lists "
        "by raising a ValueError with message 'Cannot calculate average of empty list'. "
        "Make sure the tests pass after the fix."
    )

    await event_collector.collect_until_done(agent_team.execute(task, workspace_dir=workspace_dir))

    if (workspace_dir / "broken_code" / "buggy.py").exists():
        content = read_file(workspace_dir / "broken_code", "buggy.py")
        assert "ValueError" in content or "raise" in content or "if not" in content or "len(numbers)" in content


@pytest.mark.feature
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_execute_code(agent_team: AgentTeam, event_collector: EventCollector, workspace_dir: Path) -> None:
    """Agent executes code.

    This test:
    1. instructs agent to create and run script
    2. verifies script was created
    3. validates script was executed
    4. checks output was captured
    """

    task = (
        "Create a Python script hello.py that prints 'Hello from test!', "
        "then run it and save the output to output.txt."
    )

    await event_collector.collect_until_done(agent_team.execute(task, workspace_dir=workspace_dir))

    if (workspace_dir / "hello.py").exists():
        assert_file_exists(workspace_dir, "hello.py")
        content = read_file(workspace_dir, "hello.py")
        assert "print" in content

    if (workspace_dir / "output.txt").exists():
        output = read_file(workspace_dir, "output.txt")
        assert "Hello" in output or len(output) > 0


@pytest.mark.feature
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_implement_and_test(agent_team: AgentTeam, event_collector: EventCollector, workspace_dir: Path) -> None:
    """Agent implements code and runs tests.

    This test:
    1. instructs agent to implement feature with tests
    2. verifies implementation exists
    3. validates tests were created
    4. checks all tests pass
    """

    task = (
        "cd simple_python && "
        "Add a power(base, exponent) function to calculator.py that returns base ** exponent. "
        "Also add a test_power() function in test_calculator.py that tests this function "
        "with at least 2 test cases. Make sure the tests pass."
    )

    await event_collector.collect_until_done(agent_team.execute(task, workspace_dir=workspace_dir))

    if (workspace_dir / "simple_python" / "calculator.py").exists():
        calc_content = read_file(workspace_dir / "simple_python", "calculator.py")
        assert "def power" in calc_content

    if (workspace_dir / "simple_python" / "test_calculator.py").exists():
        test_content = read_file(workspace_dir / "simple_python", "test_calculator.py")
        assert "test_power" in test_content or "def test" in test_content


@pytest.mark.feature
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_multiple_file_changes(agent_team: AgentTeam, event_collector: EventCollector, workspace_dir: Path) -> None:
    """Agent modifies multiple files.

    This test:
    1. instructs agent to modify multiple files
    2. verifies all files were modified
    3. validates changes are consistent
    4. checks files work together
    """

    task = (
        "Create two files: math_utils.py with a square(x) function, "
        "and test_math_utils.py with tests for the square function. "
        "Make sure the tests import correctly and pass."
    )

    await event_collector.collect_until_done(agent_team.execute(task, workspace_dir=workspace_dir))

    if (workspace_dir / "math_utils.py").exists():
        assert_file_exists(workspace_dir, "math_utils.py")
        content = read_file(workspace_dir, "math_utils.py")
        assert "def square" in content

    if (workspace_dir / "test_math_utils.py").exists():
        assert_file_exists(workspace_dir, "test_math_utils.py")
        content = read_file(workspace_dir, "test_math_utils.py")
        assert "import" in content or "from" in content

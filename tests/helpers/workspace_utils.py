import re
import shutil
import subprocess
from pathlib import Path

from agile_ai_sdk.utils.time import timestamp_readable

"""Workspace filesystem utilities for validating what actually happened.

This module contains utilities that validate the workspace filesystem - what
ACTUALLY HAPPENED on disk. For assertions that validate what the agent REPORTED
doing via events, see assertions.py.

Example:
    assert_file_contains(workspace, "foo.py", "bar")  # Does foo.py actually contain "bar"?
    vs.
    assert_file_modified(events, "foo.py")  # Did agent report modifying foo.py?
"""


def generate_test_run_id() -> str:
    """Generate unique run ID for test runs."""

    return f"test_{timestamp_readable()}"


def create_test_workspace(run_dir: Path, copy_fixtures: bool = True) -> Path:
    """Create isolated workspace directory for test run.

    Example:
        >>> workspace = create_test_workspace(run_dir)
        >>> workspace
        Path('.agile/runs/test_2023-12-15_14:30:52/fixtures')
        >>> list(workspace.iterdir())
        [Path('broken_code'), Path('fastapi_app'), Path('simple_python')]
    """
    fixtures_dir = run_dir / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    if copy_fixtures:
        tests_dir = Path(__file__).parent.parent
        source_fixtures_dir = tests_dir / "e2e" / "fixtures"

        for fixture_subdir in source_fixtures_dir.iterdir():
            if fixture_subdir.is_dir() and not fixture_subdir.name.startswith("__"):
                dest = fixtures_dir / fixture_subdir.name
                shutil.copytree(fixture_subdir, dest, dirs_exist_ok=True)

    return fixtures_dir


def get_workspace_dir(base_dir: Path, run_id: str) -> Path:
    """Gets workspace directory for a run.

    This function:
    1. constructs the path from base_dir and run_id
    2. returns the workspace directory path

    Args:
        base_dir: Base directory for runs (usually .agile/runs)
        run_id: Run ID from RUN_STARTED event

    Returns:
        Path to workspace directory

    Example:
        >>> workspace = get_workspace_dir(base_dir, "run_abc123")
        >>> assert workspace == base_dir / "run_abc123"
    """
    return base_dir / run_id


def assert_file_exists(workspace_dir: Path, relative_path: str) -> None:
    """Asserts that file exists in workspace."""

    file_path = workspace_dir / relative_path
    assert file_path.exists(), f"File not found: {relative_path}"


def assert_file_contains(workspace_dir: Path, relative_path: str, content: str) -> None:
    """Asserts that file contains specific content."""

    file_path = workspace_dir / relative_path
    assert file_path.exists(), f"File not found: {relative_path}"
    actual_content = file_path.read_text()
    assert content in actual_content, (
        f"Content not found in {relative_path}.\n"
        f"Looking for: {content}\n"
        f"File contains: {actual_content[:200]}..."
    )


def assert_file_matches_regex(workspace_dir: Path, relative_path: str, pattern: str) -> None:
    """Asserts that file content matches regex pattern."""

    file_path = workspace_dir / relative_path
    assert file_path.exists(), f"File not found: {relative_path}"
    actual_content = file_path.read_text()
    assert re.search(pattern, actual_content), (
        f"Pattern not found in {relative_path}.\n" f"Pattern: {pattern}\n" f"File contains: {actual_content[:200]}..."
    )


def read_file(workspace_dir: Path, relative_path: str) -> str:
    """Reads file content from workspace."""

    file_path = workspace_dir / relative_path
    assert file_path.exists(), f"File not found: {relative_path}"
    return file_path.read_text()


def assert_tests_pass(workspace_dir: Path, test_command: str = "pytest") -> None:
    """Runs tests in workspace and asserts they pass.

    This function:
    1. executes the test command in the workspace directory
    2. captures stdout and stderr
    3. asserts that the return code is 0 (success)

    Example:
        >>> assert_tests_pass(workspace_dir)
        >>> assert_tests_pass(workspace_dir, "pytest -v")
    """
    command_parts = test_command.split()
    result = subprocess.run(
        command_parts,
        cwd=workspace_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"Tests failed in workspace.\n" f"stdout: {result.stdout}\n" f"stderr: {result.stderr}"
    )

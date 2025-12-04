from pathlib import Path

import pytest

from agile_ai_sdk import TaskExecutor
from tests.helpers.assertions import assert_no_errors
from tests.helpers.event_collector import EventCollector
from tests.helpers.llm_judge import LLMJudge
from tests.helpers.workspace_utils import (
    assert_file_exists,
    assert_tests_pass,
)


@pytest.mark.scenario
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(900)
async def test_add_health_endpoint(
    executor: TaskExecutor, event_collector: EventCollector, workspace_dir: Path, test_run_logger
) -> None:
    """Add /health endpoint to FastAPI app with tests."""

    task = (
        "cd fastapi_app && "
        "Add a /health endpoint to the FastAPI app in main.py that returns "
        "{'status': 'healthy', 'version': '1.0.0'}. "
        "Also add a test_health() function in test_main.py that verifies "
        "the endpoint returns status code 200 and the correct JSON response. "
        "Make sure all tests pass by running pytest."
    )

    await event_collector.collect_until_done(executor.execute(task, workspace_dir=workspace_dir))
    event_collector.assert_completed_successfully()

    assert_file_exists(workspace_dir / "fastapi_app", "main.py")
    assert_file_exists(workspace_dir / "fastapi_app", "test_main.py")

    judge = LLMJudge()
    evaluation = await judge.evaluate_and_log(
        task=task,
        events=event_collector.events,
        workspace_dir=workspace_dir / "fastapi_app",
        test_run_logger=test_run_logger,
    )

    assert evaluation.task_completed, (
        f"Task not completed according to LLM judge.\n"
        f"Confidence: {evaluation.confidence}\n"
        f"Reasoning: {evaluation.reasoning}\n"
        f"Issues: {evaluation.issues_found}"
    )

    assert_tests_pass(workspace_dir / "fastapi_app", "pytest -v")

    assert_no_errors(event_collector.events)


@pytest.mark.scenario
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(900)
async def test_fix_broken_code(
    executor: TaskExecutor, event_collector: EventCollector, workspace_dir: Path, test_run_logger
) -> None:
    """Fix all bugs in broken_code fixture."""

    task = (
        "cd broken_code && "
        "Run pytest on test_buggy.py to see which tests are failing. "
        "You will find that calculate_average() and find_max() in buggy.py "
        "don't handle empty lists correctly. Fix both functions to raise "
        "ValueError when given an empty list. The error messages should be: "
        "'Cannot calculate average of empty list' for calculate_average and "
        "'Cannot find maximum of empty list' for find_max. "
        "After fixing, run the tests again to make sure all tests pass."
    )

    await event_collector.collect_until_done(executor.execute(task, workspace_dir=workspace_dir))

    event_collector.assert_completed_successfully()

    assert_file_exists(workspace_dir / "broken_code", "buggy.py")
    assert_file_exists(workspace_dir / "broken_code", "test_buggy.py")

    judge = LLMJudge()
    evaluation = await judge.evaluate_and_log(
        task=task,
        events=event_collector.events,
        workspace_dir=workspace_dir / "broken_code",
        test_run_logger=test_run_logger,
    )

    assert evaluation.task_completed, (
        f"Task not completed according to LLM judge.\n"
        f"Confidence: {evaluation.confidence}\n"
        f"Reasoning: {evaluation.reasoning}\n"
        f"Issues: {evaluation.issues_found}"
    )

    assert_tests_pass(workspace_dir / "broken_code", "pytest -v")

    assert_no_errors(event_collector.events)


@pytest.mark.scenario
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(900)
async def test_add_feature_with_tests(
    executor: TaskExecutor, event_collector: EventCollector, workspace_dir: Path, test_run_logger
) -> None:
    """Add complete feature with implementation, tests, and documentation."""

    task = (
        "cd simple_python && "
        "Add a divide(a, b) function to calculator.py that returns a / b. "
        "The function should raise ValueError with message 'Cannot divide by zero' "
        "when b is 0. Add a comprehensive docstring following Google style. "
        "In test_calculator.py, add test_divide() and test_divide_by_zero() functions. "
        "test_divide() should test normal division cases (e.g., 10/2=5, 15/3=5). "
        "test_divide_by_zero() should verify that dividing by zero raises ValueError. "
        "Run pytest to make sure all tests pass."
    )

    await event_collector.collect_until_done(executor.execute(task, workspace_dir=workspace_dir))

    event_collector.assert_completed_successfully()

    assert_file_exists(workspace_dir / "simple_python", "calculator.py")
    assert_file_exists(workspace_dir / "simple_python", "test_calculator.py")

    judge = LLMJudge()
    evaluation = await judge.evaluate_and_log(
        task=task,
        events=event_collector.events,
        workspace_dir=workspace_dir / "simple_python",
        test_run_logger=test_run_logger,
    )

    assert evaluation.task_completed, (
        f"Task not completed according to LLM judge.\n"
        f"Confidence: {evaluation.confidence}\n"
        f"Reasoning: {evaluation.reasoning}\n"
        f"Issues: {evaluation.issues_found}"
    )

    assert_tests_pass(workspace_dir / "simple_python", "pytest -v")

    assert_no_errors(event_collector.events)

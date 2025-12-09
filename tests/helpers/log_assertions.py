import json
from pathlib import Path

from agile_ai_sdk.models.event import Event
from tests.logging.run_logger import TestRunLogger


def assert_logs_created(test_run_logger: TestRunLogger) -> None:
    """Assert log directory and required files exist.

    Validates:
    - Log directory exists
    - events.jsonl exists
    - metadata.json exists
    """

    log_dir = test_run_logger.get_log_dir()
    assert log_dir.exists(), f"Log directory not created: {log_dir}"
    assert test_run_logger.events_file.exists(), "events.jsonl not created"
    assert (log_dir / "metadata.json").exists(), "metadata.json not created"


def assert_jsonl_valid(jsonl_path: Path) -> None:
    """Assert JSONL file is valid (one JSON object per line).

    Validates:
    - File exists and not empty
    - Each line is valid JSON
    - Each line has required event fields
    """

    assert jsonl_path.exists(), f"JSONL file not found: {jsonl_path}"

    with open(jsonl_path) as f:
        lines = f.readlines()

    assert len(lines) > 0, "JSONL file is empty"

    for i, line in enumerate(lines):
        try:
            event_data = json.loads(line)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Line {i+1} is not valid JSON: {e}") from e

        required_fields = ["timestamp", "type", "agent", "data"]
        for field in required_fields:
            assert field in event_data, f"Line {i+1} missing field: {field}"


def assert_metadata_complete(test_run_logger: TestRunLogger, check_finalized: bool = False) -> None:
    """Assert metadata.json has all required fields.

    Validates:
    - File exists and is valid JSON
    - Has required fields: test_name, test_file, test_tier, task, run_id, start_time
    - After finalization (if check_finalized=True): end_time, duration_seconds, result

    Args:
        test_run_logger: The test run logger instance
        check_finalized: If True, also check that finalization fields are present,
                         meaning the test completed/finalized successfully
    """
    metadata_path = test_run_logger.get_log_dir() / "metadata.json"
    assert metadata_path.exists(), "metadata.json not found"

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Required fields always present
    required_fields = ["test_name", "test_file", "test_tier", "task", "run_id", "start_time"]
    for field in required_fields:
        assert field in metadata, f"metadata.json missing field: {field}"
        assert metadata[field] is not None, f"metadata.json field is None: {field}"

    # Fields present after finalization (only check if explicitly requested)
    if check_finalized:
        assert "end_time" in metadata, "end_time missing (not finalized)"
        assert metadata["end_time"] is not None
        assert "duration_seconds" in metadata
        assert metadata["duration_seconds"] is not None
        assert metadata["duration_seconds"] > 0


def assert_events_match_logged(test_run_logger: TestRunLogger, collected_events: list[Event]) -> None:
    """Assert events in events.jsonl match collected events.

    Validates:
    - Same number of events
    - Same event types in same order
    - Same agent roles
    """

    with open(test_run_logger.events_file) as f:
        lines = f.readlines()

    logged_events = [json.loads(line) for line in lines]

    assert len(logged_events) == len(
        collected_events
    ), f"Event count mismatch: {len(logged_events)} logged vs {len(collected_events)} collected"

    for i, (logged, collected) in enumerate(zip(logged_events, collected_events)):
        assert (
            logged["type"] == collected.type.value
        ), f"Event {i}: type mismatch: {logged['type']} vs {collected.type.value}"
        assert (
            logged["agent"] == collected.agent.value
        ), f"Event {i}: agent mismatch: {logged['agent']} vs {collected.agent.value}"


def assert_log_files_not_empty(test_run_logger: TestRunLogger) -> None:
    """Lightweight check that log files exist and have content.

    Use this for scenario tests that don't need comprehensive validation.
    """

    assert test_run_logger.events_file.exists(), "events.jsonl not created"
    assert test_run_logger.events_file.stat().st_size > 0, "events.jsonl is empty"

    metadata_file = test_run_logger.get_log_dir() / "metadata.json"
    assert metadata_file.exists(), "metadata.json not created"
    assert metadata_file.stat().st_size > 0, "metadata.json is empty"

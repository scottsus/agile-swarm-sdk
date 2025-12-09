from typing import Any

from agile_ai_sdk.utils.time import timestamp_iso


class TestRunMetadata:
    """Metadata for a test run."""

    def __init__(self, test_name: str, test_file: str, test_tier: str, task: str, run_id: str):
        self.test_name = test_name
        self.test_file = test_file
        self.test_tier = test_tier
        self.task = task
        self.run_id = run_id
        self.start_time = timestamp_iso()
        self.end_time: str | None = None
        self.duration_seconds: float | None = None
        self.result: str | None = None
        self.error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""

        return {
            "test_name": self.test_name,
            "test_file": self.test_file,
            "test_tier": self.test_tier,
            "task": self.task,
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "result": self.result,
            "error": self.error,
        }

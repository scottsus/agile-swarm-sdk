from typing import Any

from agile_ai_sdk.models import RunStatus
from agile_ai_sdk.utils.time import timestamp_iso


class RunMetadata:
    """Metadata for a production run.

    Example:
        >>> metadata = RunMetadata(
        ...     run_id="run_2025-12-06_14:30:22",
        ...     task="Add /health endpoint"
        ... )
        >>> metadata.status
        <RunStatus.RUNNING: 'running'>
        >>> metadata.to_dict()
        {'run_id': 'run_2025-12-06_14:30:22', 'task': 'Add /health endpoint', ...}
    """

    def __init__(self, run_id: str, task: str | None = None):
        self.run_id = run_id
        self.task = task
        self.start_time = timestamp_iso()
        self.end_time: str | None = None
        self.duration_seconds: float | None = None
        self.status: RunStatus = RunStatus.RUNNING
        self.error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON persistence."""

        return {
            "run_id": self.run_id,
            "task": self.task,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "error": self.error,
        }

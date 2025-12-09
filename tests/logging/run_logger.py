import json
from pathlib import Path

from agile_ai_sdk.logging.event_logger import EventLogger
from agile_ai_sdk.models import RunStatus
from agile_ai_sdk.models.event import Event
from agile_ai_sdk.utils.time import timestamp_iso
from tests.logging.run_metadata import TestRunMetadata


class TestRunLogger:
    """Test-specific wrapper around production EventLogger.

    Adds test-specific features:
    - TestRunMetadata with test name, file, and tier
    - llm_judge/ directory for LLM evaluations
    - Result mapping (passed/failed → completed/error)

    Creates a structured log directory for each test run with:
    - metadata.json: Test info and results
    - events.jsonl: Event stream
    - llm_judge.md: LLM judge evaluations

    Example:
        >>> logger = TestRunLogger(
        ...     test_name="test_add_health_endpoint",
        ...     test_file="tests/e2e/scenarios/test_fastapi_health.py",
        ...     test_tier="scenario",
        ...     task="Add /health endpoint",
        ...     log_dir=Path("./test_logs"),
        ...     run_id="run_20251208_1234"
        ... )
        >>> logger.log_event(event)
        >>> logger.finalize(result="passed")
    """

    def __init__(
        self,
        test_name: str,
        test_file: str,
        test_tier: str,
        task: str,
        log_dir: Path,
        run_id: str,
    ):
        """Initialize test run logger."""

        self._event_logger = EventLogger(
            task=task,
            run_id=run_id,
            log_dir=log_dir,
        )

        self.metadata = TestRunMetadata(
            test_name=test_name,
            test_file=test_file,
            test_tier=test_tier,
            task=task,
            run_id=self._event_logger.metadata.run_id,
        )

        self.log_dir = self._event_logger.get_log_dir()
        (self.log_dir / "llm_judge").mkdir(exist_ok=True)

        self._write_metadata()

        self.events_file = self._event_logger.events_file

    def _write_metadata(self) -> None:
        """Write metadata to metadata.json."""

        metadata_path = self.log_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(self.metadata.to_dict(), f, indent=2)

    def log_event(self, event: Event) -> None:
        """Log an event to events.jsonl."""

        self._event_logger.log_event(event)

    def log_llm_judge_evaluation(self, evaluation_markdown: str) -> None:
        """Log LLM judge evaluation to llm_judge.md."""

        eval_path = self.log_dir / "llm_judge.md"
        eval_path.parent.mkdir(parents=True, exist_ok=True)

        with open(eval_path, "w") as f:
            f.write(f"# LLM Judge Evaluation - {timestamp_iso()}\n\n")
            f.write(evaluation_markdown)

    def finalize(self, result: str, error: str | None = None) -> None:
        """Finalize the test run with result status."""

        status_map = {
            "passed": RunStatus.COMPLETED,
            "failed": RunStatus.ERROR,
            "unknown": RunStatus.ERROR,
        }
        status = status_map.get(result, RunStatus.ERROR)

        self._event_logger.finalize(status=status, error=error)

        self.metadata.end_time = self._event_logger.metadata.end_time
        self.metadata.duration_seconds = self._event_logger.metadata.duration_seconds
        self.metadata.result = result
        self.metadata.error = error

        self._write_metadata()

    def get_log_dir(self) -> Path:
        """Get the log directory path."""

        return self.log_dir

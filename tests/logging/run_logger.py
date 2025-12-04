import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from agile_ai_sdk.models.event import Event
from tests.helpers.time_utils import timestamp_compact, timestamp_iso, timestamp_readable, utcnow
from tests.logging.run_metadata import TestRunMetadata


class TestRunLogger:
    """Logger for test run outputs.

    Creates a structured log directory for each test run with:
    - metadata.json: Test info and results
    - events.jsonl: Event stream
    - workspace/: Final workspace state
    - journal.json: Agent conversation history
    - command_outputs/: All command executions
    - llm_judge/: LLM judge evaluations

    Example:
        >>> logger = TestRunLogger(
        ...     test_name="test_add_health_endpoint",
        ...     test_file="tests/e2e/scenarios/test_fastapi_health.py",
        ...     test_tier="scenario",
        ...     task="Add /health endpoint"
        ... )
        >>> logger.log_event(event)
        >>> logger.log_command_output("pytest", stdout, stderr, returncode)
        >>> logger.finalize(result="passed")
    """

    def __init__(
        self,
        test_name: str,
        test_file: str,
        test_tier: str,
        task: str,
        log_dir: Path | None = None,
        run_id: str | None = None,
    ):
        """Initialize test run logger.

        Args:
            test_name: Name of the test
            test_file: Path to test file
            test_tier: Test tier (smoke/scenario/feature)
            task: Task description
            log_dir: Custom log directory (if None, uses ~/.agile-ai/test-runs/)
            run_id: Run ID for metadata
        """
        self.metadata = TestRunMetadata(
            test_name=test_name,
            test_file=test_file,
            test_tier=test_tier,
            task=task,
            run_id=run_id or f"run_{timestamp_compact()}",
        )

        self.log_dir = log_dir if log_dir else self._create_log_dir()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.log_dir / "command_outputs").mkdir(exist_ok=True)

        self.events_file = self.log_dir / "events.jsonl"
        self.command_counter = 0

        self._write_metadata()

    def _create_log_dir(self) -> Path:
        """Create log directory for this test run."""

        base_dir = Path.home() / ".agile-ai" / "test-runs"
        timestamp = timestamp_readable()
        log_dir = base_dir / f"{self.metadata.test_name}_{timestamp}"
        log_dir.mkdir(parents=True, exist_ok=True)

        (log_dir / "command_outputs").mkdir(exist_ok=True)
        (log_dir / "llm_judge").mkdir(exist_ok=True)

        return log_dir

    def _write_metadata(self) -> None:
        """Write metadata to file."""

        metadata_path = self.log_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(self.metadata.to_dict(), f, indent=2)

    def log_event(self, event: Event) -> None:
        """Log an event to events.jsonl."""

        def _serialize(obj: Any) -> Any:
            """Serialize objects to JSON-compatible format."""
            if isinstance(obj, datetime):
                return obj.isoformat() + "Z"
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        with open(self.events_file, "a") as f:
            event_data = {
                "timestamp": timestamp_iso(),
                "type": event.type.value,
                "agent": event.agent.value,
                "data": event.data,
            }
            f.write(json.dumps(event_data, default=_serialize) + "\n")

    def log_command_output(self, command: str, stdout: str, stderr: str, returncode: int, duration: float) -> None:
        """Log command output.

        TODO: Not currently hooked up. To implement:
        - Option 1: Emit TOOL_CALL_RESULT events from agents with stdout/stderr/returncode
        - Option 2: Parse STEP_STARTED events and extract command info (limited data)
        - See .claude/tasks/command-output-logging/ for full implementation plan

        For now, command execution info is only in events.jsonl as STEP_STARTED events.
        """
        self.command_counter += 1
        safe_command = command.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{self.command_counter:03d}_{safe_command[:30]}.txt"
        output_path = self.log_dir / "command_outputs" / filename

        with open(output_path, "w") as f:
            f.write(f"Command: {command}\n")
            f.write(f"Return code: {returncode}\n")
            f.write(f"Duration: {duration:.2f}s\n")
            f.write("\n=== STDOUT ===\n")
            f.write(stdout)
            f.write("\n=== STDERR ===\n")
            f.write(stderr)

    def log_llm_judge_evaluation(self, evaluation_markdown: str) -> None:
        """Log LLM judge evaluation in markdown format."""

        eval_path = self.log_dir / "llm_judge.md"
        eval_path.parent.mkdir(parents=True, exist_ok=True)

        with open(eval_path, "w") as f:
            f.write(f"# LLM Judge Evaluation - {timestamp_iso()}\n\n")
            f.write(evaluation_markdown)

    def save_workspace(self, workspace_dir: Path) -> None:
        """Copy workspace to log directory."""

        dest = self.log_dir / "workspace"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(workspace_dir, dest)

    def save_journal(self, journal_path: Path) -> None:
        """Copy journal to log directory."""

        if journal_path.exists():
            shutil.copy2(journal_path, self.log_dir / "journal.json")

    def finalize(self, result: str, error: str | None = None) -> None:
        """Finalize the test run log."""

        start = datetime.fromisoformat(self.metadata.start_time.rstrip("Z"))
        end = utcnow()

        self.metadata.end_time = timestamp_iso()
        self.metadata.duration_seconds = (end - start).total_seconds()
        self.metadata.result = result
        self.metadata.error = error

        self._write_metadata()

    def get_log_dir(self) -> Path:
        """Get the log directory path."""

        return self.log_dir

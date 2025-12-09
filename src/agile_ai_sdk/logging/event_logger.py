import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from agile_ai_sdk.logging.run_metadata import RunMetadata
from agile_ai_sdk.models import RunStatus
from agile_ai_sdk.models.event import Event
from agile_ai_sdk.utils.time import timestamp_iso, timestamp_readable, utcnow


class EventLogger:
    """Event logger for AgentTeam executions.

    Creates a structured log directory with:
    - metadata.json: Run info and results
    - events.jsonl: Event stream (one JSON per line)
    - workspace/: Final workspace snapshot (optional)
    - journal.json: Agent conversation history (optional)
    """

    def __init__(
        self,
        task: str | None = None,
        run_id: str | None = None,
        log_dir: Path | None = None,
    ):
        """Initialize event logger.

        Args:
            task: Task description for metadata
            run_id: Custom run identifier (auto-generated if not provided)
            log_dir: Base log directory (defaults to .agile/runs/ in cwd)
        """

        self._run_id = run_id or f"run_{timestamp_readable()}"
        self._task = task

        self.metadata = RunMetadata(run_id=self._run_id, task=task)

        self.log_dir = self._create_log_dir(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.events_file = self.log_dir / "events.jsonl"
        self.metadata_file = self.log_dir / "metadata.json"

        self._write_metadata()

    def _create_log_dir(self, custom_log_dir: Path | None) -> Path:
        """Create log directory for this run.

        Base directory for logs. If provided, creates log_dir as
        {custom_log_dir}/{run_id}.

        If None, uses .agile/runs/{run_id} in cwd.
        """

        if custom_log_dir:
            base_dir = custom_log_dir
        else:
            base_dir = Path.cwd() / ".agile" / "runs"

        log_dir = base_dir / self._run_id
        return log_dir

    def _write_metadata(self) -> None:
        """Write metadata to file."""

        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata.to_dict(), f, indent=2)

    def log_event(self, event: Event) -> None:
        """Log an event to events.jsonl.

        Handler-compatible method that can be registered with:
        team.on_any_event(logger.log_event)
        """

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

    def save_workspace(self, workspace_dir: Path) -> None:
        """Copy workspace directory to log directory."""

        dest = self.log_dir / "workspace"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(workspace_dir, dest)

    def save_journal(self, journal_path: Path) -> None:
        """Copy journal file to log directory."""

        if journal_path.exists():
            shutil.copy2(journal_path, self.log_dir / "journal.json")

    def finalize(self, status: RunStatus = RunStatus.COMPLETED, error: str | None = None) -> None:
        """Finalize the run with status and timing information.

        Example:
            >>> logger.finalize(status=RunStatus.COMPLETED)
            >>> logger.finalize(status=RunStatus.ERROR, error="Task failed")
        """
        start = datetime.fromisoformat(self.metadata.start_time.rstrip("Z"))
        end = utcnow()

        self.metadata.end_time = timestamp_iso()
        self.metadata.duration_seconds = (end - start).total_seconds()
        self.metadata.status = status
        self.metadata.error = error

        self._write_metadata()

    def get_log_dir(self) -> Path:
        """Get the log directory path for this run.

        Returns:
            Path to log directory

        Example:
            >>> logger = EventLogger()
            >>> print(f"Logs at: {logger.get_log_dir()}")
        """
        return self.log_dir

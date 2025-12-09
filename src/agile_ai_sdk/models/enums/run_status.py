from enum import Enum


class RunStatus(str, Enum):
    """Run status for agent executions."""

    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

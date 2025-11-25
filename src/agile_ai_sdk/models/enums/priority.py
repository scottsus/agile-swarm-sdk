from enum import Enum


class Priority(str, Enum):
    """Message priority levels."""

    NORMAL = "normal"
    INTERRUPT = "interrupt"

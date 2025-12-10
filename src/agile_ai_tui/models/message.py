from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from agile_ai_sdk.models import AgentRole


class MessageType(str, Enum):
    """Type of message for display."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    ERROR = "error"
    TOOL_CALL = "tool_call"


@dataclass
class ToolCallData:
    """Structured data for tool call visualization.

    Example:
        >>> data = ToolCallData(
        ...     tool_name="bash",
        ...     args={"command": "ls -la"},
        ...     result="total 48\\ndrwxr-xr-x...",
        ...     status="success"
        ... )
    """

    tool_name: str
    args: dict[str, Any] | str | None = None
    result: str | None = None
    status: Literal["started", "success", "error"] = "started"


@dataclass
class FormattedMessage:
    """Formatted event ready for display in TUI.

    Example:
        >>> msg = FormattedMessage(
        ...     sender="Dev",
        ...     content="Task completed",
        ...     message_type=MessageType.AGENT,
        ...     agent_role=AgentRole.DEV
        ... )
        >>> msg.sender
        'Dev'
    """

    sender: str
    content: str
    message_type: MessageType
    agent_role: AgentRole | None = None
    is_collapsible: bool = False
    full_content: str | None = None
    tool_data: ToolCallData | None = None

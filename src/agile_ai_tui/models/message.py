from dataclasses import dataclass
from enum import Enum

from agile_ai_sdk.models import AgentRole


class MessageType(str, Enum):
    """Type of message for display."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    ERROR = "error"


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

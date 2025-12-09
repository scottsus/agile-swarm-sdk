from dataclasses import dataclass
from typing import Literal

from agile_ai_sdk.models import AgentRole


@dataclass
class FormattedMessage:
    """Formatted event ready for display in TUI.

    Example:
        >>> msg = FormattedMessage(
        ...     sender="Dev",
        ...     content="Task completed",
        ...     message_type="agent",
        ...     agent_role=AgentRole.DEV
        ... )
        >>> msg.sender
        'Dev'
    """

    sender: str
    content: str
    message_type: Literal["user", "agent", "system", "error"]
    agent_role: AgentRole | None = None

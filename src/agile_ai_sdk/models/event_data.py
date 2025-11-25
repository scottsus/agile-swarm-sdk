from typing import Literal

from agile_ai_sdk.models.base import BaseModel


class MessageSentData(BaseModel):
    """Data payload when a message is sent."""

    action: Literal["sent"] = "sent"
    to: str
    content: str
    priority: str


class MessageReceivedData(BaseModel):
    """Data payload when a message is received."""

    action: Literal["received"] = "received"
    from_: str  # 'from' is a Python keyword
    content: str
    priority: str


class AgentStatusData(BaseModel):
    """Data payload for agent status updates."""

    status: str


class ErrorData(BaseModel):
    """Data payload for error events."""

    error: str

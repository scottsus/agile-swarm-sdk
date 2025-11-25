from typing import Any

from pydantic import Field

from agile_ai_sdk.models.base import BaseModel
from agile_ai_sdk.models.enums import AgentRole, EventType
from agile_ai_sdk.models.enums.human_role import HumanRole


class Event(BaseModel):
    """Event emitted during task execution."""

    type: EventType
    agent: AgentRole | HumanRole
    data: dict[str, Any] = Field(default_factory=dict)

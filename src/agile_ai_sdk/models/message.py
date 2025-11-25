from agile_ai_sdk.models.base import BaseModel
from agile_ai_sdk.models.enums import AgentRole, HumanRole, Priority


class Message(BaseModel):
    """Message passed between agents or from humans."""

    source: AgentRole | HumanRole
    target: AgentRole
    content: str
    priority: Priority = Priority.NORMAL

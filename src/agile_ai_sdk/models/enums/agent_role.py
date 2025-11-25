from enum import Enum


class AgentRole(str, Enum):
    """Agent role identifiers."""

    EM = "engineering_manager"
    PLANNER = "planner"
    DEV = "developer"
    SENIOR_REVIEWER = "senior_reviewer"

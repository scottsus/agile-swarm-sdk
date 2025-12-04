from pydantic import BaseModel, Field


class TaskEvaluation(BaseModel):
    """Result of task completion evaluation."""

    task_completed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    issues_found: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class CodeQualityEvaluation(BaseModel):
    """Result of code quality evaluation."""

    passes: bool
    criteria_results: dict[str, bool]
    reasoning: str
    issues: list[str] = Field(default_factory=list)

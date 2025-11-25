import uuid
from datetime import datetime

from pydantic import BaseModel as BasePydanticModel
from pydantic import Field


class BaseModel(BasePydanticModel):
    """Base model with automatic ID generation and timestamp tracking."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

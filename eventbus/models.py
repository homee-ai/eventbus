from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class Priority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class Event(BaseModel):
    event_type: str = Field(..., description="Event type, e.g. job.completed or user.registered")
    priority: Priority = Field(default=Priority.NORMAL, description="Priority level of the event")
    detail: Optional[dict] = Field(default_factory=dict, description="Detailed event information")
    attributes: Optional[dict] = Field(default_factory=dict, description="Additional contextual data, just for logging")

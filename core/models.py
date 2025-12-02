from enum import Enum
from typing import Dict
from pydantic import BaseModel, Field


class EventPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Event(BaseModel):
    type: str = Field(..., description="Event type, e.g. job.completed or user.registered")
    priority: EventPriority = Field(default=EventPriority.NORMAL, description="Priority level of the event")
    detail: Dict = Field(default_factory=dict, description="Detailed event information")
    metadata: Dict = Field(default_factory=dict, description="Additional contextual data, just for logging")

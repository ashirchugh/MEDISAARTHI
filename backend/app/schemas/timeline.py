from typing import Optional
from pydantic import BaseModel, ConfigDict


class TimelineEventBase(BaseModel):
    date: str
    fact: str
    source: str = "previous_consultation"
    confidence: float = 0.95


class TimelineEventCreate(TimelineEventBase):
    patient_id: str


class TimelineEventResponse(TimelineEventBase):
    id: int
    patient_id: str

    model_config = ConfigDict(from_attributes=True)

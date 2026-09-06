from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict


class InterviewStartRequest(BaseModel):
    patient_id: str
    language: str = "hi"


class InitialQuestion(BaseModel):
    text: str
    type: str = "text"


class InterviewResponse(BaseModel):
    interview_id: str
    patient_id: str
    status: str
    language: str
    started_at: Optional[datetime] = None
    initial_question: Optional[InitialQuestion] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewMessageCreate(BaseModel):
    role: str  # 'system', 'assistant', 'patient'
    text: str
    language: str = "hi"


class InterviewMessageResponse(BaseModel):
    id: int
    interview_id: str
    role: str
    text: str
    language: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewRespondRequest(BaseModel):
    interview_id: str
    message: str


class ExtractedFactItem(BaseModel):
    field_name: str
    value: str
    status: str = "confirmed"

    model_config = ConfigDict(from_attributes=True)


class NextQuestion(BaseModel):
    text: str
    type: str = "text"


class InterviewRespondResponse(BaseModel):
    interview_id: str
    status: str
    received_message: str
    extracted_facts: List[ExtractedFactItem]
    current_topic: str
    next_question: NextQuestion
    interview_completed: bool = False

    model_config = ConfigDict(from_attributes=True)


class InterviewVoiceResponse(BaseModel):
    interview_id: str
    status: str
    transcript: str
    received_message: str
    extracted_facts: List[ExtractedFactItem]
    current_topic: str
    next_question: NextQuestion
    interview_completed: bool = False

    model_config = ConfigDict(from_attributes=True)


class InterviewDetailResponse(BaseModel):
    interview_id: str
    patient_id: str
    status: str
    language: str
    current_topic: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    messages: List[InterviewMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InterviewCompleteRequest(BaseModel):
    interview_id: str


class InterviewCompleteResponse(BaseModel):
    interview_id: str
    status: str
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

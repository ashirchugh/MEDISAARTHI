from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class PatientBase(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    preferred_language: str = "hi"
    phone: Optional[str] = None
    uhid: Optional[str] = None
    registration_time: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientResponse(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    language: str
    phone: Optional[str] = None
    uhid: Optional[str] = None
    registration_time: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PatientListItem(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    language: str
    current_complaint: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    status: str = "Ready for review"
    priority: str = "Normal"
    arrival_time: Optional[str] = None
    registration_time: Optional[str] = None
    uhid: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

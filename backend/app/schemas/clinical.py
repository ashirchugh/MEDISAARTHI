from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.timeline import TimelineEventResponse


class ClinicalFactBase(BaseModel):
    field_name: str
    value: str
    source: str = "current_interview"
    confidence: float = 1.0
    status: str = "confirmed"


class ClinicalFactCreate(ClinicalFactBase):
    patient_id: str
    interview_id: Optional[str] = None


class ClinicalFactResponse(ClinicalFactBase):
    id: int
    patient_id: str
    interview_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MedicationBase(BaseModel):
    name: str
    dosage: str
    frequency: Optional[str] = None
    source: str = "patient_history"


class MedicationCreate(MedicationBase):
    patient_id: str


class MedicationResponse(MedicationBase):
    id: int
    patient_id: str

    model_config = ConfigDict(from_attributes=True)


class AllergyBase(BaseModel):
    allergen: str
    reaction: Optional[str] = None
    source: str = "patient_history"


class AllergyCreate(AllergyBase):
    patient_id: str


class AllergyResponse(AllergyBase):
    id: int
    patient_id: str

    model_config = ConfigDict(from_attributes=True)


class ConditionItem(BaseModel):
    year: Optional[str] = None
    condition: str
    status: Optional[str] = "Active"
    notes: Optional[str] = None


class PatientHistoryResponse(BaseModel):
    patient_id: str
    conditions: List[ConditionItem] = []
    medications: List[MedicationResponse] = []
    allergies: List[AllergyResponse] = []
    timeline: List[TimelineEventResponse] = []

    model_config = ConfigDict(from_attributes=True)

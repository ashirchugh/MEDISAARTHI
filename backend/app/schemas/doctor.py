"""Doctor Summary Data Schemas for Medisaarthi Pre-Consultation Engine.

Provides structured, type-safe schemas representing patient snapshot, current complaints,
past history, medications, allergies, important clinical findings, missing topics,
and verification metadata for the doctor dashboard.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class PatientSnapshot(BaseModel):
    patient_id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    preferred_language: Optional[str] = None
    uhid: Optional[str] = None
    phone: Optional[str] = None
    registration_time: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CurrentComplaintFact(BaseModel):
    field_name: str
    value: str
    status: str = "confirmed"
    source: str = "current_interview"
    confidence: float = 1.0

    model_config = ConfigDict(from_attributes=True)


class CurrentComplaintSection(BaseModel):
    chief_complaint: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    location: Optional[str] = None
    trigger: Optional[str] = None
    associated_symptoms: Optional[str] = None
    facts: List[CurrentComplaintFact] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PastMedicalHistoryItem(BaseModel):
    condition: str
    date: Optional[str] = None
    source: Optional[str] = "previous_consultation"
    confidence: float = 0.95

    model_config = ConfigDict(from_attributes=True)


class MedicationItem(BaseModel):
    name: str
    dosage: str
    frequency: Optional[str] = None
    source: str = "patient_history"

    model_config = ConfigDict(from_attributes=True)


class AllergyItem(BaseModel):
    allergen: str
    reaction: Optional[str] = None
    source: str = "patient_history"

    model_config = ConfigDict(from_attributes=True)


class ImportantFindingItem(BaseModel):
    finding: str
    value: str
    category: str = "symptom"
    status: str = "confirmed"

    model_config = ConfigDict(from_attributes=True)


class MissingInformationItem(BaseModel):
    field_name: str
    description: str
    importance: str = "standard"

    model_config = ConfigDict(from_attributes=True)


class InterviewMetadata(BaseModel):
    interview_id: Optional[str] = None
    status: str = "not_started"
    language: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_topic: Optional[str] = None
    total_messages: int = 0

    model_config = ConfigDict(from_attributes=True)


class DoctorSummaryData(BaseModel):
    patient_snapshot: PatientSnapshot
    current_complaint: CurrentComplaintSection
    past_medical_history: List[PastMedicalHistoryItem] = Field(default_factory=list)
    medications: List[MedicationItem] = Field(default_factory=list)
    allergies: List[AllergyItem] = Field(default_factory=list)
    allergy_status: str = "No allergies recorded"
    important_findings: List[ImportantFindingItem] = Field(default_factory=list)
    missing_information: List[MissingInformationItem] = Field(default_factory=list)
    priority_flags: List[str] = Field(default_factory=list)
    interview_metadata: InterviewMetadata
    verification_status: str = "AI-assisted / unverified"

    model_config = ConfigDict(from_attributes=True)


class DoctorNarrativeSummary(BaseModel):
    patient_id: str
    patient_snapshot: str = Field(
        ...,
        description="Concise demographic summary line (e.g., 'Rajesh Kumar, 48-year-old male')",
    )
    presenting_complaint: str = Field(
        ...,
        description="One-line summary of chief complaint and duration",
    )
    interview_summary: str = Field(
        ...,
        description="Bulleted summary of reported details: severity, location, triggers, symptoms",
    )
    relevant_history: str = Field(
        ...,
        description="Bulleted past medical conditions with recorded dates",
    )
    medications: str = Field(
        ...,
        description="Bulleted active medications with dosage and frequency",
    )
    allergies: str = Field(
        ...,
        description="Bulleted known allergies or explicit NKDA statement",
    )
    important_findings: str = Field(
        ...,
        description="Bulleted clinically notable findings or acute symptoms reported",
    )
    missing_information: str = Field(
        ...,
        description="Bulleted unresolved topics or 'None recorded'",
    )
    priority_flags: str = Field(
        ...,
        description="Explicit deterministic priority/safety flags or 'None'",
    )
    verification_note: str = Field(
        default="AI-assisted pre-consultation intake summary. Doctor verification required before clinical decision making.",
        description="Mandatory verification disclaimer note",
    )

    model_config = ConfigDict(from_attributes=True)


class DoctorEditAuditItem(BaseModel):
    audit_id: str
    patient_id: str
    interview_id: Optional[str] = None
    field_name: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    changed_by: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorSummaryEditRequest(BaseModel):
    chief_complaint: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    location: Optional[str] = None
    trigger: Optional[str] = None
    associated_symptoms: Optional[str] = None
    past_medical_history: Optional[List[PastMedicalHistoryItem]] = None
    medications: Optional[List[MedicationItem]] = None
    allergies: Optional[List[AllergyItem]] = None

    model_config = ConfigDict(extra="forbid")


class DoctorSummaryEditResponse(BaseModel):
    patient_id: str
    updated_fields: List[str]
    verification_status: str
    audit_entries: List[DoctorEditAuditItem]

    model_config = ConfigDict(from_attributes=True)


class DoctorSummaryVerifyResponse(BaseModel):
    patient_id: str
    verification_status: str
    verified_by: str
    verified_at: datetime

    model_config = ConfigDict(from_attributes=True)


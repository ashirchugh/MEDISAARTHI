from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from backend.app.models.patient import Patient
from backend.app.models.clinical_fact import ClinicalFact
from backend.app.models.medication import Medication
from backend.app.models.allergy import Allergy
from backend.app.models.timeline_event import TimelineEvent
from backend.app.schemas.patient import PatientCreate, PatientResponse
from backend.app.schemas.clinical import (
    PatientHistoryResponse,
    ConditionItem,
    MedicationResponse,
    AllergyResponse,
)
from backend.app.schemas.timeline import TimelineEventResponse


def get_patient_by_id(db: Session, patient_id: str) -> Optional[Patient]:
    """Retrieve a patient from PostgreSQL by their human-facing patient_id (e.g. P1001)."""
    stmt = select(Patient).where(Patient.patient_id.ilike(patient_id.strip()))
    return db.scalars(stmt).first()


def get_patient_history(db: Session, patient_id: str) -> Optional[PatientHistoryResponse]:
    """Retrieve structured past conditions, medications, allergies, and timeline for a patient."""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        return None

    # Fetch conditions from clinical facts with field_name in ('condition', 'past_history', 'diagnosis')
    stmt_facts = select(ClinicalFact).where(
        ClinicalFact.patient_id == patient.patient_id,
        ClinicalFact.field_name.in_(["condition", "past_history", "diagnosis"]),
    )
    facts = db.scalars(stmt_facts).all()

    conditions: List[ConditionItem] = []
    for fact in facts:
        # e.g., value might be "Essential Hypertension (Diagnosed 2021)" or just condition
        conditions.append(
            ConditionItem(
                condition=fact.value,
                status=fact.status.capitalize() if fact.status else "Active",
                notes=f"Source: {fact.source}",
            )
        )

    # Fetch medications
    stmt_meds = select(Medication).where(Medication.patient_id == patient.patient_id)
    meds = db.scalars(stmt_meds).all()
    med_responses = [
        MedicationResponse(
            id=m.id,
            patient_id=m.patient_id,
            name=m.name,
            dosage=m.dosage,
            frequency=m.frequency,
            source=m.source,
        )
        for m in meds
    ]

    # Fetch allergies
    stmt_allergies = select(Allergy).where(Allergy.patient_id == patient.patient_id)
    allergies = db.scalars(stmt_allergies).all()
    allergy_responses = [
        AllergyResponse(
            id=a.id,
            patient_id=a.patient_id,
            allergen=a.allergen,
            reaction=a.reaction,
            source=a.source,
        )
        for a in allergies
    ]

    # Fetch timeline events
    stmt_timeline = select(TimelineEvent).where(
        TimelineEvent.patient_id == patient.patient_id
    ).order_by(TimelineEvent.id.asc())
    timeline_events = db.scalars(stmt_timeline).all()
    timeline_responses = [
        TimelineEventResponse(
            id=t.id,
            patient_id=t.patient_id,
            date=t.date,
            fact=t.fact,
            source=t.source,
            confidence=t.confidence,
        )
        for t in timeline_events
    ]

    return PatientHistoryResponse(
        patient_id=patient.patient_id,
        conditions=conditions,
        medications=med_responses,
        allergies=allergy_responses,
        timeline=timeline_responses,
    )


def create_patient(db: Session, data: PatientCreate) -> Patient:
    """Create a new patient record in PostgreSQL."""
    patient = Patient(
        patient_id=data.patient_id,
        name=data.name,
        age=data.age,
        gender=data.gender.lower(),
        preferred_language=data.preferred_language,
        phone=data.phone,
        uhid=data.uhid,
        registration_time=data.registration_time,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def list_patients(db: Session) -> List[Patient]:
    """List all registered patients."""
    stmt = select(Patient).order_by(Patient.id.asc())
    return list(db.scalars(stmt).all())

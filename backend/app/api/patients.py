from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.schemas.patient import PatientCreate, PatientResponse
from backend.app.schemas.clinical import PatientHistoryResponse
from backend.app.services.patient_service import (
    get_patient_by_id,
    get_patient_history,
    create_patient,
    list_patients,
)

router = APIRouter(tags=["Patients"])


@router.get(
    "/patients",
    response_model=List[PatientResponse],
    summary="List all registered patients",
)
def get_patients_endpoint(db: Session = Depends(get_db)):
    """Retrieve all patients from PostgreSQL."""
    patients = list_patients(db)
    return [
        PatientResponse(
            patient_id=p.patient_id,
            name=p.name,
            age=p.age,
            gender=p.gender,
            language=p.preferred_language,
            phone=p.phone,
            uhid=p.uhid,
            registration_time=p.registration_time,
            created_at=p.created_at,
        )
        for p in patients
    ]


@router.post(
    "/patients",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create/register a new patient",
)
def create_patient_endpoint(request: PatientCreate, db: Session = Depends(get_db)):
    """Register a new patient record in PostgreSQL."""
    existing = get_patient_by_id(db, request.patient_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with ID '{request.patient_id}' already exists",
        )
    patient = create_patient(db, request)
    return PatientResponse(
        patient_id=patient.patient_id,
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        language=patient.preferred_language,
        phone=patient.phone,
        uhid=patient.uhid,
        registration_time=patient.registration_time,
        created_at=patient.created_at,
    )


@router.get(
    "/patients/{patient_id}",
    response_model=PatientResponse,
    summary="Retrieve a patient by human-facing Patient ID",
)
def get_patient_endpoint(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve patient demographic information from PostgreSQL."""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found",
        )
    return PatientResponse(
        patient_id=patient.patient_id,
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        language=patient.preferred_language,
        phone=patient.phone,
        uhid=patient.uhid,
        registration_time=patient.registration_time,
        created_at=patient.created_at,
    )


@router.get(
    "/patients/{patient_id}/history",
    response_model=PatientHistoryResponse,
    summary="Retrieve structured clinical history, medications, allergies, and timeline",
)
def get_patient_history_endpoint(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve structured conditions, active medications, allergies, and medical timeline."""
    history = get_patient_history(db, patient_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found",
        )
    return history


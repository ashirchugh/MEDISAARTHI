from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.schemas.patient import PatientListItem
from backend.app.schemas.doctor import (
    DoctorSummaryData,
    DoctorNarrativeSummary,
    DoctorSummaryEditRequest,
    DoctorSummaryEditResponse,
    DoctorSummaryVerifyResponse,
    DoctorEditAuditItem,
)
from backend.app.services.doctor_service import get_doctor_patient_list
from backend.app.services.summary_service import (
    build_doctor_summary,
    get_doctor_narrative_summary,
    edit_doctor_summary,
    verify_doctor_summary,
    get_doctor_summary_audit_trail,
)

router = APIRouter(tags=["Doctor Dashboard"])


def get_doctor_id(
    x_doctor_id: Optional[str] = Header(None, alias="X-Doctor-ID"),
) -> str:
    """Extract and validate the doctor identity from request headers."""
    if not x_doctor_id or not x_doctor_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Doctor-ID' is required for doctor summary modification and verification.",
        )
    return x_doctor_id.strip()


@router.get(
    "/doctor/patients",
    response_model=List[PatientListItem],
    summary="Retrieve doctor's pre-consultation patient queue",
)
def get_doctor_patients_endpoint(db: Session = Depends(get_db)):
    """Retrieve full list of patients waiting with their complaint, priority, and verification status."""
    return get_doctor_patient_list(db)


@router.get(
    "/doctor/patients/{patient_id}/summary",
    response_model=DoctorSummaryData,
    summary="Retrieve assembled structured clinical summary for doctor review",
)
def get_patient_summary_endpoint(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve structured DoctorSummaryData assembled from PostgreSQL records."""
    summary = build_doctor_summary(db, patient_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found.",
        )
    return summary


@router.get(
    "/doctor/patients/{patient_id}/summary/narrative",
    response_model=DoctorNarrativeSummary,
    summary="Retrieve AI-generated doctor-readable pre-consultation narrative summary",
)
def get_patient_summary_narrative_endpoint(patient_id: str, db: Session = Depends(get_db)):
    """Retrieve doctor-readable pre-consultation narrative summary generated from validated DoctorSummaryData."""
    narrative = get_doctor_narrative_summary(db, patient_id)
    if not narrative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found.",
        )
    return narrative


@router.patch(
    "/doctor/patients/{patient_id}/summary",
    response_model=DoctorSummaryEditResponse,
    summary="Modify structured clinical summary fields with audit tracking",
)
def edit_patient_summary_endpoint(
    patient_id: str,
    edit_data: DoctorSummaryEditRequest,
    db: Session = Depends(get_db),
    doctor_id: str = Depends(get_doctor_id),
):
    """Doctor edit endpoint for correcting AI-assisted clinical facts with immutable audit logging."""
    res = edit_doctor_summary(db, patient_id, edit_data, doctor_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found.",
        )
    return res


@router.post(
    "/doctor/patients/{patient_id}/summary/verify",
    response_model=DoctorSummaryVerifyResponse,
    summary="Mark the pre-consultation summary as Doctor Verified",
)
def verify_patient_summary_endpoint(
    patient_id: str,
    db: Session = Depends(get_db),
    doctor_id: str = Depends(get_doctor_id),
):
    """Doctor verification endpoint to officially verify the clinical intake summary."""
    res = verify_doctor_summary(db, patient_id, doctor_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found.",
        )
    return res


@router.get(
    "/doctor/patients/{patient_id}/summary/audit",
    response_model=List[DoctorEditAuditItem],
    summary="Retrieve doctor correction audit log for a patient",
)
def get_patient_summary_audit_endpoint(
    patient_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve complete audit trail of doctor modifications and corrections."""
    return get_doctor_summary_audit_trail(db, patient_id)

from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.patient import Patient
from backend.app.models.clinical_fact import ClinicalFact
from backend.app.schemas.patient import PatientListItem


def get_doctor_patient_list(db: Session) -> List[PatientListItem]:
    """Retrieve full patient queue for the doctor's pre-consultation dashboard."""
    stmt_patients = select(Patient).order_by(Patient.id.asc())
    patients = db.scalars(stmt_patients).all()

    patient_items: List[PatientListItem] = []
    for p in patients:
        # Query chief complaint from clinical_facts
        stmt_complaint = select(ClinicalFact).where(
            ClinicalFact.patient_id == p.patient_id,
            ClinicalFact.field_name == "chief_complaint",
        ).order_by(ClinicalFact.id.desc())
        complaint_fact = db.scalars(stmt_complaint).first()

        stmt_duration = select(ClinicalFact).where(
            ClinicalFact.patient_id == p.patient_id,
            ClinicalFact.field_name == "duration",
        ).order_by(ClinicalFact.id.desc())
        duration_fact = db.scalars(stmt_duration).first()

        stmt_severity = select(ClinicalFact).where(
            ClinicalFact.patient_id == p.patient_id,
            ClinicalFact.field_name == "severity",
        ).order_by(ClinicalFact.id.desc())
        severity_fact = db.scalars(stmt_severity).first()

        stmt_priority = select(ClinicalFact).where(
            ClinicalFact.patient_id == p.patient_id,
            ClinicalFact.field_name == "priority",
        ).order_by(ClinicalFact.id.desc())
        priority_fact = db.scalars(stmt_priority).first()

        stmt_status = select(ClinicalFact).where(
            ClinicalFact.patient_id == p.patient_id,
            ClinicalFact.field_name == "status",
        ).order_by(ClinicalFact.id.desc())
        status_fact = db.scalars(stmt_status).first()

        complaint = complaint_fact.value if complaint_fact else "General Checkup"
        duration = duration_fact.value if duration_fact else "Recent"
        severity = severity_fact.value if severity_fact else "5/10"
        priority = priority_fact.value if priority_fact else ("Priority" if "chest" in complaint.lower() or "8" in severity else "Normal")
        status = status_fact.value if status_fact else "Ready for review"

        patient_items.append(
            PatientListItem(
                patient_id=p.patient_id,
                name=p.name,
                age=p.age,
                gender=p.gender.capitalize() if p.gender else "Male",
                language=p.preferred_language,
                current_complaint=complaint,
                duration=duration,
                severity=severity,
                status=status,
                priority=priority,
                arrival_time=p.registration_time or "09:15 AM",
                registration_time=p.registration_time or "09:15 AM",
                uhid=p.uhid,
            )
        )

    return patient_items

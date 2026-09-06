"""Doctor Summary Assembly Service for Medisaarthi Pre-Consultation Engine.

Aggregates structured PostgreSQL clinical records (Patient, Interview, ClinicalFacts,
Medications, Allergies, and TimelineEvents) into a validated, deterministic DoctorSummaryData
object without making external LLM calls.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.app.models.patient import Patient
from backend.app.models.interview import Interview
from backend.app.models.interview_message import InterviewMessage
from backend.app.models.clinical_fact import ClinicalFact
from backend.app.models.medication import Medication
from backend.app.models.allergy import Allergy
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.summary_verification import SummaryVerification
from backend.app.models.doctor_edit_audit import DoctorEditAudit

from backend.app.schemas.doctor import (
    PatientSnapshot,
    CurrentComplaintFact,
    CurrentComplaintSection,
    PastMedicalHistoryItem,
    MedicationItem,
    AllergyItem,
    ImportantFindingItem,
    MissingInformationItem,
    InterviewMetadata,
    DoctorSummaryData,
    DoctorNarrativeSummary,
    DoctorEditAuditItem,
    DoctorSummaryEditRequest,
    DoctorSummaryEditResponse,
    DoctorSummaryVerifyResponse,
)
from backend.app.services.rules.question_graph import get_required_topics

logger = logging.getLogger(__name__)


def build_doctor_summary(db: Session, patient_id: str) -> Optional[DoctorSummaryData]:
    """Assemble a structured DoctorSummaryData object strictly from PostgreSQL data."""
    clean_pid = patient_id.strip()

    # 1. Fetch Patient
    stmt_patient = select(Patient).where(Patient.patient_id.ilike(clean_pid))
    patient = db.scalars(stmt_patient).first()
    if not patient:
        logger.warning(f"[build_doctor_summary] Patient '{clean_pid}' not found.")
        return None

    # 2. Build Patient Snapshot
    snapshot = PatientSnapshot(
        patient_id=patient.patient_id,
        name=patient.name,
        age=patient.age,
        gender=patient.gender.capitalize() if patient.gender else None,
        preferred_language=patient.preferred_language,
        uhid=patient.uhid,
        phone=patient.phone,
        registration_time=patient.registration_time,
    )

    # 3. Fetch Latest Interview
    stmt_interview = (
        select(Interview)
        .where(Interview.patient_id == patient.patient_id)
        .order_by(Interview.id.desc())
    )
    interview = db.scalars(stmt_interview).first()

    # 4. Assemble Interview Metadata
    if interview:
        stmt_msg_count = (
            select(func.count(InterviewMessage.id))
            .where(InterviewMessage.interview_id == interview.interview_id)
        )
        msg_count = db.scalar(stmt_msg_count) or 0

        metadata = InterviewMetadata(
            interview_id=interview.interview_id,
            status=interview.status,
            language=interview.language,
            started_at=interview.started_at,
            completed_at=interview.completed_at,
            current_topic=interview.current_topic,
            total_messages=msg_count,
        )
    else:
        metadata = InterviewMetadata(
            interview_id=None,
            status="not_started",
            language=patient.preferred_language,
            started_at=None,
            completed_at=None,
            current_topic=None,
            total_messages=0,
        )

    # 5. Load Clinical Facts
    stmt_facts = select(ClinicalFact).where(
        ClinicalFact.patient_id == patient.patient_id
    ).order_by(ClinicalFact.id.asc())

    clinical_facts_db = db.scalars(stmt_facts).all()
    facts_map: Dict[str, ClinicalFact] = {f.field_name: f for f in clinical_facts_db}

    # 6. Assemble Current Complaint Section
    chief_complaint = facts_map["chief_complaint"].value if "chief_complaint" in facts_map else None
    duration = facts_map["duration"].value if "duration" in facts_map else None
    severity = facts_map["severity"].value if "severity" in facts_map else None
    location = facts_map["location"].value if "location" in facts_map else None
    trigger = facts_map["trigger"].value if "trigger" in facts_map else None
    associated_symptoms = facts_map["associated_symptoms"].value if "associated_symptoms" in facts_map else None

    complaint_facts: List[CurrentComplaintFact] = [
        CurrentComplaintFact(
            field_name=f.field_name,
            value=f.value,
            status=f.status,
            source=f.source,
            confidence=f.confidence,
        )
        for f in clinical_facts_db
        if f.field_name not in ["priority", "status", "condition"]
    ]

    current_complaint_section = CurrentComplaintSection(
        chief_complaint=chief_complaint,
        duration=duration,
        severity=severity,
        location=location,
        trigger=trigger,
        associated_symptoms=associated_symptoms,
        facts=complaint_facts,
    )

    # 7. Identify Missing / Unresolved Information from Question Graph
    required_topics = get_required_topics(chief_complaint, facts_map)
    missing_info: List[MissingInformationItem] = []
    for topic in required_topics:
        if topic not in facts_map:
            importance = "required" if topic in ["chief_complaint", "duration", "severity"] else "standard"
            desc = f"Information regarding {topic.replace('_', ' ')} has not been provided."
            missing_info.append(
                MissingInformationItem(
                    field_name=topic,
                    description=desc,
                    importance=importance,
                )
            )

    # 8. Extract Important Clinical Findings
    important_findings: List[ImportantFindingItem] = []
    for field_name, f in facts_map.items():
        if field_name in ["priority", "status", "condition"]:
            continue
        val_lower = f.value.lower().strip()
        if f.status == "denied" or val_lower in ["absent", "none reported", "no"]:
            continue

        if field_name == "severity":
            important_findings.append(
                ImportantFindingItem(
                    finding="Reported Severity",
                    value=f"{f.value} / 10" if f.value.isdigit() else f.value,
                    category="severity",
                    status=f.status,
                )
            )
        elif field_name == "temperature":
            important_findings.append(
                ImportantFindingItem(
                    finding="Recorded Body Temperature",
                    value=f.value,
                    category="vital",
                    status=f.status,
                )
            )
        elif field_name in ["chills", "cough", "vomiting", "bowel_symptoms", "associated_symptoms", "trigger", "radiation", "movement_effect"]:
            category = "associated_symptom" if "symptom" in field_name else "symptom"
            important_findings.append(
                ImportantFindingItem(
                    finding=field_name.replace("_", " ").title(),
                    value=f.value,
                    category=category,
                    status=f.status,
                )
            )

    # 9. Priority Flags (Explicit deterministic safety/priority records only, no diagnostic inference)
    priority_flags: List[str] = []
    if "priority" in facts_map and facts_map["priority"].value in ["Priority", "Urgent"]:
        priority_flags.append(facts_map["priority"].value)
    elif "safety_flag" in facts_map and facts_map["safety_flag"].value:
        priority_flags.append(facts_map["safety_flag"].value)

    # 10. Retrieve Past Medical History (TimelineEvents)
    stmt_timeline = (
        select(TimelineEvent)
        .where(TimelineEvent.patient_id == patient.patient_id)
        .order_by(TimelineEvent.id.asc())
    )
    timeline_events = db.scalars(stmt_timeline).all()
    past_history: List[PastMedicalHistoryItem] = [
        PastMedicalHistoryItem(
            condition=t.fact,
            date=t.date,
            source=t.source,
            confidence=t.confidence,
        )
        for t in timeline_events
    ]

    # 11. Retrieve Medications
    stmt_meds = (
        select(Medication)
        .where(Medication.patient_id == patient.patient_id)
        .order_by(Medication.id.asc())
    )
    meds_db = db.scalars(stmt_meds).all()
    medications: List[MedicationItem] = [
        MedicationItem(
            name=m.name,
            dosage=m.dosage,
            frequency=m.frequency,
            source=m.source,
        )
        for m in meds_db
    ]

    # 12. Retrieve Allergies
    stmt_allergies = (
        select(Allergy)
        .where(Allergy.patient_id == patient.patient_id)
        .order_by(Allergy.id.asc())
    )
    allergies_db = db.scalars(stmt_allergies).all()
    allergies: List[AllergyItem] = []
    allergy_status = "No allergies recorded"

    if allergies_db:
        has_nkda = any("no known" in a.allergen.lower() or "none" in a.allergen.lower() for a in allergies_db)
        if has_nkda and len(allergies_db) == 1:
            allergy_status = "Patient explicitly reported no known allergies"
        else:
            allergy_status = "Recorded allergies"
            for a in allergies_db:
                if "no known" not in a.allergen.lower():
                    allergies.append(
                        AllergyItem(
                            allergen=a.allergen,
                            reaction=a.reaction,
                            source=a.source,
                        )
                    )

    # 13. Fetch Verification Status
    stmt_ver = select(SummaryVerification).where(SummaryVerification.patient_id == patient.patient_id).order_by(SummaryVerification.id.desc())
    verification = db.scalars(stmt_ver).first()
    verification_status = verification.verification_status if verification else "AI-assisted / unverified"

    # 14. Assemble Final DoctorSummaryData Object
    return DoctorSummaryData(
        patient_snapshot=snapshot,
        current_complaint=current_complaint_section,
        past_medical_history=past_history,
        medications=medications,
        allergies=allergies,
        allergy_status=allergy_status,
        important_findings=important_findings,
        missing_information=missing_info,
        priority_flags=priority_flags,
        interview_metadata=metadata,
        verification_status=verification_status,
    )


def generate_deterministic_narrative(data: DoctorSummaryData) -> DoctorNarrativeSummary:
    """Generate a clean, structured doctor-readable pre-consultation narrative from DoctorSummaryData without an LLM."""
    snap = data.patient_snapshot
    comp = data.current_complaint

    # 1. Patient Snapshot
    age_gender = (
        f"{snap.age}-year-old {snap.gender.lower() if snap.gender else 'patient'}"
        if snap.age
        else f"{snap.gender or 'Patient'}"
    )
    lang_str = f"Preferred Language: {snap.preferred_language.upper() if snap.preferred_language else 'Not specified'}"
    uhid_str = f"UHID: {snap.uhid}" if snap.uhid else "UHID: N/A"
    snapshot_text = f"{snap.name}, {age_gender} ({uhid_str}, {lang_str})"

    # 2. Presenting Complaint
    dur_str = f" for {comp.duration}" if comp.duration else ""
    presenting_complaint = f"{comp.chief_complaint or 'General clinical consultation'}{dur_str}."

    # 3. Interview Summary
    summary_lines = []
    if comp.severity:
        sev_val = f"{comp.severity} / 10" if comp.severity.isdigit() else comp.severity
        summary_lines.append(f"- Severity: {sev_val}")
    if comp.location:
        summary_lines.append(f"- Location: {comp.location}")
    if comp.trigger:
        summary_lines.append(f"- Aggravating / Relieving Factors: {comp.trigger}")
    if comp.associated_symptoms:
        summary_lines.append(f"- Associated Symptoms: {comp.associated_symptoms}")

    # Add other acute complaint facts
    for f in comp.facts:
        if f.field_name not in ["chief_complaint", "duration", "severity", "location", "trigger", "associated_symptoms"]:
            if f.status != "denied" and f.value.lower() not in ["absent", "none", "no"]:
                summary_lines.append(f"- {f.field_name.replace('_', ' ').title()}: {f.value}")
            elif f.status == "denied":
                summary_lines.append(f"- {f.field_name.replace('_', ' ').title()}: Absent / Denied")

    interview_summary = "\n".join(summary_lines) if summary_lines else "- Patient intake dialogue recorded."

    # 4. Relevant Past History
    if data.past_medical_history:
        history_lines = [
            f"- {h.condition}{f' ({h.date})' if h.date else ''}"
            for h in data.past_medical_history
        ]
        relevant_history = "\n".join(history_lines)
    else:
        relevant_history = "- No past medical conditions recorded in EMR."

    # 5. Medications
    if data.medications:
        med_lines = [
            f"- {m.name} {m.dosage}{f' — {m.frequency}' if m.frequency else ''}"
            for m in data.medications
        ]
        medications_text = "\n".join(med_lines)
    else:
        medications_text = "- No active medications recorded."

    # 6. Allergies
    allergy_lines = [f"- Status: {data.allergy_status}"]
    for a in data.allergies:
        react = f" (Reaction: {a.reaction})" if a.reaction else ""
        allergy_lines.append(f"- {a.allergen}{react}")
    allergies_text = "\n".join(allergy_lines)

    # 7. Important Findings
    if data.important_findings:
        findings_lines = [f"- {f.finding}: {f.value}" for f in data.important_findings]
        important_findings = "\n".join(findings_lines)
    else:
        important_findings = "- No acute findings recorded."

    # 8. Missing Information
    if data.missing_information:
        missing_lines = [
            f"- {m.field_name.replace('_', ' ').title()}: Not recorded / unresolved"
            for m in data.missing_information
        ]
        missing_info = "\n".join(missing_lines)
    else:
        missing_info = "- All standard intake topics for this complaint were addressed."

    # 9. Priority Flags
    if data.priority_flags:
        priority_flags_text = "\n".join([f"- {flag}" for flag in data.priority_flags])
    else:
        priority_flags_text = "- None"

    ver_note = (
        "Doctor verified pre-consultation clinical summary."
        if data.verification_status == "Verified"
        else "AI-assisted pre-consultation intake summary. Doctor verification required before clinical decision making."
    )

    return DoctorNarrativeSummary(
        patient_id=snap.patient_id,
        patient_snapshot=snapshot_text,
        presenting_complaint=presenting_complaint,
        interview_summary=interview_summary,
        relevant_history=relevant_history,
        medications=medications_text,
        allergies=allergies_text,
        important_findings=important_findings,
        missing_information=missing_info,
        priority_flags=priority_flags_text,
        verification_note=ver_note,
    )


def get_doctor_narrative_summary(
    db: Session,
    patient_id: str,
    ai_provider: Optional[Any] = None,
) -> Optional[DoctorNarrativeSummary]:
    """Retrieve validated DoctorSummaryData and generate a doctor-readable pre-consultation narrative."""
    from backend.app.services.ai import get_ai_provider

    doctor_summary_data = build_doctor_summary(db, patient_id)
    if not doctor_summary_data:
        return None

    provider = ai_provider or get_ai_provider()
    return provider.generate_narrative_summary(doctor_summary_data)


def edit_doctor_summary(
    db: Session,
    patient_id: str,
    edit_data: DoctorSummaryEditRequest,
    doctor_id: str,
) -> Optional[DoctorSummaryEditResponse]:
    """Apply doctor modifications to structured PostgreSQL records and record an atomic audit trail."""
    clean_pid = patient_id.strip()

    # 1. Fetch Patient
    stmt_patient = select(Patient).where(Patient.patient_id.ilike(clean_pid))
    patient = db.scalars(stmt_patient).first()
    if not patient:
        logger.warning(f"[edit_doctor_summary] Patient '{clean_pid}' not found.")
        return None

    # 2. Fetch Latest Interview (if any)
    stmt_interview = (
        select(Interview)
        .where(Interview.patient_id == patient.patient_id)
        .order_by(Interview.id.desc())
    )
    interview = db.scalars(stmt_interview).first()
    interview_id = interview.interview_id if interview else None

    updated_fields: List[str] = []
    audit_entries_created: List[DoctorEditAuditItem] = []

    try:
        # 3. Update scalar complaint facts
        scalar_fields = [
            "chief_complaint",
            "duration",
            "severity",
            "location",
            "trigger",
            "associated_symptoms",
        ]

        for field in scalar_fields:
            new_val = getattr(edit_data, field)
            if new_val is not None:
                new_val_str = str(new_val).strip()

                stmt_fact = select(ClinicalFact).where(
                    (ClinicalFact.patient_id == patient.patient_id)
                    & (ClinicalFact.field_name == field)
                ).order_by(ClinicalFact.id.desc())
                fact = db.scalars(stmt_fact).first()

                if fact:
                    old_val = fact.value
                    if old_val != new_val_str:
                        fact.value = new_val_str
                        fact.source = "doctor_verified"
                        fact.status = "confirmed"

                        audit_record = DoctorEditAudit(
                            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                            patient_id=patient.patient_id,
                            interview_id=interview_id,
                            field_name=field,
                            original_value=old_val,
                            corrected_value=new_val_str,
                            changed_by=doctor_id,
                            changed_at=datetime.utcnow(),
                        )
                        db.add(audit_record)
                        updated_fields.append(field)
                        audit_entries_created.append(
                            DoctorEditAuditItem(
                                audit_id=audit_record.audit_id,
                                patient_id=audit_record.patient_id,
                                interview_id=audit_record.interview_id,
                                field_name=audit_record.field_name,
                                original_value=audit_record.original_value,
                                corrected_value=audit_record.corrected_value,
                                changed_by=audit_record.changed_by,
                                changed_at=audit_record.changed_at,
                            )
                        )
                else:
                    new_fact = ClinicalFact(
                        interview_id=interview_id,
                        patient_id=patient.patient_id,
                        field_name=field,
                        value=new_val_str,
                        source="doctor_verified",
                        status="confirmed",
                        confidence=1.0,
                    )
                    db.add(new_fact)
                    audit_record = DoctorEditAudit(
                        audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                        patient_id=patient.patient_id,
                        interview_id=interview_id,
                        field_name=field,
                        original_value=None,
                        corrected_value=new_val_str,
                        changed_by=doctor_id,
                        changed_at=datetime.utcnow(),
                    )
                    db.add(audit_record)
                    updated_fields.append(field)
                    audit_entries_created.append(
                        DoctorEditAuditItem(
                            audit_id=audit_record.audit_id,
                            patient_id=audit_record.patient_id,
                            interview_id=audit_record.interview_id,
                            field_name=audit_record.field_name,
                            original_value=audit_record.original_value,
                            corrected_value=audit_record.corrected_value,
                            changed_by=audit_record.changed_by,
                            changed_at=audit_record.changed_at,
                        )
                    )

        # 4. Update medications if provided
        if edit_data.medications is not None:
            stmt_meds = select(Medication).where(Medication.patient_id == patient.patient_id).order_by(Medication.id.asc())
            current_meds = db.scalars(stmt_meds).all()
            old_meds_summary = "; ".join([f"{m.name} {m.dosage} ({m.frequency or ''})".strip() for m in current_meds]) if current_meds else None
            new_meds_summary = "; ".join([f"{m.name} {m.dosage} ({m.frequency or ''})".strip() for m in edit_data.medications]) if edit_data.medications else None

            if old_meds_summary != new_meds_summary:
                for m in current_meds:
                    db.delete(m)
                for m in edit_data.medications:
                    new_med = Medication(
                        patient_id=patient.patient_id,
                        name=m.name.strip(),
                        dosage=m.dosage.strip(),
                        frequency=m.frequency.strip() if m.frequency else None,
                        source="doctor_verified",
                    )
                    db.add(new_med)

                audit_record = DoctorEditAudit(
                    audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                    patient_id=patient.patient_id,
                    interview_id=interview_id,
                    field_name="medications",
                    original_value=old_meds_summary,
                    corrected_value=new_meds_summary,
                    changed_by=doctor_id,
                    changed_at=datetime.utcnow(),
                )
                db.add(audit_record)
                updated_fields.append("medications")
                audit_entries_created.append(
                    DoctorEditAuditItem(
                        audit_id=audit_record.audit_id,
                        patient_id=audit_record.patient_id,
                        interview_id=audit_record.interview_id,
                        field_name=audit_record.field_name,
                        original_value=audit_record.original_value,
                        corrected_value=audit_record.corrected_value,
                        changed_by=audit_record.changed_by,
                        changed_at=audit_record.changed_at,
                    )
                )

        # 5. Update allergies if provided
        if edit_data.allergies is not None:
            stmt_allergies = select(Allergy).where(Allergy.patient_id == patient.patient_id).order_by(Allergy.id.asc())
            current_allergies = db.scalars(stmt_allergies).all()
            old_allergies_summary = "; ".join([f"{a.allergen} ({a.reaction or ''})".strip() for a in current_allergies]) if current_allergies else None
            new_allergies_summary = "; ".join([f"{a.allergen} ({a.reaction or ''})".strip() for a in edit_data.allergies]) if edit_data.allergies else None

            if old_allergies_summary != new_allergies_summary:
                for a in current_allergies:
                    db.delete(a)
                for a in edit_data.allergies:
                    new_allergy = Allergy(
                        patient_id=patient.patient_id,
                        allergen=a.allergen.strip(),
                        reaction=a.reaction.strip() if a.reaction else None,
                        source="doctor_verified",
                    )
                    db.add(new_allergy)

                audit_record = DoctorEditAudit(
                    audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                    patient_id=patient.patient_id,
                    interview_id=interview_id,
                    field_name="allergies",
                    original_value=old_allergies_summary,
                    corrected_value=new_allergies_summary,
                    changed_by=doctor_id,
                    changed_at=datetime.utcnow(),
                )
                db.add(audit_record)
                updated_fields.append("allergies")
                audit_entries_created.append(
                    DoctorEditAuditItem(
                        audit_id=audit_record.audit_id,
                        patient_id=audit_record.patient_id,
                        interview_id=audit_record.interview_id,
                        field_name=audit_record.field_name,
                        original_value=audit_record.original_value,
                        corrected_value=audit_record.corrected_value,
                        changed_by=audit_record.changed_by,
                        changed_at=audit_record.changed_at,
                    )
                )

        # 6. Update past medical history if provided
        if edit_data.past_medical_history is not None:
            stmt_hist = select(TimelineEvent).where(TimelineEvent.patient_id == patient.patient_id).order_by(TimelineEvent.id.asc())
            current_hist = db.scalars(stmt_hist).all()
            old_hist_summary = "; ".join([f"{t.fact} ({t.date or ''})".strip() for t in current_hist]) if current_hist else None
            new_hist_summary = "; ".join([f"{t.condition} ({t.date or ''})".strip() for t in edit_data.past_medical_history]) if edit_data.past_medical_history else None

            if old_hist_summary != new_hist_summary:
                for t in current_hist:
                    db.delete(t)
                for t in edit_data.past_medical_history:
                    new_event = TimelineEvent(
                        patient_id=patient.patient_id,
                        fact=t.condition.strip(),
                        date=t.date.strip() if t.date else None,
                        source="doctor_verified",
                        confidence=1.0,
                    )
                    db.add(new_event)

                audit_record = DoctorEditAudit(
                    audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                    patient_id=patient.patient_id,
                    interview_id=interview_id,
                    field_name="past_medical_history",
                    original_value=old_hist_summary,
                    corrected_value=new_hist_summary,
                    changed_by=doctor_id,
                    changed_at=datetime.utcnow(),
                )
                db.add(audit_record)
                updated_fields.append("past_medical_history")
                audit_entries_created.append(
                    DoctorEditAuditItem(
                        audit_id=audit_record.audit_id,
                        patient_id=audit_record.patient_id,
                        interview_id=audit_record.interview_id,
                        field_name=audit_record.field_name,
                        original_value=audit_record.original_value,
                        corrected_value=audit_record.corrected_value,
                        changed_by=audit_record.changed_by,
                        changed_at=audit_record.changed_at,
                    )
                )

        # 7. Re-verification status handling: on edit, revert status to "AI-assisted / unverified"
        stmt_ver = select(SummaryVerification).where(SummaryVerification.patient_id == patient.patient_id).order_by(SummaryVerification.id.desc())
        verification = db.scalars(stmt_ver).first()

        if not verification:
            verification = SummaryVerification(
                verification_id=f"VER-{uuid.uuid4().hex[:8].upper()}",
                patient_id=patient.patient_id,
                interview_id=interview_id,
                verification_status="AI-assisted / unverified",
                created_at=datetime.utcnow(),
            )
            db.add(verification)
        elif updated_fields:
            verification.verification_status = "AI-assisted / unverified"
            verification.updated_at = datetime.utcnow()

        db.commit()

        return DoctorSummaryEditResponse(
            patient_id=patient.patient_id,
            updated_fields=updated_fields,
            verification_status=verification.verification_status,
            audit_entries=audit_entries_created,
        )

    except Exception as exc:
        db.rollback()
        logger.error(f"[edit_doctor_summary] Transaction failed: {exc}", exc_info=True)
        raise exc


def verify_doctor_summary(
    db: Session,
    patient_id: str,
    doctor_id: str,
) -> Optional[DoctorSummaryVerifyResponse]:
    """Mark the clinical summary for a patient as Doctor Verified."""
    clean_pid = patient_id.strip()

    stmt_patient = select(Patient).where(Patient.patient_id.ilike(clean_pid))
    patient = db.scalars(stmt_patient).first()
    if not patient:
        logger.warning(f"[verify_doctor_summary] Patient '{clean_pid}' not found.")
        return None

    stmt_interview = (
        select(Interview)
        .where(Interview.patient_id == patient.patient_id)
        .order_by(Interview.id.desc())
    )
    interview = db.scalars(stmt_interview).first()
    interview_id = interview.interview_id if interview else None

    try:
        stmt_ver = select(SummaryVerification).where(SummaryVerification.patient_id == patient.patient_id).order_by(SummaryVerification.id.desc())
        verification = db.scalars(stmt_ver).first()

        verified_time = datetime.utcnow()
        if not verification:
            verification = SummaryVerification(
                verification_id=f"VER-{uuid.uuid4().hex[:8].upper()}",
                patient_id=patient.patient_id,
                interview_id=interview_id,
                verification_status="Verified",
                verified_by=doctor_id,
                verified_at=verified_time,
                created_at=verified_time,
            )
            db.add(verification)
        else:
            verification.verification_status = "Verified"
            verification.verified_by = doctor_id
            verification.verified_at = verified_time
            verification.updated_at = verified_time

        db.commit()

        return DoctorSummaryVerifyResponse(
            patient_id=patient.patient_id,
            verification_status="Verified",
            verified_by=doctor_id,
            verified_at=verified_time,
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"[verify_doctor_summary] Failed to verify: {exc}", exc_info=True)
        raise exc


def get_doctor_summary_audit_trail(db: Session, patient_id: str) -> List[DoctorEditAuditItem]:
    """Retrieve complete audit trail of doctor modifications for a patient."""
    clean_pid = patient_id.strip()
    stmt = (
        select(DoctorEditAudit)
        .where(DoctorEditAudit.patient_id.ilike(clean_pid))
        .order_by(DoctorEditAudit.changed_at.desc(), DoctorEditAudit.id.desc())
    )
    audits = db.scalars(stmt).all()
    return [
        DoctorEditAuditItem(
            audit_id=a.audit_id,
            patient_id=a.patient_id,
            interview_id=a.interview_id,
            field_name=a.field_name,
            original_value=a.original_value,
            corrected_value=a.corrected_value,
            changed_by=a.changed_by,
            changed_at=a.changed_at,
        )
        for a in audits
    ]


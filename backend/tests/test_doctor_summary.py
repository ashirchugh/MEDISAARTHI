"""Comprehensive Test Suite for Doctor Clinical Summary Data Assembly (Step 3A).

Verifies that DoctorSummaryData is assembled strictly from PostgreSQL records
(Patient, Interview, ClinicalFacts, Medications, Allergies, TimelineEvents)
without invoking Gemini or fabricating information.
"""
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.patient import Patient
from backend.app.models.interview import Interview
from backend.app.models.interview_message import InterviewMessage
from backend.app.models.clinical_fact import ClinicalFact
from backend.app.models.medication import Medication
from backend.app.models.allergy import Allergy
from backend.app.models.timeline_event import TimelineEvent
from backend.app.services.summary_service import build_doctor_summary
from backend.app.schemas.doctor import DoctorSummaryData


def test_doctor_summary_existing_patient_rajesh(client: TestClient, db_session: Session):
    """Test 1: Doctor summary for existing seeded patient P1001 (Rajesh Kumar)."""
    res = client.get("/doctor/patients/P1001/summary")
    assert res.status_code == 200
    data = res.json()

    # Patient Snapshot
    snapshot = data["patient_snapshot"]
    assert snapshot["patient_id"] == "P1001"
    assert snapshot["name"] == "Rajesh Kumar"
    assert snapshot["age"] == 48
    assert snapshot["gender"] == "Male"
    assert snapshot["preferred_language"] == "hi"
    assert snapshot["uhid"] == "APX-2026-0891"

    # Current Complaint
    complaint = data["current_complaint"]
    assert complaint["chief_complaint"] is not None
    assert "chest" in complaint["chief_complaint"].lower()

    # Past Medical History
    history = data["past_medical_history"]
    assert len(history) >= 2
    conditions_text = " ".join([h["condition"] for h in history])
    assert "Hypertension" in conditions_text
    assert "Diabetes" in conditions_text

    # Medications
    meds = data["medications"]
    assert len(meds) >= 2
    med_names = [m["name"] for m in meds]
    assert "Amlodipine" in med_names
    assert "Metformin" in med_names

    # Allergies
    assert "No known" in data["allergy_status"] or "allergies" in data["allergy_status"]

    # Verification Status
    assert data["verification_status"] == "AI-assisted / unverified"


def test_current_complaint_assembly(client: TestClient, db_session: Session):
    """Test 2: Current complaint section correctly maps structured facts."""
    summary = build_doctor_summary(db_session, "P1001")
    assert summary is not None
    comp = summary.current_complaint
    assert comp.chief_complaint == "Chest pain"
    assert comp.duration == "3 days"
    assert comp.severity == "7/10"
    assert len(comp.facts) >= 3


def test_past_history_retrieval(client: TestClient, db_session: Session):
    """Test 3: Past history correctly retrieved from TimelineEvents."""
    summary = build_doctor_summary(db_session, "P1001")
    assert summary is not None
    assert any("Hypertension" in h.condition for h in summary.past_medical_history)
    assert any("Diabetes" in h.condition for h in summary.past_medical_history)


def test_medications_retrieval(client: TestClient, db_session: Session):
    """Test 4: Medications correctly retrieved without fabrication."""
    summary = build_doctor_summary(db_session, "P1001")
    assert summary is not None
    med_map = {m.name: m for m in summary.medications}
    assert "Amlodipine" in med_map
    assert med_map["Amlodipine"].dosage == "5 mg"
    assert "Metformin" in med_map
    assert med_map["Metformin"].dosage == "500 mg"


def test_allergies_retrieval_and_distinction(client: TestClient, db_session: Session):
    """Test 5: Distinguishes 'No known allergies' from explicit drug allergies."""
    # P1001 has NKDA
    summary_p1001 = build_doctor_summary(db_session, "P1001")
    assert summary_p1001.allergy_status == "Patient explicitly reported no known allergies"

    # P1002 has Penicillin allergy
    summary_p1002 = build_doctor_summary(db_session, "P1002")
    assert summary_p1002.allergy_status == "Recorded allergies"
    assert any(a.allergen == "Penicillin" for a in summary_p1002.allergies)


def test_missing_information_identification(client: TestClient, db_session: Session):
    """Test 6: Missing information correctly calculated from Question Graph."""
    # Create fresh patient with only chief_complaint and duration
    new_patient = Patient(
        patient_id="P_INCOMPLETE",
        name="Test Incomplete",
        age=30,
        gender="male",
        preferred_language="en",
    )
    db_session.add(new_patient)
    db_session.flush()

    interview = Interview(
        interview_id="INT_INC_01",
        patient_id="P_INCOMPLETE",
        status="active",
        language="en",
        current_topic="location",
    )
    db_session.add(interview)
    db_session.flush()

    db_session.add(ClinicalFact(interview_id="INT_INC_01", patient_id="P_INCOMPLETE", field_name="chief_complaint", value="chest_pain", source="current_interview", confidence=0.95))
    db_session.add(ClinicalFact(interview_id="INT_INC_01", patient_id="P_INCOMPLETE", field_name="duration", value="2 days", source="current_interview", confidence=0.95))
    db_session.commit()

    summary = build_doctor_summary(db_session, "P_INCOMPLETE")
    assert summary is not None
    missing_fields = [m.field_name for m in summary.missing_information]

    # For chest_pain: location, severity, trigger, associated_symptoms should be missing
    assert "location" in missing_fields
    assert "severity" in missing_fields
    assert "trigger" in missing_fields
    assert "associated_symptoms" in missing_fields
    assert "chief_complaint" not in missing_fields
    assert "duration" not in missing_fields


def test_denied_facts_not_marked_missing(client: TestClient, db_session: Session):
    """Test 7: Explicitly denied facts (e.g. cough=Absent) are resolved and NOT missing."""
    patient = Patient(
        patient_id="P_DENIED_TEST",
        name="Test Denied",
        age=35,
        gender="female",
        preferred_language="hi",
    )
    db_session.add(patient)
    db_session.flush()

    interview = Interview(
        interview_id="INT_DENIED_01",
        patient_id="P_DENIED_TEST",
        status="active",
        language="hi",
        current_topic="temperature",
    )
    db_session.add(interview)
    db_session.flush()

    db_session.add(ClinicalFact(interview_id="INT_DENIED_01", patient_id="P_DENIED_TEST", field_name="chief_complaint", value="fever", status="confirmed"))
    db_session.add(ClinicalFact(interview_id="INT_DENIED_01", patient_id="P_DENIED_TEST", field_name="duration", value="2 days", status="confirmed"))
    db_session.add(ClinicalFact(interview_id="INT_DENIED_01", patient_id="P_DENIED_TEST", field_name="cough", value="Absent", status="denied"))
    db_session.commit()

    summary = build_doctor_summary(db_session, "P_DENIED_TEST")
    assert summary is not None
    missing_fields = [m.field_name for m in summary.missing_information]

    # Cough is denied -> must NOT be in missing information
    assert "cough" not in missing_fields
    # Temperature and chills are not yet asked -> MUST be missing
    assert "temperature" in missing_fields
    assert "chills" in missing_fields


def test_patient_with_no_interview(client: TestClient, db_session: Session):
    """Test 8: Patient with no interview returns valid metadata with status='not_started'."""
    patient = Patient(
        patient_id="P_NO_INT",
        name="No Interview Patient",
        age=40,
        gender="other",
        preferred_language="en",
    )
    db_session.add(patient)
    db_session.commit()

    res = client.get("/doctor/patients/P_NO_INT/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["interview_metadata"]["status"] == "not_started"
    assert data["interview_metadata"]["interview_id"] is None
    assert data["interview_metadata"]["total_messages"] == 0
    assert data["current_complaint"]["chief_complaint"] is None


def test_patient_not_found_returns_404(client: TestClient):
    """Test 9: Requesting summary for non-existent patient ID returns 404."""
    res = client.get("/doctor/patients/P_NON_EXISTENT_9999/summary")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_completed_interview_metadata(client: TestClient, db_session: Session):
    """Test 10: Completed interview records completed_at and status='completed'."""
    patient = Patient(
        patient_id="P_COMPLETED",
        name="Completed Patient",
        age=50,
        gender="male",
        preferred_language="hi",
    )
    db_session.add(patient)
    db_session.flush()

    interview = Interview(
        interview_id="INT_COMP_01",
        patient_id="P_COMPLETED",
        status="completed",
        language="hi",
        current_topic="completion",
        started_at=datetime(2026, 9, 6, 9, 0, 0),
        completed_at=datetime(2026, 9, 6, 9, 15, 0),
    )
    db_session.add(interview)
    db_session.commit()

    summary = build_doctor_summary(db_session, "P_COMPLETED")
    assert summary is not None
    assert summary.interview_metadata.status == "completed"
    assert summary.interview_metadata.completed_at is not None


def test_active_incomplete_interview_metadata(client: TestClient, db_session: Session):
    """Test 11: Active interview displays ongoing status and missing fields."""
    summary = build_doctor_summary(db_session, "P1001")
    assert summary is not None
    assert summary.interview_metadata.status == "active"
    assert summary.interview_metadata.interview_id == "INT001"


def test_no_fabricated_information(client: TestClient, db_session: Session):
    """Test 12: Ensure that if a patient has no allergies or history, none are fabricated."""
    patient = Patient(
        patient_id="P_BARE_BONES",
        name="Bare Patient",
        age=22,
        gender="female",
        preferred_language="hi",
    )
    db_session.add(patient)
    db_session.commit()

    summary = build_doctor_summary(db_session, "P_BARE_BONES")
    assert summary is not None
    assert summary.medications == []
    assert summary.allergies == []
    assert summary.past_medical_history == []
    assert summary.allergy_status == "No allergies recorded"


def test_existing_doctor_patient_list_api(client: TestClient):
    """Test 13: Existing /doctor/patients endpoint continues functioning seamlessly."""
    res = client.get("/doctor/patients")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) >= 5
    p1001 = next(p for p in patients if p["patient_id"] == "P1001")
    assert p1001["name"] == "Rajesh Kumar"

"""Tests for Step 3B: Gemini-Powered Doctor Summary Narrative with Strict Grounding & Deterministic Fallback."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.doctor import (
    PatientSnapshot,
    CurrentComplaintSection,
    CurrentComplaintFact,
    PastMedicalHistoryItem,
    MedicationItem,
    AllergyItem,
    ImportantFindingItem,
    MissingInformationItem,
    InterviewMetadata,
    DoctorSummaryData,
    DoctorNarrativeSummary,
)
from backend.app.services.summary_service import (
    generate_deterministic_narrative,
    get_doctor_narrative_summary,
    build_doctor_summary,
)
from backend.app.services.ai.gemini_provider import GeminiAIProvider
from backend.app.services.ai.mock_provider import MockAIProvider
from backend.app.services.rules.fact_extractor import extract_facts_from_message


@pytest.fixture
def sample_doctor_summary_data():
    """Build a standard DoctorSummaryData fixture for unit testing."""
    return DoctorSummaryData(
        patient_snapshot=PatientSnapshot(
            patient_id="P1001",
            name="Rajesh Kumar",
            age=48,
            gender="Male",
            preferred_language="hi",
            uhid="UHID-2024-001",
            phone="+91-9876543210",
            registration_time="09:15 AM",
        ),
        current_complaint=CurrentComplaintSection(
            chief_complaint="chest_pain",
            duration="3 days",
            severity="8",
            location="left",
            trigger="walking",
            associated_symptoms="sweating",
            facts=[
                CurrentComplaintFact(field_name="chief_complaint", value="chest_pain", status="confirmed"),
                CurrentComplaintFact(field_name="duration", value="3 days", status="confirmed"),
                CurrentComplaintFact(field_name="severity", value="8", status="confirmed"),
                CurrentComplaintFact(field_name="location", value="left", status="confirmed"),
                CurrentComplaintFact(field_name="trigger", value="walking", status="confirmed"),
                CurrentComplaintFact(field_name="associated_symptoms", value="sweating", status="confirmed"),
                CurrentComplaintFact(field_name="cough", value="Absent", status="denied"),
            ],
        ),
        past_medical_history=[
            PastMedicalHistoryItem(condition="Hypertension", date="March 2021", source="previous_consultation"),
            PastMedicalHistoryItem(condition="Type 2 Diabetes", date="July 2023", source="previous_consultation"),
        ],
        medications=[
            MedicationItem(name="Amlodipine", dosage="5 mg", frequency="once daily"),
            MedicationItem(name="Metformin", dosage="500 mg", frequency="twice daily"),
        ],
        allergies=[
            AllergyItem(allergen="Penicillin", reaction="Skin Rash"),
        ],
        allergy_status="Recorded allergies",
        important_findings=[
            ImportantFindingItem(finding="Reported Severity", value="8 / 10", category="severity"),
            ImportantFindingItem(finding="Associated Symptoms", value="sweating", category="associated_symptom"),
        ],
        missing_information=[
            MissingInformationItem(field_name="radiation", description="Information regarding radiation has not been provided."),
        ],
        priority_flags=["Priority"],
        interview_metadata=InterviewMetadata(
            interview_id="int-1001",
            status="in_progress",
            language="hi",
            total_messages=4,
        ),
        verification_status="AI-assisted / unverified",
    )


def test_test_a_deterministic_narrative_from_doctor_summary(sample_doctor_summary_data):
    """Test A: Valid DoctorSummaryData -> valid narrative structure and content."""
    narrative = generate_deterministic_narrative(sample_doctor_summary_data)
    assert isinstance(narrative, DoctorNarrativeSummary)
    assert narrative.patient_id == "P1001"
    assert "Rajesh Kumar" in narrative.patient_snapshot
    assert "48-year-old male" in narrative.patient_snapshot
    assert "chest_pain" in narrative.presenting_complaint
    assert "3 days" in narrative.presenting_complaint
    assert "8 / 10" in narrative.interview_summary
    assert "walking" in narrative.interview_summary
    assert "sweating" in narrative.interview_summary
    assert "Hypertension" in narrative.relevant_history
    assert "March 2021" in narrative.relevant_history
    assert "Amlodipine 5 mg" in narrative.medications
    assert "Penicillin" in narrative.allergies
    assert "Priority" in narrative.priority_flags
    assert "verification required" in narrative.verification_note.lower()


def test_test_b_mock_provider_returns_narrative(sample_doctor_summary_data):
    """Test B: Mock provider generates narrative containing only supplied facts."""
    provider = MockAIProvider()
    narrative = provider.generate_narrative_summary(sample_doctor_summary_data)
    assert isinstance(narrative, DoctorNarrativeSummary)
    assert "Rajesh Kumar" in narrative.patient_snapshot
    assert "Amlodipine 5 mg — once daily" in narrative.medications


def test_test_f_medication_integrity_preserved(sample_doctor_summary_data):
    """Test F: Medication name/dosage/frequency remain unchanged."""
    narrative = generate_deterministic_narrative(sample_doctor_summary_data)
    assert "Amlodipine 5 mg — once daily" in narrative.medications
    assert "Metformin 500 mg — twice daily" in narrative.medications


def test_test_g_dates_remain_unchanged(sample_doctor_summary_data):
    """Test G: Dates remain unchanged in relevant history."""
    narrative = generate_deterministic_narrative(sample_doctor_summary_data)
    assert "March 2021" in narrative.relevant_history
    assert "July 2023" in narrative.relevant_history


def test_test_h_explicitly_denied_facts_preserved(sample_doctor_summary_data):
    """Test H: Explicitly denied facts remain denied."""
    narrative = generate_deterministic_narrative(sample_doctor_summary_data)
    assert "Cough: Absent / Denied" in narrative.interview_summary


def test_test_i_missing_information_preserved(sample_doctor_summary_data):
    """Test I: Missing information remains recorded as not recorded / unresolved."""
    narrative = generate_deterministic_narrative(sample_doctor_summary_data)
    assert "Radiation: Not recorded / unresolved" in narrative.missing_information


def test_test_j_priority_flags_exact(sample_doctor_summary_data):
    """Test J: Priority flags remain exactly those supplied by DoctorSummaryData."""
    narrative = generate_deterministic_narrative(sample_doctor_summary_data)
    assert narrative.priority_flags == "- Priority"

    # Empty priority flags case
    sample_doctor_summary_data.priority_flags = []
    narrative_no_flags = generate_deterministic_narrative(sample_doctor_summary_data)
    assert narrative_no_flags.priority_flags == "- None"


def test_test_k_gemini_malformed_response_fallback(sample_doctor_summary_data):
    """Test K: Gemini malformed response gracefully falls back to deterministic narrative."""
    provider = GeminiAIProvider(api_key="fake-key-for-test")
    
    # Mock client generate_content to return bad text
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = "INVALID_JSON_CONTENT{{"
    mock_client.models.generate_content.return_value = mock_response
    provider._client = mock_client

    narrative = provider.generate_narrative_summary(sample_doctor_summary_data)
    assert isinstance(narrative, DoctorNarrativeSummary)
    assert narrative.patient_id == "P1001"
    assert "Rajesh Kumar" in narrative.patient_snapshot
    assert "Amlodipine 5 mg" in narrative.medications


def test_test_l_gemini_unavailable_fallback(sample_doctor_summary_data):
    """Test L: Gemini unavailable / exception gracefully falls back to deterministic narrative."""
    provider = GeminiAIProvider(api_key=None)
    provider._client = None

    narrative = provider.generate_narrative_summary(sample_doctor_summary_data)
    assert isinstance(narrative, DoctorNarrativeSummary)
    assert narrative.patient_id == "P1001"
    assert "Rajesh Kumar" in narrative.patient_snapshot


def test_test_m_step_3a_summary_endpoint_unchanged(client):
    """Test M: Existing Step 3A GET /doctor/patients/{patient_id}/summary endpoint remains unchanged."""
    response = client.get("/doctor/patients/P1001/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_snapshot"]["patient_id"] == "P1001"
    assert "chest pain" in data["current_complaint"]["chief_complaint"].lower()
    assert "past_medical_history" in data
    assert "medications" in data
    assert "allergies" in data
    assert "important_findings" in data
    assert "missing_information" in data


def test_test_n_narrative_patient_not_found(client):
    """Test N: Patient not found returns 404 on narrative endpoint."""
    response = client.get("/doctor/patients/NON_EXISTENT_ID/summary/narrative")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_test_o_p1001_narrative_endpoint_end_to_end(client):
    """Test O: P1001 narrative endpoint works end-to-end and returns valid DoctorNarrativeSummary."""
    response = client.get("/doctor/patients/P1001/summary/narrative")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "P1001"
    assert "Rajesh Kumar" in data["patient_snapshot"]
    assert "Chest pain" in data["presenting_complaint"] or "chest pain" in data["presenting_complaint"].lower()
    assert "Amlodipine" in data["medications"]
    assert "AI-assisted" in data["verification_note"]


def test_test_p_location_mapping_regression():
    """Test P: Location/severity/trigger mapping regression test.
    Ensure severity or trigger statements do not accidentally populate the location field.
    """
    # 1. Message containing scale and walking trigger
    msg1 = "Scale par lagbhag 8 hai, chalne par badh jata hai."
    facts1 = extract_facts_from_message(msg1, current_topic="location")
    # Location should NOT be populated with the full sentence
    assert "location" not in facts1 or facts1["location"][0] in ["left", "right", "center", "chest", "chhati"]
    assert "severity" in facts1
    assert facts1["severity"][0] == "8"
    assert "trigger" in facts1
    assert "walking" in facts1["trigger"][0].lower()

    # 2. Message answering location properly
    msg2 = "Dard chhati ke left side mein hai."
    facts2 = extract_facts_from_message(msg2, current_topic="location")
    assert "location" in facts2
    assert "left" in facts2["location"][0].lower()

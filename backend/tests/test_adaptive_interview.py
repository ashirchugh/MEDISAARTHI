"""Tests for Adaptive Interviewing and Conditional Question Graph Branching.

Verifies that follow-up questions are dynamically determined based on clinical facts
already confirmed or denied by the patient.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.services.rules.question_graph import get_required_topics
from backend.app.models.clinical_fact import ClinicalFact


def test_scenario_a_fever_with_cough_triggers_respiratory_branch():
    """Scenario A: Patient has fever + cough -> verify respiratory follow-up occurs."""
    facts = {
        "chief_complaint": ClinicalFact(field_name="chief_complaint", value="fever", status="confirmed"),
        "duration": ClinicalFact(field_name="duration", value="2 days", status="confirmed"),
        "cough": ClinicalFact(field_name="cough", value="Dry cough and sore throat", status="confirmed"),
    }
    topics = get_required_topics("fever", facts)

    # Must contain respiratory follow-up
    assert "respiratory_symptoms" in topics
    # Must NOT contain irrelevant GI follow-ups
    assert "vomiting" not in topics
    assert "bowel_symptoms" not in topics


def test_scenario_b_fever_no_cough_with_gi_triggers_gi_branch():
    """Scenario B: Patient has fever + no cough + vomiting/abdominal symptoms -> verify GI follow-up occurs."""
    facts = {
        "chief_complaint": ClinicalFact(field_name="chief_complaint", value="fever", status="confirmed"),
        "duration": ClinicalFact(field_name="duration", value="2 days", status="confirmed"),
        "cough": ClinicalFact(field_name="cough", value="Absent", status="denied"),
        "vomiting": ClinicalFact(field_name="vomiting", value="Vomiting present", status="confirmed"),
        "associated_symptoms": ClinicalFact(field_name="associated_symptoms", value="Stomach pain", status="confirmed"),
    }
    topics = get_required_topics("fever", facts)

    # Must contain GI follow-ups
    assert "bowel_symptoms" in topics
    # Must NOT contain respiratory follow-up
    assert "respiratory_symptoms" not in topics


def test_scenario_c_fever_only_duration_asks_missing_fever_questions():
    """Scenario C: Patient only reports fever and duration -> verify standard missing fever questions."""
    facts = {
        "chief_complaint": ClinicalFact(field_name="chief_complaint", value="fever", status="confirmed"),
        "duration": ClinicalFact(field_name="duration", value="2 days", status="confirmed"),
    }
    topics = get_required_topics("fever", facts)

    # Core fever questions must be present
    assert "temperature" in topics
    assert "chills" in topics
    assert "cough" in topics
    assert "associated_symptoms" in topics
    # Conditional branches not triggered
    assert "respiratory_symptoms" not in topics
    assert "bowel_symptoms" not in topics


def test_scenario_d_denied_cough_not_asked_again():
    """Scenario D: Patient explicitly denies cough -> verify cough is not treated as missing."""
    facts = {
        "chief_complaint": ClinicalFact(field_name="chief_complaint", value="fever", status="confirmed"),
        "duration": ClinicalFact(field_name="duration", value="2 days", status="confirmed"),
        "cough": ClinicalFact(field_name="cough", value="Absent", status="denied"),
        "temperature": ClinicalFact(field_name="temperature", value="101.5°F", status="confirmed"),
    }
    topics = get_required_topics("fever", facts)

    # Find next missing topic
    missing = [t for t in topics if t not in facts]
    assert "cough" not in missing
    assert "chills" in missing
    assert "respiratory_symptoms" not in topics


def test_scenario_e_multi_fact_skips_known_questions(client: TestClient):
    """Scenario E: Patient provides multiple symptoms in one response -> verify system skips known topics."""
    # Start interview
    res_start = client.post("/interview/start", json={"patient_id": "P1001", "language": "en"})
    int_id = res_start.json()["interview_id"]

    # Provide comprehensive multi-fact statement
    full_msg = "I have chest pain in the center of my chest for 3 days, severity 8/10, worsened by walking, with sweating."
    res_turn = client.post("/interview/respond", json={"interview_id": int_id, "message": full_msg})
    data = res_turn.json()

    extracted = {f["field_name"]: f["value"] for f in data["extracted_facts"]}
    assert extracted.get("chief_complaint") == "chest_pain"
    assert "3" in extracted.get("duration", "")
    assert "8" in extracted.get("severity", "")

    # Because all topics were answered in 1 turn, interview completes or asks remaining missing topic
    assert data["current_topic"] in ["completion", "associated_symptoms", "trigger"]

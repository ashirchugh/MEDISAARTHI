"""Tests for Step 3C: Doctor Verification & Editing Workflow with Immutable Audit Trail."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.schemas.doctor import (
    DoctorSummaryEditRequest,
    MedicationItem,
    AllergyItem,
    PastMedicalHistoryItem,
)
from backend.app.services.summary_service import edit_doctor_summary, verify_doctor_summary, get_doctor_summary_audit_trail


def test_test_a_get_current_summary(client: TestClient):
    """Test A: Patient summary can be retrieved before any edit."""
    res = client.get("/doctor/patients/P1001/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["patient_snapshot"]["patient_id"] == "P1001"
    assert "verification_status" in data


def test_test_b_doctor_update_chief_complaint(client: TestClient):
    """Test B: Doctor can update chief complaint with audit record created."""
    headers = {"X-Doctor-ID": "dr_smith"}
    payload = {"chief_complaint": "Severe Atypical Chest Pain"}
    res = client.patch("/doctor/patients/P1001/summary", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == "P1001"
    assert "chief_complaint" in data["updated_fields"]
    assert any(a["field_name"] == "chief_complaint" and a["corrected_value"] == "Severe Atypical Chest Pain" for a in data["audit_entries"])

    # Confirm updated value in GET summary
    get_res = client.get("/doctor/patients/P1001/summary")
    assert get_res.json()["current_complaint"]["chief_complaint"] == "Severe Atypical Chest Pain"


def test_test_c_doctor_update_severity(client: TestClient):
    """Test C: Doctor can update severity."""
    headers = {"X-Doctor-ID": "dr_smith"}
    payload = {"severity": "6"}
    res = client.patch("/doctor/patients/P1001/summary", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "severity" in data["updated_fields"]

    # Verify structured summary reflects 6
    get_res = client.get("/doctor/patients/P1001/summary")
    assert get_res.json()["current_complaint"]["severity"] == "6"


def test_test_d_doctor_update_location(client: TestClient):
    """Test D: Doctor can update location."""
    headers = {"X-Doctor-ID": "dr_smith"}
    payload = {"location": "Substernal Left Precordial"}
    res = client.patch("/doctor/patients/P1001/summary", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "location" in data["updated_fields"]


def test_test_e_doctor_update_associated_symptoms(client: TestClient):
    """Test E: Doctor can update associated symptoms."""
    headers = {"X-Doctor-ID": "dr_smith"}
    payload = {"associated_symptoms": "Sweating and mild lightheadedness"}
    res = client.patch("/doctor/patients/P1001/summary", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "associated_symptoms" in data["updated_fields"]


def test_test_f_doctor_update_medications(client: TestClient):
    """Test F: Doctor can update active medications list safely."""
    headers = {"X-Doctor-ID": "dr_smith"}
    new_meds = [
        {"name": "Amlodipine", "dosage": "10 mg", "frequency": "once daily", "source": "doctor_verified"},
        {"name": "Atorvastatin", "dosage": "20 mg", "frequency": "once daily at night", "source": "doctor_verified"},
    ]
    res = client.patch("/doctor/patients/P1001/summary", json={"medications": new_meds}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "medications" in data["updated_fields"]

    # Check GET summary reflects new meds
    get_res = client.get("/doctor/patients/P1001/summary")
    med_names = [m["name"] for m in get_res.json()["medications"]]
    assert "Atorvastatin" in med_names
    assert any(m["name"] == "Amlodipine" and m["dosage"] == "10 mg" for m in get_res.json()["medications"])


def test_test_g_doctor_update_allergies(client: TestClient):
    """Test G: Doctor can update allergy records."""
    headers = {"X-Doctor-ID": "dr_smith"}
    new_allergies = [
        {"allergen": "Sulfa drugs", "reaction": "Skin Hives", "source": "doctor_verified"}
    ]
    res = client.patch("/doctor/patients/P1001/summary", json={"allergies": new_allergies}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "allergies" in data["updated_fields"]

    # Verify structured summary reflects updated allergies
    get_res = client.get("/doctor/patients/P1001/summary")
    allergens = [a["allergen"] for a in get_res.json()["allergies"]]
    assert "Sulfa drugs" in allergens


def test_test_h_doctor_update_past_medical_history(client: TestClient):
    """Test H: Doctor can update past medical history."""
    headers = {"X-Doctor-ID": "dr_smith"}
    new_history = [
        {"condition": "Hypertension", "date": "March 2021", "source": "doctor_verified", "confidence": 1.0},
        {"condition": "Dyslipidemia", "date": "January 2024", "source": "doctor_verified", "confidence": 1.0},
    ]
    res = client.patch("/doctor/patients/P1001/summary", json={"past_medical_history": new_history}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "past_medical_history" in data["updated_fields"]


def test_test_i_j_k_l_audit_trail_integrity(client: TestClient):
    """Tests I, J, K, L: Audit history is created only on changes, recoverable, and tracks multiple edits."""
    headers = {"X-Doctor-ID": "dr_alice"}

    # Edit 1: change trigger
    res1 = client.patch("/doctor/patients/P1002/summary", json={"trigger": "Exertion after heavy meals"}, headers=headers)
    assert res1.status_code == 200
    assert "trigger" in res1.json()["updated_fields"]

    # Edit 2: sending the same value again should NOT generate an audit entry
    res2 = client.patch("/doctor/patients/P1002/summary", json={"trigger": "Exertion after heavy meals"}, headers=headers)
    assert res2.status_code == 200
    assert "trigger" not in res2.json()["updated_fields"]
    assert len(res2.json()["audit_entries"]) == 0

    # Retrieve full audit trail via GET /audit
    audit_res = client.get("/doctor/patients/P1002/summary/audit")
    assert audit_res.status_code == 200
    audits = audit_res.json()
    assert len(audits) >= 1
    assert any(a["field_name"] == "trigger" and a["changed_by"] == "dr_alice" for a in audits)


def test_test_m_invalid_field_rejected(client: TestClient):
    """Test M: Extra / invalid fields in patch request are rejected with 422."""
    headers = {"X-Doctor-ID": "dr_smith"}
    payload = {"invalid_field_name": "arbitrary value"}
    res = client.patch("/doctor/patients/P1001/summary", json=payload, headers=headers)
    assert res.status_code == 422


def test_test_n_protected_fields_immutable(client: TestClient):
    """Test N: Protected fields like patient_id, interview_id cannot be edited via request."""
    headers = {"X-Doctor-ID": "dr_smith"}
    payload = {"patient_id": "P9999"}
    res = client.patch("/doctor/patients/P1001/summary", json=payload, headers=headers)
    assert res.status_code == 422


def test_test_o_missing_patient_returns_404(client: TestClient):
    """Test O: Editing or verifying non-existent patient returns 404."""
    headers = {"X-Doctor-ID": "dr_smith"}
    res = client.patch("/doctor/patients/NON_EXISTENT_PID/summary", json={"severity": "5"}, headers=headers)
    assert res.status_code == 404

    v_res = client.post("/doctor/patients/NON_EXISTENT_PID/summary/verify", headers=headers)
    assert v_res.status_code == 404


def test_test_p_missing_doctor_id_header(client: TestClient):
    """Test P: Missing X-Doctor-ID header returns 400 Bad Request."""
    res = client.patch("/doctor/patients/P1001/summary", json={"severity": "5"})
    assert res.status_code == 400
    assert "X-Doctor-ID" in res.json()["detail"]

    v_res = client.post("/doctor/patients/P1001/summary/verify")
    assert v_res.status_code == 400


def test_test_q_r_s_doctor_verify_flow(client: TestClient):
    """Tests Q, R, S: Doctor can verify summary; status becomes 'Verified' with doctor ID and timestamp."""
    headers = {"X-Doctor-ID": "dr_johnson"}
    res = client.post("/doctor/patients/P1003/summary/verify", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == "P1003"
    assert data["verification_status"] == "Verified"
    assert data["verified_by"] == "dr_johnson"
    assert data["verified_at"] is not None

    # Check GET /summary returns "Verified"
    get_res = client.get("/doctor/patients/P1003/summary")
    assert get_res.json()["verification_status"] == "Verified"


def test_test_t_u_edit_verified_resets_status(client: TestClient):
    """Tests T, U: Editing a verified summary resets status back to 'AI-assisted / unverified' requiring re-verification."""
    headers = {"X-Doctor-ID": "dr_johnson"}

    # 1. Verify
    client.post("/doctor/patients/P1004/summary/verify", headers=headers)
    assert client.get("/doctor/patients/P1004/summary").json()["verification_status"] == "Verified"

    # 2. Modify a field
    edit_res = client.patch("/doctor/patients/P1004/summary", json={"severity": "4"}, headers=headers)
    assert edit_res.status_code == 200
    assert edit_res.json()["verification_status"] == "AI-assisted / unverified"

    # 3. GET /summary confirms unverified
    get_res = client.get("/doctor/patients/P1004/summary")
    assert get_res.json()["verification_status"] == "AI-assisted / unverified"

    # 4. Doctor verifies again
    re_ver = client.post("/doctor/patients/P1004/summary/verify", headers=headers)
    assert re_ver.json()["verification_status"] == "Verified"


def test_test_v_gemini_not_called_during_patch(client: TestClient):
    """Test V: Gemini AI Provider is NOT called during PATCH operations."""
    headers = {"X-Doctor-ID": "dr_smith"}
    with patch("backend.app.services.ai.gemini_provider.GeminiAIProvider.extract_facts") as mock_extract, \
         patch("backend.app.services.ai.gemini_provider.GeminiAIProvider.generate_narrative_summary") as mock_narrative:
        res = client.patch("/doctor/patients/P1001/summary", json={"duration": "5 days"}, headers=headers)
        assert res.status_code == 200
        mock_extract.assert_not_called()
        mock_narrative.assert_not_called()


def test_test_w_x_narrative_uses_corrected_values(client: TestClient):
    """Tests W, X: Narrative regenerated after edit reflects the corrected structured values."""
    headers = {"X-Doctor-ID": "dr_smith"}

    # Edit location
    client.patch("/doctor/patients/P1001/summary", json={"location": "Left sternal border"}, headers=headers)

    # Fetch narrative
    res = client.get("/doctor/patients/P1001/summary/narrative")
    assert res.status_code == 200
    data = res.json()
    assert "Left sternal border" in data["interview_summary"] or "Left sternal" in data["interview_summary"]


def test_test_z_transaction_rollback_on_failure(db_session):
    """Test Z: If audit persistence fails, all modifications are safely rolled back."""
    from backend.app.services.summary_service import edit_doctor_summary

    with patch.object(db_session, "add", side_effect=RuntimeError("Database Write Failure")):
        with pytest.raises(RuntimeError):
            edit_doctor_summary(
                db=db_session,
                patient_id="P1001",
                edit_data=DoctorSummaryEditRequest(severity="1"),
                doctor_id="dr_error_tester",
            )

    # Confirm original value was preserved and not corrupted
    from backend.app.models.clinical_fact import ClinicalFact
    fact = db_session.query(ClinicalFact).filter(ClinicalFact.patient_id == "P1001", ClinicalFact.field_name == "severity").first()
    if fact:
        assert fact.value != "1"

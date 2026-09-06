import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test /health endpoint returns active database connection status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_get_patient_success(client: TestClient):
    """Test retrieving existing patient P1001."""
    response = client.get("/patients/P1001")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "P1001"
    assert data["name"] == "Rajesh Kumar"
    assert data["age"] == 48
    assert data["gender"] == "male"
    assert data["language"] == "hi"


def test_get_patient_not_found(client: TestClient):
    """Test retrieving non-existent patient returns 404."""
    response = client.get("/patients/P9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_patient_history(client: TestClient):
    """Test retrieving structured clinical history for P1001."""
    response = client.get("/patients/P1001/history")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "P1001"

    # Verify medications
    med_names = [m["name"] for m in data["medications"]]
    assert "Amlodipine" in med_names
    assert "Metformin" in med_names

    # Verify allergies
    assert len(data["allergies"]) > 0

    # Verify timeline
    assert len(data["timeline"]) >= 3


def test_start_interview(client: TestClient):
    """Test starting a pre-consultation interview for a patient."""
    payload = {
        "patient_id": "P1001",
        "language": "hi",
    }
    response = client.post("/interview/start", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == "P1001"
    assert data["status"] == "active"
    assert "interview_id" in data
    assert data["initial_question"] is not None
    assert "नमस्ते" in data["initial_question"]["text"]


def test_start_interview_english(client: TestClient):
    """Test starting an interview in English."""
    payload = {
        "patient_id": "P1003",
        "language": "en",
    }
    response = client.post("/interview/start", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == "P1003"
    assert "Hello" in data["initial_question"]["text"]


def test_start_interview_invalid_patient(client: TestClient):
    """Test starting interview for non-existent patient returns 404."""
    payload = {
        "patient_id": "P9999",
        "language": "hi",
    }
    response = client.post("/interview/start", json=payload)
    assert response.status_code == 404


def test_get_doctor_patients(client: TestClient):
    """Test retrieving doctor queue patient list."""
    response = client.get("/doctor/patients")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

    # Check P1001 details in list
    p1001 = next((p for p in data if p["patient_id"] == "P1001"), None)
    assert p1001 is not None
    assert p1001["name"] == "Rajesh Kumar"
    assert p1001["current_complaint"] == "Chest pain"
    assert p1001["priority"] == "Priority"

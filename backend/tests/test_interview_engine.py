import pytest
from fastapi.testclient import TestClient


def test_start_and_single_step_interview(client: TestClient):
    """Test starting an interview and responding with single fact 'I have chest pain'."""
    # 1. Start interview
    start_res = client.post("/interview/start", json={"patient_id": "P1001", "language": "en"})
    assert start_res.status_code == 201
    int_id = start_res.json()["interview_id"]

    # 2. Respond with complaint
    res = client.post("/interview/respond", json={"interview_id": int_id, "message": "I have chest pain"})
    assert res.status_code == 200
    data = res.json()
    assert data["interview_id"] == int_id
    assert data["status"] == "active"
    assert data["current_topic"] == "duration"
    assert data["interview_completed"] is False
    assert any(f["field_name"] == "chief_complaint" and f["value"] == "chest_pain" for f in data["extracted_facts"])
    assert "How long" in data["next_question"]["text"]

    # 3. Respond with duration
    res_dur = client.post("/interview/respond", json={"interview_id": int_id, "message": "for 3 days"})
    assert res_dur.status_code == 200
    data_dur = res_dur.json()
    assert any(f["field_name"] == "duration" and f["value"] == "3 days" for f in data_dur["extracted_facts"])
    # Next topic should be location (not duration again)
    assert data_dur["current_topic"] == "location"
    assert "Where exactly" in data_dur["next_question"]["text"]


def test_multi_fact_extraction_english(client: TestClient):
    """Test multi-fact extraction in English: 'I have chest pain for 3 days'."""
    start_res = client.post("/interview/start", json={"patient_id": "P1001", "language": "en"})
    assert start_res.status_code == 201
    int_id = start_res.json()["interview_id"]

    res = client.post(
        "/interview/respond",
        json={"interview_id": int_id, "message": "I have chest pain for 3 days"}
    )
    assert res.status_code == 200
    data = res.json()
    extracted = {f["field_name"]: f["value"] for f in data["extracted_facts"]}
    assert extracted.get("chief_complaint") == "chest_pain"
    assert extracted.get("duration") == "3 days"
    # Duration was already extracted, so next topic should jump directly to location
    assert data["current_topic"] == "location"


def test_multi_fact_extraction_hindi(client: TestClient):
    """Test multi-fact extraction in Hindi/Hinglish: 'Mujhe 3 din se seene mein dard hai'."""
    start_res = client.post("/interview/start", json={"patient_id": "P1001", "language": "hi"})
    assert start_res.status_code == 201
    int_id = start_res.json()["interview_id"]

    res = client.post(
        "/interview/respond",
        json={"interview_id": int_id, "message": "Mujhe 3 din se seene mein dard hai"}
    )
    assert res.status_code == 200
    data = res.json()
    extracted = {f["field_name"]: f["value"] for f in data["extracted_facts"]}
    assert extracted.get("chief_complaint") == "chest_pain"
    assert extracted.get("duration") == "3 days"
    assert data["current_topic"] == "location"
    assert "कहाँ महसूस" in data["next_question"]["text"]


def test_fever_full_question_flow(client: TestClient):
    """Test complete question flow for fever until completion."""
    start_res = client.post("/interview/start", json={"patient_id": "P1002", "language": "hi"})
    int_id = start_res.json()["interview_id"]

    # 1. Chief Complaint & Duration
    r1 = client.post("/interview/respond", json={"interview_id": int_id, "message": "मुझे 4 दिनों से तेज़ बुखार है"})
    d1 = r1.json()
    assert d1["current_topic"] == "temperature"

    # 2. Temperature
    r2 = client.post("/interview/respond", json={"interview_id": int_id, "message": "101.8 F नापा था"})
    d2 = r2.json()
    assert d2["current_topic"] == "chills"

    # 3. Chills
    r3 = client.post("/interview/respond", json={"interview_id": int_id, "message": "हाँ, तेज़ ठंड और कंपकंपी लगती है"})
    d3 = r3.json()
    assert d3["current_topic"] == "cough"

    # 4. Cough (Positive answer triggers adaptive respiratory follow-up)
    r4 = client.post("/interview/respond", json={"interview_id": int_id, "message": "हल्की सूखी खांसी है"})
    d4 = r4.json()
    assert d4["current_topic"] == "respiratory_symptoms"

    # 5. Respiratory symptoms follow-up -> completion
    r5 = client.post("/interview/respond", json={"interview_id": int_id, "message": "बलगम नहीं है, सांस की तकलीफ़ नहीं है"})
    d5 = r5.json()
    assert d5["interview_completed"] is True
    assert d5["current_topic"] == "completion"
    assert "धन्यवाद" in d5["next_question"]["text"]


def test_headache_question_flow(client: TestClient):
    """Test question flow for headache complaint in English."""
    start_res = client.post("/interview/start", json={"patient_id": "P1003", "language": "en"})
    int_id = start_res.json()["interview_id"]

    # 1. Chief complaint
    r1 = client.post("/interview/respond", json={"interview_id": int_id, "message": "I have severe headache"})
    d1 = r1.json()
    assert d1["current_topic"] == "duration"

    # 2. Duration & Severity in one turn
    r2 = client.post("/interview/respond", json={"interview_id": int_id, "message": "2 days, severity is 8 out of 10"})
    d2 = r2.json()
    # Location was skipped in prompt? Location is required: location comes next
    assert d2["current_topic"] == "location"


def test_unknown_uncertainty_handling(client: TestClient):
    """Test that expressing uncertainty ('pata nahi' / 'I don't know') does not fabricate facts."""
    start_res = client.post("/interview/start", json={"patient_id": "P1001", "language": "hi"})
    int_id = start_res.json()["interview_id"]

    # 1. State complaint
    client.post("/interview/respond", json={"interview_id": int_id, "message": "seene mein dard hai"})

    # 2. When asked duration, respond with uncertainty
    r2 = client.post("/interview/respond", json={"interview_id": int_id, "message": "pata nahi yaad nahi"})
    d2 = r2.json()
    # It should record duration as unknown and move forward to location
    assert d2["current_topic"] == "location"
    assert any(f["field_name"] == "duration" and f["status"] == "unknown" for f in d2["extracted_facts"])


def test_invalid_interview_id(client: TestClient):
    """Test responding to non-existent interview returns 404."""
    res = client.post("/interview/respond", json={"interview_id": "INT_NONEXISTENT", "message": "Hello"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_completed_interview_rejects_response(client: TestClient):
    """Test that an interview marked as completed cannot accept new responses."""
    start_res = client.post("/interview/start", json={"patient_id": "P1001", "language": "en"})
    int_id = start_res.json()["interview_id"]

    # Step through until completed or manually simulate completed
    # 1. chest pain + duration + location + severity + trigger + associated_symptoms
    r1 = client.post("/interview/respond", json={"interview_id": int_id, "message": "I have chest pain for 3 days"})
    assert r1.status_code == 200
    r2 = client.post("/interview/respond", json={"interview_id": int_id, "message": "In the center, severity is 8 out of 10"})
    assert r2.status_code == 200
    r3 = client.post("/interview/respond", json={"interview_id": int_id, "message": "It gets worse when I walk"})
    assert r3.status_code == 200
    r4 = client.post("/interview/respond", json={"interview_id": int_id, "message": "No other symptoms, no sweating"})
    assert r4.status_code == 200
    assert r4.json()["interview_completed"] is True

    # Attempting to respond to completed interview
    r_after = client.post("/interview/respond", json={"interview_id": int_id, "message": "One more thing"})
    assert r_after.status_code == 400
    assert "not active" in r_after.json()["detail"].lower() or "completed" in r_after.json()["detail"].lower()


def test_abdominal_and_back_pain_flows(client: TestClient):
    """Test abdominal pain and back pain specific complaint flows."""
    # Abdominal pain
    s1 = client.post("/interview/start", json={"patient_id": "P1002", "language": "en"})
    id1 = s1.json()["interview_id"]
    res_ab = client.post("/interview/respond", json={"interview_id": id1, "message": "Severe stomach pain for 2 days"})
    assert res_ab.status_code == 200
    assert res_ab.json()["current_topic"] == "location"

    # Back pain
    s2 = client.post("/interview/start", json={"patient_id": "P1003", "language": "hi"})
    id2 = s2.json()["interview_id"]
    res_bp = client.post("/interview/respond", json={"interview_id": id2, "message": "Mujhe 1 hafte se kamar mein dard hai"})
    assert res_bp.status_code == 200
    assert res_bp.json()["current_topic"] == "location"


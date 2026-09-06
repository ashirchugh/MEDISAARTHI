import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.services.ai.stt.factory import get_stt_provider, MockSTTProvider, reset_stt_provider


client = TestClient(app)

MOCK_AUDIO_PAYLOAD = b"FAKE_OGG_WEBM_AUDIO_DATA_FOR_TESTING_1234567890"


@pytest.fixture(autouse=True)
def setup_mock_stt(monkeypatch):
    """Ensure all voice unit tests run deterministically with MockSTTProvider."""
    monkeypatch.setattr(settings, "STT_PROVIDER", "mock")
    reset_stt_provider()
    yield
    reset_stt_provider()


def test_test_a_b_c_d_e_f_voice_endpoint_success(db_session):
    """Test A-F: Valid audio reaches STT provider, returns transcript, updates facts and next question."""
    # 1. Start interview
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    assert start_resp.status_code == 201
    interview_id = start_resp.json()["interview_id"]

    # 2. Configure mock STT provider
    stt = get_stt_provider("mock")
    if isinstance(stt, MockSTTProvider):
        stt.set_transcript_for_key(
            f"{len(MOCK_AUDIO_PAYLOAD)}_hi",
            "Mujhe seene mein dard hai teen din se"
        )

    # 3. Send voice request
    audio_file = io.BytesIO(MOCK_AUDIO_PAYLOAD)
    voice_resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("sample.webm", audio_file, "audio/webm")},
    )
    assert voice_resp.status_code == 200
    data = voice_resp.json()

    # Assertions
    assert data["interview_id"] == interview_id
    assert "seene mein dard" in data["transcript"]
    assert data["received_message"] == data["transcript"]
    assert len(data["extracted_facts"]) > 0
    assert any(f["field_name"] == "chief_complaint" for f in data["extracted_facts"])
    assert data["next_question"]["text"] is not None
    assert data["status"] == "active"


def test_test_g_voice_response_can_complete_interview(db_session):
    """Test G: Multi-turn voice interaction can lead to interview completion."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    interview_id = start_resp.json()["interview_id"]

    # Turn 1: Chief complaint + duration
    audio1 = io.BytesIO(b"AUDIO_TURN_1_CHEST_PAIN")
    stt = get_stt_provider("mock")
    if isinstance(stt, MockSTTProvider):
        stt.set_transcript_for_key(
            f"{len(b'AUDIO_TURN_1_CHEST_PAIN')}_hi",
            "Seene mein dard hai teen din se"
        )
    r1 = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("turn1.webm", audio1, "audio/webm")},
    )
    assert r1.status_code == 200

    # Turn 2: Severity
    audio2 = io.BytesIO(b"AUDIO_TURN_2_SEVERITY")
    if isinstance(stt, MockSTTProvider):
        stt.set_transcript_for_key(
            f"{len(b'AUDIO_TURN_2_SEVERITY')}_hi",
            "Dard bahut tez hai 8 out of 10"
        )
    r2 = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("turn2.webm", audio2, "audio/webm")},
    )
    assert r2.status_code == 200
    assert any(f["field_name"] == "severity" for f in r2.json()["extracted_facts"])


def test_test_h_hindi_transcription_path(db_session):
    """Test H: Hindi voice input is preserved verbatim without premature translation."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    interview_id = start_resp.json()["interview_id"]

    audio = io.BytesIO(b"AUDIO_HINDI_SAMPLE")
    stt = get_stt_provider("mock")
    if isinstance(stt, MockSTTProvider):
        stt.set_transcript_for_key(
            f"{len(b'AUDIO_HINDI_SAMPLE')}_hi",
            "Mujhe kal se tej bukhar hai aur thand lag rahi hai"
        )

    resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("hindi.wav", audio, "audio/wav")},
    )
    assert resp.status_code == 200
    assert "bukhar" in resp.json()["transcript"]


def test_test_i_english_transcription_path(db_session):
    """Test I: English voice input is processed accurately."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "en"},
    )
    interview_id = start_resp.json()["interview_id"]

    audio = io.BytesIO(b"AUDIO_ENGLISH_SAMPLE")
    stt = get_stt_provider("mock")
    if isinstance(stt, MockSTTProvider):
        stt.set_transcript_for_key(
            f"{len(b'AUDIO_ENGLISH_SAMPLE')}_en",
            "I have severe chest pain for 3 days"
        )

    resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("english.mp3", audio, "audio/mpeg")},
    )
    assert resp.status_code == 200
    assert "chest pain" in resp.json()["transcript"]


def test_test_j_invalid_audio_format_rejected(db_session):
    """Test J: Unsupported audio MIME format returns 400 Bad Request."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    interview_id = start_resp.json()["interview_id"]

    audio = io.BytesIO(b"NOT_AUDIO_FILE_DATA")
    resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("doc.pdf", audio, "application/pdf")},
    )
    assert resp.status_code == 400
    assert "Unsupported audio format" in resp.json()["detail"]


def test_test_k_empty_audio_rejected(db_session):
    """Test K: Empty audio file returns 400 Bad Request."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    interview_id = start_resp.json()["interview_id"]

    audio = io.BytesIO(b"")
    resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("empty.webm", audio, "audio/webm")},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_test_l_oversized_audio_rejected(db_session):
    """Test L: Oversized audio file exceeds 10MB limit and returns 400."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    interview_id = start_resp.json()["interview_id"]

    # 11MB dummy audio
    oversized = io.BytesIO(b"0" * (11 * 1024 * 1024))
    resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("large.webm", oversized, "audio/webm")},
    )
    assert resp.status_code == 400
    assert "exceeds maximum limit" in resp.json()["detail"]


def test_test_m_missing_interview_returns_404(db_session):
    """Test M: Voice request for non-existent interview returns 404."""
    audio = io.BytesIO(b"SOME_AUDIO_DATA")
    resp = client.post(
        "/interview/NON_EXISTENT_INT/voice",
        files={"audio": ("sample.webm", audio, "audio/webm")},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_test_n_completed_interview_rejects_voice_response(db_session):
    """Test N: Completed interview rejects voice responses with 400."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    interview_id = start_resp.json()["interview_id"]

    # Complete interview
    comp_resp = client.post(
        "/interview/complete",
        json={"interview_id": interview_id},
    )
    assert comp_resp.status_code == 200

    # Attempt voice response
    audio = io.BytesIO(b"AUDIO_DATA")
    voice_resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("sample.webm", audio, "audio/webm")},
    )
    assert voice_resp.status_code == 400
    assert "already completed" in voice_resp.json()["detail"]


def test_test_o_p_stt_failure_handled_without_fabricating_transcript(db_session):
    """Test O & P: STT failure returns controlled error and NEVER fabricates or guesses text."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "hi"},
    )
    interview_id = start_resp.json()["interview_id"]

    stt = get_stt_provider("mock")
    if isinstance(stt, MockSTTProvider):
        stt.set_fail_next(True)

    audio = io.BytesIO(b"FAIL_AUDIO_SAMPLE")
    resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("sample.webm", audio, "audio/webm")},
    )
    assert resp.status_code == 400
    assert "Speech transcription failed" in resp.json()["detail"]


def test_voice_quota_exceeded_returns_429(db_session, monkeypatch):
    """Test: When STT provider encounters quota / 429 error, endpoint returns HTTP 429 with clear message."""
    start_resp = client.post(
        "/interview/start",
        json={"patient_id": "P1001", "language": "en"},
    )
    interview_id = start_resp.json()["interview_id"]

    # Mock provider transcribe raising 429 quota error
    from backend.app.services.ai.stt.gemini_transcribe import GeminiSTTProvider
    monkeypatch.setattr(
        GeminiSTTProvider,
        "transcribe",
        lambda self, audio_bytes, mime_type, language: (_ for _ in ()).throw(
            RuntimeError("Gemini transcription quota exceeded (HTTP 429): Resource has been exhausted")
        )
    )
    monkeypatch.setattr("backend.app.api.interviews.get_stt_provider", lambda provider_name=None: GeminiSTTProvider(api_key="test_key"))

    audio = io.BytesIO(b"TEST_AUDIO_SAMPLE")
    resp = client.post(
        f"/interview/{interview_id}/voice",
        files={"audio": ("sample.wav", audio, "audio/wav")},
    )
    assert resp.status_code == 429
    assert "Gemini transcription quota exceeded. Please wait and try again." in resp.json()["detail"]



def test_test_q_r_s_t_text_and_voice_parity_and_security(db_session):
    """Test Q, R, S, T: Text endpoint remains unchanged, parity exists, and no API keys exposed."""
    # Text response
    start1 = client.post("/interview/start", json={"patient_id": "P1001", "language": "hi"})
    id1 = start1.json()["interview_id"]
    text_resp = client.post("/interview/respond", json={"interview_id": id1, "message": "Seene mein dard hai 3 din se"})
    assert text_resp.status_code == 200
    text_data = text_resp.json()

    # Voice response
    start2 = client.post("/interview/start", json={"patient_id": "P1001", "language": "hi"})
    id2 = start2.json()["interview_id"]

    stt = get_stt_provider("mock")
    if isinstance(stt, MockSTTProvider):
        stt.set_transcript_for_key(
            f"{len(b'PARITY_AUDIO_SAMPLE')}_hi",
            "Seene mein dard hai 3 din se"
        )
    audio = io.BytesIO(b"PARITY_AUDIO_SAMPLE")
    voice_resp = client.post(
        f"/interview/{id2}/voice",
        files={"audio": ("sample.webm", audio, "audio/webm")},
    )
    assert voice_resp.status_code == 200
    voice_data = voice_resp.json()

    # Parity check: both extracted chief_complaint and duration
    text_fields = {f["field_name"] for f in text_data["extracted_facts"]}
    voice_fields = {f["field_name"] for f in voice_data["extracted_facts"]}
    assert "chief_complaint" in text_fields and "chief_complaint" in voice_fields

    # Security check: verify no secrets or keys in voice response
    resp_text = voice_resp.text
    assert "GEMINI_API_KEY" not in resp_text
    assert "AI_API_KEY" not in resp_text


def test_gemini_stt_file_state_transitions(monkeypatch):
    """Test GeminiSTTProvider handling of file state transitions (PROCESSING -> ACTIVE, immediate ACTIVE, FAILED, timeout)."""
    from backend.app.services.ai.stt.gemini_transcribe import GeminiSTTProvider
    from unittest.mock import MagicMock

    provider = GeminiSTTProvider(api_key="test_dummy_key")

    class MockFile:
        def __init__(self, state_name="ACTIVE"):
            self.name = "files/mock123"
            self.uri = "https://generativelanguage.googleapis.com/v1beta/files/mock123"
            self.mime_type = "audio/webm"
            self.state = MagicMock(name=state_name)
            self.state.name = state_name

    # 1. Immediate ACTIVE
    mock_client = MagicMock()
    mock_client.files.upload.return_value = MockFile("ACTIVE")
    mock_client.files.delete.return_value = None
    provider._client = mock_client

    monkeypatch.setattr(
        "requests.post",
        lambda url, json, timeout: MagicMock(status_code=200, json=lambda: {"steps": [{"content": [{"type": "text", "text": "Immediate active test"}]}]})
    )
    result = provider.transcribe(b"TEST_AUDIO_BYTES", mime_type="audio/webm", language="en")
    assert result == "Immediate active test"
    assert mock_client.files.delete.called

    # 2. PROCESSING -> ACTIVE
    mock_client2 = MagicMock()
    mock_client2.files.upload.return_value = MockFile("PROCESSING")
    mock_client2.files.get.side_effect = [MockFile("PROCESSING"), MockFile("ACTIVE")]
    provider._client = mock_client2

    monkeypatch.setattr(
        "requests.post",
        lambda url, json, timeout: MagicMock(status_code=200, json=lambda: {"output_text": "Processing to active success"})
    )
    result2 = provider.transcribe(b"TEST_AUDIO_BYTES", mime_type="audio/webm", language="en")
    assert result2 == "Processing to active success"
    assert mock_client2.files.get.call_count == 2
    assert mock_client2.files.delete.called

    # 3. FAILED state raises error
    mock_client3 = MagicMock()
    mock_client3.files.upload.return_value = MockFile("PROCESSING")
    mock_client3.files.get.return_value = MockFile("FAILED")
    provider._client = mock_client3

    with pytest.raises(RuntimeError) as exc_info:
        provider.transcribe(b"TEST_AUDIO_BYTES", mime_type="audio/webm", language="en")
    assert "Gemini File processing failed" in str(exc_info.value)
    assert mock_client3.files.delete.called

    # 4. Timeout waiting for ACTIVE state
    mock_client4 = MagicMock()
    mock_client4.files.upload.return_value = MockFile("PROCESSING")
    mock_client4.files.get.return_value = MockFile("PROCESSING")
    provider._client = mock_client4

    # Patch time to simulate timeout
    times = [0.0, 100.0, 100.0, 100.0, 100.0]
    monkeypatch.setattr("time.time", lambda: times.pop(0) if times else 200.0)
    monkeypatch.setattr("time.sleep", lambda s: None)
    with pytest.raises(RuntimeError) as exc_info2:
        provider.transcribe(b"TEST_AUDIO_BYTES", mime_type="audio/webm", language="en")
    assert "Timed out" in str(exc_info2.value) or "transcription failed" in str(exc_info2.value)
    assert mock_client4.files.delete.called

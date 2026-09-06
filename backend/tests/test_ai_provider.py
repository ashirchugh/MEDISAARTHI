import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.services.ai.base import AIProvider
from backend.app.services.ai.mock_provider import MockAIProvider
from backend.app.services.ai.gemini_provider import GeminiAIProvider
from backend.app.services.ai import get_ai_provider
from backend.app.services.ai.schemas import (
    LLMExtractedFact,
    LLMExtractedFactsResult,
    LLMQuestionResult,
)


def test_ai_provider_factory():
    """Test get_ai_provider factory returns correct provider instance."""
    mock_p = get_ai_provider("mock")
    assert isinstance(mock_p, MockAIProvider)
    assert mock_p.provider_name == "mock"

    gemini_p = get_ai_provider("gemini")
    assert isinstance(gemini_p, GeminiAIProvider)
    assert gemini_p.provider_name == "gemini"


def test_gemini_provider_init_without_key():
    """Test GeminiAIProvider initializes in fallback mode without API key."""
    provider = GeminiAIProvider(api_key="")
    assert provider.provider_name == "gemini"
    assert provider._client is None

    # Extraction should safely fall back to deterministic extraction
    res = provider.extract_facts(
        message="Mujhe 3 din se bukhar hai",
        language="hi",
        current_topic="chief_complaint",
    )
    assert isinstance(res, LLMExtractedFactsResult)
    fact_dict = {f.field_name: f.value for f in res.facts}
    assert fact_dict.get("chief_complaint") == "fever"
    assert fact_dict.get("duration") == "3 days"


def test_mock_provider_extraction():
    """Test MockAIProvider extracts facts for English and Hindi."""
    provider = MockAIProvider()

    # English multi-fact
    res_en = provider.extract_facts(
        message="I have severe chest pain for 2 days",
        language="en",
        current_topic="chief_complaint",
    )
    facts_en = {f.field_name: f.value for f in res_en.facts}
    assert facts_en.get("chief_complaint") == "chest_pain"
    assert facts_en.get("duration") == "2 days"

    # Hindi uncertainty
    res_hi = provider.extract_facts(
        message="pata nahi yaad nahi",
        language="hi",
        current_topic="location",
    )
    assert any(f.field_name == "location" and f.status == "unknown" for f in res_hi.facts)


def test_gemini_structured_extraction_success():
    """Test GeminiAIProvider with successful parsed structured JSON response."""
    provider = GeminiAIProvider(api_key="mock-key-for-test")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = LLMExtractedFactsResult(
        facts=[
            LLMExtractedFact(
                field_name="chief_complaint",
                value="chest_pain",
                evidence="chest pain",
                status="confirmed",
                confidence=0.98,
            ),
            LLMExtractedFact(
                field_name="duration",
                value="3 days",
                evidence="3 days",
                status="confirmed",
                confidence=0.95,
            ),
            LLMExtractedFact(
                field_name="location",
                value="Center of chest",
                evidence="central chest",
                status="confirmed",
                confidence=0.92,
            ),
        ]
    )
    mock_client.models.generate_content.return_value = mock_response
    provider._client = mock_client

    res = provider.extract_facts(
        message="I have central chest pain since 3 days",
        language="en",
        current_topic="location",
        allowed_fields=["chief_complaint", "duration", "location", "severity"],
    )

    assert len(res.facts) >= 3
    fact_map = {f.field_name: f.value for f in res.facts}
    assert fact_map["chief_complaint"] == "chest_pain"
    assert fact_map["duration"] == "3 days"
    assert fact_map["location"] == "Center of chest"


def test_gemini_invalid_json_fallback():
    """Test that if Gemini returns invalid/corrupted output, it falls back to deterministic extraction."""
    provider = GeminiAIProvider(api_key="mock-key-for-test")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = "INVALID_NON_JSON_OUTPUT"
    mock_client.models.generate_content.return_value = mock_response
    provider._client = mock_client

    # Deterministic fallback should extract chief_complaint and duration
    res = provider.extract_facts(
        message="Mujhe 3 din se seene mein dard hai",
        language="hi",
        current_topic="chief_complaint",
    )

    fact_map = {f.field_name: f.value for f in res.facts}
    assert fact_map.get("chief_complaint") == "chest_pain"
    assert fact_map.get("duration") == "3 days"


def test_gemini_api_exception_fallback():
    """Test that network/API exceptions are caught and fallback is activated."""
    provider = GeminiAIProvider(api_key="mock-key-for-test")

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Rate limit reached / Timeout")
    provider._client = mock_client

    res = provider.extract_facts(
        message="I have high fever since yesterday",
        language="en",
        current_topic="chief_complaint",
    )

    fact_map = {f.field_name: f.value for f in res.facts}
    assert fact_map.get("chief_complaint") == "fever"
    assert fact_map.get("duration") is not None


def test_gemini_natural_question_generation():
    """Test natural question generation with mock Gemini client."""
    provider = GeminiAIProvider(api_key="mock-key-for-test")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = LLMQuestionResult(
        question_text="क्या आप बता सकते हैं कि यह तकलीफ़ ठीक किस जगह हो रही है?"
    )
    mock_client.models.generate_content.return_value = mock_response
    provider._client = mock_client

    q = provider.generate_question(
        topic="location",
        language="hi",
        patient_name="Rajesh Kumar",
        fallback_template="आपको यह तकलीफ़ ठीक कहाँ महसूस हो रही है?",
    )

    assert "तकलीफ़ ठीक किस जगह" in q


def test_gemini_natural_question_fallback_on_error():
    """Test question generation returns fallback template when Gemini fails."""
    provider = GeminiAIProvider(api_key="mock-key-for-test")

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Gemini Service Unavailable")
    provider._client = mock_client

    fallback = "On a scale from 1 to 10, how severe is it?"
    q = provider.generate_question(
        topic="severity",
        language="en",
        patient_name="Rahul",
        fallback_template=fallback,
    )

    assert q == fallback


def test_hallucination_prevention_test_a():
    """Test A:
    Input: 'Mujhe seene mein dard hai, teen din se.'
    Expected: chief_complaint = chest_pain, duration = 3 days
    Must NOT contain: severity, trigger, associated_symptoms.
    """
    provider = GeminiAIProvider(api_key="")  # deterministic / grounded fallback
    res = provider.extract_facts(
        message="Mujhe seene mein dard hai, teen din se.",
        language="hi",
        current_topic="chief_complaint",
        allowed_fields=["chief_complaint", "duration", "severity", "location", "trigger", "associated_symptoms"],
    )
    fact_map = {f.field_name: f for f in res.facts}
    assert "chief_complaint" in fact_map
    assert fact_map["chief_complaint"].value == "chest_pain"
    assert "duration" in fact_map
    assert "3" in fact_map["duration"].value

    # Must NOT contain unmentioned facts
    assert "severity" not in fact_map
    assert "trigger" not in fact_map
    assert "associated_symptoms" not in fact_map


def test_hallucination_prevention_test_b():
    """Test B:
    Input: 'Mujhe kal se bukhar hai, temperature 102 degree tha aur thand lag rahi hai.'
    Expected: chief_complaint = fever, duration = since yesterday, temperature = 102 degrees, chills = present
    Must NOT contain: severity = 102, cough, body ache.
    """
    provider = GeminiAIProvider(api_key="")
    res = provider.extract_facts(
        message="Mujhe kal se bukhar hai, temperature 102 degree tha aur thand lag rahi hai.",
        language="hi",
        current_topic="chief_complaint",
        allowed_fields=["chief_complaint", "duration", "temperature", "chills", "severity", "cough", "associated_symptoms"],
    )
    fact_map = {f.field_name: f for f in res.facts}
    assert fact_map["chief_complaint"].value == "fever"
    assert "yesterday" in fact_map["duration"].value.lower() or "1 day" in fact_map["duration"].value.lower()
    assert "temperature" in fact_map
    assert "102" in fact_map["temperature"].value
    assert "chills" in fact_map
    assert fact_map["chills"].status == "confirmed"

    # Must NOT contain temperature as severity or unstated symptoms
    assert "severity" not in fact_map
    assert "cough" not in fact_map
    assert "associated_symptoms" not in fact_map


def test_hallucination_prevention_test_c():
    """Test C:
    Input: 'Sir mein dard hai, do din se.'
    Expected: chief_complaint = headache, duration = 2 days
    Do NOT invent: location, severity, headache_character, photophobia.
    """
    provider = GeminiAIProvider(api_key="")
    res = provider.extract_facts(
        message="Sir mein dard hai, do din se.",
        language="hi",
        current_topic="chief_complaint",
        allowed_fields=["chief_complaint", "duration", "location", "severity", "headache_character", "associated_symptoms"],
    )
    fact_map = {f.field_name: f for f in res.facts}
    assert fact_map["chief_complaint"].value == "headache"
    assert "2" in fact_map["duration"].value
    assert "severity" not in fact_map
    assert "headache_character" not in fact_map
    assert "associated_symptoms" not in fact_map


def test_hallucination_prevention_test_d():
    """Test D:
    Input: 'Pet mein dard hai, pata nahi kitne din se.'
    Expected: chief_complaint = abdominal_pain, duration = unknown
    Do NOT invent a duration.
    """
    provider = GeminiAIProvider(api_key="")
    res = provider.extract_facts(
        message="Pet mein dard hai, pata nahi kitne din se.",
        language="hi",
        current_topic="chief_complaint",
        allowed_fields=["chief_complaint", "duration", "location", "severity", "vomiting", "bowel_symptoms"],
    )
    fact_map = {f.field_name: f for f in res.facts}
    assert fact_map["chief_complaint"].value == "abdominal_pain"
    assert "duration" in fact_map
    assert fact_map["duration"].status == "unknown"


def test_hallucination_prevention_test_e():
    """Test E:
    Input: 'Kamr mein dard hai, shayad ek hafte se.'
    Expected: chief_complaint = back_pain, duration = approximately 1 week, status = uncertain
    """
    provider = GeminiAIProvider(api_key="")
    res = provider.extract_facts(
        message="Kamr mein dard hai, shayad ek hafte se.",
        language="hi",
        current_topic="chief_complaint",
        allowed_fields=["chief_complaint", "duration", "severity", "radiation", "movement_effect"],
    )
    fact_map = {f.field_name: f for f in res.facts}
    assert fact_map["chief_complaint"].value == "back_pain"
    assert "duration" in fact_map
    assert fact_map["duration"].status == "uncertain"
    assert "1 week" in fact_map["duration"].value.lower() or "hafte" in fact_map["duration"].value.lower()


def test_gemini_grounding_rejects_hallucinated_facts():
    """Test that GeminiAIProvider strictly rejects hallucinated facts returned by the LLM."""
    provider = GeminiAIProvider(api_key="mock-key-for-test")
    mock_client = MagicMock()
    mock_response = MagicMock()
    # LLM hallucinates cough, severity=102, and associated_symptoms that were NOT in the patient message
    mock_response.parsed = LLMExtractedFactsResult(
        facts=[
            LLMExtractedFact(field_name="chief_complaint", value="fever", evidence="bukhar", status="confirmed", confidence=0.99),
            LLMExtractedFact(field_name="temperature", value="102°F", evidence="102 degree", status="confirmed", confidence=0.98),
            LLMExtractedFact(field_name="severity", value="102", evidence="102 degree", status="confirmed", confidence=0.95),  # HALLUCINATED CONVERSION
            LLMExtractedFact(field_name="cough", value="dry cough", evidence="dry cough", status="confirmed", confidence=0.90),  # HALLUCINATED SYMPTOM
            LLMExtractedFact(field_name="associated_symptoms", value="body ache", evidence="", status="confirmed", confidence=0.85),  # HALLUCINATED SYMPTOM
        ]
    )
    mock_client.models.generate_content.return_value = mock_response
    provider._client = mock_client

    patient_msg = "Mujhe kal se bukhar hai, temperature 102 degree tha."
    res = provider.extract_facts(
        message=patient_msg,
        language="hi",
        current_topic="chief_complaint",
        allowed_fields=["chief_complaint", "duration", "temperature", "severity", "cough", "associated_symptoms"],
    )

    fact_map = {f.field_name: f.value for f in res.facts}
    assert fact_map["chief_complaint"] == "fever"
    assert "102" in fact_map["temperature"]

    # Strictly rejected hallucinations:
    assert "severity" not in fact_map
    assert "cough" not in fact_map
    assert "associated_symptoms" not in fact_map


def test_full_interview_with_gemini_provider(client: TestClient):
    """Test full interview interaction via API using GeminiAIProvider configured."""
    with patch("backend.app.services.rules.interview_engine.get_ai_provider") as mock_get_p:
        gemini_provider = GeminiAIProvider(api_key="mock-key")
        mock_client = MagicMock()

        # Step 1 response
        mock_client.models.generate_content.return_value.parsed = LLMExtractedFactsResult(
            facts=[
                LLMExtractedFact(field_name="chief_complaint", value="headache", evidence="headache", status="confirmed", confidence=0.96),
                LLMExtractedFact(field_name="duration", value="2 days", evidence="2 days", status="confirmed", confidence=0.94),
            ]
        )
        gemini_provider._client = mock_client
        mock_get_p.return_value = gemini_provider

        # Start interview
        start_res = client.post("/interview/start", json={"patient_id": "P1003", "language": "en"})
        int_id = start_res.json()["interview_id"]

        # Turn 1: Patient responds
        res = client.post(
            "/interview/respond",
            json={"interview_id": int_id, "message": "I've had a bad headache for 2 days"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["current_topic"] == "location"
        extracted = {f["field_name"]: f["value"] for f in data["extracted_facts"]}
        assert extracted.get("chief_complaint") == "headache"
        assert extracted.get("duration") == "2 days"


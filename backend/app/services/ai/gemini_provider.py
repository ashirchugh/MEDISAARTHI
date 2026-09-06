import json
import logging
import re
import time
from typing import Dict, List, Optional, Any

from backend.app.core.config import settings
from backend.app.schemas.doctor import DoctorSummaryData, DoctorNarrativeSummary
from backend.app.services.ai.base import AIProvider
from backend.app.services.ai.schemas import (
    LLMExtractedFact,
    LLMExtractedFactsResult,
    LLMQuestionResult,
)
from backend.app.services.rules.fact_extractor import extract_facts_from_message

logger = logging.getLogger(__name__)

CLINICAL_EXTRACTION_SYSTEM_PROMPT = """You are the Strict Clinical Fact Extractor for Medisaarthi, an AI pre-consultation intake platform for hospitals.
Your sole responsibility is to extract clinical facts that are EXPLICITLY and DIRECTLY stated by the patient in English, Hindi, or Hinglish into validated JSON.

CRITICAL ZERO-HALLUCINATION & CLINICAL INTEGRITY RULES:
1. STRICT ZERO-HALLUCINATION POLICY:
   - Extract ONLY facts explicitly and unequivocally stated by the patient in the current message.
   - NEVER invent, infer, predict, assume, or extrapolate a symptom or clinical detail.
   - NEVER fill a missing field with a medically plausible value (e.g., do NOT add cough to fever, do NOT add triggers or sweating to chest pain, do NOT add headache characteristics or photophobia unless explicitly stated).
   - If a symptom or detail is NOT stated by the patient, DO NOT include it in the facts list.

2. NEVER POPULATE FIELDS JUST BECAUSE THEY ARE IN allowed_fields:
   - `allowed_fields` is provided only as a reference for standard clinical field names.
   - If the patient did not provide information for an allowed field, that field MUST REMAIN MISSING. The clinical question engine will ask for it in subsequent turns.

3. MANDATORY EVIDENCE QUOTE:
   - For every extracted fact, you MUST provide the `evidence` field containing the exact verbatim words or phrase from the patient's message that supports this fact.
   - If you cannot point to an exact quote from the patient's text, DO NOT EXTRACT THE FACT.

4. SEVERITY vs. TEMPERATURE DISAMBIGUATION:
   - Severity is a pain/discomfort intensity scale rating (e.g., 1-10 numerical scale like "8/10", or explicit intensity words like "mild", "moderate", "severe", "bahut tez", "halka").
   - Temperature is a body thermal reading (e.g., "102 degree", "101.5°F", "high fever", "tapman 102").
   - A temperature reading like "102 degree" MUST be stored as `field_name: "temperature"` with value "102 degrees" or "102°F".
   - A temperature reading MUST NEVER be assigned to `field_name: "severity"`.

5. UNCERTAINTY & UNKNOWN HANDLING:
   - If the patient says they don't know or cannot remember (e.g., "pata nahi", "I don't know", "yaad nahi", "not sure"), set `value: "Unknown"` and `status: "unknown"`.
   - If the patient is uncertain or estimating (e.g., "shayad ek hafte se", "maybe 3 days", "approx 2 weeks"), set `status: "uncertain"` with an approximate value.
   - Distinguish "unknown" (patient doesn't know) from "denied" (patient explicitly denies, e.g. "khansi nahi hai" -> `status: "denied"`, `value: "Absent"`).

6. CHIEF COMPLAINTS & COLLOQUIAL PHRASES:
   - "seene mein dard" / "chest pain" -> `chief_complaint: "chest_pain"`
   - "bukhar" / "fever" -> `chief_complaint: "fever"`
   - "sar dard" / "sir mein dard" / "headache" -> `chief_complaint: "headache"`
   - "pet mein dard" / "stomach pain" -> `chief_complaint: "abdominal_pain"`
   - "kamar mein dard" / "back pain" -> `chief_complaint: "back_pain"`

7. PRESERVE EXPLICIT PATIENT STATEMENTS EVEN IF UNUSUAL:
   - Do not distort or convert one clinical concept into another.
"""

QUESTION_GENERATION_SYSTEM_PROMPT = """You are a warm, polite, patient-friendly healthcare intake assistant for Medisaarthi.
Your task is to rephrase the required clinical inquiry into a natural, empathetic, conversational question in the specified language (English or patient-friendly Hindi/Hinglish).

RULES:
1. Inquire strictly about the requested clinical topic.
2. Do NOT diagnose, suggest possible conditions, or create alarm.
3. Keep the sentence concise, simple, respectful, and easy to understand.
"""

DOCTOR_SUMMARY_NARRATIVE_SYSTEM_PROMPT = """You are a clinical documentation assistant, not a diagnostician.
Your sole responsibility is to organize the validated, structured clinical pre-consultation intake data (DoctorSummaryData) into a concise, doctor-readable narrative summary adhering strictly to the DoctorNarrativeSummary schema.

CRITICAL ZERO-HALLUCINATION & CLINICAL INTEGRITY RULES:
1. Use ONLY information contained in the supplied DoctorSummaryData JSON.
2. NEVER invent, hallucinate, assume, or extrapolate any information.
3. NEVER infer a diagnosis or medical condition.
4. NEVER infer a disease from symptoms (e.g., do not suggest myocardial infarction, pneumonia, migraine, gastritis, etc.).
5. NEVER infer causality (e.g., do not claim symptom X is caused by event Y unless explicitly recorded).
6. NEVER infer severity beyond explicitly supplied values.
7. NEVER add treatment recommendations or clinical advice.
8. NEVER recommend tests, labs, imaging, or investigations.
9. NEVER prescribe medication or suggest dosages.
10. NEVER change medication names, dosages, or frequencies. Transcribe them verbatim.
11. NEVER change dates or timelines.
12. NEVER change patient demographics (name, age, gender, uhid, language).
13. NEVER convert missing information into a negative finding.
14. Preserve explicitly denied information (e.g., 'Absent / Denied').
15. Preserve uncertainty exactly as recorded.
16. Preserve priority_flags exactly as supplied in DoctorSummaryData.
17. NEVER create new priority flags or triage categories.
18. NEVER override deterministic safety rules.
19. NEVER introduce external medical knowledge that is not in the input.
20. If a field or topic is missing/unresolved, explicitly state that it is not recorded or not available rather than guessing.
21. The verification_note must explicitly state: 'AI-assisted pre-consultation intake summary. Doctor verification required before clinical decision making.'
"""

# Topic validation keywords mapping for grounding verification
TOPIC_GROUNDING_KEYWORDS = {
    "chest_pain": ["chest", "seene", "seena", "chhati", "सीने", "छाती", "heart", "cardiac"],
    "fever": ["fever", "bukhar", "bukhaar", "बुखार", "tapman", "तापमान", "temp", "hararat", "degree", "डिग्री"],
    "headache": ["headache", "sir", "sar", "head", "सिर", "सर", "migraine", "माथा", "matha"],
    "abdominal_pain": ["pet", "stomach", "abdomen", "abdominal", "belly", "पेट", "आंत"],
    "back_pain": ["kamar", "kamr", "back", "peeth", "spine", "कमर", "पीठ"],
    "temperature": ["degree", "deg", "fever", "bukhar", "tapman", "तापमान", "temp", "10", "9", "°f", "°c", "डिग्री"],
    "chills": ["thand", "chills", "shivering", "kampkampi", "kanpkampi", "ठंड", "कंपकंपी"],
    "cough": ["cough", "khansi", "khasi", "gale", "throat", "खांसी", "खाँसी", "खराश"],
    "vomiting": ["vomit", "ulti", "nausea", "matli", "michlana", "उल्टी", "मिचलाना"],
    "bowel_symptoms": ["motion", "stools", "dast", "diarrhea", "kabz", "constipation", "दस्त", "कब्ज", "कब्ज़"],
    "trigger": ["walk", "walking", "chalne", "chalte", "exertion", "mehnat", "stairs", "sidhiya", "rest", "aaram", "चलने", "आराम", "मेहनत"],
    "location": ["left", "right", "center", "centre", "central", "beech", "side", "taraf", "forehead", "mathe", "lower", "upper", "chest", "seene", "seena", "chhati", "sir", "sar", "pet", "kamar", "kamr", "बाईं", "दाईं", "बीच"],
    "headache_character": ["throbbing", "pulsat", "dhadak", "sharp", "tez", "light", "roshni", "sound", "aawaz", "noise", "photo", "धड़कता", "रोशनी", "आवाज़"],
    "radiation": ["leg", "pair", "thigh", "hand", "arm", "shoot", "spread", "radiat", "पैर", "हाथ"],
    "respiratory_symptoms": ["sputum", "phlegm", "balgam", "khankhar", "breathless", "saans", "throat", "kharash", "बलगम", "कफ", "सांस"],
    "numbness_or_weakness": ["numb", "sunn", "tingling", "pins", "jhanjhanahat", "weak", "kamzori", "सुन्न", "कमजोरी"],
    "movement_effect": ["bend", "jhuk", "sit", "baith", "walk", "chal", "lie", "lying", "letne", "rest", "aaram", "झुकने", "बैठने", "लेटने"],
    "associated_symptoms": ["sweat", "pasina", "breathless", "saans", "ghabrahat", "palpitat", "body ache", "badan dard", "nausea", "ulti", "पसीना", "सांस", "घबराहट", "बदन"],
}


class GeminiAIProvider(AIProvider):
    """Google Gemini AI Provider using official google-genai SDK with strict grounding validation and automatic fallback."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.effective_gemini_api_key
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-2.5-flash"
        self._client = None

        if self.api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"[GeminiAIProvider] Initialized successfully with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"[GeminiAIProvider] Failed to initialize google-genai client: {e}. Will use fallback.")
                self._client = None
        else:
            logger.info("[GeminiAIProvider] No API key configured. Operates in fallback mode.")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _validate_and_ground_fact(self, fact: LLMExtractedFact, patient_message: str) -> Optional[LLMExtractedFact]:
        """Validate that an extracted fact is strictly grounded in the patient's text and adheres to clinical safety."""
        lower_msg = patient_message.lower().strip()
        field = fact.field_name
        val_str = str(fact.value).strip()
        val_lower = val_str.lower()
        evidence = (fact.evidence or "").lower().strip()

        # 1. Evidence Grounding Check
        if evidence:
            # Check if evidence words appear in the patient message
            ev_words = [w for w in re.findall(r"\w+", evidence) if len(w) > 2]
            if ev_words and not any(w in lower_msg for w in ev_words):
                logger.warning(f"[GroundingReject] Fact '{field}' evidence '{evidence}' not found in patient message: '{patient_message}'")
                return None
        else:
            # If evidence is missing, check if keywords for this field exist in patient message
            topic_keys = TOPIC_GROUNDING_KEYWORDS.get(field, [])
            if topic_keys and not any(k in lower_msg for k in topic_keys):
                if field not in ["duration", "severity"]:
                    logger.warning(f"[GroundingReject] Fact '{field}' lacks evidence and keyword support in message: '{patient_message}'")
                    return None

        # 2. Field-Specific Disambiguation & Sanity Checks
        # A. Severity vs Temperature Disambiguation
        if field == "severity":
            # Severity must NOT contain temperature readings, degrees, or bukhar/tapman
            if re.search(r"\b(degrees?|deg|°f|°c|tapman|bukhar|तापमान|fever)\b", val_lower):
                logger.warning(f"[GroundingReject] Temperature reading '{val_str}' incorrectly assigned to severity. Discarding.")
                return None
            # If the value is a number > 10, it cannot be a 1-10 severity rating
            m_num = re.search(r"\b(\d+)\b", val_str)
            if m_num and int(m_num.group(1)) > 10:
                logger.warning(f"[GroundingReject] Numeric severity '{val_str}' exceeds scale 10. Discarding.")
                return None
            # Check if message mentions severity concepts (scale, rating, bahut tez, halka, etc.) or is a standalone number
            has_sev_keyword = any(k in lower_msg for k in ["scale", "severity", "rating", "dard", "pain", "out of 10", "/10", "bahut", "tez", "halka", "severe", "moderate", "mild", "तेज़", "दर्द"])
            if not has_sev_keyword and not (len(re.findall(r"\b\w+\b", lower_msg)) <= 3 and m_num and int(m_num.group(1)) <= 10):
                logger.warning(f"[GroundingReject] Severity '{val_str}' has no severity context in message: '{patient_message}'. Discarding.")
                return None

        # B. Temperature Validation
        elif field == "temperature":
            has_temp_keyword = any(k in lower_msg for k in ["degree", "deg", "fever", "bukhar", "tapman", "तापमान", "°", "डिग्री", "10", "9"])
            if not has_temp_keyword:
                logger.warning(f"[GroundingReject] Temperature '{val_str}' not supported by message: '{patient_message}'. Discarding.")
                return None

        # C. Cough Validation
        elif field == "cough":
            if not any(k in lower_msg for k in ["cough", "khansi", "khasi", "gale", "throat", "खांसी", "खाँसी"]):
                logger.warning(f"[GroundingReject] Cough fact '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # D. Chills Validation
        elif field == "chills":
            if not any(k in lower_msg for k in ["thand", "chills", "shivering", "kampkampi", "kanpkampi", "ठंड", "कंपकंपी"]):
                logger.warning(f"[GroundingReject] Chills fact '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # E. Associated Symptoms Validation
        elif field == "associated_symptoms":
            if not any(k in lower_msg for k in ["sweat", "pasina", "breathless", "saans", "ghabrahat", "palpitat", "body ache", "badan dard", "nausea", "ulti", "पसीना", "सांस", "घबराहट", "बदन"]):
                logger.warning(f"[GroundingReject] Associated symptoms '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # F. Trigger Validation
        elif field == "trigger":
            if not any(k in lower_msg for k in ["walk", "walking", "chalne", "chalte", "exertion", "mehnat", "stairs", "sidhiya", "rest", "aaram", "चलने", "आराम", "मेहनत"]):
                logger.warning(f"[GroundingReject] Trigger '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # G. Location Validation
        elif field == "location":
            if not any(k in lower_msg for k in ["left", "right", "center", "centre", "beech", "side", "taraf", "forehead", "mathe", "lower", "upper", "बाईं", "दाईं", "बीच", "sir", "sar", "pet", "kamar", "seene", "chest"]):
                logger.warning(f"[GroundingReject] Location '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # H. Headache Character Validation
        elif field == "headache_character":
            if not any(k in lower_msg for k in ["throbbing", "pulsat", "dhadak", "sharp", "tez", "light", "roshni", "sound", "aawaz", "noise", "photo", "धड़कता", "रोशनी", "आवाज़"]):
                logger.warning(f"[GroundingReject] Headache character '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # I. Vomiting Validation
        elif field == "vomiting":
            if not any(k in lower_msg for k in ["vomit", "ulti", "nausea", "matli", "michlana", "उल्टी", "मिचलाना"]):
                logger.warning(f"[GroundingReject] Vomiting '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # J. Bowel Symptoms Validation
        elif field == "bowel_symptoms":
            if not any(k in lower_msg for k in ["motion", "stools", "dast", "diarrhea", "kabz", "constipation", "दस्त", "कब्ज", "कब्ज़"]):
                logger.warning(f"[GroundingReject] Bowel symptoms '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # K. Radiation Validation
        elif field == "radiation":
            if not any(k in lower_msg for k in ["leg", "pair", "thigh", "hand", "arm", "shoot", "spread", "radiat", "पैर", "हाथ"]):
                logger.warning(f"[GroundingReject] Radiation '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # L. Movement Effect Validation
        elif field == "movement_effect":
            if not any(k in lower_msg for k in ["bend", "jhuk", "sit", "baith", "walk", "chal", "lie", "lying", "letne", "rest", "aaram", "झुकने", "बैठने", "लेटने"]):
                logger.warning(f"[GroundingReject] Movement effect '{val_str}' not present in message: '{patient_message}'. Discarding.")
                return None

        # 3. Status Adjustments for Uncertainty / Unknown
        new_status = fact.status
        if any(u in lower_msg for u in ["pata nahi", "patta nahi", "yaad nahi", "malum nahi", "don't know", "dont know", "not sure", "no idea"]):
            if field == "duration" and ("din" in lower_msg or "kitne" in lower_msg or "kab" in lower_msg or "how" in lower_msg or "time" in lower_msg):
                new_status = "unknown"
                val_str = "Unknown"
        elif any(unc in lower_msg for unc in ["shayad", "maybe", "approx", "lagbhag", "लगभग", "शायद", "around", "probably"]):
            new_status = "uncertain"

        return LLMExtractedFact(
            field_name=field,
            value=val_str,
            evidence=fact.evidence,
            status=new_status,
            confidence=fact.confidence,
        )

    def extract_facts(
        self,
        message: str,
        language: str = "hi",
        current_topic: Optional[str] = None,
        known_facts: Optional[Dict[str, str]] = None,
        allowed_fields: Optional[List[str]] = None,
    ) -> LLMExtractedFactsResult:
        start_time = time.time()
        logger.info(f"[GeminiAIProvider] extract_facts called (topic={current_topic}, lang={language})")

        # Always run deterministic extractor first as baseline
        deterministic_map = extract_facts_from_message(message, current_topic=current_topic)

        if not self._client:
            logger.info("[GeminiAIProvider] Client unavailable; returning deterministic facts fallback.")
            return self._build_result_from_deterministic(deterministic_map, allowed_fields)

        prompt_context = {
            "conversation_language": language,
            "current_topic": current_topic,
            "patient_message": message,
            "known_facts": known_facts or {},
            "allowed_fields": allowed_fields or [],
        }

        user_prompt = f"""Context and Patient Message:
{json.dumps(prompt_context, ensure_ascii=False, indent=2)}

Extract all clinical facts present in the patient message. Follow the schema strictly. Provide verbatim evidence for each fact."""

        try:
            from google.genai import types

            response = None
            models_to_try = [self.model_name]
            if "gemini-flash-latest" not in models_to_try:
                models_to_try.append("gemini-flash-latest")
            if "gemini-3.1-flash-lite-preview" not in models_to_try:
                models_to_try.append("gemini-3.1-flash-lite-preview")

            last_exc = None
            for m in models_to_try:
                try:
                    response = self._client.models.generate_content(
                        model=m,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=CLINICAL_EXTRACTION_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            response_schema=LLMExtractedFactsResult,
                            temperature=0.0,
                        ),
                    )
                    if response:
                        self.model_name = m
                        break
                except Exception as e:
                    last_exc = e
                    continue

            if not response:
                if last_exc:
                    raise last_exc
                return self._build_result_from_deterministic(deterministic_map, allowed_fields)

            latency = time.time() - start_time
            logger.info(f"[GeminiAIProvider] Extraction succeeded using {self.model_name} in {latency:.2f}s")

            parsed_result: Optional[LLMExtractedFactsResult] = None
            if response.parsed and isinstance(response.parsed, LLMExtractedFactsResult):
                parsed_result = response.parsed
            elif response.text:
                raw_json = json.loads(response.text)
                parsed_result = LLMExtractedFactsResult.model_validate(raw_json)

            if parsed_result:
                # Strictly validate and ground Gemini facts against patient message
                validated_gemini_facts: List[LLMExtractedFact] = []
                for fact in parsed_result.facts:
                    validated_fact = self._validate_and_ground_fact(fact, message)
                    if validated_fact:
                        validated_gemini_facts.append(validated_fact)

                grounded_result = LLMExtractedFactsResult(facts=validated_gemini_facts)
                return self._merge_facts(grounded_result, deterministic_map, allowed_fields, patient_message=message)
            else:
                logger.warning("[GeminiAIProvider] Empty response from Gemini. Falling back to deterministic.")
                return self._build_result_from_deterministic(deterministic_map, allowed_fields)

        except Exception as exc:
            latency = time.time() - start_time
            logger.warning(
                f"[GeminiAIProvider] Gemini extraction failed ({type(exc).__name__}: {exc}) in {latency:.2f}s. "
                "Activating deterministic fallback."
            )
            return self._build_result_from_deterministic(deterministic_map, allowed_fields)

    def generate_question(
        self,
        topic: str,
        language: str = "hi",
        patient_name: Optional[str] = None,
        known_facts: Optional[Dict[str, str]] = None,
        fallback_template: str = "",
    ) -> str:
        if not self._client or topic == "completion":
            return fallback_template

        start_time = time.time()
        prompt_payload = {
            "target_topic": topic,
            "target_language": "Hindi" if language == "hi" else "English",
            "patient_name": patient_name,
            "known_facts": known_facts or {},
            "default_reference_question": fallback_template,
        }

        user_prompt = f"""Inquire about the target topic in a natural, polite manner for the patient:
{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}"""

        try:
            from google.genai import types

            response = None
            models_to_try = [self.model_name]
            if "gemini-flash-latest" not in models_to_try:
                models_to_try.append("gemini-flash-latest")
            if "gemini-3.1-flash-lite-preview" not in models_to_try:
                models_to_try.append("gemini-3.1-flash-lite-preview")

            for m in models_to_try:
                try:
                    response = self._client.models.generate_content(
                        model=m,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=QUESTION_GENERATION_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            response_schema=LLMQuestionResult,
                            temperature=0.3,
                        ),
                    )
                    if response:
                        self.model_name = m
                        break
                except Exception:
                    continue

            latency = time.time() - start_time
            if response and response.parsed and isinstance(response.parsed, LLMQuestionResult):
                logger.info(f"[GeminiAIProvider] Natural question generated using {self.model_name} in {latency:.2f}s")
                return response.parsed.question_text.strip()
            elif response and response.text:
                raw_json = json.loads(response.text)
                q_res = LLMQuestionResult.model_validate(raw_json)
                logger.info(f"[GeminiAIProvider] Natural question generated using {self.model_name} in {latency:.2f}s")
                return q_res.question_text.strip()
        except Exception as exc:
            logger.warning(
                f"[GeminiAIProvider] Question generation failed ({type(exc).__name__}: {exc}). Using template fallback."
            )

        return fallback_template

    def generate_summary(
        self,
        patient_data: dict,
        clinical_facts: list,
    ) -> str:
        return "Gemini Clinical Summary: Pre-consultation briefing recorded."

    def generate_narrative_summary(
        self,
        doctor_summary_data: Any,
    ) -> Any:
        from backend.app.services.summary_service import generate_deterministic_narrative

        if not self._client:
            logger.info("[GeminiAIProvider] Client unavailable for narrative summary. Using deterministic fallback.")
            return generate_deterministic_narrative(doctor_summary_data)

        start_time = time.time()
        try:
            from google.genai import types

            summary_dict = (
                doctor_summary_data.model_dump(mode="json")
                if hasattr(doctor_summary_data, "model_dump")
                else doctor_summary_data
            )
            user_prompt = f"""Organize the following validated clinical intake records into a clean, concise, doctor-readable narrative summary for pre-consultation review:

{json.dumps(summary_dict, ensure_ascii=False, indent=2)}

Adhere strictly to the DoctorNarrativeSummary schema and all clinical safety and zero-hallucination rules."""

            response = None
            models_to_try = [self.model_name]
            if "gemini-flash-latest" not in models_to_try:
                models_to_try.append("gemini-flash-latest")
            if "gemini-3.1-flash-lite-preview" not in models_to_try:
                models_to_try.append("gemini-3.1-flash-lite-preview")

            for m in models_to_try:
                try:
                    response = self._client.models.generate_content(
                        model=m,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=DOCTOR_SUMMARY_NARRATIVE_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            response_schema=DoctorNarrativeSummary,
                            temperature=0.0,
                        ),
                    )
                    if response:
                        self.model_name = m
                        break
                except Exception as e:
                    logger.warning(f"[GeminiAIProvider] Model {m} failed for narrative generation: {e}")
                    continue

            latency = time.time() - start_time

            parsed_summary: Optional[DoctorNarrativeSummary] = None
            if response and response.parsed and isinstance(response.parsed, DoctorNarrativeSummary):
                parsed_summary = response.parsed
            elif response and response.text:
                raw_json = json.loads(response.text)
                parsed_summary = DoctorNarrativeSummary.model_validate(raw_json)

            if parsed_summary:
                logger.info(f"[GeminiAIProvider] Doctor narrative generated successfully using {self.model_name} in {latency:.2f}s")
                expected_pid = (
                    doctor_summary_data.patient_snapshot.patient_id
                    if hasattr(doctor_summary_data, "patient_snapshot")
                    else ""
                )
                if expected_pid and parsed_summary.patient_id != expected_pid:
                    parsed_summary.patient_id = expected_pid

                expected_flags = (
                    doctor_summary_data.priority_flags
                    if hasattr(doctor_summary_data, "priority_flags")
                    else []
                )
                if not expected_flags and (
                    "priority" in parsed_summary.priority_flags.lower()
                    or "urgent" in parsed_summary.priority_flags.lower()
                ):
                    parsed_summary.priority_flags = "- None"
                elif expected_flags and parsed_summary.priority_flags.strip() in ["- None", "None"]:
                    parsed_summary.priority_flags = "\n".join([f"- {f}" for f in expected_flags])

                if not parsed_summary.verification_note:
                    parsed_summary.verification_note = "AI-assisted pre-consultation intake summary. Doctor verification required before clinical decision making."

                return parsed_summary
            else:
                logger.warning("[GeminiAIProvider] Empty response from Gemini for narrative summary. Using deterministic fallback.")
                return generate_deterministic_narrative(doctor_summary_data)

        except Exception as exc:
            latency = time.time() - start_time
            logger.warning(
                f"[GeminiAIProvider] Narrative generation failed ({type(exc).__name__}: {exc}) in {latency:.2f}s. "
                "Falling back to deterministic narrative."
            )
            return generate_deterministic_narrative(doctor_summary_data)

    def _merge_facts(
        self,
        gemini_result: LLMExtractedFactsResult,
        deterministic_map: Dict[str, tuple],
        allowed_fields: Optional[List[str]],
        patient_message: str = "",
    ) -> LLMExtractedFactsResult:
        """Merge validated Gemini facts with deterministic facts."""
        merged_facts: Dict[str, LLMExtractedFact] = {}

        # 1. Add validated Gemini facts
        for fact in gemini_result.facts:
            if allowed_fields and fact.field_name not in allowed_fields:
                continue
            merged_facts[fact.field_name] = fact

        # 2. Add or reconcile deterministic facts
        for field_name, (val, status) in deterministic_map.items():
            if allowed_fields and field_name not in allowed_fields:
                continue

            fact_status = status if status in ["confirmed", "unknown", "denied", "uncertain"] else "confirmed"

            if field_name not in merged_facts:
                merged_facts[field_name] = LLMExtractedFact(
                    field_name=field_name,
                    value=val,
                    status=fact_status,
                    confidence=0.95 if fact_status == "confirmed" else 0.8,
                )
            else:
                existing_fact = merged_facts[field_name]
                if existing_fact.confidence < 0.5 and fact_status == "confirmed":
                    merged_facts[field_name] = LLMExtractedFact(
                        field_name=field_name,
                        value=val,
                        status=fact_status,
                        confidence=0.95,
                    )

        return LLMExtractedFactsResult(facts=list(merged_facts.values()))

    def _build_result_from_deterministic(
        self, deterministic_map: Dict[str, tuple], allowed_fields: Optional[List[str]]
    ) -> LLMExtractedFactsResult:
        facts: List[LLMExtractedFact] = []
        for field_name, (value, status) in deterministic_map.items():
            if allowed_fields and field_name not in allowed_fields:
                continue
            fact_status = status if status in ["confirmed", "unknown", "denied", "uncertain"] else "confirmed"
            facts.append(
                LLMExtractedFact(
                    field_name=field_name,
                    value=value,
                    status=fact_status,
                    confidence=0.95 if fact_status == "confirmed" else 0.8,
                )
            )
        return LLMExtractedFactsResult(facts=facts)

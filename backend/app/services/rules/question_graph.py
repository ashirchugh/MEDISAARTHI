"""Question Graph and Deterministic Adaptive Pathways for Medisaarthi Pre-Consultation Engine.

Defines the required clinical topic sequence, conditional branching logic, and bilingual question templates
for the supported demo complaints:
1. chest_pain
2. fever
3. headache
4. abdominal_pain
5. back_pain

The Question Graph is deterministic and authoritative. Gemini never decides medical pathways.
"""
from typing import Dict, List, Optional, Any

# Base topics for each complaint in standard intake order
BASE_COMPLAINT_TOPICS: Dict[str, List[str]] = {
    "chest_pain": [
        "chief_complaint",
        "duration",
        "location",
        "severity",
        "trigger",
        "associated_symptoms",
    ],
    "fever": [
        "chief_complaint",
        "duration",
        "temperature",
        "chills",
        "cough",
    ],
    "headache": [
        "chief_complaint",
        "duration",
        "location",
        "severity",
        "headache_character",
        "associated_symptoms",
    ],
    "abdominal_pain": [
        "chief_complaint",
        "duration",
        "location",
        "severity",
        "vomiting",
        "bowel_symptoms",
    ],
    "back_pain": [
        "chief_complaint",
        "duration",
        "location",
        "severity",
        "radiation",
        "movement_effect",
    ],
}

# Alias for backward compatibility
COMPLAINT_TOPICS = BASE_COMPLAINT_TOPICS

# Fallback generic topics if complaint is not yet classified
DEFAULT_TOPICS: List[str] = [
    "chief_complaint",
    "duration",
    "severity",
    "associated_symptoms",
]

# Bilingual question templates
QUESTION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "chief_complaint": {
        "en": "What brings you to the hospital today?",
        "hi": "नमस्ते। आपको आज किस वजह से अस्पताल आना पड़ा?",
    },
    "duration": {
        "en": "How long have you been experiencing this problem?",
        "hi": "यह समस्या आपको कब से हो रही है?",
    },
    "location": {
        "en": "Where exactly do you feel the pain or discomfort?",
        "hi": "आपको यह तकलीफ़ ठीक कहाँ महसूस हो रही है?",
    },
    "severity": {
        "en": "On a scale from 1 to 10, how severe is the pain or discomfort?",
        "hi": "1 से 10 के पैमाने पर यह तकलीफ़ कितनी ज़्यादा है?",
    },
    "trigger": {
        "en": "Does physical exertion or walking trigger or worsen the chest pain?",
        "hi": "क्या चलने-फिरने या मेहनत करने पर सीने का दर्द बढ़ जाता है?",
    },
    "associated_symptoms": {
        "en": "Are you experiencing any other symptoms, such as breathlessness, sweating, or nausea?",
        "hi": "क्या आपको इसके साथ सांस लेने में दिक्कत, पसीना या घबराहट महसूस हो रही है?",
    },
    "temperature": {
        "en": "Did you measure your body temperature at home, and was it high?",
        "hi": "क्या आपने बुखार नापा था और तापमान कितना दर्ज हुआ था?",
    },
    "chills": {
        "en": "Are you experiencing chills or shivering with the fever?",
        "hi": "क्या बुखार के साथ ठंड या कंपकंपी महसूस हो रही है?",
    },
    "cough": {
        "en": "Do you have a cough, sore throat, or difficulty breathing?",
        "hi": "क्या आपको खांसी, गले में ख़राश या सांस लेने में तकलीफ़ है?",
    },
    "respiratory_symptoms": {
        "en": "Do you have any phlegm/sputum with the cough, or difficulty breathing?",
        "hi": "क्या खांसी के साथ बलगम आ रहा है या सांस लेने में परेशानी हो रही है?",
    },
    "headache_character": {
        "en": "Is the headache throbbing or sharp, and does bright light or noise make it worse?",
        "hi": "क्या सिर में धड़कता हुआ दर्द है और क्या तेज़ रोशनी या आवाज़ से तकलीफ़ बढ़ती है?",
    },
    "vomiting": {
        "en": "Are you feeling nauseous or having vomiting along with stomach pain?",
        "hi": "क्या पेट दर्द के साथ उल्टी या जी मिचलाने जैसी तकलीफ़ हो रही है?",
    },
    "bowel_symptoms": {
        "en": "Have you experienced loose stools, constipation, or changes in bowel habits?",
        "hi": "क्या दस्त, कब्ज़ या पेट साफ़ होने में कोई बदलाव आया है?",
    },
    "radiation": {
        "en": "Does the back pain radiate or shoot down into your legs or hips?",
        "hi": "क्या पीठ का दर्द नीचे पैरों या कूल्हों की तरफ़ जाता है?",
    },
    "numbness_or_weakness": {
        "en": "Do you feel any numbness, tingling, or weakness in your legs or feet?",
        "hi": "क्या पैरों में सुन्नपन, झनझनाहट या कमजोरी महसूस हो रही है?",
    },
    "movement_effect": {
        "en": "Does bending, prolonged sitting, or walking worsen the back pain?",
        "hi": "क्या झुकने, ज़्यादा देर बैठने या चलने से पीठ का दर्द बढ़ता है?",
    },
    "completion": {
        "en": "Thank you. All your pre-consultation information has been recorded for your doctor.",
        "hi": "धन्यवाद। आपकी सभी आवश्यक जानकारियाँ डॉक्टर के लिए सुरक्षित रूप से दर्ज कर ली गई हैं।",
    },
}

COMPLAINT_SYNONYMS = {
    "stomach_pain": "abdominal_pain",
    "belly_pain": "abdominal_pain",
    "pet_dard": "abdominal_pain",
    "lower_back_pain": "back_pain",
    "kamar_dard": "back_pain",
    "peeth_dard": "back_pain",
    "sar_dard": "headache",
    "sir_dard": "headache",
    "head_pain": "headache",
    "bukhar": "fever",
    "seene_mein_dard": "chest_pain",
}


def _extract_val_and_status(fact_obj: Any) -> tuple:
    """Helper to extract (value, status) from a dict, object, or string."""
    if hasattr(fact_obj, "value") and hasattr(fact_obj, "status"):
        return str(fact_obj.value), str(fact_obj.status)
    elif isinstance(fact_obj, dict):
        return str(fact_obj.get("value", "")), str(fact_obj.get("status", "confirmed"))
    elif isinstance(fact_obj, tuple) and len(fact_obj) == 2:
        return str(fact_obj[0]), str(fact_obj[1])
    else:
        return str(fact_obj or ""), "confirmed"


def _is_fact_present(fact_obj: Any) -> bool:
    """Return True if the fact was reported as present/confirmed (not denied/Absent)."""
    val, status = _extract_val_and_status(fact_obj)
    if status == "denied":
        return False
    val_lower = val.lower().strip()
    if val_lower in ["absent", "none", "none reported", "no", "nahi", "नहीं", "no cough", "no vomiting"]:
        return False
    return bool(val_lower)


def get_required_topics(
    complaint: Optional[str],
    known_facts: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Return the adaptively planned list of required topics for a given complaint,
    dynamically evaluating clinical pathways and follow-up relevance based on
    symptoms already confirmed or denied by the patient.
    """
    if not complaint:
        return DEFAULT_TOPICS

    clean_complaint = complaint.lower().strip().replace(" ", "_")
    canonical = COMPLAINT_SYNONYMS.get(clean_complaint, clean_complaint)

    base = list(BASE_COMPLAINT_TOPICS.get(canonical, DEFAULT_TOPICS))
    facts = known_facts or {}

    # Adaptive Branching Rules
    if canonical == "fever":
        # 1. Respiratory Pathway:
        # If cough is present or mentioned, branch into respiratory follow-up (sputum/breathlessness)
        cough_fact = facts.get("cough")
        has_cough = cough_fact is not None and _is_fact_present(cough_fact)
        cough_denied = cough_fact is not None and not _is_fact_present(cough_fact)

        # 2. GI Pathway:
        # If GI symptoms (vomiting, abdominal pain, nausea) are reported during fever
        vomiting_fact = facts.get("vomiting")
        has_vomiting = vomiting_fact is not None and _is_fact_present(vomiting_fact)
        assoc_val, _ = _extract_val_and_status(facts.get("associated_symptoms", ""))
        has_gi_mention = has_vomiting or any(
            w in assoc_val.lower() for w in ["pet", "stomach", "abdomen", "vomit", "ulti", "nausea", "dast", "loose motion"]
        )

        planned_topics = ["chief_complaint", "duration", "temperature", "chills", "cough"]

        if has_cough:
            # Add respiratory follow-up
            planned_topics.append("respiratory_symptoms")

        if has_gi_mention:
            # Branch into GI follow-ups
            if "vomiting" not in planned_topics:
                planned_topics.append("vomiting")
            if "bowel_symptoms" not in planned_topics:
                planned_topics.append("bowel_symptoms")

        # If no specific respiratory or GI branch was taken, ask general associated symptoms
        if not has_cough and not has_gi_mention:
            planned_topics.append("associated_symptoms")

        return planned_topics

    elif canonical == "chest_pain":
        planned_topics = list(base)
        # If location or facts suggest radiation to arm/jaw, ensure radiation is checked
        loc_val, _ = _extract_val_and_status(facts.get("location", ""))
        if any(w in loc_val.lower() for w in ["arm", "left side", "jaw", "neck", "shoulder"]):
            if "radiation" not in planned_topics:
                planned_topics.append("radiation")
        return planned_topics

    elif canonical == "back_pain":
        planned_topics = list(base)
        # If radiation to legs is confirmed present, branch into neurological check (numbness/weakness)
        rad_fact = facts.get("radiation")
        if rad_fact is not None and _is_fact_present(rad_fact):
            if "numbness_or_weakness" not in planned_topics:
                planned_topics.append("numbness_or_weakness")
        return planned_topics

    elif canonical == "abdominal_pain":
        planned_topics = list(base)
        # If fever or chills mentioned with abdominal pain, add temperature check
        assoc_val, _ = _extract_val_and_status(facts.get("associated_symptoms", ""))
        if any(w in assoc_val.lower() for w in ["fever", "bukhar", "chills", "thand"]):
            if "temperature" not in planned_topics:
                planned_topics.append("temperature")
        return planned_topics

    elif canonical == "headache":
        return list(base)

    return base


def get_question_template(topic: str, language: str = "hi") -> str:
    """Retrieve the deterministic question string for a topic in English or Hindi."""
    lang_key = "hi" if language.lower().startswith("hi") else "en"
    topic_templates = QUESTION_TEMPLATES.get(topic, {})
    return topic_templates.get(
        lang_key,
        topic_templates.get("en", f"Please provide information regarding {topic}."),
    )

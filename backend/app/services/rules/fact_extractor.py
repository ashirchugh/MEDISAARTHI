"""Deterministic Fact Extractor for Medisaarthi Pre-Consultation Engine.

Extracts structured clinical facts from English, Hindi (Devanagari & Romanized Hinglish) patient expressions.
Designed to be deterministic, safe, and easily testable without external LLM dependencies.
"""
import re
from typing import Dict, Optional, Tuple, List

# Uncertainty detection expressions (Hindi / Hinglish / English)
UNCERTAINTY_PATTERNS = [
    r"\bi\s*don'?t\s*know\b",
    r"\bnot\s*sure\b",
    r"\bno\s*idea\b",
    r"\bpata\s*nahi\b",
    r"\bpatta\s*nahi\b",
    r"\bपता\s*नहीं\b",
    r"\bmalum\s*nahi\b",
    r"\bmaaloom\s*nahi\b",
    r"\bमालूम\s*नहीं\b",
    r"\byaad\s*nahi\b",
    r"\bयाद\s*नहीं\b",
    r"\bsamajh\s*nahi\b",
    r"\bcannot\s*say\b",
    r"\bcan'?t\s*say\b",
]

# Complaint keyword mappings
COMPLAINT_PATTERNS = {
    "chest_pain": [
        r"\bchest\s*pain\b",
        r"\bseene\s*m(?:ein|e)\s*dard\b",
        r"\bसीने\s*में\s*दर्द\b",
        r"\bchhati\s*m(?:ein|e)\s*dard\b",
        r"\bछाती\s*में\s*दर्द\b",
        r"\bchest\s*tightness\b",
        r"\bchest\s*pressure\b",
        r"\bheart\s*pain\b",
        r"\bseena\s*dard\b",
        r"\bchhati\s*dard\b",
    ],
    "fever": [
        r"\bfever\b",
        r"\bbukhar\b",
        r"\bbukhaar\b",
        r"\bबुखार\b",
        r"\btapman\b",
        r"\bतापमान\b",
        r"\bpyrexia\b",
        r"\bhigh\s*temp\b",
        r"\bhararat\b",
    ],
    "headache": [
        r"\bheadache\b",
        r"\bsir\s*dard\b",
        r"\bsar\s*dard\b",
        r"\bसिर\s*दर्द\b",
        r"\bसर\s*दर्द\b",
        r"\bmigraine\b",
        r"\bमाइग्रेन\b",
        r"\bmatha\s*dard\b",
        r"\bsir\s*m(?:ein|e)\s*dard\b",
        r"\bsar\s*m(?:ein|e)\s*dard\b",
        r"\bhead\s*pain\b",
    ],
    "abdominal_pain": [
        r"\babdominal\s*pain\b",
        r"\bstomach\s*pain\b",
        r"\bstomach\s*ache\b",
        r"\bbelly\s*pain\b",
        r"\bpet\s*dard\b",
        r"\bपेट\s*दर्द\b",
        r"\bpet\s*m(?:ein|e)\s*dard\b",
        r"\bपेट\s*में\s*दर्द\b",
        r"\bpet\s*kharaab\b",
        r"\bbelly\s*ache\b",
    ],
    "back_pain": [
        r"\bback\s*pain\b",
        r"\bkam[a]?r\s*dard\b",
        r"\bकमर\s*दर्द\b",
        r"\bpeeth\s*dard\b",
        r"\bपीठ\s*दर्द\b",
        r"\blower\s*back\b",
        r"\bspine\s*pain\b",
        r"\bkam[a]?r\s*m(?:ein|e)\s*dard\b",
        r"\bकमर\s*में\s*दर्द\b",
    ],
}

# Number words mapping (Hindi / English)
NUMBER_WORDS = {
    "one": 1, "ek": 1, "एक": 1,
    "two": 2, "do": 2, "दो": 2,
    "three": 3, "teen": 3, "tin": 3, "तीन": 3,
    "four": 4, "chaar": 4, "char": 4, "चार": 4,
    "five": 5, "paanch": 5, "panch": 5, "पांच": 5, "पाँच": 5,
    "six": 6, "chhah": 6, "che": 6, "छह": 6,
    "seven": 7, "saat": 7, "sat": 7, "सात": 7,
    "eight": 8, "aath": 8, "ath": 8, "आठ": 8,
    "nine": 9, "nau": 9, "नौ": 9,
    "ten": 10, "das": 10, "dus": 10, "दस": 10,
}


def is_uncertainty_response(text: str) -> bool:
    """Detect if the patient expressed uncertainty / lack of knowledge."""
    lower_text = text.lower().strip()
    for pat in UNCERTAINTY_PATTERNS:
        if re.search(pat, lower_text):
            return True
    return False


def extract_chief_complaint(text: str) -> Optional[str]:
    """Identify chief complaint key from text."""
    lower_text = text.lower()
    for complaint_key, patterns in COMPLAINT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, lower_text):
                return complaint_key
    return None


def extract_duration(text: str) -> Optional[str]:
    """Extract duration string (e.g., '3 days', '24 hours', '2 weeks')."""
    lower_text = text.lower()

    # Match numeric duration: e.g. "3 days", "3 din se", "4 दिनों से", "24 hours", "2 hafte"
    m_num = re.search(
        r"(\d+)\s*(days?|din|dino|dinoñ|ghante|hours?|weeks?|hafte|months?|mahine|mahina|दिन|दिनों|घंटे|घण्टे|हफ्ते|हफ़्ते|महीने|महीना)",
        lower_text,
    )
    if m_num:
        num = m_num.group(1)
        unit_raw = m_num.group(2)
        if unit_raw in ["din", "dino", "dinoñ", "day", "days", "दिन", "दिनों"]:
            unit = "days" if int(num) != 1 else "day"
        elif unit_raw in ["ghante", "hour", "hours", "घंटे", "घण्टे"]:
            unit = "hours" if int(num) != 1 else "hour"
        elif unit_raw in ["hafte", "week", "weeks", "हफ्ते", "हफ़्ते"]:
            unit = "weeks" if int(num) != 1 else "week"
        elif unit_raw in ["mahine", "mahina", "month", "months", "महीने", "महीना"]:
            unit = "months" if int(num) != 1 else "month"
        else:
            unit = unit_raw
        return f"{num} {unit}"

    # Match word numbers: e.g. "teen din se", "three days", "दो हफ्ते से"
    for word, num in NUMBER_WORDS.items():
        pat = rf"\b{word}\s*(days?|din|dino|ghante|hours?|weeks?|hafte|months?|mahine|दिन|दिनों|घंटे|हफ्ते|महीने)\b"
        m_word = re.search(pat, lower_text)
        if m_word:
            unit_raw = m_word.group(1)
            unit = "days" if unit_raw in ["din", "dino", "day", "days", "दिन", "दिनों"] else (
                "hours" if unit_raw in ["ghante", "hour", "घंटे"] else (
                    "weeks" if unit_raw in ["hafte", "week", "हफ्ते"] else "months"
                )
            )
            return f"{num} {unit}"

    # Match special time indicators
    if re.search(r"\b(since\s*yesterday|kal\s*se|कल\s*से)\b", lower_text):
        return "1 day (Since yesterday)"
    if re.search(r"\b(today\s*morning|aaj\s*subah\s*se|आज\s*सुबह\s*से)\b", lower_text):
        return "Since this morning"

    return None


def extract_severity(text: str) -> Optional[str]:
    """Extract pain/symptom severity rating from 1 to 10."""
    lower_text = text.lower()

    # Reject if text is solely referencing temperature/fever degree without severity scale context
    if re.search(r"\b(degrees?|deg|°f|°c|tapman|bukhar|तापमान)\b", lower_text) and not re.search(r"\b(scale|severity|rating|out\s*of|/10|आउट\s*ऑफ)\b", lower_text):
        return None

    # Explicit scale: "8/10", "8 out of 10", "scale 8", "severity 8", "8 आउट ऑफ 10"
    m_scale = re.search(r"\b(\d+)\s*(?:\/\s*10|out\s*of\s*10|out\s*of\s*ten|आउट\s*ऑफ\s*10)\b", lower_text)
    if m_scale:
        val = int(m_scale.group(1))
        if 1 <= val <= 10:
            return str(val)

    # Check if text mentions severity context: "severity is 8", "दर्द 7 है", "scale par lagbhag 8"
    m_context = re.search(r"\b(?:severity|scale|पैमाने|rating|दर्द|pain)\s*(?:par|pe|is|=|:)?\s*(?:lagbhag|approx|around|शायद)?\s*(\d+)\b", lower_text)
    if m_context:
        val = int(m_context.group(1))
        if 1 <= val <= 10:
            return str(val)

    # Qualitative severity keywords
    if re.search(r"\b(severe|bahut\s*tez|bahut\s*zyada|unbearable|bahut\s*dard)\b", lower_text) or any(k in lower_text for k in ["बहुत तेज़", "असहनीय"]):
        return "8"
    if re.search(r"\b(moderate|madhyam|beech\s*ka)\b", lower_text) or "मध्यम" in lower_text:
        return "5"
    if re.search(r"\b(mild|halka|thoda)\b", lower_text) or "हल्का" in lower_text:
        return "3"

    # If the text is ONLY a standalone number (e.g. "8" or "7 out of 10"), accept it
    cleaned_tokens = re.findall(r"\b\w+\b", lower_text)
    if len(cleaned_tokens) <= 3:
        for tok in cleaned_tokens:
            if tok.isdigit():
                val = int(tok)
                if 1 <= val <= 10:
                    return str(val)
            if tok in NUMBER_WORDS:
                return str(NUMBER_WORDS[tok])

    return None


def extract_location(text: str) -> Optional[str]:
    """Extract location of pain or discomfort."""
    lower_text = text.lower()
    if re.search(r"\b(center|centre|beech\s*m(?:ein|e)|central|substernal)\b", lower_text) or "बीच में" in lower_text:
        return "Center"
    if re.search(r"\b(left\s*side|bai\s*taraf|left\s*chest|left\s*arm)\b", lower_text) or "बाईं तरफ" in lower_text:
        return "Left side"
    if re.search(r"\b(right\s*side|dayi\s*taraf|right\s*lower|right\s*iliac)\b", lower_text) or "दाईं तरफ" in lower_text:
        return "Right lower abdomen" if ("pet" in lower_text or "abdomen" in lower_text or "पेट" in lower_text) else "Right side"
    if re.search(r"\b(forehead|mathe\s*p(?:ar|e)|head|one\s*side\s*of\s*head|half\s*head)\b", lower_text) or any(k in lower_text for k in ["माथे", "माथा"]):
        return "Unilateral / Forehead"
    if re.search(r"\b(lower\s*back|niche\s*kamar|lumber|spine)\b", lower_text) or "निचली कमर" in lower_text:
        return "Lower lumbar back"
    return None


def extract_trigger(text: str) -> Optional[str]:
    """Extract trigger/aggravating factors."""
    lower_text = text.lower()
    if re.search(r"\b(walk|walking|chalne\s*par|chalte\s*waqt|exertion|mehnat|stairs|sidhiya)\b", lower_text) or any(k in lower_text for k in ["चलने", "मेहनत"]):
        return "Physical exertion / Walking"
    if re.search(r"\b(rest|aaram\s*karne\s*par)\b", lower_text) or "आराम" in lower_text:
        return "Relieved by rest"
    return None


def extract_temperature(text: str) -> Optional[str]:
    """Extract recorded temperature."""
    lower_text = text.lower()
    # Match explicit numeric degree readings: 101.8 F, 102 degrees, 100.4°F, 102 F
    m_temp = re.search(r"\b(\d{2,3}(?:\.\d)?)\s*(?:degrees?|deg|f|c|°f|°c|डिग्री|बुखार)?\b", lower_text)
    if m_temp:
        try:
            val = float(m_temp.group(1))
            if 95.0 <= val <= 108.0:
                return f"{val}°F"
        except ValueError:
            pass

    # High grade fever terms if explicitly referencing fever temperature
    if re.search(r"\b(high\s*grade|high\s*temp|102\s*degree|101\s*degree)\b", lower_text) or any(k in lower_text for k in ["तेज़ तापमान", "हाई फीवर", "102 डिग्री"]):
        return "High grade (Recorded at home)"
    return None


def extract_chills(text: str) -> Optional[str]:
    """Extract chills and shivering presence."""
    lower_text = text.lower()
    if re.search(r"\b(yes|haan|chills|thand|shivering|kampkampi|kanpkampi)\b", lower_text) or any(k in lower_text for k in ["हाँ", "हा", "ठंड", "कंपकंपी"]):
        return "Present (Chills and rigors)"
    if re.search(r"\b(no\s*chills|chills\s*nahi|thand\s*nahi)\b", lower_text) or any(k in lower_text for k in ["ठंड नहीं", "कंपकंपी नहीं"]):
        return "Absent"
    return None


def extract_cough(text: str) -> Optional[str]:
    """Extract cough & respiratory symptoms."""
    lower_text = text.lower()
    if re.search(r"\b(cough|khansi|khasi|dry\s*cough|sukhi\s*khansi)\b", lower_text) or any(k in lower_text for k in ["खांसी", "खाँसी", "सूखी खांसी"]):
        return "Dry cough" if ("dry" in lower_text or "sukhi" in lower_text or "सूखी" in lower_text) else "Cough present"
    if re.search(r"\b(sore\s*throat|gale\s*m(?:ein|e)\s*kharash)\b", lower_text) or "गले में खराश" in lower_text:
        return "Sore throat"
    if re.search(r"\b(no\s*cough|khansi\s*nahi)\b", lower_text) or any(k in lower_text for k in ["खांसी नहीं", "खाँसी नहीं"]):
        return "Absent"
    return None


def extract_headache_character(text: str) -> Optional[str]:
    """Extract migraine/headache characteristics."""
    lower_text = text.lower()
    if re.search(r"\b(throbbing|dhadakta|pulsating|pulsing|धड़कता)\b", lower_text):
        return "Pulsating / Throbbing"
    if re.search(r"\b(light\s*sensitivity|photophobia|roshni|aawaz|noise|रोशनी|आवाज़)\b", lower_text):
        return "Photophobia & Phonophobia"
    if re.search(r"\b(sharp|tez|तेज़)\b", lower_text):
        return "Sharp"
    return None


def extract_vomiting(text: str) -> Optional[str]:
    """Extract vomiting / nausea facts."""
    lower_text = text.lower()
    if re.search(r"\b(vomiting|ulti|vomit|haan\s*ulti|उल्टी)\b", lower_text):
        return "Vomiting present"
    if re.search(r"\b(nausea|ji\s*michlana|matli|ulti\s*jaisa|जी\s*मिचलाना)\b", lower_text):
        return "Nausea present (No vomiting)"
    if re.search(r"\b(no\s*vomiting|ulti\s*nahi)\b", lower_text) or any(k in lower_text for k in ["उल्टी नहीं", "जी नहीं मिचला"]):
        return "Absent"
    return None


def extract_bowel_symptoms(text: str) -> Optional[str]:
    """Extract bowel irregularity facts."""
    lower_text = text.lower()
    if re.search(r"\b(loose\s*motion|loose\s*stools|dast|diarrhea|दस्त)\b", lower_text):
        return "Loose stools / Diarrhea"
    if re.search(r"\b(constipation|kabz|कब्ज़|कब्ज)\b", lower_text):
        return "Constipation"
    if re.search(r"\b(normal|theek\s*hai|koi\s*badlav\s*nahi|no\s*issue|सामान्य|ठीक\s*है)\b", lower_text):
        return "Normal bowel habits"
    return None


def extract_radiation(text: str) -> Optional[str]:
    """Extract pain radiation to extremities."""
    lower_text = text.lower()
    if re.search(r"\b(leg|pair|thigh|shoots\s*down|left\s*leg|niche\s*pair|पैर|पैरों)\b", lower_text):
        return "Radiates to left leg"
    if re.search(r"\b(no\s*radiation|kahi\s*nahi\s*jata|only\s*back|sirf\s*kamar|कहीं\s*नहीं)\b", lower_text):
        return "Localized (No radiation)"
    return None


def extract_movement_effect(text: str) -> Optional[str]:
    """Extract mechanical movement effect."""
    lower_text = text.lower()
    if re.search(r"\b(bending|jhukne|sitting|baithne|walking|chalne|झुकने|बैठने|चलने)\b", lower_text):
        return "Worsens with bending / prolonged sitting"
    if re.search(r"\b(lying\s*down|letne\s*par|rest|लेटने|आराम)\b", lower_text):
        return "Relieved by lying down"
    return None


def extract_associated_symptoms(text: str) -> Optional[str]:
    """Extract breathlessness, sweating, palpitations, etc."""
    lower_text = text.lower()
    found: List[str] = []
    if re.search(r"\b(breathless|shortness\s*of\s*breath|saans\s*lene\s*m(?:ein|e)\s*dikkat|saans\s*phulna|सांस\s*लेने\s*में\s*दिक्कत|सांस\s*फूलना)\b", lower_text):
        found.append("Breathlessness on exertion")
    if re.search(r"\b(sweat|sweating|pasina|diaphoresis|पसीना)\b", lower_text):
        found.append("Diaphoresis (Sweating)")
    if re.search(r"\b(palpitation|palpitations|ghabrahat|heart\s*racing|घबराहट)\b", lower_text):
        found.append("Palpitations")
    if re.search(r"\b(badan\s*dard|body\s*ache|बदन\s*दर्द|बदन\s*में\s*दर्द)\b", lower_text):
        found.append("Generalized body ache")
    if re.search(r"\b(nausea|ulti\s*jaisa|vomiting|ulti|उल्टी)\b", lower_text):
        found.append("Nausea")
    if found:
        return ", ".join(found)
    if re.search(r"\b(no|nahi|kuch\s*aur\s*nahi|none|nothing\s*else|नहीं|कुछ\s*नहीं)\b", lower_text):
        return "None reported"
    return None


def extract_respiratory_symptoms(text: str) -> Optional[str]:
    """Extract sputum/phlegm or breathlessness."""
    lower_text = text.lower()
    if re.search(r"\b(no\s*sputum|no\s*balgam|balgam\s*nahi|saans\s*nahi|nahi\s*hai|kuch\s*nahi|only\s*dry|sirf\s*sukhi)\b", lower_text) or any(k in lower_text for k in ["बलगम नहीं", "सांस की तकलीफ़ नहीं", "नहीं है", "नहीं"]):
        if not re.search(r"\b(haan|yes|productive)\b", lower_text) and not any(k in lower_text for k in ["हाँ", "हां"]):
            return "Absent"
    found: List[str] = []
    if re.search(r"\b(sputum|phlegm|balgam|khankhar)\b", lower_text) or any(k in lower_text for k in ["बलगम", "कफ"]):
        if not re.search(r"\b(balgam\s*nahi|no\s*balgam)\b", lower_text) and "बलगम नहीं" not in lower_text:
            found.append("Productive sputum")
    if re.search(r"\b(breathless|shortness\s*of\s*breath|saans\s*phulna|saans\s*lene)\b", lower_text) or "सांस फूलना" in lower_text:
        if not re.search(r"\b(saans\s*nahi|no\s*breathless)\b", lower_text) and "सांस की तकलीफ़ नहीं" not in lower_text:
            found.append("Shortness of breath")
    if re.search(r"\b(sore\s*throat|kharash|gale\s*m(?:ein|e)|throat\s*pain)\b", lower_text) or "खराश" in lower_text:
        found.append("Sore throat")
    if found:
        return ", ".join(found)
    return None


def extract_numbness_or_weakness(text: str) -> Optional[str]:
    """Extract neurological numbness, tingling, or motor weakness."""
    lower_text = text.lower()
    found: List[str] = []
    if re.search(r"\b(numb|numbness|sunn|sunnpan|सुन्न|सुन्नपन)\b", lower_text):
        found.append("Numbness in lower extremities")
    if re.search(r"\b(tingling|pins\s*and\s*needles|jhanjhanahat|झनझनाहट)\b", lower_text):
        found.append("Tingling sensation")
    if re.search(r"\b(weak|weakness|kamzori|kamjori|कमजोरी)\b", lower_text):
        found.append("Motor weakness")
    if found:
        return ", ".join(found)
    if re.search(r"\b(no|nahi|koi\s*sunnpan\s*nahi|nahi\s*hai|नहीं)\b", lower_text):
        return "No numbness or weakness"
    return None


# Dispatcher map from topic name to specialized extractor function
TOPIC_EXTRACTORS = {
    "chief_complaint": extract_chief_complaint,
    "duration": extract_duration,
    "severity": extract_severity,
    "location": extract_location,
    "trigger": extract_trigger,
    "temperature": extract_temperature,
    "chills": extract_chills,
    "cough": extract_cough,
    "respiratory_symptoms": extract_respiratory_symptoms,
    "headache_character": extract_headache_character,
    "vomiting": extract_vomiting,
    "bowel_symptoms": extract_bowel_symptoms,
    "radiation": extract_radiation,
    "numbness_or_weakness": extract_numbness_or_weakness,
    "movement_effect": extract_movement_effect,
    "associated_symptoms": extract_associated_symptoms,
}


def extract_facts_from_message(
    message: str, current_topic: Optional[str] = None
) -> Dict[str, Tuple[str, str]]:
    """Extract clinical facts from patient message.

    Returns:
        Dict mapping field_name -> (value, status)
        where status is 'confirmed' or 'unknown'.
    """
    extracted: Dict[str, Tuple[str, str]] = {}
    cleaned_message = message.strip()
    if not cleaned_message:
        return extracted

    # 1. Global extraction passes for key universal fields
    complaint = extract_chief_complaint(cleaned_message)
    if complaint:
        extracted["chief_complaint"] = (complaint, "confirmed")

    # Check for duration and duration uncertainty/approximation
    lower_msg = cleaned_message.lower()
    has_duration_uncertainty = bool(
        re.search(
            r"\b(?:pata|patta|malum|maaloom|yaad|don'?t\s*know|not\s*sure|no\s*idea)\s*(?:nahi|नहीं)?\s*(?:kitne|kitna|kab|how|how\s*many|since\s*when)\s*(?:din|dino|days?|ghante|hours?|hafte|weeks?|mahine|months?|se|time|when)?\b",
            lower_msg,
        )
        or re.search(
            r"\b(?:kitne|kitna|kab|how\s*many)\s*(?:din|dino|days?|ghante|hours?|hafte|weeks?|mahine|months?)\s*(?:se)?\s*(?:pata|patta|malum|yaad|maloom)\s*nahi\b",
            lower_msg,
        )
    )

    if has_duration_uncertainty or (current_topic == "duration" and is_uncertainty_response(cleaned_message)):
        extracted["duration"] = ("Unknown", "unknown")
    elif re.search(r"\b(shayad|maybe|approx|approximately|around|probably|lagbhag|लगभग|शायद)\b", lower_msg):
        dur = extract_duration(cleaned_message)
        if dur:
            extracted["duration"] = (f"Approximately {dur}", "uncertain")
        elif "hafte" in lower_msg or "week" in lower_msg:
            extracted["duration"] = ("Approximately 1 week", "uncertain")
        elif "din" in lower_msg or "day" in lower_msg:
            extracted["duration"] = ("Approximately a few days", "uncertain")
    else:
        duration = extract_duration(cleaned_message)
        if duration:
            extracted["duration"] = (duration, "confirmed")

    # If message is purely an uncertainty response without a complaint
    if is_uncertainty_response(cleaned_message) and not complaint:
        if current_topic and current_topic not in extracted:
            extracted[current_topic] = ("Unknown / Patient uncertain", "unknown")
        return extracted

    # Extract severity globally if explicit context exists or current_topic is severity
    sev = extract_severity(cleaned_message)
    if sev:
        if current_topic == "severity" or re.search(r"\b(scale|severity|rating|out\s*of|/10|आउट\s*ऑफ)\b", lower_msg):
            extracted["severity"] = (sev, "confirmed")

    # 2. Topic-guided extraction if current_topic is expected
    if current_topic and current_topic in TOPIC_EXTRACTORS and current_topic not in extracted:
        extractor_fn = TOPIC_EXTRACTORS[current_topic]
        res = extractor_fn(cleaned_message)
        if res:
            extracted[current_topic] = (res, "confirmed")
        elif current_topic == "temperature" and re.search(r"\b(high|tez|तेज़|तेज|bahut|बहुत|not\s*measured|नापा\s*नहीं)\b", cleaned_message.lower()):
            extracted[current_topic] = ("High grade (Uncalibrated)", "confirmed")

    # 3. Check other specific extractors if mentioned in multi-fact statements
    for topic_name in ["temperature", "location", "trigger", "chills", "cough", "vomiting", "bowel_symptoms", "radiation", "movement_effect", "associated_symptoms"]:
        if topic_name not in extracted:
            fn = TOPIC_EXTRACTORS[topic_name]
            val = fn(cleaned_message)
            if val:
                extracted[topic_name] = (val, "confirmed")

    return extracted

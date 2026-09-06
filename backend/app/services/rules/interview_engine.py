"""Pre-Consultation Interview Engine for Medisaarthi.

Manages conversational state, topic transitions, database persistence of facts and dialogue turns,
and coordinates with AI providers for natural language extraction and question generation while
strictly enforcing the Question Graph state machine.
"""
from datetime import datetime
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.interview import Interview
from backend.app.models.interview_message import InterviewMessage
from backend.app.models.clinical_fact import ClinicalFact
from backend.app.services.rules.question_graph import (
    get_required_topics,
    get_question_template,
)
from backend.app.services.ai.base import AIProvider
from backend.app.services.ai import get_ai_provider

logger = logging.getLogger(__name__)


class ExtractedFactResult:
    def __init__(self, field_name: str, value: str, status: str = "confirmed"):
        self.field_name = field_name
        self.value = value
        self.status = status


class InterviewStepResult:
    def __init__(
        self,
        interview_id: str,
        status: str,
        received_message: str,
        extracted_facts: List[ExtractedFactResult],
        current_topic: str,
        next_question: Dict[str, str],
        interview_completed: bool = False,
    ):
        self.interview_id = interview_id
        self.status = status
        self.received_message = received_message
        self.extracted_facts = extracted_facts
        self.current_topic = current_topic
        self.next_question = next_question
        self.interview_completed = interview_completed


def process_patient_response(
    db: Session,
    interview_id: str,
    message: str,
    ai_provider: Optional[AIProvider] = None,
) -> InterviewStepResult:
    """Process an incoming patient message during an active interview session."""
    # 1. Fetch and validate interview session
    stmt = select(Interview).where(Interview.interview_id.ilike(interview_id.strip()))
    interview = db.scalars(stmt).first()

    if not interview:
        raise ValueError(f"Interview session '{interview_id}' not found.")

    if interview.status != "active":
        raise ValueError(
            f"Interview session '{interview_id}' is already {interview.status} and cannot receive new messages."
        )

    # 2. Store patient message in conversation history
    clean_message = message.strip()
    patient_msg = InterviewMessage(
        interview_id=interview.interview_id,
        role="patient",
        text=clean_message,
        language=interview.language,
        timestamp=datetime.utcnow(),
    )
    db.add(patient_msg)
    db.flush()

    # 3. Fetch existing clinical facts for this active session
    stmt_facts = select(ClinicalFact).where(
        ClinicalFact.interview_id == interview.interview_id
    )
    existing_facts = db.scalars(stmt_facts).all()
    existing_facts_map = {f.field_name: f for f in existing_facts}

    # 4. Resolve active provider and required topics
    provider = ai_provider or get_ai_provider()
    chief_complaint_val: Optional[str] = (
        existing_facts_map["chief_complaint"].value
        if "chief_complaint" in existing_facts_map
        else None
    )
    allowed_fields = (
        get_required_topics(chief_complaint_val, existing_facts_map)
        if chief_complaint_val
        else None
    )

    # 5. Extract structured facts via AI Provider (with deterministic fallback)
    known_facts_dict = {k: v.value for k, v in existing_facts_map.items()}
    extraction_result = provider.extract_facts(
        message=clean_message,
        language=interview.language,
        current_topic=interview.current_topic,
        known_facts=known_facts_dict,
        allowed_fields=allowed_fields,
    )

    # 6. Persist newly extracted facts into PostgreSQL (with conflict handling)
    new_extracted_results: List[ExtractedFactResult] = []
    for fact in extraction_result.facts:
        field_name = fact.field_name
        value = fact.value
        fact_status = fact.status
        confidence = fact.confidence

        if field_name in existing_facts_map:
            existing_fact = existing_facts_map[field_name]
            # If incoming fact has low confidence and existing is confirmed, preserve existing
            if confidence < 0.5 and existing_fact.status == "confirmed":
                logger.info(
                    f"Preserving existing confirmed fact '{field_name}' over low confidence incoming value."
                )
            else:
                existing_fact.value = value
                existing_fact.status = fact_status
                existing_fact.confidence = confidence
        else:
            new_fact = ClinicalFact(
                interview_id=interview.interview_id,
                patient_id=interview.patient_id,
                field_name=field_name,
                value=value,
                source="current_interview",
                confidence=confidence,
                status=fact_status,
            )
            db.add(new_fact)
            existing_facts_map[field_name] = new_fact

        new_extracted_results.append(
            ExtractedFactResult(field_name=field_name, value=value, status=fact_status)
        )

    db.flush()

    # 7. Re-evaluate Chief Complaint and Question Graph State with updated facts
    if "chief_complaint" in existing_facts_map:
        chief_complaint_val = existing_facts_map["chief_complaint"].value

    required_topics = get_required_topics(chief_complaint_val, existing_facts_map)

    # 8. Find next missing topic in Question Graph
    next_topic: Optional[str] = None
    for topic in required_topics:
        if topic not in existing_facts_map:
            next_topic = topic
            break

    interview_completed = False
    if next_topic is None:
        # All required topics answered -> Mark completed
        interview_completed = True
        next_topic = "completion"
        question_text = get_question_template("completion", interview.language)
        interview.current_topic = "completion"
        interview.status = "completed"
        interview.completed_at = datetime.utcnow()
    else:
        # Generate conversational wording using AI Provider with template fallback
        fallback_text = get_question_template(next_topic, interview.language)
        patient_name = interview.patient.name if interview.patient else None
        known_facts_for_q = {k: v.value for k, v in existing_facts_map.items()}

        question_text = provider.generate_question(
            topic=next_topic,
            language=interview.language,
            patient_name=patient_name,
            known_facts=known_facts_for_q,
            fallback_template=fallback_text,
        )
        interview.current_topic = next_topic

    # 9. Store assistant response in interview_messages
    assistant_msg = InterviewMessage(
        interview_id=interview.interview_id,
        role="assistant",
        text=question_text,
        language=interview.language,
        timestamp=datetime.utcnow(),
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(interview)

    return InterviewStepResult(
        interview_id=interview.interview_id,
        status=interview.status,
        received_message=clean_message,
        extracted_facts=new_extracted_results,
        current_topic=next_topic,
        next_question={"text": question_text, "type": "text"},
        interview_completed=interview_completed,
    )

from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.models.patient import Patient
from backend.app.models.interview import Interview
from backend.app.models.interview_message import InterviewMessage
from backend.app.schemas.interview import (
    InterviewResponse,
    InitialQuestion,
    InterviewRespondResponse,
    ExtractedFactItem,
    NextQuestion,
)
from backend.app.services.rules.interview_engine import process_patient_response


def start_interview(db: Session, patient_id: str, language: str = "hi") -> InterviewResponse:
    """Initialize an interview session and generate the initial intake greeting."""
    # Verify patient exists
    stmt_patient = select(Patient).where(Patient.patient_id.ilike(patient_id.strip()))
    patient = db.scalars(stmt_patient).first()
    if not patient:
        raise ValueError(f"Patient with ID '{patient_id}' not found")

    # Generate sequential or unique interview ID (e.g. INT001, INT002...)
    count_stmt = select(func.count(Interview.id))
    current_count = db.scalar(count_stmt) or 0
    interview_id = f"INT{current_count + 1:03d}"

    # Determine initial question text based on language and patient name
    if language.lower() == "hi":
        question_text = f"नमस्ते {patient.name} जी। आपको किस वजह से अस्पताल आना पड़ा?"
    else:
        question_text = f"Hello {patient.name}. What brings you to the hospital today?"

    # Create Interview database record
    interview = Interview(
        interview_id=interview_id,
        patient_id=patient.patient_id,
        status="active",
        language=language.lower(),
        current_topic="chief_complaint",
        started_at=datetime.utcnow(),
    )
    db.add(interview)
    db.flush()

    # Store initial AI message in interview_messages table
    initial_msg = InterviewMessage(
        interview_id=interview_id,
        role="assistant",
        text=question_text,
        language=language.lower(),
        timestamp=datetime.utcnow(),
    )
    db.add(initial_msg)
    db.commit()
    db.refresh(interview)

    return InterviewResponse(
        interview_id=interview.interview_id,
        patient_id=interview.patient_id,
        status=interview.status,
        language=interview.language,
        started_at=interview.started_at,
        initial_question=InitialQuestion(text=question_text, type="text"),
    )


def respond_to_interview(
    db: Session, interview_id: str, message: str
) -> InterviewRespondResponse:
    """Process a patient turn and generate the next interview question."""
    step_result = process_patient_response(
        db=db, interview_id=interview_id, message=message
    )

    extracted_items = [
        ExtractedFactItem(
            field_name=f.field_name,
            value=f.value,
            status=f.status,
        )
        for f in step_result.extracted_facts
    ]

    return InterviewRespondResponse(
        interview_id=step_result.interview_id,
        status=step_result.status,
        received_message=step_result.received_message,
        extracted_facts=extracted_items,
        current_topic=step_result.current_topic,
        next_question=NextQuestion(
            text=step_result.next_question["text"],
            type=step_result.next_question.get("type", "text"),
        ),
        interview_completed=step_result.interview_completed,
    )


def get_interview(db: Session, interview_id: str) -> Optional[Interview]:
    """Retrieve an interview record with messages by ID."""
    stmt = select(Interview).where(Interview.interview_id.ilike(interview_id.strip()))
    return db.scalars(stmt).first()


def add_interview_message(
    db: Session, interview_id: str, role: str, text: str, language: str = "hi"
) -> InterviewMessage:
    """Append a conversational message to an existing interview session."""
    msg = InterviewMessage(
        interview_id=interview_id,
        role=role,
        text=text,
        language=language,
        timestamp=datetime.utcnow(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

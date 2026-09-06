import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.schemas.interview import (
    InterviewStartRequest,
    InterviewResponse,
    InterviewRespondRequest,
    InterviewRespondResponse,
    InterviewVoiceResponse,
    InterviewDetailResponse,
    InterviewMessageResponse,
    InterviewCompleteRequest,
    InterviewCompleteResponse,
)
from backend.app.services.interview_service import (
    start_interview,
    respond_to_interview,
    get_interview,
)
from backend.app.services.ai.stt.factory import get_stt_provider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Interviews"])

MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit for MVP
ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "video/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/ogg",
    "audio/aac",
}


@router.post(
    "/interview/start",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a pre-consultation interview session",
)
def start_interview_endpoint(
    request: InterviewStartRequest, db: Session = Depends(get_db)
):
    """Create an interview session for a patient and return the initial intake question."""
    try:
        response = start_interview(
            db=db, patient_id=request.patient_id, language=request.language
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize interview session: {str(e)}",
        )


@router.post(
    "/interview/respond",
    response_model=InterviewRespondResponse,
    status_code=status.HTTP_200_OK,
    summary="Process patient response and determine next clinical question",
)
def respond_interview_endpoint(
    request: InterviewRespondRequest, db: Session = Depends(get_db)
):
    """Process incoming patient answer, extract structured clinical facts, and return the next question."""
    try:
        response = respond_to_interview(
            db=db,
            interview_id=request.interview_id,
            message=request.message,
        )
        return response
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process interview response: {str(e)}",
        )


@router.post(
    "/interview/{interview_id}/voice",
    response_model=InterviewVoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload patient spoken audio, transcribe via STT, and progress the interview",
)
async def respond_interview_voice_endpoint(
    interview_id: str,
    audio: UploadFile = File(..., description="Uploaded audio file stream"),
    db: Session = Depends(get_db),
):
    """Voice interaction endpoint: transcribes spoken audio into verbatim text and routes to the interview engine."""
    # 1. Validate interview exists
    interview = get_interview(db, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID '{interview_id}' not found.",
        )

    # 2. Validate interview is active
    if interview.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview '{interview_id}' is already completed. Cannot process voice responses.",
        )

    # 3. Validate audio file format
    content_type = (audio.content_type or "audio/webm").split(";")[0].strip().lower()
    if content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported audio format '{audio.content_type}'. "
                "Supported formats: audio/webm, audio/wav, audio/mpeg, audio/mp4, audio/ogg."
            ),
        )

    # 4. Read and validate audio file payload
    try:
        audio_bytes = await audio.read()
    except Exception as read_exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read audio stream: {str(read_exc)}",
        )

    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty (0 bytes). Please record a valid response.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio file size exceeds maximum limit of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    # 5. Transcribe audio via STT Provider
    stt_provider = get_stt_provider()
    try:
        transcript = stt_provider.transcribe(
            audio_bytes=audio_bytes,
            mime_type=content_type,
            language=interview.language or "hi",
        )
    except Exception as stt_exc:
        logger.error(f"[VoiceEndpoint] STT transcription failed: {stt_exc}")
        err_msg = str(stt_exc).lower()
        if "429" in err_msg or "quota" in err_msg or "too_many_requests" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini transcription quota exceeded. Please wait and try again.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Speech transcription failed. Please speak clearly or use text input.",
        )

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Speech could not be recognized. Please try speaking again or type your answer.",
        )

    # 6. Pass verbatim transcript into the EXISTING interview response service
    try:
        respond_result = respond_to_interview(
            db=db,
            interview_id=interview_id,
            message=transcript.strip(),
        )
    except ValueError as val_err:
        error_msg = str(val_err)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as resp_exc:
        logger.error(f"[VoiceEndpoint] Interview processing failed: {resp_exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process clinical interview response: {str(resp_exc)}",
        )

    # 7. Return voice response with transcript and next adaptive question
    return InterviewVoiceResponse(
        interview_id=respond_result.interview_id,
        status=respond_result.status,
        transcript=transcript.strip(),
        received_message=respond_result.received_message,
        extracted_facts=respond_result.extracted_facts,
        current_topic=respond_result.current_topic,
        next_question=respond_result.next_question,
        interview_completed=respond_result.interview_completed,
    )


@router.get(
    "/interview/{interview_id}",
    response_model=InterviewDetailResponse,
    summary="Retrieve interview status and history",
)
def get_interview_endpoint(interview_id: str, db: Session = Depends(get_db)):
    """Fetch an active or completed interview session with conversation history."""
    interview = get_interview(db, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID '{interview_id}' not found",
        )
    return InterviewDetailResponse(
        interview_id=interview.interview_id,
        patient_id=interview.patient_id,
        status=interview.status,
        language=interview.language,
        current_topic=interview.current_topic,
        started_at=interview.started_at,
        completed_at=interview.completed_at,
        messages=[
            InterviewMessageResponse(
                id=m.id,
                interview_id=m.interview_id,
                role=m.role,
                text=m.text,
                language=m.language,
                timestamp=m.timestamp,
            )
            for m in (interview.messages or [])
        ],
    )


@router.post(
    "/interview/complete",
    response_model=InterviewCompleteResponse,
    summary="Explicitly complete an interview session",
)
def complete_interview_endpoint(
    request: InterviewCompleteRequest, db: Session = Depends(get_db)
):
    """Mark an interview session as completed."""
    interview = get_interview(db, request.interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview with ID '{request.interview_id}' not found",
        )
    interview.status = "completed"
    if not interview.completed_at:
        interview.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(interview)
    return InterviewCompleteResponse(
        interview_id=interview.interview_id,
        status=interview.status,
        completed_at=interview.completed_at,
    )

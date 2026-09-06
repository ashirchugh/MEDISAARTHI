from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class LLMExtractedFact(BaseModel):
    field_name: str = Field(
        ...,
        description="Standard clinical field name, e.g., 'chief_complaint', 'duration', 'severity', 'location', 'trigger', 'temperature', 'chills', 'cough', 'vomiting', 'bowel_symptoms', 'radiation', 'movement_effect', 'associated_symptoms'",
    )
    value: str = Field(
        ...,
        description="Extracted value or patient statement",
    )
    evidence: Optional[str] = Field(
        None,
        description="Exact quote or phrase from the patient message providing evidence for this fact",
    )
    status: Literal["confirmed", "unknown", "denied", "uncertain"] = Field(
        default="confirmed",
        description="Clinical fact status: confirmed, unknown, denied, or uncertain",
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )

    model_config = ConfigDict(from_attributes=True)


class LLMExtractedFactsResult(BaseModel):
    facts: List[LLMExtractedFact] = Field(
        default_factory=list,
        description="List of clinical facts extracted from the patient message",
    )

    model_config = ConfigDict(from_attributes=True)


class LLMQuestionResult(BaseModel):
    question_text: str = Field(
        ...,
        description="Natural patient-friendly conversational question text in the target language",
    )

    model_config = ConfigDict(from_attributes=True)

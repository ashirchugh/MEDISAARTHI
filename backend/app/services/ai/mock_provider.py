import logging
from typing import Dict, List, Optional, Any

from backend.app.services.ai.base import AIProvider
from backend.app.services.ai.schemas import LLMExtractedFact, LLMExtractedFactsResult
from backend.app.services.rules.fact_extractor import extract_facts_from_message

logger = logging.getLogger(__name__)


class MockAIProvider(AIProvider):
    """Mock AI Provider using deterministic rule-based extraction for fast, offline operation and testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def extract_facts(
        self,
        message: str,
        language: str = "hi",
        current_topic: Optional[str] = None,
        known_facts: Optional[Dict[str, str]] = None,
        allowed_fields: Optional[List[str]] = None,
    ) -> LLMExtractedFactsResult:
        logger.debug(f"[MockAIProvider] Extracting facts from message: '{message[:50]}...'")
        extracted_map = extract_facts_from_message(message, current_topic=current_topic)
        facts: List[LLMExtractedFact] = []

        for field_name, (value, status) in extracted_map.items():
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

    def generate_question(
        self,
        topic: str,
        language: str = "hi",
        patient_name: Optional[str] = None,
        known_facts: Optional[Dict[str, str]] = None,
        fallback_template: str = "",
    ) -> str:
        logger.debug(f"[MockAIProvider] Generating question for topic='{topic}', lang='{language}'")
        return fallback_template

    def generate_summary(
        self,
        patient_data: dict,
        clinical_facts: list,
    ) -> str:
        return "Mock Clinical Summary: Pre-consultation information recorded."

    def generate_narrative_summary(
        self,
        doctor_summary_data: Any,
    ) -> Any:
        from backend.app.services.summary_service import generate_deterministic_narrative

        return generate_deterministic_narrative(doctor_summary_data)

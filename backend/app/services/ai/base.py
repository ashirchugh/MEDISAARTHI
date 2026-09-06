from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from backend.app.services.ai.schemas import LLMExtractedFactsResult


class AIProvider(ABC):
    """Abstract interface for AI language understanding and generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'mock', 'gemini')."""
        pass

    @abstractmethod
    def extract_facts(
        self,
        message: str,
        language: str = "hi",
        current_topic: Optional[str] = None,
        known_facts: Optional[Dict[str, str]] = None,
        allowed_fields: Optional[List[str]] = None,
    ) -> LLMExtractedFactsResult:
        """Extract structured clinical facts from patient message.

        Args:
            message: Patient raw text response.
            language: Active conversation language ('hi' or 'en').
            current_topic: Topic currently being inquired about.
            known_facts: Dictionary of already collected clinical facts.
            allowed_fields: Whitelist of valid field names for this flow.

        Returns:
            LLMExtractedFactsResult containing list of validated facts.
        """
        pass

    @abstractmethod
    def generate_question(
        self,
        topic: str,
        language: str = "hi",
        patient_name: Optional[str] = None,
        known_facts: Optional[Dict[str, str]] = None,
        fallback_template: str = "",
    ) -> str:
        """Generate conversational wording for the next clinical topic decided by Question Graph.

        Args:
            topic: Clinical topic decided by Question Graph.
            language: Active language ('hi' or 'en').
            patient_name: Patient's name for personalization.
            known_facts: Known clinical facts for context.
            fallback_template: Deterministic question template to fall back on.

        Returns:
            Natural question string.
        """
        pass

    @abstractmethod
    def generate_summary(
        self,
        patient_data: dict,
        clinical_facts: list,
    ) -> str:
        """Generate clinical doctor summary from collected facts (legacy signature)."""
        pass

    @abstractmethod
    def generate_narrative_summary(
        self,
        doctor_summary_data: Any,
    ) -> Any:
        """Generate structured DoctorNarrativeSummary from validated DoctorSummaryData."""
        pass


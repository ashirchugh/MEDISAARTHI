from typing import Optional
from backend.app.core.config import settings
from backend.app.services.ai.base import AIProvider
from backend.app.services.ai.mock_provider import MockAIProvider
from backend.app.services.ai.gemini_provider import GeminiAIProvider


def get_ai_provider(provider_name: Optional[str] = None) -> AIProvider:
    """Factory function to retrieve the configured AIProvider."""
    name = (provider_name or settings.AI_PROVIDER).lower().strip()
    if name == "gemini":
        return GeminiAIProvider()
    return MockAIProvider()


__all__ = ["AIProvider", "MockAIProvider", "GeminiAIProvider", "get_ai_provider"]

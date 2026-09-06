import logging
from typing import Optional
from backend.app.core.config import settings
from backend.app.services.ai.stt.base import STTProvider
from backend.app.services.ai.stt.gemini_transcribe import GeminiSTTProvider
from backend.app.services.ai.stt.mock_provider import MockSTTProvider

logger = logging.getLogger(__name__)

_stt_provider_instance: Optional[STTProvider] = None


def get_stt_provider(provider_type: Optional[str] = None) -> STTProvider:
    """Factory function to get the configured Speech-to-Text provider."""
    global _stt_provider_instance

    chosen_type = (provider_type or settings.STT_PROVIDER or "mock").lower().strip()

    if _stt_provider_instance is not None:
        if _stt_provider_instance.provider_name == chosen_type:
            return _stt_provider_instance

    if chosen_type == "gemini":
        if settings.effective_gemini_api_key:
            _stt_provider_instance = GeminiSTTProvider()
        else:
            logger.warning(
                "[STTFactory] STT_PROVIDER='gemini' requested, but no GEMINI_API_KEY was found. "
                "Falling back to MockSTTProvider."
            )
            _stt_provider_instance = MockSTTProvider()
    elif chosen_type == "mock":
        _stt_provider_instance = MockSTTProvider()
    else:
        logger.warning(
            f"[STTFactory] Unknown STT_PROVIDER '{chosen_type}'. Defaulting to MockSTTProvider."
        )
        _stt_provider_instance = MockSTTProvider()

    return _stt_provider_instance


def reset_stt_provider():
    """Reset cached STT provider instance."""
    global _stt_provider_instance
    _stt_provider_instance = None

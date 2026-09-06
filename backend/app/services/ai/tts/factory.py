import logging
from typing import Optional
from backend.app.core.config import settings
from backend.app.services.ai.tts.base import TTSProvider
from backend.app.services.ai.tts.mock_provider import MockTTSProvider

logger = logging.getLogger(__name__)


def get_tts_provider(provider_type: Optional[str] = None) -> TTSProvider:
    """Factory function to get the configured Text-to-Speech provider.
    
    Default MVP uses browser-native window.speechSynthesis on the client side,
    with MockTTSProvider / backend fallback.
    """
    chosen_type = (provider_type or settings.TTS_PROVIDER or "browser").lower().strip()
    return MockTTSProvider()

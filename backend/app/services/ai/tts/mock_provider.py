import logging
from backend.app.services.ai.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class MockTTSProvider(TTSProvider):
    """Mock Text-to-Speech Provider returning mock audio byte buffers."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def synthesize(self, text: str, language: str = "hi") -> bytes:
        if not text or not text.strip():
            raise ValueError("Text payload is empty.")
        # Minimal synthetic header/bytes representing synthesized audio
        return b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"

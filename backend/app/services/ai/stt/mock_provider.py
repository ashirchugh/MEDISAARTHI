import logging
from typing import Dict
from backend.app.services.ai.stt.base import STTProvider

logger = logging.getLogger(__name__)


class MockSTTProvider(STTProvider):
    """Deterministic Mock Speech-to-Text Provider for testing, CI/CD, and offline verification."""

    def __init__(
        self, default_transcript: str = "Mujhe seene mein dard hai, teen din se."
    ):
        self.default_transcript = default_transcript
        self._custom_transcripts: Dict[str, str] = {}
        self._fail_next: bool = False

    @property
    def provider_name(self) -> str:
        return "mock"

    def set_transcript_for_key(self, key: str, transcript: str):
        """Map a key or audio signature to a specific transcript."""
        self._custom_transcripts[key] = transcript

    def set_fail_next(self, fail: bool = True):
        """Simulate an upstream STT failure."""
        self._fail_next = fail

    def transcribe(
        self, audio_bytes: bytes, mime_type: str = "audio/webm", language: str = "hi"
    ) -> str:
        """Return deterministic transcription matching language or configured test keys."""
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio payload is empty.")

        if self._fail_next:
            self._fail_next = False
            raise RuntimeError("Simulated STT provider upstream error.")

        # Check explicit length/language tag
        tag = f"{len(audio_bytes)}_{language}"
        if tag in self._custom_transcripts:
            return self._custom_transcripts[tag]

        # Check custom transcripts by exact text markers or custom keys
        if language == "en":
            return "I have had chest pain for three days."

        return self.default_transcript

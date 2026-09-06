from abc import ABC, abstractmethod


class STTProvider(ABC):
    """Abstract Base Class for Speech-to-Text Providers in Medisaarthi."""

    @abstractmethod
    def transcribe(
        self, audio_bytes: bytes, mime_type: str = "audio/webm", language: str = "hi"
    ) -> str:
        """Transcribe audio bytes to verbatim text in the requested language (Hindi, English, or Hinglish).
        
        Args:
            audio_bytes: Raw binary audio payload.
            mime_type: MIME format of the uploaded audio (e.g. 'audio/webm', 'audio/wav', 'audio/mpeg').
            language: Interview language ('hi' or 'en').
            
        Returns:
            Verbatim transcribed patient speech string.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique provider identifier string (e.g. 'gemini', 'mock')."""
        pass

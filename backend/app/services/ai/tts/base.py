from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Abstract Base Class for Text-to-Speech Providers in Medisaarthi."""

    @abstractmethod
    def synthesize(self, text: str, language: str = "hi") -> bytes:
        """Synthesize text into speech audio bytes.
        
        Args:
            text: Text to synthesize.
            language: Target spoken language ('hi' or 'en').
            
        Returns:
            Binary audio bytes (e.g. mp3/wav).
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

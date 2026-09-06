import logging
import os
import tempfile
import time
import requests
from typing import Optional
from backend.app.core.config import settings
from backend.app.services.ai.stt.base import STTProvider

logger = logging.getLogger(__name__)


class GeminiSTTProvider(STTProvider):
    """Google Gemini Speech-to-Text Provider using the Gemini Files API + Interactions API.
    
    Uploads audio bytes ephemerally via client.files.upload, polls until the file state reaches
    ACTIVE, creates a transcription interaction with model='gemini-3.5-transcribe', reads the
    verbatim transcript, and immediately cleans up both local and remote files via client.files.delete().
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.effective_gemini_api_key
        self.model_name = (
            model_name
            or getattr(settings, "STT_MODEL", None)
            or "gemini-3.5-transcribe"
        )
        self._client = None

        if self.api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
                logger.info(
                    f"[GeminiSTTProvider] Initialized successfully with model: {self.model_name}"
                )
            except Exception as e:
                logger.warning(
                    f"[GeminiSTTProvider] Failed to initialize google-genai client: {e}"
                )
                self._client = None
        else:
            logger.info("[GeminiSTTProvider] No API key configured. Operates in fallback mode.")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def transcribe(
        self, audio_bytes: bytes, mime_type: str = "audio/webm", language: str = "hi"
    ) -> str:
        """Transcribe audio bytes using Gemini 3.5 Transcribe via Files API + Interactions API."""
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio payload is empty.")

        if not self._client or not self.api_key:
            raise RuntimeError(
                "Gemini STT provider is not configured with an active API key."
            )

        # Map browser mime types to supported file extensions for temporary upload
        clean_mime = mime_type.split(";")[0].strip().lower()
        suffix = ".webm"
        if "wav" in clean_mime:
            suffix = ".wav"
        elif "mp3" in clean_mime or "mpeg" in clean_mime:
            suffix = ".mp3"
        elif "mp4" in clean_mime or "m4a" in clean_mime:
            suffix = ".mp4"
        elif "ogg" in clean_mime:
            suffix = ".ogg"

        temp_path = None
        uploaded_file = None

        try:
            # 1. Create temporary local file for upload
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                temp_path = tmp.name

            # 2. Upload to Gemini Files API
            uploaded_file = self._client.files.upload(file=temp_path)
            logger.info(
                f"[GeminiSTTProvider] Audio uploaded to Gemini Files API: {uploaded_file.name}"
            )

            # 3. Poll until file reaches ACTIVE state
            start_time = time.time()
            timeout_seconds = 30.0
            poll_interval = 0.5
            current_file = uploaded_file

            while True:
                state_val = getattr(current_file, "state", None)
                state_str = (state_val.name if hasattr(state_val, "name") else str(state_val)).upper()

                if "ACTIVE" in state_str:
                    logger.info(f"[GeminiSTTProvider] File {uploaded_file.name} is ACTIVE.")
                    break
                elif "FAILED" in state_str:
                    # Extract full metadata and detailed error from Gemini File object
                    file_name = getattr(current_file, "name", str(uploaded_file.name))
                    file_state = getattr(current_file, "state", "FAILED")
                    file_mime = getattr(current_file, "mime_type", mime_type)
                    file_size = getattr(current_file, "size_bytes", None) or len(audio_bytes)
                    
                    err_obj = getattr(current_file, "error", None)
                    err_code = getattr(err_obj, "code", None) or (err_obj.get("code") if isinstance(err_obj, dict) else None)
                    err_msg = getattr(err_obj, "message", None) or (err_obj.get("message") if isinstance(err_obj, dict) else (str(err_obj) if err_obj else "Unknown processing failure"))
                    err_details = getattr(err_obj, "details", None) or (err_obj.get("details") if isinstance(err_obj, dict) else None)

                    log_msg = (
                        f"[GeminiSTTProvider] Gemini File processing FAILED!\n"
                        f"  File Name: {file_name}\n"
                        f"  State: {file_state}\n"
                        f"  MIME Type: {file_mime}\n"
                        f"  Size Bytes: {file_size}\n"
                        f"  Error Code: {err_code}\n"
                        f"  Error Message: {err_msg}\n"
                        f"  Error Details: {err_details}\n"
                        f"  Full Error Object: {repr(err_obj)}"
                    )
                    logger.error(log_msg)
                    print(log_msg, flush=True)

                    raise RuntimeError(
                        f"Gemini File processing failed ({file_name}): {err_msg} (code: {err_code}, details: {err_details})"
                    )

                if time.time() - start_time > timeout_seconds:
                    raise TimeoutError(
                        f"Timed out waiting for audio file {uploaded_file.name} to reach ACTIVE state (last state: {state_str})."
                    )

                time.sleep(poll_interval)
                current_file = self._client.files.get(name=uploaded_file.name)

            # 4. Create transcription interaction with gemini-3.5-transcribe
            url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={self.api_key}"
            payload = {
                "model": self.model_name,
                "input": [
                    {
                        "type": "audio",
                        "uri": current_file.uri if hasattr(current_file, "uri") else uploaded_file.uri,
                        "mime_type": current_file.mime_type if hasattr(current_file, "mime_type") else uploaded_file.mime_type,
                    }
                ],
            }

            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 429:
                logger.warning(
                    f"[GeminiSTTProvider] Rate limited / quota exceeded (HTTP 429): {resp.text}"
                )
                raise RuntimeError(
                    f"Gemini transcription quota exceeded (HTTP 429): {resp.text}"
                )

            if resp.status_code != 200:
                raise RuntimeError(
                    f"Gemini Interactions API error (HTTP {resp.status_code}): {resp.text}"
                )

            data = resp.json()
            transcript = ""

            # Check direct output_text or extract from steps
            if "output_text" in data and data["output_text"]:
                transcript = data["output_text"]
            elif "steps" in data:
                for step in data.get("steps", []):
                    for item in step.get("content", []):
                        if item.get("type") == "text" and item.get("text"):
                            transcript += item.get("text")

            transcript = transcript.strip().strip('`"\'').strip()
            if not transcript:
                raise ValueError("STT model returned an empty transcription response.")

            return transcript

        except Exception as exc:
            logger.error(f"[GeminiSTTProvider] Audio transcription error: {exc}")
            raise RuntimeError(f"Speech-to-Text transcription failed: {str(exc)}")

        finally:
            # Ephemeral cleanup: delete local temporary file immediately
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.debug(f"[GeminiSTTProvider] Local temp cleanup error: {e}")

            # Ephemeral cleanup: delete remote Gemini File immediately
            if uploaded_file and hasattr(uploaded_file, "name") and self._client:
                try:
                    self._client.files.delete(name=uploaded_file.name)
                    logger.info(
                        f"[GeminiSTTProvider] Cleaned up remote Gemini file: {uploaded_file.name}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[GeminiSTTProvider] Failed to delete Gemini file {uploaded_file.name}: {e}"
                    )

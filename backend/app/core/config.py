from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "Medisaarthi Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # PostgreSQL Connection URL
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/medisaarthi"

    # CORS Origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    # AI / Audio Providers (Default: Mock)
    AI_PROVIDER: str = "mock"  # "mock" or "gemini"
    AI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    STT_PROVIDER: str = "mock"
    STT_MODEL: str = "gemini-3.5-transcribe"
    STT_API_KEY: str = ""
    TTS_PROVIDER: str = "mock"
    TTS_MODEL: str = "gemini-2.5-flash"
    TTS_API_KEY: str = ""

    @property
    def effective_gemini_api_key(self) -> str:
        return self.GEMINI_API_KEY or self.AI_API_KEY

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(origin).rstrip("/") for origin in parsed]
            except Exception:
                pass
        elif isinstance(v, list):
            return [str(origin).rstrip("/") for origin in v]
        return ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()

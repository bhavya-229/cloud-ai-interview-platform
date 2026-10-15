from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Cloud AI Interview Platform"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # Security & JWT
    JWT_SECRET_KEY: str = "local-dev-jwt-secret-key-replace-in-production-abcdef123456"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # LLM / AI Configuration
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"
    INTERVIEW_QUESTION_COUNT: int = 5

    # Storage Abstraction
    UPLOAD_DIR: str = "uploads"
    STORAGE_BACKEND: str = "local"  # 'local' currently, 's3' in future cloud phase

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

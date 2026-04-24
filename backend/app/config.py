import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./maverickai.db"

    # JWT
    SECRET_KEY: str = "maverickai-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gpt-oss:120b-cloud"
    OLLAMA_CODE_MODEL: str = "gpt-oss:120b-cloud"
    OLLAMA_FAST_MODEL: str = "gpt-oss:120b-cloud"

    # n8n
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

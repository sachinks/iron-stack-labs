# config.py
"""Settings management for the LLM Gateway."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_api_key: str = "ollama"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.2:latest"
    secret_key: str = "super-secret-fallback-key-change-in-production"
    algorithm: str = "HS256"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

try:
    settings = Settings()
except Exception as e:
    # Graceful fallback instantiation
    settings = Settings(_env_file=None)

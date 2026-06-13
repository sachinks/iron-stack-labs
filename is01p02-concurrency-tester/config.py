# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = "ollama"
    openai_base_url: str = "http://localhost:11434/v1"
    model_name: str = "llama3.2"
    concurrent_users: int = 10
    requests_per_user: int = 5
    test_prompt: str = "Reply with exactly one sentence about Python."
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

try:
    settings = Settings()
except Exception as e:
    # Fallback to default configurations if env files fail
    settings = Settings(_env_file=None)

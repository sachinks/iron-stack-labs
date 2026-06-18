from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the MRL benchmarker."""
    
    # Configure Pydantic to read from a .env file and ignore unrecognised values
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_url: str = "http://127.0.0.1:11434"
    embed_model: str = "nomic-embed-text"


settings = Settings()

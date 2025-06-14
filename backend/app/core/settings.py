import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Manages application settings and secrets."""

    # Load from a .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LangSmith
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://eu.api.smith.langchain.com"
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "MediCapital Lead Engine"

    # API Keys
    GOOGLE_API_KEY: str
    BRAVE_API_KEY: str

    # Database
    DATABASE_URL: str = "sqlite:///./medicapital.db"

    # Application
    LOG_LEVEL: str = "INFO"


# Instantiate settings to be imported by other modules
settings = Settings()

# Set environment variables for LangSmith, as it's read directly by the library
os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

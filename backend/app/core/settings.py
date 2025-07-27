import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Build a path to the .env file
# The settings.py file is in backend/app/core, and the .env file is in backend/
# So we go up two levels from this file's directory.
env_path = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Manages application settings and secrets."""

    # Load from a .env file
    model_config = SettingsConfigDict(
        env_file=env_path, env_file_encoding="utf-8", extra="ignore"
    )

    # LangSmith
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://eu.api.smith.langchain.com"
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "MediCapital Lead Engine"

    # API Keys
    GOOGLE_API_KEY: str
    BRAVE_API_KEY: str
    SERPER_API_KEY: str
    TAVILY_API_KEY: str
    FIRECRAWL_API_KEY: str
    SCRAPINGDOG_API_KEY: str
    PEOPLE_DATA_LABS_API_KEY: str = ""  # Optional with default empty string
    HUNTER_IO_API_KEY: str = ""  # Optional with default empty string

    # Database - MongoDB
    MONGODB_URI: str
    MONGODB_DATABASE: str = "medicapital"
    DB_USER: str
    DB_PASSWORD: str

    # Application
    LOG_LEVEL: str = "INFO"


# Instantiate settings to be imported by other modules
settings = Settings()

# Set environment variables for LangSmith, as it's read directly by the library
os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

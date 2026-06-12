"""
config.py - Central application configuration using Pydantic Settings.
Loads all environment variables and provides typed settings throughout the app.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    # --- LLM Provider ---
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    # Default model for Groq
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    # Default model for OpenAI fallback
    OPENAI_MODEL: str = "gpt-4o-mini"

    # --- Security ---
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # --- Application ---
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    APP_NAME: str = "SenAI CRM Agentic Platform"
    APP_VERSION: str = "1.0.0"

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # --- Web Scraping ---
    SCRAPE_TIMEOUT_SECONDS: int = 10
    REPUTATION_CACHE_TTL_SECONDS: int = 3600

    # --- Agent ---
    AGENT_MAX_STEPS: int = 10
    AGENT_DRY_RUN: bool = False

    @property
    def llm_api_key(self) -> Optional[str]:
        """Return the active LLM API key (Groq preferred over OpenAI)."""
        return self.GROQ_API_KEY or self.OPENAI_API_KEY

    @property
    def llm_base_url(self) -> Optional[str]:
        """Return the base URL for the active LLM provider."""
        if self.GROQ_API_KEY:
            return "https://api.groq.com/openai/v1"
        return None  # None uses OpenAI default

    @property
    def llm_model(self) -> str:
        """Return the active model name."""
        if self.GROQ_API_KEY:
            return self.GROQ_MODEL
        return self.OPENAI_MODEL

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — call this anywhere to get config."""
    return Settings()


# Module-level singleton for convenient imports
settings = get_settings()

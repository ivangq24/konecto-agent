"""
Application Configuration Module

This module defines the application settings using Pydantic Settings, which
automatically loads configuration from environment variables and .env files.

The Settings class provides:
- API configuration (name, version, debug mode)
- OpenAI API settings (API key, model selection, embedding model)
- Database configuration (storage type, paths)
- Data paths (raw and processed data directories)
- Agent configuration (temperature, max iterations, verbosity)
- Langfuse observability settings

All settings can be overridden via environment variables or .env file.
Settings are cached using LRU cache for performance.
"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be configured via environment variables or .env file.
    Settings are validated using Pydantic and cached for performance.
    
    Attributes:
        app_name: Application name
        app_version: Application version
        debug: Enable debug mode
        openai_api_key: OpenAI API key (required)
        openai_model: OpenAI model to use for chat completions
        openai_embedding_model: OpenAI model to use for embeddings
        data_storage: Storage backend type ("chroma", "sqlite", or "memory")
        sqlite_db_path: Path to SQLite database file
        chroma_persist_directory: Directory for ChromaDB persistence
        raw_data_path: Path to raw data directory
        processed_data_path: Path to processed data directory
        agent_temperature: LLM temperature (0.0 = deterministic)
        agent_max_iterations: Maximum agent iterations
        agent_verbose: Enable verbose agent logging
        langfuse_enabled: Enable Langfuse observability
        langfuse_public_key: Langfuse public API key
        langfuse_secret_key: Langfuse secret API key
        langfuse_host: Langfuse host URL
    """
    
    # API Settings
    app_name: str = "Konecto AI Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Database Configuration
    data_storage: Literal["chroma", "sqlite", "memory"] = "sqlite"
    sqlite_db_path: str = "data/processed/actuators.db"
    chroma_persist_directory: str = "data/processed/chroma"
    
    # Data Paths
    raw_data_path: str = "data/raw"
    processed_data_path: str = "data/processed"
    
    # Agent Configuration
    agent_temperature: float = 0.0
    agent_max_iterations: int = 3
    agent_verbose: bool = False  # Set to True for debugging
    
    # Langfuse Configuration (Observability)
    # Use Langfuse Cloud for observability: https://cloud.langfuse.com
    # 1. Create a free account at https://cloud.langfuse.com
    # 2. Get your API keys from Settings → API Keys
    # 3. Configure LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in your .env
    langfuse_enabled: bool = True
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to ensure only one Settings instance is created,
    improving performance and ensuring consistency across the application.
    
    Returns:
        Settings: Cached Settings instance with loaded configuration
    """
    return Settings()


"""
Application Configuration for BioAge-X Backend API.
Uses Pydantic Settings for environment variables and paths.
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "BioAge-X"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "bioage-x-dev-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT}/data/bioage_platform.db"

    # Storage paths
    UPLOAD_DIR: Path = PROJECT_ROOT / "data" / "raw"
    PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
    EXAMPLE_DIR: Path = PROJECT_ROOT / "data" / "example"

    # External Integrations (Optional Credentials)
    NCBI_API_KEY: Optional[str] = None

    # AI Research Assistant (Optional Google Gemini Integration)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_ENABLED: bool = False

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)

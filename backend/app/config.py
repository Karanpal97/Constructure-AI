"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    app_name: str = "Constructure AI Email Assistant"
    debug: bool = False
    
    # Google OAuth settings
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "https://constructure-ai.onrender.com/auth/callback"
    
    # Frontend URL for CORS and redirects
    frontend_url: str = "https://constructure-ai.vercel.app/"
    
    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # AI Provider settings (gemini or openai)
    ai_provider: str = "gemini"  # Use "gemini" (free) or "openai" (paid)
    
    # Google Gemini settings (FREE)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    
    # OpenAI settings (PAID - optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Redis settings (optional, for production session management)
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


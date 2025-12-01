"""Pytest configuration and fixtures."""

import pytest
import os

# Set test environment variables
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def test_settings():
    """Test settings fixture."""
    from app.config import Settings
    
    return Settings(
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        jwt_secret_key="test-jwt-secret",
        openai_api_key="test-openai-key",
        frontend_url="http://localhost:3000",
    )


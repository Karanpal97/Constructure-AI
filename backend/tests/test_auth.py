"""Tests for authentication utilities."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from jose import jwt

from app.services.auth import create_jwt_token, verify_jwt_token
from app.models import UserProfile


class TestJWTOperations:
    """Tests for JWT token operations."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('app.services.auth.get_settings') as mock:
            settings = MagicMock()
            settings.jwt_secret_key = "test-secret-key"
            settings.jwt_algorithm = "HS256"
            settings.jwt_expiration_hours = 24
            mock.return_value = settings
            yield settings
    
    @pytest.fixture
    def sample_user(self):
        """Sample user profile for testing."""
        return UserProfile(
            id="user123",
            email="test@example.com",
            name="Test User",
            picture="https://example.com/pic.jpg"
        )
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock Google credentials."""
        creds = MagicMock()
        creds.token = "access_token"
        creds.refresh_token = "refresh_token"
        creds.token_uri = "https://oauth2.googleapis.com/token"
        creds.client_id = "client_id"
        creds.client_secret = "client_secret"
        creds.scopes = ["email", "profile"]
        creds.expiry = datetime.utcnow() + timedelta(hours=1)
        return creds
    
    def test_create_jwt_token(self, mock_settings, sample_user, mock_credentials):
        """Test JWT token creation."""
        token = create_jwt_token(sample_user, mock_credentials)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify payload
        payload = jwt.decode(
            token,
            mock_settings.jwt_secret_key,
            algorithms=[mock_settings.jwt_algorithm]
        )
        
        assert payload["sub"] == sample_user.id
        assert payload["email"] == sample_user.email
        assert payload["name"] == sample_user.name
    
    def test_verify_valid_token(self, mock_settings, sample_user, mock_credentials):
        """Test verifying a valid JWT token."""
        token = create_jwt_token(sample_user, mock_credentials)
        
        payload = verify_jwt_token(token)
        
        assert payload["sub"] == sample_user.id
        assert payload["email"] == sample_user.email
    
    def test_verify_expired_token(self, mock_settings):
        """Test verifying an expired token raises exception."""
        from fastapi import HTTPException
        
        # Create an expired token
        expired_payload = {
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
        }
        
        expired_token = jwt.encode(
            expired_payload,
            mock_settings.jwt_secret_key,
            algorithm=mock_settings.jwt_algorithm
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(expired_token)
        
        assert exc_info.value.status_code == 401
    
    def test_verify_invalid_token(self, mock_settings):
        """Test verifying an invalid token raises exception."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401


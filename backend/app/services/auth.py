"""Google OAuth2 authentication service."""

import structlog
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from fastapi import HTTPException, status

from app.config import get_settings
from app.models import UserProfile

logger = structlog.get_logger()

# Gmail API scopes required for email operations
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

# In-memory token storage (use Redis in production)
_token_storage: dict[str, dict] = {}


def get_oauth_flow(redirect_uri: Optional[str] = None) -> Flow:
    """Create Google OAuth2 flow."""
    settings = get_settings()
    
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri or settings.google_redirect_uri],
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri or settings.google_redirect_uri,
    )
    
    return flow


def get_authorization_url(state: Optional[str] = None) -> Tuple[str, str]:
    """Generate Google OAuth2 authorization URL."""
    flow = get_oauth_flow()
    
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    
    logger.info("Generated OAuth authorization URL", state=state)
    return authorization_url, state


async def exchange_code_for_tokens(code: str, redirect_uri: Optional[str] = None) -> Credentials:
    """Exchange authorization code for tokens."""
    try:
        flow = get_oauth_flow(redirect_uri)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        logger.info("Successfully exchanged code for tokens")
        return credentials
    except Exception as e:
        logger.error("Failed to exchange code for tokens", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google: {str(e)}"
        )


async def get_user_profile(credentials: Credentials) -> UserProfile:
    """Fetch user profile from Google."""
    try:
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        profile = UserProfile(
            id=user_info["id"],
            email=user_info["email"],
            name=user_info.get("name", user_info["email"]),
            picture=user_info.get("picture"),
        )
        
        logger.info("Fetched user profile", user_id=profile.id, email=profile.email)
        return profile
    except Exception as e:
        logger.error("Failed to fetch user profile", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user profile from Google"
        )


def create_jwt_token(user: UserProfile, credentials: Credentials) -> str:
    """Create JWT token for authenticated session."""
    settings = get_settings()
    
    expiration = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "exp": expiration,
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    # Store Google credentials for later use
    _token_storage[user.id] = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }
    
    logger.info("Created JWT token", user_id=user.id)
    return token


def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token."""
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.warning("Invalid JWT token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_google_credentials(user_id: str) -> Optional[Credentials]:
    """Retrieve stored Google credentials for a user."""
    settings = get_settings()
    
    stored = _token_storage.get(user_id)
    if not stored:
        logger.warning("No stored credentials for user", user_id=user_id)
        return None
    
    credentials = Credentials(
        token=stored["access_token"],
        refresh_token=stored["refresh_token"],
        token_uri=stored["token_uri"],
        client_id=stored["client_id"] or settings.google_client_id,
        client_secret=stored["client_secret"] or settings.google_client_secret,
        scopes=stored["scopes"],
    )
    
    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        try:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            # Update stored credentials
            _token_storage[user_id]["access_token"] = credentials.token
            _token_storage[user_id]["expiry"] = credentials.expiry.isoformat() if credentials.expiry else None
            
            logger.info("Refreshed Google credentials", user_id=user_id)
        except Exception as e:
            logger.error("Failed to refresh credentials", user_id=user_id, error=str(e))
            # Clear invalid credentials
            del _token_storage[user_id]
            return None
    
    return credentials


def revoke_user_session(user_id: str) -> bool:
    """Revoke user's session and stored credentials."""
    if user_id in _token_storage:
        del _token_storage[user_id]
        logger.info("Revoked user session", user_id=user_id)
        return True
    return False


"""Authentication routes."""

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.models import TokenResponse, UserProfile
from app.services.auth import (
    get_authorization_url,
    exchange_code_for_tokens,
    get_user_profile,
    create_jwt_token,
    verify_jwt_token,
    revoke_user_session,
    get_google_credentials,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login")
async def login():
    """Initiate Google OAuth2 login flow."""
    logger.info("Initiating OAuth login")
    
    authorization_url, state = get_authorization_url()
    
    return {
        "authorization_url": authorization_url,
        "state": state,
    }


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(None, description="State parameter for CSRF protection"),
    error: str = Query(None, description="Error from OAuth provider"),
):
    """Handle OAuth2 callback from Google."""
    settings = get_settings()
    
    if error:
        logger.warning("OAuth callback error", error=error)
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={error}",
            status_code=status.HTTP_302_FOUND,
        )
    
    try:
        # Exchange code for tokens
        credentials = await exchange_code_for_tokens(code)
        
        # Get user profile
        user = await get_user_profile(credentials)
        
        # Create JWT token
        token = create_jwt_token(user, credentials)
        
        logger.info("OAuth callback successful", user_id=user.id)
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/callback?token={token}",
            status_code=status.HTTP_302_FOUND,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=authentication_failed",
            status_code=status.HTTP_302_FOUND,
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user(token: str = Query(..., description="JWT token")):
    """Get current user profile."""
    payload = verify_jwt_token(token)
    
    return UserProfile(
        id=payload["sub"],
        email=payload["email"],
        name=payload["name"],
        picture=payload.get("picture"),
    )


@router.post("/logout")
async def logout(token: str = Query(..., description="JWT token")):
    """Logout and revoke session."""
    payload = verify_jwt_token(token)
    user_id = payload["sub"]
    
    revoke_user_session(user_id)
    
    logger.info("User logged out", user_id=user_id)
    return {"message": "Successfully logged out"}


@router.get("/verify")
async def verify_token(token: str = Query(..., description="JWT token")):
    """Verify if token is valid."""
    try:
        payload = verify_jwt_token(token)
        
        # Also check if we have valid Google credentials
        credentials = get_google_credentials(payload["sub"])
        
        return {
            "valid": True,
            "user_id": payload["sub"],
            "email": payload["email"],
            "has_gmail_access": credentials is not None,
        }
    except HTTPException:
        return {"valid": False}


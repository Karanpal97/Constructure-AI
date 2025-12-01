"""Email routes for Gmail operations."""

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from app.models import (
    Email,
    EmailSummary,
    EmailResponse,
    SendEmailRequest,
    DeleteEmailRequest,
    ActionResult,
    EmailCategory,
    DailyDigest,
)
from app.services.auth import verify_jwt_token, get_google_credentials
from app.services.gmail import fetch_emails, send_email, delete_email, get_email_by_id
from app.services.ai import (
    summarize_emails,
    generate_responses_for_emails,
    generate_email_response,
    categorize_emails,
    generate_daily_digest,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/emails", tags=["Emails"])


def get_credentials_from_token(token: str):
    """Extract user credentials from JWT token."""
    payload = verify_jwt_token(token)
    user_id = payload["sub"]
    
    credentials = get_google_credentials(user_id)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gmail authorization expired. Please re-authenticate.",
        )
    
    return credentials, payload


@router.get("/list", response_model=List[EmailSummary])
async def list_emails(
    token: str = Query(..., description="JWT token"),
    count: int = Query(5, ge=1, le=50, description="Number of emails to fetch"),
    query: Optional[str] = Query(None, description="Gmail search query"),
):
    """Fetch and summarize recent emails."""
    logger.info("Fetching emails", count=count, query=query)
    
    credentials, payload = get_credentials_from_token(token)
    
    # Fetch emails
    emails = await fetch_emails(credentials, max_results=count, query=query)
    
    # Generate summaries
    summaries = await summarize_emails(emails)
    
    return summaries


@router.get("/responses", response_model=List[EmailResponse])
async def get_email_responses(
    token: str = Query(..., description="JWT token"),
    count: int = Query(5, ge=1, le=10, description="Number of emails to generate responses for"),
    tone: str = Query("professional", description="Tone of responses"),
):
    """Generate AI responses for recent emails."""
    logger.info("Generating email responses", count=count, tone=tone)
    
    credentials, payload = get_credentials_from_token(token)
    
    # Fetch emails
    emails = await fetch_emails(credentials, max_results=count)
    
    # Generate responses
    responses = await generate_responses_for_emails(emails, tone)
    
    return responses


@router.get("/response/{email_id}", response_model=EmailResponse)
async def get_single_response(
    email_id: str,
    token: str = Query(..., description="JWT token"),
    tone: str = Query("professional", description="Tone of response"),
):
    """Generate AI response for a specific email."""
    logger.info("Generating response for email", email_id=email_id, tone=tone)
    
    credentials, payload = get_credentials_from_token(token)
    
    # Fetch the specific email
    email = await get_email_by_id(credentials, email_id)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    
    # Generate response
    response = await generate_email_response(email, tone)
    
    return response


@router.post("/send", response_model=ActionResult)
async def send_reply(
    request: SendEmailRequest,
    token: str = Query(..., description="JWT token"),
):
    """Send an email reply."""
    logger.info("Sending email reply", email_id=request.email_id)
    
    credentials, payload = get_credentials_from_token(token)
    
    # Get original email for threading
    original_email = await get_email_by_id(credentials, request.email_id)
    if not original_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original email not found",
        )
    
    # Send reply
    result = await send_email(
        credentials=credentials,
        to=original_email.sender_email,
        subject=f"Re: {original_email.subject}" if not original_email.subject.startswith("Re:") else original_email.subject,
        body=request.reply_content,
        thread_id=request.thread_id or original_email.thread_id,
    )
    
    return ActionResult(
        success=result["success"],
        message=f"Reply sent successfully to {original_email.sender_email}",
        action="send",
        email_id=result.get("message_id"),
    )


@router.post("/delete", response_model=ActionResult)
async def delete_email_endpoint(
    request: DeleteEmailRequest,
    token: str = Query(..., description="JWT token"),
):
    """Delete (trash) an email."""
    logger.info("Deleting email", email_id=request.email_id, confirmed=request.confirm)
    
    if not request.confirm:
        return ActionResult(
            success=False,
            message="Please confirm deletion by setting confirm=true",
            action="delete",
            email_id=request.email_id,
        )
    
    credentials, payload = get_credentials_from_token(token)
    
    result = await delete_email(credentials, request.email_id)
    
    return ActionResult(
        success=result["success"],
        message=result["message"],
        action="delete",
        email_id=request.email_id,
    )


@router.get("/categorize", response_model=List[EmailCategory])
async def categorize_inbox(
    token: str = Query(..., description="JWT token"),
    count: int = Query(20, ge=5, le=50, description="Number of emails to categorize"),
):
    """Categorize emails using AI."""
    logger.info("Categorizing emails", count=count)
    
    credentials, payload = get_credentials_from_token(token)
    
    # Fetch emails
    emails = await fetch_emails(credentials, max_results=count)
    
    # Categorize
    categories = await categorize_emails(emails)
    
    return categories


@router.get("/digest", response_model=DailyDigest)
async def daily_digest_endpoint(
    token: str = Query(..., description="JWT token"),
    count: int = Query(20, ge=5, le=50, description="Number of emails to include in digest"),
):
    """Generate daily email digest."""
    logger.info("Generating daily digest", count=count)
    
    credentials, payload = get_credentials_from_token(token)
    
    # Fetch emails
    emails = await fetch_emails(credentials, max_results=count)
    
    # Generate digest
    digest = await generate_daily_digest(emails)
    
    return digest


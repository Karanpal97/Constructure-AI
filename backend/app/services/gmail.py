"""Gmail API service for email operations."""

import base64
import structlog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fastapi import HTTPException, status

from app.models import Email

logger = structlog.get_logger()


def get_gmail_service(credentials: Credentials):
    """Build Gmail API service."""
    return build("gmail", "v1", credentials=credentials)


def parse_email_headers(headers: List[dict]) -> dict:
    """Parse email headers into a dictionary."""
    parsed = {}
    for header in headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")
        parsed[name] = value
    return parsed


def decode_email_body(payload: dict) -> str:
    """Decode email body from base64."""
    body = ""
    
    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    elif "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break
            elif mime_type == "text/html" and part.get("body", {}).get("data") and not body:
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            elif "parts" in part:
                # Handle nested parts
                body = decode_email_body(part)
                if body:
                    break
    
    return body


def extract_sender_info(from_header: str) -> tuple[str, str]:
    """Extract sender name and email from From header."""
    if "<" in from_header and ">" in from_header:
        name = from_header.split("<")[0].strip().strip('"')
        email = from_header.split("<")[1].split(">")[0].strip()
        return name or email, email
    return from_header, from_header


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(HttpError),
)
async def fetch_emails(
    credentials: Credentials,
    max_results: int = 5,
    query: Optional[str] = None
) -> List[Email]:
    """Fetch emails from Gmail inbox."""
    logger.info("Fetching emails", max_results=max_results, query=query)
    
    try:
        service = get_gmail_service(credentials)
        
        # Build query
        q = query or "in:inbox"
        
        # List messages
        results = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            q=q
        ).execute()
        
        messages = results.get("messages", [])
        emails = []
        
        for msg in messages:
            # Get full message details
            full_msg = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()
            
            payload = full_msg.get("payload", {})
            headers = parse_email_headers(payload.get("headers", []))
            
            sender_name, sender_email = extract_sender_info(headers.get("from", "Unknown"))
            
            email = Email(
                id=full_msg["id"],
                thread_id=full_msg.get("threadId", ""),
                sender=sender_name,
                sender_email=sender_email,
                subject=headers.get("subject", "(No Subject)"),
                snippet=full_msg.get("snippet", ""),
                body=decode_email_body(payload),
                date=headers.get("date", ""),
                is_unread="UNREAD" in full_msg.get("labelIds", []),
                labels=full_msg.get("labelIds", []),
            )
            emails.append(email)
        
        logger.info("Successfully fetched emails", count=len(emails))
        return emails
        
    except HttpError as e:
        logger.error("Gmail API error while fetching emails", error=str(e))
        if e.resp.status == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Gmail authorization expired. Please re-authenticate."
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch emails from Gmail: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error fetching emails", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching emails"
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(HttpError),
)
async def send_email(
    credentials: Credentials,
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
) -> dict:
    """Send an email via Gmail."""
    logger.info("Sending email", to=to, subject=subject, has_thread=bool(thread_id))
    
    try:
        service = get_gmail_service(credentials)
        
        # Get user's email for From header
        profile = service.users().getProfile(userId="me").execute()
        from_email = profile.get("emailAddress", "")
        
        # Create message
        message = MIMEMultipart()
        message["to"] = to
        message["from"] = from_email
        message["subject"] = subject
        
        # Add threading headers if replying
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
        if references:
            message["References"] = references
        
        message.attach(MIMEText(body, "plain"))
        
        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        # Send message
        send_body = {"raw": raw}
        if thread_id:
            send_body["threadId"] = thread_id
        
        result = service.users().messages().send(
            userId="me",
            body=send_body
        ).execute()
        
        logger.info("Successfully sent email", message_id=result.get("id"))
        return {
            "success": True,
            "message_id": result.get("id"),
            "thread_id": result.get("threadId"),
        }
        
    except HttpError as e:
        logger.error("Gmail API error while sending email", error=str(e))
        if e.resp.status == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Gmail authorization expired. Please re-authenticate."
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send email: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error sending email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while sending email"
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(HttpError),
)
async def delete_email(credentials: Credentials, email_id: str) -> dict:
    """Delete (trash) an email."""
    logger.info("Deleting email", email_id=email_id)
    
    try:
        service = get_gmail_service(credentials)
        
        # Move to trash
        service.users().messages().trash(
            userId="me",
            id=email_id
        ).execute()
        
        logger.info("Successfully deleted email", email_id=email_id)
        return {
            "success": True,
            "email_id": email_id,
            "message": "Email moved to trash successfully",
        }
        
    except HttpError as e:
        logger.error("Gmail API error while deleting email", error=str(e), email_id=email_id)
        if e.resp.status == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Gmail authorization expired. Please re-authenticate."
            )
        if e.resp.status == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to delete email: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error deleting email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting email"
        )


async def get_email_by_id(credentials: Credentials, email_id: str) -> Optional[Email]:
    """Fetch a single email by ID."""
    logger.info("Fetching email by ID", email_id=email_id)
    
    try:
        service = get_gmail_service(credentials)
        
        full_msg = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()
        
        payload = full_msg.get("payload", {})
        headers = parse_email_headers(payload.get("headers", []))
        
        sender_name, sender_email = extract_sender_info(headers.get("from", "Unknown"))
        
        email = Email(
            id=full_msg["id"],
            thread_id=full_msg.get("threadId", ""),
            sender=sender_name,
            sender_email=sender_email,
            subject=headers.get("subject", "(No Subject)"),
            snippet=full_msg.get("snippet", ""),
            body=decode_email_body(payload),
            date=headers.get("date", ""),
            is_unread="UNREAD" in full_msg.get("labelIds", []),
            labels=full_msg.get("labelIds", []),
        )
        
        return email
        
    except HttpError as e:
        if e.resp.status == 404:
            return None
        raise
    except Exception as e:
        logger.error("Error fetching email by ID", error=str(e))
        return None


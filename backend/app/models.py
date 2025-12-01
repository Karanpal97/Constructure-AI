"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class UserProfile(BaseModel):
    """User profile from Google OAuth."""
    id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    

class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


class Email(BaseModel):
    """Email representation."""
    id: str
    thread_id: str
    sender: str
    sender_email: str
    subject: str
    snippet: str
    body: str
    date: str
    is_unread: bool = False
    labels: List[str] = []


class EmailSummary(BaseModel):
    """Email with AI-generated summary."""
    email: Email
    summary: str
    category: Optional[str] = None


class EmailResponse(BaseModel):
    """AI-generated email response."""
    email_id: str
    original_subject: str
    original_sender: str
    suggested_reply: str
    tone: str = "professional"


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message in conversation."""
    role: ChatMessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


class ChatRequest(BaseModel):
    """Chat request from user."""
    message: str
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    """Chat response with potential actions."""
    message: str
    action_type: Optional[str] = None
    action_data: Optional[dict] = None
    emails: Optional[List[EmailSummary]] = None
    suggested_replies: Optional[List[EmailResponse]] = None


class SendEmailRequest(BaseModel):
    """Request to send an email reply."""
    email_id: str
    reply_content: str
    thread_id: Optional[str] = None


class DeleteEmailRequest(BaseModel):
    """Request to delete an email."""
    email_id: str
    confirm: bool = False


class ActionResult(BaseModel):
    """Result of an email action."""
    success: bool
    message: str
    action: str
    email_id: Optional[str] = None


class EmailCategory(BaseModel):
    """Category for email grouping."""
    name: str
    emails: List[EmailSummary]
    count: int


class DailyDigest(BaseModel):
    """Daily email digest."""
    date: str
    total_emails: int
    summary: str
    categories: List[EmailCategory]
    action_items: List[str]
    urgent_emails: List[EmailSummary]


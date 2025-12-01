"""Chat routes for the AI chatbot."""

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime

from app.models import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ChatMessageRole,
    EmailSummary,
    EmailResponse,
)
from app.services.auth import verify_jwt_token, get_google_credentials
from app.services.gmail import fetch_emails, send_email, delete_email, get_email_by_id
from app.services.ai import (
    parse_user_intent,
    generate_chat_response,
    summarize_emails,
    generate_email_response,
    categorize_emails,
    generate_daily_digest,
    CommandType,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["Chat"])

# In-memory storage for conversation context (use Redis in production)
_conversation_context: dict[str, dict] = {}


def get_context(user_id: str) -> dict:
    """Get or create conversation context for user."""
    if user_id not in _conversation_context:
        _conversation_context[user_id] = {
            "recent_emails": [],
            "pending_action": None,
            "pending_email_id": None,
        }
    return _conversation_context[user_id]


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    token: str = Query(..., description="JWT token"),
):
    """Process a chat message and execute email operations."""
    payload = verify_jwt_token(token)
    user_id = payload["sub"]
    user_name = payload["name"]
    
    logger.info("Processing chat message", user_id=user_id, message=request.message[:100])
    
    credentials = get_google_credentials(user_id)
    if not credentials:
        return ChatResponse(
            message="Your Gmail session has expired. Please log in again to continue.",
            action_type="reauth_required",
        )
    
    context = get_context(user_id)
    
    # Check for pending confirmation
    if context.get("pending_action"):
        return await handle_pending_action(request.message, context, credentials, user_name)
    
    # Parse user intent
    action, params = await parse_user_intent(request.message, context)
    
    logger.info("Parsed intent", action=action, params=params)
    
    # Execute action
    try:
        if action == CommandType.READ_EMAILS:
            return await handle_read_emails(credentials, params, context, user_name)
        
        elif action == CommandType.GENERATE_RESPONSE:
            return await handle_generate_response(credentials, params, context, user_name)
        
        elif action == CommandType.SEND_EMAIL:
            return await handle_send_email(credentials, params, context, user_name)
        
        elif action == CommandType.DELETE_EMAIL:
            return await handle_delete_email(credentials, params, context, user_name)
        
        elif action == CommandType.CATEGORIZE:
            return await handle_categorize(credentials, params, context, user_name)
        
        elif action == CommandType.DAILY_DIGEST:
            return await handle_daily_digest(credentials, params, context, user_name)
        
        elif action == CommandType.HELP:
            return handle_help(user_name)
        
        else:
            return ChatResponse(
                message=f"I'm not sure I understood that, {user_name}. You can ask me to:\n\n"
                       "• **Read emails**: \"Show me my last 5 emails\"\n"
                       "• **Generate replies**: \"Write a reply to email 2\"\n"
                       "• **Send emails**: \"Send that reply\" (after generating one)\n"
                       "• **Delete emails**: \"Delete the email from John\"\n"
                       "• **Categorize**: \"Organize my inbox\"\n"
                       "• **Daily digest**: \"Give me today's email summary\"\n\n"
                       "What would you like me to do?",
                action_type="unknown",
            )
            
    except HTTPException as e:
        logger.error("Error processing chat", error=str(e))
        return ChatResponse(
            message=f"I ran into an issue: {e.detail}. Please try again.",
            action_type="error",
        )
    except Exception as e:
        logger.error("Unexpected error processing chat", error=str(e))
        return ChatResponse(
            message="Something went wrong. Please try again or rephrase your request.",
            action_type="error",
        )


async def handle_read_emails(credentials, params, context, user_name) -> ChatResponse:
    """Handle read emails command."""
    count = params.get("count", 5)
    query = params.get("query")
    
    emails = await fetch_emails(credentials, max_results=count, query=query)
    summaries = await summarize_emails(emails)
    
    # Store in context for later reference
    context["recent_emails"] = [
        {
            "id": s.email.id,
            "sender": s.email.sender,
            "sender_email": s.email.sender_email,
            "subject": s.email.subject,
            "summary": s.summary,
        }
        for s in summaries
    ]
    
    if not summaries:
        return ChatResponse(
            message=f"You don't have any emails matching that criteria, {user_name}.",
            action_type="read_emails",
            emails=[],
        )
    
    message = f"Here are your last {len(summaries)} emails, {user_name}:\n\n"
    for i, s in enumerate(summaries, 1):
        message += f"**{i}. {s.email.subject}**\n"
        message += f"   From: {s.email.sender}\n"
        message += f"   Summary: {s.summary}\n\n"
    
    message += "You can ask me to reply to any of these, delete them, or get more details."
    
    return ChatResponse(
        message=message,
        action_type="read_emails",
        emails=summaries,
    )


async def handle_generate_response(credentials, params, context, user_name) -> ChatResponse:
    """Handle generate response command."""
    email_num = params.get("email_number")
    email_id = params.get("email_id")
    
    # Get email from context or by ID
    if email_num and context.get("recent_emails"):
        if 1 <= email_num <= len(context["recent_emails"]):
            email_id = context["recent_emails"][email_num - 1]["id"]
    
    if not email_id and context.get("recent_emails"):
        # Default to first email
        email_id = context["recent_emails"][0]["id"]
    
    if not email_id:
        return ChatResponse(
            message="Please show me your emails first by saying 'Show my emails', then I can help you reply.",
            action_type="error",
        )
    
    email = await get_email_by_id(credentials, email_id)
    if not email:
        return ChatResponse(
            message="I couldn't find that email. Try showing your emails again.",
            action_type="error",
        )
    
    response = await generate_email_response(email, params.get("tone", "professional"))
    
    # Store for potential sending
    context["pending_response"] = {
        "email_id": email_id,
        "thread_id": email.thread_id,
        "to": email.sender_email,
        "subject": email.subject,
        "reply": response.suggested_reply,
    }
    
    message = f"Here's a suggested reply for the email from **{email.sender}** about \"*{email.subject}*\":\n\n"
    message += f"---\n{response.suggested_reply}\n---\n\n"
    message += "Would you like me to send this reply? Just say 'Send it' or 'Yes, send'."
    
    return ChatResponse(
        message=message,
        action_type="generate_response",
        suggested_replies=[response],
    )


async def handle_send_email(credentials, params, context, user_name) -> ChatResponse:
    """Handle send email command."""
    pending = context.get("pending_response")
    
    if not pending:
        return ChatResponse(
            message="I don't have a reply ready to send. Let me generate one first. Which email would you like to reply to?",
            action_type="error",
        )
    
    # Check if user provided custom content
    custom_content = params.get("content")
    reply_content = custom_content if custom_content else pending["reply"]
    
    result = await send_email(
        credentials=credentials,
        to=pending["to"],
        subject=f"Re: {pending['subject']}" if not pending["subject"].startswith("Re:") else pending["subject"],
        body=reply_content,
        thread_id=pending.get("thread_id"),
    )
    
    # Clear pending
    context["pending_response"] = None
    
    return ChatResponse(
        message=f"✅ Done! I've sent the reply to **{pending['to']}**. Is there anything else you'd like me to help with?",
        action_type="send_email",
        action_data=result,
    )


async def handle_delete_email(credentials, params, context, user_name) -> ChatResponse:
    """Handle delete email command."""
    email_num = params.get("email_number")
    sender = params.get("sender")
    subject_keyword = params.get("subject_keyword")
    email_id = params.get("email_id")
    
    # Find email to delete
    target_email = None
    
    if email_num and context.get("recent_emails"):
        if 1 <= email_num <= len(context["recent_emails"]):
            target_email = context["recent_emails"][email_num - 1]
    elif sender and context.get("recent_emails"):
        for e in context["recent_emails"]:
            if sender.lower() in e["sender"].lower() or sender.lower() in e["sender_email"].lower():
                target_email = e
                break
    elif subject_keyword and context.get("recent_emails"):
        for e in context["recent_emails"]:
            if subject_keyword.lower() in e["subject"].lower():
                target_email = e
                break
    elif email_id:
        target_email = {"id": email_id}
    
    if not target_email:
        return ChatResponse(
            message="I couldn't find the email you want to delete. Try showing your emails first with 'Show my emails'.",
            action_type="error",
        )
    
    # Store pending deletion and ask for confirmation
    context["pending_action"] = "delete"
    context["pending_email_id"] = target_email["id"]
    context["pending_email_info"] = target_email
    
    email_desc = target_email.get("subject", "Unknown")
    if target_email.get("sender"):
        email_desc = f"\"{target_email['subject']}\" from {target_email['sender']}"
    
    return ChatResponse(
        message=f"⚠️ Are you sure you want to delete the email {email_desc}?\n\nSay **'Yes, delete it'** to confirm or **'Cancel'** to abort.",
        action_type="confirm_delete",
        action_data={"email_id": target_email["id"]},
    )


async def handle_pending_action(message: str, context: dict, credentials, user_name) -> ChatResponse:
    """Handle pending action confirmation."""
    message_lower = message.lower().strip()
    
    if context["pending_action"] == "delete":
        if any(word in message_lower for word in ["yes", "confirm", "delete", "do it", "sure"]):
            email_id = context["pending_email_id"]
            email_info = context.get("pending_email_info", {})
            
            result = await delete_email(credentials, email_id)
            
            # Clear pending
            context["pending_action"] = None
            context["pending_email_id"] = None
            context["pending_email_info"] = None
            
            # Remove from recent emails
            if context.get("recent_emails"):
                context["recent_emails"] = [e for e in context["recent_emails"] if e["id"] != email_id]
            
            email_desc = email_info.get("subject", "the email")
            
            return ChatResponse(
                message=f"🗑️ Done! I've moved \"{email_desc}\" to trash. Anything else?",
                action_type="delete_email",
                action_data=result,
            )
        else:
            # Cancelled
            context["pending_action"] = None
            context["pending_email_id"] = None
            context["pending_email_info"] = None
            
            return ChatResponse(
                message="No problem, I've cancelled the deletion. What else can I help you with?",
                action_type="cancelled",
            )
    
    # Unknown pending action
    context["pending_action"] = None
    return ChatResponse(
        message="What would you like me to do?",
        action_type="unknown",
    )


async def handle_categorize(credentials, params, context, user_name) -> ChatResponse:
    """Handle categorize command."""
    count = params.get("count", 20)
    
    emails = await fetch_emails(credentials, max_results=count)
    categories = await categorize_emails(emails)
    
    message = f"📊 Here's how I've organized your last {len(emails)} emails, {user_name}:\n\n"
    
    for cat in categories:
        message += f"**{cat.name}** ({cat.count} emails)\n"
        for i, email_summary in enumerate(cat.emails[:3], 1):
            message += f"  {i}. {email_summary.email.subject} - {email_summary.summary[:50]}...\n"
        if cat.count > 3:
            message += f"  ...and {cat.count - 3} more\n"
        message += "\n"
    
    return ChatResponse(
        message=message,
        action_type="categorize",
        action_data={"categories": [c.model_dump() for c in categories]},
    )


async def handle_daily_digest(credentials, params, context, user_name) -> ChatResponse:
    """Handle daily digest command."""
    count = params.get("count", 20)
    
    emails = await fetch_emails(credentials, max_results=count)
    digest = await generate_daily_digest(emails)
    
    message = f"📬 **Your Daily Email Digest** ({digest.date})\n\n"
    message += f"You have **{digest.total_emails} emails** to review.\n\n"
    message += f"**Summary**: {digest.summary}\n\n"
    
    if digest.urgent_emails:
        message += "🚨 **Urgent**:\n"
        for e in digest.urgent_emails:
            message += f"  • {e.email.subject} from {e.email.sender}\n"
        message += "\n"
    
    if digest.action_items:
        message += "📋 **Action Items**:\n"
        for item in digest.action_items:
            message += f"  • {item}\n"
        message += "\n"
    
    message += "Would you like me to show you any specific category or help you respond to any emails?"
    
    return ChatResponse(
        message=message,
        action_type="daily_digest",
        action_data=digest.model_dump(),
    )


def handle_help(user_name: str) -> ChatResponse:
    """Handle help command."""
    message = f"👋 Hi {user_name}! I'm your AI email assistant. Here's what I can do:\n\n"
    message += "**📧 Read Emails**\n"
    message += "  • \"Show me my last 5 emails\"\n"
    message += "  • \"Show emails from John\"\n"
    message += "  • \"Find emails about invoice\"\n\n"
    message += "**✍️ Reply to Emails**\n"
    message += "  • \"Write a reply to email 2\"\n"
    message += "  • \"Reply to the email from Sarah\"\n"
    message += "  • \"Generate a professional response\"\n\n"
    message += "**🗑️ Delete Emails**\n"
    message += "  • \"Delete email number 3\"\n"
    message += "  • \"Delete the email from promotions\"\n\n"
    message += "**📊 Organize**\n"
    message += "  • \"Categorize my inbox\"\n"
    message += "  • \"Give me today's email digest\"\n\n"
    message += "Just type naturally - I'll understand! 😊"
    
    return ChatResponse(
        message=message,
        action_type="help",
    )


@router.get("/welcome")
async def get_welcome_message(token: str = Query(..., description="JWT token")):
    """Get welcome message for new session."""
    payload = verify_jwt_token(token)
    user_name = payload["name"]
    
    return {
        "message": f"👋 Welcome back, **{user_name}**! I'm your AI email assistant.\n\n"
                  "I can help you:\n"
                  "• 📧 Read and summarize your emails\n"
                  "• ✍️ Generate smart replies\n"
                  "• 🗑️ Delete unwanted messages\n"
                  "• 📊 Organize your inbox\n\n"
                  "Try saying **\"Show me my last 5 emails\"** to get started!",
        "user_name": user_name,
    }


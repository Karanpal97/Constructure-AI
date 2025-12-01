"""AI service for email summaries, responses, and natural language understanding.
Supports both Google Gemini (FREE) and OpenAI (PAID).
"""

import structlog
from typing import List, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential
from fastapi import HTTPException, status

from app.config import get_settings
from app.models import Email, EmailSummary, EmailResponse, EmailCategory, DailyDigest

logger = structlog.get_logger()

# AI Client abstraction
class AIClient:
    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.ai_provider.lower()
        
        if self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.settings.gemini_api_key)
            self.model = genai.GenerativeModel(self.settings.gemini_model)
            logger.info("Using Google Gemini AI (FREE)")
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            logger.info("Using OpenAI (PAID)")
    
    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Generate text using the configured AI provider."""
        if self.provider == "gemini":
            # Gemini combines system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        else:
            # OpenAI
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()


# Global AI client instance
_ai_client: Optional[AIClient] = None

def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_email_summary(email: Email) -> str:
    """Generate AI summary of an email."""
    logger.info("Generating email summary", email_id=email.id, subject=email.subject)
    
    client = get_ai_client()
    
    system_prompt = "You are a helpful email assistant that creates concise, accurate summaries of emails."
    user_prompt = f"""Summarize this email in 1-2 concise sentences. Focus on the key points and any action items.

From: {email.sender} <{email.sender_email}>
Subject: {email.subject}
Date: {email.date}

Content:
{email.body[:3000]}
"""
    
    try:
        summary = client.generate(system_prompt, user_prompt, max_tokens=150)
        logger.info("Generated email summary", email_id=email.id)
        return summary
    except Exception as e:
        logger.error("Failed to generate email summary", error=str(e), email_id=email.id)
        return f"Unable to generate summary: {email.snippet[:100]}..."


async def summarize_emails(emails: List[Email]) -> List[EmailSummary]:
    """Generate summaries for a list of emails."""
    summaries = []
    
    for email in emails:
        summary = await generate_email_summary(email)
        summaries.append(EmailSummary(
            email=email,
            summary=summary,
        ))
    
    return summaries


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_email_response(email: Email, tone: str = "professional") -> EmailResponse:
    """Generate an AI response to an email."""
    logger.info("Generating email response", email_id=email.id, tone=tone)
    
    client = get_ai_client()
    
    system_prompt = f"You are a helpful email assistant that writes {tone}, clear, and contextually appropriate email replies. Keep responses concise but complete."
    user_prompt = f"""Generate a {tone} reply to this email. The reply should:
- Be appropriate and context-aware
- Address the main points of the original email
- Be ready to send without further editing
- Not include placeholders like [Your Name]

Original Email:
From: {email.sender} <{email.sender_email}>
Subject: {email.subject}
Date: {email.date}

Content:
{email.body[:3000]}

Generate only the reply body, no subject line or headers."""
    
    try:
        reply = client.generate(system_prompt, user_prompt, max_tokens=500)
        logger.info("Generated email response", email_id=email.id)
        
        return EmailResponse(
            email_id=email.id,
            original_subject=email.subject,
            original_sender=email.sender_email,
            suggested_reply=reply,
            tone=tone,
        )
    except Exception as e:
        logger.error("Failed to generate email response", error=str(e), email_id=email.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate email response"
        )


async def generate_responses_for_emails(emails: List[Email], tone: str = "professional") -> List[EmailResponse]:
    """Generate responses for a list of emails."""
    responses = []
    
    for email in emails:
        response = await generate_email_response(email, tone)
        responses.append(response)
    
    return responses


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def categorize_emails(emails: List[Email]) -> List[EmailCategory]:
    """Categorize emails into groups using AI."""
    logger.info("Categorizing emails", count=len(emails))
    
    client = get_ai_client()
    
    # Prepare email list for categorization
    email_summaries = []
    for i, email in enumerate(emails):
        email_summaries.append(f"{i+1}. From: {email.sender}, Subject: {email.subject}, Snippet: {email.snippet[:100]}")
    
    email_list = "\n".join(email_summaries)
    
    system_prompt = "You are an email categorization assistant. Return only valid JSON."
    user_prompt = f"""Categorize these emails into the following categories: Work, Personal, Promotions, Urgent, Other.

Emails:
{email_list}

Return a JSON object with category names as keys and arrays of email numbers (1-based) as values.
Example: {{"Work": [1, 3], "Personal": [2], "Promotions": [4, 5], "Urgent": [1], "Other": []}}

Only return the JSON, no explanation."""
    
    try:
        import json
        response_text = client.generate(system_prompt, user_prompt, max_tokens=200)
        
        # Extract JSON from response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        categories_raw = json.loads(response_text.strip())
        
        # Build category objects
        categories = []
        for cat_name, email_nums in categories_raw.items():
            cat_emails = []
            for num in email_nums:
                if 1 <= num <= len(emails):
                    email = emails[num - 1]
                    summary = await generate_email_summary(email)
                    cat_emails.append(EmailSummary(email=email, summary=summary, category=cat_name))
            
            if cat_emails:
                categories.append(EmailCategory(
                    name=cat_name,
                    emails=cat_emails,
                    count=len(cat_emails),
                ))
        
        logger.info("Categorized emails", categories=len(categories))
        return categories
        
    except Exception as e:
        logger.error("Failed to categorize emails", error=str(e))
        # Fallback: return all as "Other"
        summaries = await summarize_emails(emails)
        return [EmailCategory(
            name="All Emails",
            emails=summaries,
            count=len(summaries),
        )]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_daily_digest(emails: List[Email]) -> DailyDigest:
    """Generate a daily email digest."""
    logger.info("Generating daily digest", email_count=len(emails))
    
    client = get_ai_client()
    
    # Prepare email summaries
    email_info = []
    for i, email in enumerate(emails):
        email_info.append(f"{i+1}. From: {email.sender}\n   Subject: {email.subject}\n   Preview: {email.snippet[:150]}")
    
    email_list = "\n\n".join(email_info)
    
    system_prompt = "You are an executive assistant creating a daily email digest. Be concise and actionable. Return only valid JSON."
    user_prompt = f"""Create a daily email digest summary for these {len(emails)} emails.

Emails:
{email_list}

Provide:
1. A brief overall summary (2-3 sentences)
2. List any action items or follow-ups needed
3. Identify any urgent emails (by number)

Format as JSON:
{{
    "summary": "overall summary here",
    "action_items": ["action 1", "action 2"],
    "urgent_email_numbers": [1, 2]
}}"""
    
    try:
        import json
        from datetime import datetime
        
        response_text = client.generate(system_prompt, user_prompt, max_tokens=400)
        
        # Extract JSON from response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        digest_raw = json.loads(response_text.strip())
        
        # Get categories
        categories = await categorize_emails(emails)
        
        # Get urgent emails
        urgent_numbers = digest_raw.get("urgent_email_numbers", [])
        urgent_emails = []
        for num in urgent_numbers:
            if 1 <= num <= len(emails):
                email = emails[num - 1]
                summary = await generate_email_summary(email)
                urgent_emails.append(EmailSummary(email=email, summary=summary, category="Urgent"))
        
        digest = DailyDigest(
            date=datetime.now().strftime("%Y-%m-%d"),
            total_emails=len(emails),
            summary=digest_raw.get("summary", ""),
            categories=categories,
            action_items=digest_raw.get("action_items", []),
            urgent_emails=urgent_emails,
        )
        
        logger.info("Generated daily digest")
        return digest
        
    except Exception as e:
        logger.error("Failed to generate daily digest", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate daily digest"
        )


# Natural Language Command Understanding

class CommandType:
    READ_EMAILS = "read_emails"
    GENERATE_RESPONSE = "generate_response"
    SEND_EMAIL = "send_email"
    DELETE_EMAIL = "delete_email"
    CATEGORIZE = "categorize"
    DAILY_DIGEST = "daily_digest"
    HELP = "help"
    UNKNOWN = "unknown"


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
async def parse_user_intent(message: str, context: Optional[dict] = None) -> Tuple[str, dict]:
    """Parse natural language command into action and parameters."""
    logger.info("Parsing user intent", message=message[:100])
    
    client = get_ai_client()
    
    context_str = ""
    if context and context.get("recent_emails"):
        context_str = "\n\nRecently fetched emails:\n"
        for i, email in enumerate(context["recent_emails"][:5]):
            context_str += f"{i+1}. From: {email.get('sender', 'Unknown')}, Subject: {email.get('subject', 'No Subject')}\n"
    
    system_prompt = "You are an email assistant command parser. Return only valid JSON."
    user_prompt = f"""Parse this user message into an action and parameters for an email assistant.

User message: "{message}"
{context_str}

Available actions:
- read_emails: Fetch and show emails (params: count, query/filter)
- generate_response: Generate reply suggestions (params: email_number or email_id)
- send_email: Send an email reply (params: email_number or email_id, content)
- delete_email: Delete an email (params: email_number, sender, or subject_keyword)
- categorize: Group emails by category
- daily_digest: Generate daily email summary
- help: Show available commands
- unknown: Cannot understand the request

Return JSON:
{{
    "action": "action_name",
    "params": {{}},
    "natural_response": "A friendly response to the user"
}}

Examples:
- "Show me my last 5 emails" -> {{"action": "read_emails", "params": {{"count": 5}}, "natural_response": "Let me fetch your last 5 emails..."}}
- "Delete the email from John" -> {{"action": "delete_email", "params": {{"sender": "John"}}, "natural_response": "I'll delete the email from John. Would you like me to confirm?"}}
- "Reply to email 2 saying I'll get back tomorrow" -> {{"action": "send_email", "params": {{"email_number": 2, "content": "I'll get back tomorrow"}}, "natural_response": "I'll send a reply to email #2..."}}"""
    
    try:
        import json
        response_text = client.generate(system_prompt, user_prompt, max_tokens=300)
        
        # Extract JSON from response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        result = json.loads(response_text.strip())
        
        action = result.get("action", CommandType.UNKNOWN)
        params = result.get("params", {})
        
        logger.info("Parsed user intent", action=action, params=params)
        return action, params
        
    except Exception as e:
        logger.error("Failed to parse user intent", error=str(e))
        return CommandType.UNKNOWN, {}


async def generate_chat_response(
    message: str,
    user_name: str,
    action: str,
    result: Optional[dict] = None,
    error: Optional[str] = None
) -> str:
    """Generate a natural language response for the chatbot."""
    client = get_ai_client()
    
    context = f"User: {user_name}\nAction performed: {action}\n"
    
    if result:
        context += f"Result: {str(result)[:500]}\n"
    if error:
        context += f"Error: {error}\n"
    
    system_prompt = f"You are a friendly email assistant helping {user_name}. Be helpful, concise, and professional."
    user_prompt = f"""{context}
    
User's message was: "{message}"

Generate a helpful, friendly response explaining what happened or what you did. 
Be conversational and natural. If there was an error, be reassuring and suggest solutions."""
    
    try:
        return client.generate(system_prompt, user_prompt, max_tokens=300)
    except Exception as e:
        logger.error("Failed to generate chat response", error=str(e))
        if error:
            return f"I encountered an issue: {error}. Please try again."
        return "I've completed your request."

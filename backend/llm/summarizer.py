"""
llm/summarizer.py - Thread summarization using LLM.
Generates concise summaries of email thread history for agent context.
"""
import logging
from typing import Optional, List
from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

SUMMARIZER_SYSTEM_PROMPT = """You are a CRM assistant that summarizes customer email threads.
Create a concise summary (3-5 sentences) that captures:
1. Who the customer is and their issue
2. The key events/requests in the thread
3. Current status and any unresolved items
4. Customer sentiment trend

Be factual and objective. Output plain text, no bullet points."""


def _get_llm_client() -> Optional[AsyncOpenAI]:
    """Create LLM client for Groq or OpenAI."""
    if settings.GROQ_API_KEY:
        return AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    elif settings.OPENAI_API_KEY:
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return None


async def summarize_thread(
    emails: List[dict],
    contact_name: Optional[str] = None,
) -> str:
    """
    Summarize a thread of emails.
    
    Args:
        emails: List of dicts with 'subject', 'body', 'received_at'
        contact_name: Customer name for context
    
    Returns:
        Plain text summary string
    """
    if not emails:
        return "No emails in this thread."

    # Build thread transcript
    transcript_parts = []
    for i, email in enumerate(emails[-5:], 1):  # Last 5 emails max
        transcript_parts.append(
            f"Email {i} ({email.get('received_at', 'unknown date')}):\n"
            f"Subject: {email.get('subject', '')}\n"
            f"Body: {str(email.get('body', ''))[:500]}\n"
        )
    
    transcript = "\n---\n".join(transcript_parts)
    customer_ctx = f"Customer: {contact_name}\n\n" if contact_name else ""
    
    client = _get_llm_client()
    if not client:
        return f"Thread with {len(emails)} email(s). Latest subject: {emails[-1].get('subject', 'N/A')}"

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SUMMARIZER_SYSTEM_PROMPT},
                {"role": "user", "content": f"{customer_ctx}Thread:\n{transcript}"},
            ],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Thread summarization failed: {e}")
        return f"Thread with {len(emails)} email(s). Could not generate summary."

"""
llm/reply_generator.py - LLM-based email reply drafter using Groq or OpenAI.
Generates contextual, policy-aware draft replies for customer emails.
"""
import logging
from typing import Optional
from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

REPLY_SYSTEM_PROMPT = """You are a senior customer success manager at a B2B SaaS company called SenAI.
Write professional, empathetic, and concise email replies.

Guidelines:
- Address the customer by name if provided
- Be warm but professional
- Acknowledge their concern directly
- Provide clear next steps or information
- Keep replies under 200 words unless complex policy explanations are needed
- Never promise things you cannot guarantee
- If escalating, be transparent: "I'm escalating this to our specialist team"
- For legal/GDPR matters: acknowledge within 24h, reference your DPA
- For security threats: do NOT engage with demands; route to security team
- Sign off as: "The SenAI Customer Success Team"
"""


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


async def generate_reply(
    subject: str,
    body: str,
    contact_name: Optional[str] = None,
    classification: Optional[str] = None,
    policy_context: Optional[str] = None,
    tone: str = "professional",
) -> str:
    """
    Generate a draft email reply using LLM.
    
    Args:
        subject: Original email subject
        body: Original email body (cleaned)
        contact_name: Customer's name for personalization
        classification: Email classification label for context
        policy_context: Relevant policy text from RAG retrieval
        tone: Reply tone (professional, empathetic, formal)
    
    Returns:
        Draft reply string
    """
    client = _get_llm_client()
    
    # Build context-rich prompt
    context_parts = []
    if contact_name:
        context_parts.append(f"Customer name: {contact_name}")
    if classification:
        context_parts.append(f"Issue type: {classification.replace('_', ' ').title()}")
    if policy_context:
        context_parts.append(f"\nRelevant company policy:\n{policy_context}")
    
    context_str = "\n".join(context_parts)
    
    user_prompt = f"""Context:
{context_str}

Original email:
Subject: {subject}
Body: {body[:1500]}

Write a {tone} reply to this customer email."""

    if not client:
        # Fallback reply when no LLM is available
        logger.warning("No LLM configured, generating templated reply")
        return _templated_reply(contact_name, classification)

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": REPLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Reply generation failed: {e}")
        return _templated_reply(contact_name, classification)


def _templated_reply(
    contact_name: Optional[str],
    classification: Optional[str],
) -> str:
    """Fallback template reply when LLM is unavailable."""
    name = contact_name or "Valued Customer"
    
    templates = {
        "refund_request": (
            f"Dear {name},\n\nThank you for reaching out. "
            "We have received your refund request and our team is reviewing it. "
            "You can expect a response within 2 business days.\n\n"
            "The SenAI Customer Success Team"
        ),
        "technical_support": (
            f"Dear {name},\n\nThank you for reporting this issue. "
            "Our technical team has been notified and is investigating. "
            "We'll keep you updated on the progress.\n\n"
            "The SenAI Customer Success Team"
        ),
        "legal_gdpr": (
            f"Dear {name},\n\nWe have received your data subject request "
            "and will respond within the statutory 30-day period as required by GDPR. "
            "Your request has been logged with reference ID pending.\n\n"
            "The SenAI Data Protection Team"
        ),
    }
    
    return templates.get(
        classification or "",
        f"Dear {name},\n\nThank you for contacting SenAI. "
        "Our team has received your message and will get back to you shortly.\n\n"
        "The SenAI Customer Success Team"
    )

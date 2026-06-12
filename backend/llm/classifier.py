"""
llm/classifier.py - LLM-based email classifier using Groq or OpenAI.
Used as the second-layer classification when heuristics have low confidence.
"""
import logging
from typing import Optional, Tuple
from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

# Classification labels the LLM can produce
VALID_LABELS = [
    "legal_gdpr", "security_threat", "legal_threat", "refund_request",
    "pricing_inquiry", "technical_support", "complaint",
    "ai_misinformation", "general_inquiry", "spam"
]

CLASSIFIER_SYSTEM_PROMPT = """You are an email classification specialist for a B2B SaaS CRM platform.
Classify the given email into exactly ONE of these categories:
- legal_gdpr: GDPR/privacy requests, data subject requests
- security_threat: ransomware, hacking threats, security breaches
- legal_threat: lawsuit threats, attorney mentions, SLA breach legal threats
- refund_request: refund, money back, chargeback, cancellation
- pricing_inquiry: pricing questions, upgrade/downgrade, billing
- technical_support: bugs, errors, outages, technical problems
- complaint: general frustration, dissatisfaction, negative feedback
- ai_misinformation: chatbot/AI gave wrong information
- general_inquiry: neutral questions, information requests
- spam: unsolicited, irrelevant, automated emails

Respond with ONLY the category label, nothing else."""


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


async def classify_with_llm(
    subject: str,
    body: str,
    fallback_label: str = "general_inquiry",
) -> Tuple[str, float]:
    """
    Classify email using LLM. Falls back to provided label if LLM unavailable.
    
    Returns:
        Tuple of (label, confidence)
    """
    client = _get_llm_client()
    if not client:
        logger.warning("No LLM API key configured, using fallback label")
        return fallback_label, 0.5

    prompt = f"Subject: {subject}\n\nBody:\n{body[:2000]}"  # Truncate to 2K chars

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=20,
            temperature=0.0,  # Deterministic classification
        )
        raw_label = response.choices[0].message.content.strip().lower()
        
        # Validate label
        if raw_label in VALID_LABELS:
            return raw_label, 0.85  # LLM classifications get high confidence
        else:
            logger.warning(f"LLM returned invalid label: {raw_label}")
            return fallback_label, 0.5

    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        return fallback_label, 0.5

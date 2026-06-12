"""
services/heuristic_service.py - Rule-based heuristic classifier.
First-pass classification using keyword patterns before LLM inference.
"""
import re
from typing import Tuple, Optional
import html


# ---------------------------------------------------------------------------
# Keyword pattern library (ordered by priority - higher priority first)
# ---------------------------------------------------------------------------

HEURISTIC_RULES = [
    # Legal / GDPR
    {
        "label": "legal_gdpr",
        "keywords": ["gdpr", "right to be forgotten", "data portability", "data subject request",
                     "personal data", "privacy request", "right of access", "erase my data"],
        "weight": 10,
    },
    # Security threats
    {
        "label": "security_threat",
        "keywords": ["ransom", "ransomware", "bitcoin", "cryptocurrency payment", "hack",
                     "breach", "exploit", "malware", "ddos", "threat actor"],
        "weight": 10,
    },
    # Legal threats
    {
        "label": "legal_threat",
        "keywords": ["sue", "lawsuit", "attorney", "lawyer", "legal action", "litigation",
                     "court", "solicitor", "barrister", "injunction", "sla breach"],
        "weight": 9,
    },
    # Refund requests
    {
        "label": "refund_request",
        "keywords": ["refund", "money back", "chargeback", "dispute charge", "cancel subscription",
                     "cancellation", "get my money", "credit back"],
        "weight": 7,
    },
    # Pricing / Billing
    {
        "label": "pricing_inquiry",
        "keywords": ["pricing", "price", "upgrade", "downgrade", "plan", "seats", "pro-rata",
                     "invoice", "billing", "subscription cost", "quote"],
        "weight": 5,
    },
    # Technical support
    {
        "label": "technical_support",
        "keywords": ["error", "bug", "not working", "broken", "crash", "outage", "down",
                     "timeout", "cannot access", "login issue", "502", "503", "500"],
        "weight": 6,
    },
    # Complaint / Frustration
    {
        "label": "complaint",
        "keywords": ["unacceptable", "frustrated", "angry", "terrible", "awful", "worst",
                     "disappointed", "disgusted", "furious", "appalled", "final warning"],
        "weight": 6,
    },
    # Chatbot / AI issues
    {
        "label": "ai_misinformation",
        "keywords": ["chatbot told me", "ai said", "bot said", "your ai", "your chatbot",
                     "chatbot gave", "chatbot misinformation", "chatbot error"],
        "weight": 8,
    },
    # General inquiry
    {
        "label": "general_inquiry",
        "keywords": ["question", "wondering", "curious", "how does", "can you explain",
                     "need info", "information about"],
        "weight": 1,
    },
]

# Blocklist: emails from these domains/senders are auto-ignored
BLOCKLIST_PATTERNS = [
    r"noreply@",
    r"no-reply@",
    r"donotreply@",
    r"mailer-daemon@",
    r"postmaster@",
    r"bounce\+",
    r"@bounce\.",
    r"notifications@github\.com",
    r"alerts@",
]

# Spam keywords
SPAM_KEYWORDS = [
    "unsubscribe", "click here to win", "you've been selected",
    "lottery winner", "nigerian prince", "wire transfer",
]


def clean_html(text: str) -> str:
    """Remove HTML tags and unescape HTML entities from email body."""
    # Unescape HTML entities (&amp; -> &, &lt; -> <, etc.)
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_blocklisted(sender_email: str) -> bool:
    """Check if sender email matches any blocklist pattern."""
    sender_lower = sender_email.lower()
    for pattern in BLOCKLIST_PATTERNS:
        if re.search(pattern, sender_lower):
            return True
    return False


def classify_heuristic(subject: str, body: str) -> Tuple[str, float]:
    """
    Apply rule-based heuristic classification to email content.
    
    Returns:
        Tuple of (label, confidence) where confidence in [0, 1]
        Low confidence (<0.6) signals that LLM review is needed.
    """
    text = f"{subject} {body}".lower()
    
    # Check for spam
    for kw in SPAM_KEYWORDS:
        if kw in text:
            return "spam", 0.95
    
    # Score each label
    scores: dict[str, float] = {}
    for rule in HEURISTIC_RULES:
        score = 0.0
        matched = 0
        for kw in rule["keywords"]:
            if kw in text:
                matched += 1
                score += rule["weight"]
        if matched > 0:
            # Confidence bonus for multiple keyword matches
            confidence_bonus = min(0.1 * (matched - 1), 0.3)
            scores[rule["label"]] = score + confidence_bonus

    if not scores:
        return "general_inquiry", 0.3  # Very low confidence — send to LLM

    # Pick the highest-scoring label
    best_label = max(scores, key=scores.__getitem__)
    raw_score = scores[best_label]
    
    # Normalize to confidence range [0.4, 0.95]
    # Higher weight rules produce higher confidence
    max_possible = max(r["weight"] for r in HEURISTIC_RULES) + 0.3
    confidence = min(0.4 + (raw_score / max_possible) * 0.55, 0.95)
    
    return best_label, round(confidence, 3)

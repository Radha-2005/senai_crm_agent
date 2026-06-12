"""
services/classification_service.py - Multi-layer classification pipeline.
Combines heuristic rules + LLM inference with confidence gating.
"""
import logging
from typing import Optional, Tuple

from backend.services.heuristic_service import classify_heuristic
from backend.db.models import SentimentLabel

logger = logging.getLogger(__name__)

# Confidence threshold below which we escalate to LLM
HEURISTIC_CONFIDENCE_THRESHOLD = 0.6

# Sentiment scoring map
SENTIMENT_SCORES = {
    SentimentLabel.POSITIVE.value: 1.0,
    SentimentLabel.NEUTRAL.value: 0.5,
    SentimentLabel.NEGATIVE.value: 0.2,
    SentimentLabel.CRITICAL.value: 0.0,
}


def classify_sentiment(subject: str, body: str) -> Tuple[str, float]:
    """
    Rule-based sentiment analysis using keyword scoring.
    Returns (sentiment_label, confidence).
    """
    text = f"{subject} {body}".lower()

    critical_keywords = [
        "sue", "lawsuit", "legal action", "ransom", "ransomware",
        "final warning", "last chance", "going to court", "attorney",
        "sla breach", "class action", "data breach"
    ]
    negative_keywords = [
        "angry", "frustrated", "terrible", "awful", "unacceptable",
        "disappointed", "furious", "disgrace", "outrage", "scam",
        "refund", "cancel", "worst", "horrible", "useless",
        "cannot", "failed", "broken", "error", "issue"
    ]
    positive_keywords = [
        "thank", "thanks", "great", "excellent", "love", "amazing",
        "wonderful", "perfect", "happy", "pleased", "appreciate",
        "fantastic", "awesome", "brilliant"
    ]

    critical_score = sum(1 for kw in critical_keywords if kw in text)
    negative_score = sum(1 for kw in negative_keywords if kw in text)
    positive_score = sum(1 for kw in positive_keywords if kw in text)

    if critical_score >= 1:
        return SentimentLabel.CRITICAL.value, min(0.7 + critical_score * 0.1, 0.95)
    elif negative_score >= 2:
        return SentimentLabel.NEGATIVE.value, min(0.6 + negative_score * 0.05, 0.90)
    elif positive_score >= 2:
        return SentimentLabel.POSITIVE.value, min(0.6 + positive_score * 0.05, 0.90)
    else:
        return SentimentLabel.NEUTRAL.value, 0.5


def detect_sentiment_deterioration(
    sentiments: list[str],
    window: int = 3,
) -> bool:
    """
    Check if the last N emails in a thread show deteriorating sentiment.
    Used to trigger proactive escalation.
    """
    if len(sentiments) < window:
        return False
    
    recent = sentiments[-window:]
    scores = [SENTIMENT_SCORES.get(s, 0.5) for s in recent]
    
    # Deterioration = STRICTLY decreasing scores (each step worse than the last)
    # Flat/stable sentiment (e.g. all neutral) does NOT count as deterioration
    return all(scores[i] > scores[i + 1] for i in range(len(scores) - 1))


def classify_email(
    subject: str,
    body: str,
    use_llm: bool = False,
) -> Tuple[str, float, str, float]:
    """
    Multi-layer classification pipeline.
    
    Returns:
        Tuple of (classification, classification_confidence, sentiment, sentiment_confidence)
    """
    # Layer 1: Heuristic classification
    heuristic_label, heuristic_confidence = classify_heuristic(subject, body)
    
    # Layer 2: If confidence too low and LLM available, we signal for LLM
    # (Actual LLM call happens in the agent pipeline via llm/classifier.py)
    needs_llm = heuristic_confidence < HEURISTIC_CONFIDENCE_THRESHOLD and use_llm
    
    final_label = heuristic_label
    final_confidence = heuristic_confidence
    
    # Layer 3: Sentiment analysis
    sentiment, sentiment_confidence = classify_sentiment(subject, body)

    if needs_llm:
        logger.info(f"Low confidence ({heuristic_confidence:.2f}) -> LLM review needed")

    return final_label, final_confidence, sentiment, sentiment_confidence

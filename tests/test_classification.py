"""
tests/test_classification.py - Tests for classification and sentiment analysis.
"""
import pytest
from backend.services.heuristic_service import classify_heuristic
from backend.services.classification_service import (
    classify_sentiment,
    detect_sentiment_deterioration,
    classify_email,
    HEURISTIC_CONFIDENCE_THRESHOLD,
)


class TestHeuristicClassification:
    """Test rule-based heuristic classification."""

    def test_gdpr_classification(self):
        """GDPR keywords should classify as legal_gdpr."""
        label, conf = classify_heuristic(
            "GDPR Data Portability Request",
            "I am requesting my right to data portability under GDPR Article 20.",
        )
        assert label == "legal_gdpr"
        assert conf > 0.5

    def test_ransomware_classification(self):
        """Ransomware keywords should classify as security_threat."""
        label, conf = classify_heuristic(
            "Urgent Security Notice",
            "Your systems have been compromised. Pay ransom in bitcoin or data will be published.",
        )
        assert label == "security_threat"
        assert conf > 0.5

    def test_refund_classification(self):
        """Refund keywords should classify correctly."""
        label, conf = classify_heuristic(
            "Refund Request",
            "I want my money back. Please process a refund for my subscription.",
        )
        assert label == "refund_request"

    def test_pricing_classification(self):
        """Pricing inquiry keywords."""
        label, conf = classify_heuristic(
            "Upgrade to Enterprise Plan",
            "Can you tell me the pricing for upgrading to the Enterprise plan with 10 additional seats?",
        )
        assert label == "pricing_inquiry"

    def test_spam_classification(self):
        """Spam keywords."""
        label, conf = classify_heuristic(
            "You've Been Selected!",
            "Congratulations! You are our lottery winner. Click here to win your prize!",
        )
        assert label == "spam"
        assert conf > 0.8

    def test_low_confidence_general(self):
        """Neutral emails should have low confidence."""
        label, conf = classify_heuristic(
            "Hello",
            "Just checking in.",
        )
        # Should return something with low confidence
        assert conf < 0.7

    def test_legal_threat(self):
        """Legal threat keywords should score high."""
        label, conf = classify_heuristic(
            "Notice of Legal Action",
            "My attorney has been notified. We are pursuing legal action. SLA breach confirmed.",
        )
        assert label in ("legal_threat", "security_threat", "legal_gdpr")


class TestSentimentAnalysis:
    """Test sentiment classification."""

    def test_critical_sentiment_legal(self):
        """Legal threats should produce critical sentiment."""
        sentiment, conf = classify_sentiment(
            "Lawsuit Notice",
            "I am going to sue your company. My attorney is ready. SLA breach.",
        )
        assert sentiment == "critical"
        assert conf > 0.6

    def test_negative_sentiment_angry(self):
        """Angry language should produce negative/critical sentiment."""
        sentiment, conf = classify_sentiment(
            "Terrible Service",
            "This is unacceptable. I am extremely frustrated and furious with your awful service.",
        )
        assert sentiment in ("negative", "critical")

    def test_positive_sentiment(self):
        """Positive language should produce positive sentiment."""
        sentiment, conf = classify_sentiment(
            "Thank You!",
            "Thank you so much for the excellent and amazing service! I really appreciate it.",
        )
        assert sentiment == "positive"

    def test_neutral_sentiment(self):
        """Neutral language should produce neutral sentiment."""
        sentiment, conf = classify_sentiment(
            "Feature Question",
            "I am wondering how the export feature works.",
        )
        assert sentiment == "neutral"


class TestSentimentDeterioration:
    """Test sentiment trend detection."""

    def test_deteriorating_sentiment(self):
        """Three consecutive worsening sentiments should trigger deterioration."""
        sentiments = ["positive", "neutral", "negative", "critical"]
        assert detect_sentiment_deterioration(sentiments, window=3) is True

    def test_stable_sentiment(self):
        """Consistent neutral sentiment should not trigger deterioration."""
        sentiments = ["neutral", "neutral", "neutral"]
        assert detect_sentiment_deterioration(sentiments) is False

    def test_improving_sentiment(self):
        """Improving sentiment should not trigger deterioration."""
        sentiments = ["critical", "negative", "neutral"]
        assert detect_sentiment_deterioration(sentiments) is False

    def test_insufficient_history(self):
        """Single email cannot show deterioration."""
        assert detect_sentiment_deterioration(["negative"]) is False

    def test_low_confidence_triggers_llm(self):
        """Test that low confidence is detectable."""
        label, conf, sentiment, _ = classify_email("Hi", "just wondering")
        # Low confidence cases
        assert conf < HEURISTIC_CONFIDENCE_THRESHOLD or label == "general_inquiry"

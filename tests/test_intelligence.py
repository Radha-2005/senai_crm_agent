"""
tests/test_intelligence.py - Tests for web intelligence and reputation service.
"""
import pytest
import time
from backend.web_intelligence.reputation_service import (
    get_company_reputation,
    clear_reputation_cache,
    get_cache_stats,
    _is_cache_valid,
)
from backend.web_intelligence.scraper import extract_sentiment_signals, extract_text_from_html


class TestScraper:
    """Test web scraping utilities."""

    def test_extract_text_from_html(self):
        """HTML content should be converted to plain text."""
        html = "<h1>Title</h1><p>Some content here.</p><script>alert('x')</script>"
        text = extract_text_from_html(html)
        assert "Title" in text
        assert "Some content here" in text
        assert "<h1>" not in text
        assert "<script>" not in text

    def test_sentiment_signal_negative(self):
        """Negative signals should be detected correctly."""
        text = "The company is facing a lawsuit and fraud investigation. Bad reviews everywhere."
        signals = extract_sentiment_signals(text)
        assert signals["negative"] >= 2

    def test_sentiment_signal_positive(self):
        """Positive signals should be detected correctly."""
        text = "Award-winning certified trusted company. Highly rated and recommended partner."
        signals = extract_sentiment_signals(text)
        assert signals["positive"] >= 3

    def test_sentiment_signal_neutral(self):
        """Neutral text should have low signal counts."""
        text = "The company offers software products and services."
        signals = extract_sentiment_signals(text)
        assert signals["positive"] + signals["negative"] == 0


@pytest.mark.anyio
class TestReputationService:
    """Test reputation caching service."""

    async def test_reputation_returns_data(self):
        """Reputation service should return a valid result."""
        result = await get_company_reputation("TestCorp Inc")
        assert "company" in result
        assert "risk_level" in result
        assert "risk_score" in result
        assert result["risk_level"] in ("low", "medium", "high")
        assert 0.0 <= result["risk_score"] <= 1.0

    async def test_reputation_caching(self):
        """Second call for same company should use cache."""
        clear_reputation_cache()
        
        company = "CachingTest Corp"
        # First call
        result1 = await get_company_reputation(company)
        cached_at1 = result1.get("cached_at")
        
        # Second call should be instant (from cache)
        result2 = await get_company_reputation(company)
        cached_at2 = result2.get("cached_at")
        
        assert cached_at1 == cached_at2  # Same cache entry

    async def test_cache_lifecycle(self):
        """Cache entries should be tracked by stats."""
        clear_reputation_cache()
        
        await get_company_reputation("LifecycleTest Inc")
        stats = get_cache_stats()
        
        assert stats["total_entries"] >= 1
        assert stats["valid_entries"] >= 1

    def test_clear_cache(self):
        """Clear cache should remove all entries."""
        count = clear_reputation_cache()
        stats = get_cache_stats()
        assert stats["total_entries"] == 0

    def test_cache_validity(self):
        """Test TTL-based cache validity."""
        fresh_entry = {"cached_at": time.time()}
        stale_entry = {"cached_at": time.time() - 99999}
        
        assert _is_cache_valid(fresh_entry) is True
        assert _is_cache_valid(stale_entry) is False

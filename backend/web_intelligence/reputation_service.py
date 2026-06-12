"""
web_intelligence/reputation_service.py - Company reputation aggregation service.
Caches results to avoid repeated scraping of the same company.
"""
import logging
import time
from typing import Dict, Any, Optional

from backend.config import settings
from backend.web_intelligence.scraper import search_company_news, extract_sentiment_signals

logger = logging.getLogger(__name__)

# In-memory TTL cache for reputation data
_reputation_cache: Dict[str, Dict[str, Any]] = {}


def _is_cache_valid(cached_entry: Dict[str, Any]) -> bool:
    """Check if cached entry is still valid based on TTL."""
    ttl = settings.REPUTATION_CACHE_TTL_SECONDS
    return (time.time() - cached_entry.get("cached_at", 0)) < ttl


async def get_company_reputation(company_name: str) -> Dict[str, Any]:
    """
    Get aggregated reputation data for a company.
    Caches results to reduce repeated HTTP requests.
    
    Returns:
        Dict with reputation score, risk level, recent news, and signals
    """
    cache_key = company_name.lower().strip()
    
    # Check cache
    if cache_key in _reputation_cache and _is_cache_valid(_reputation_cache[cache_key]):
        logger.info(f"Reputation cache hit for: {company_name}")
        return _reputation_cache[cache_key]

    logger.info(f"Fetching reputation data for: {company_name}")

    # Gather news/web signals
    news_items = await search_company_news(company_name)
    
    # Calculate aggregate sentiment from news
    all_text = " ".join(item.get("summary", "") for item in news_items)
    signals = extract_sentiment_signals(all_text)
    
    # Risk score calculation
    neg = signals.get("negative", 0)
    pos = signals.get("positive", 0)
    
    if neg >= 3:
        risk_level = "high"
        risk_score = 0.8 + min(neg * 0.05, 0.15)
    elif neg >= 1:
        risk_level = "medium"
        risk_score = 0.4 + neg * 0.1
    else:
        risk_level = "low"
        risk_score = max(0.1, 0.3 - pos * 0.05)

    result = {
        "company": company_name,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 3),
        "positive_signals": pos,
        "negative_signals": neg,
        "recent_news": news_items[:3],  # Top 3 news items
        "recommendation": _get_recommendation(risk_level),
        "cached_at": time.time(),
    }

    # Store in cache
    _reputation_cache[cache_key] = result
    return result


def _get_recommendation(risk_level: str) -> str:
    """Get handling recommendation based on risk level."""
    recommendations = {
        "high": "HIGH RISK: Prioritize concession or escalation to prevent PR damage",
        "medium": "MEDIUM RISK: Handle carefully, consider proactive outreach",
        "low": "LOW RISK: Standard handling protocol applies",
    }
    return recommendations.get(risk_level, "Standard handling protocol applies")


def clear_reputation_cache() -> int:
    """Clear all cached reputation data. Returns number of entries cleared."""
    count = len(_reputation_cache)
    _reputation_cache.clear()
    return count


def get_cache_stats() -> Dict[str, Any]:
    """Return cache statistics."""
    valid = sum(1 for v in _reputation_cache.values() if _is_cache_valid(v))
    return {
        "total_entries": len(_reputation_cache),
        "valid_entries": valid,
        "expired_entries": len(_reputation_cache) - valid,
        "ttl_seconds": settings.REPUTATION_CACHE_TTL_SECONDS,
    }

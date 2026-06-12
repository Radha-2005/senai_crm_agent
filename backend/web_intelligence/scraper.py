"""
web_intelligence/scraper.py - Web scraping utilities for public company data.
Uses httpx for async HTTP requests with graceful error handling.
"""
import logging
import re
from typing import Optional, Dict, List
import asyncio

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from backend.config import settings

logger = logging.getLogger(__name__)


async def fetch_page(url: str, timeout: int = None) -> Optional[str]:
    """
    Fetch HTML content from a URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds (defaults to config)
    
    Returns:
        HTML string or None on failure
    """
    if not HTTPX_AVAILABLE:
        logger.warning("httpx not available, cannot fetch pages")
        return None

    timeout = timeout or settings.SCRAPE_TIMEOUT_SECONDS
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; SenAI-CRM/1.0; +https://senai.io/bot)"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} fetching {url}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def extract_text_from_html(html: str) -> str:
    """Extract readable text content from HTML."""
    # Remove script and style tags
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_sentiment_signals(text: str) -> Dict[str, int]:
    """
    Extract positive/negative sentiment signals from web content.
    Returns counts of positive vs negative indicators.
    """
    text_lower = text.lower()
    
    negative_signals = [
        "lawsuit", "fraud", "scam", "breach", "hack", "data leak",
        "complaint", "bad reviews", "overcharged", "refund refused",
        "poor service", "terrible", "avoid", "do not use", "warning",
        "class action", "investigation", "fine", "penalty"
    ]
    
    positive_signals = [
        "award", "certified", "trusted", "reliable", "excellent",
        "best in class", "highly rated", "recommended", "partner",
        "growth", "expanding", "innovative", "leader"
    ]
    
    neg_count = sum(1 for s in negative_signals if s in text_lower)
    pos_count = sum(1 for s in positive_signals if s in text_lower)
    
    return {"negative": neg_count, "positive": pos_count}


async def search_company_news(company_name: str) -> List[Dict[str, str]]:
    """
    Simulate searching for recent news about a company.
    In production, this would use a news API (e.g., NewsAPI, Google News).
    
    Returns list of news article summaries.
    """
    # In a real deployment, integrate with a news API
    # For now, return simulated data based on company name patterns
    logger.info(f"Searching news for company: {company_name}")
    
    # Simulate async operation
    await asyncio.sleep(0.1)
    
    return [
        {
            "title": f"Recent activity for {company_name}",
            "summary": "No significant recent news found in public sources.",
            "source": "web_search",
            "sentiment": "neutral",
        }
    ]

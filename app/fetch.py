import feedparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any

from app.config import config

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_feed(feed: Dict[str, Any]) -> Dict[str, Any]:
    """Fetches and parses an RSS feed with retries on failure."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    response = requests.get(
        feed["url"],
        timeout=config["request_timeout_sec"],
        headers=headers
    )
    response.raise_for_status()
    return feedparser.parse(response.content)
import feedparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any, Tuple, Optional
import logging

from app.config import config

logger = logging.getLogger(__name__)

class FeedNotModifiedException(Exception):
    """Excepción lanzada cuando un feed no ha sido modificado (304)."""
    pass

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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_feed_with_cache(feed: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str, str]:
    """Fetches RSS feed with ETag and Last-Modified support.
    
    Returns:
        Tuple[parsed_feed, etag, last_modified]
        - parsed_feed: None si no hay cambios (304), dict con el feed parseado si hay cambios
        - etag: ETag del response
        - last_modified: Last-Modified del response
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    
    # Agregar headers de cache si están disponibles
    if feed.get("etag"):
        headers["If-None-Match"] = feed["etag"]
    
    if feed.get("last_modified"):
        headers["If-Modified-Since"] = feed["last_modified"]
    
    try:
        response = requests.get(
            feed["url"],
            timeout=config["request_timeout_sec"],
            headers=headers
        )
        
        # Si el feed no ha sido modificado
        if response.status_code == 304:
            logger.info(f"Feed {feed['name']} no modificado (304)")
            raise FeedNotModifiedException("Feed not modified")
        
        response.raise_for_status()
        
        # Extraer headers de cache
        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")
        
        # Parsear el feed
        parsed_feed = feedparser.parse(response.content)
        
        logger.info(f"Feed {feed['name']} actualizado. ETag: {etag}, Last-Modified: {last_modified}")
        
        return parsed_feed, etag, last_modified
        
    except FeedNotModifiedException:
        # Re-lanzar para que el caller pueda manejar el caso de no modificado
        raise
    except Exception as e:
        logger.error(f"Error fetching feed {feed['name']}: {e}")
        raise
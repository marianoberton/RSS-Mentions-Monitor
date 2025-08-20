from typing import List, Dict, Any
from app.config import config

def get_enabled_feeds() -> List[Dict[str, Any]]:
    """Returns a list of enabled feeds from the configuration."""
    return [feed for feed in config.get("feeds", []) if feed.get("enabled")]
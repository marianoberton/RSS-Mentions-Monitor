import hashlib
from datetime import datetime
import pytz
from typing import Optional

def get_utc_now() -> datetime:
    return datetime.now(pytz.utc)

def format_date(dt: datetime, tz_name: str) -> str:
    """Formats a datetime object to a string in the specified timezone."""
    tz = pytz.timezone(tz_name)
    return dt.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S %Z')

def escape_html(text: str) -> str:
    """Escapes HTML special characters in a string."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_article_id(entry) -> str:
    """Generates a unique ID for an article."""
    if hasattr(entry, 'id') and entry.id:
        return entry.id
    if hasattr(entry, 'link') and entry.link:
        return entry.link
    
    to_hash = f"{entry.title}{entry.published}{entry.link}"
    return hashlib.sha256(to_hash.encode()).hexdigest()
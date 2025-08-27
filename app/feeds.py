from typing import List, Dict, Any
from app.config import config
from app.storage import get_feeds_ready_for_fetch, init_feed_state_from_config

def get_enabled_feeds() -> List[Dict[str, Any]]:
    """Returns a list of enabled feeds from the configuration."""
    return [feed for feed in config.get("feeds", []) if feed.get("enabled")]

def get_feeds_for_processing() -> List[Dict[str, Any]]:
    """Returns feeds that are ready for processing based on their schedule and state."""
    # Asegurar que el estado de feeds esté inicializado
    init_feed_state_from_config()
    
    # Obtener feeds listos para procesar
    return get_feeds_ready_for_fetch()

def sync_feeds_with_config():
    """Sincroniza el estado de feeds con la configuración actual."""
    init_feed_state_from_config()
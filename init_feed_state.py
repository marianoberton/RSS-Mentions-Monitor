#!/usr/bin/env python3
"""
Script para inicializar el estado de feeds desde la configuración.
Este script debe ejecutarse una vez para migrar al nuevo sistema de ETags y scheduler adaptativo.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import init_db, init_feed_state_from_config, get_feed_health_stats
from app.config import config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Inicializa el estado de feeds y muestra estadísticas."""
    logger.info("Inicializando sistema de estado de feeds...")
    
    # Asegurar que la base de datos esté inicializada
    init_db()
    
    # Inicializar estado de feeds desde configuración
    init_feed_state_from_config()
    
    # Mostrar estadísticas
    stats = get_feed_health_stats()
    
    logger.info(f"\n===== ESTADO DE FEEDS INICIALIZADO =====")
    logger.info(f"Total de feeds: {stats['total_feeds']}")
    logger.info(f"Feeds saludables: {stats['healthy_feeds']}")
    logger.info(f"Feeds con errores: {stats['error_feeds']}")
    
    logger.info("\n===== DETALLE DE FEEDS =====")
    for feed in stats['feeds']:
        status_emoji = "✅" if feed['status'] == 'healthy' else "❌"
        logger.info(f"{status_emoji} {feed['name']} - Intervalo: {feed['fetch_interval_minutes']}min")
        if feed['error_count'] > 0:
            logger.info(f"   Errores: {feed['error_count']} - Último error: {feed['last_error']}")
    
    logger.info("\n✅ Inicialización completada. El sistema ahora usa ETags y scheduler adaptativo.")
    logger.info("💡 Los feeds se procesarán automáticamente según su schedule individual.")

if __name__ == "__main__":
    main()
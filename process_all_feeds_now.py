#!/usr/bin/env python3
"""
Script para procesar todos los feeds de una vez y dejar el sistema completamente actualizado.
"""

import logging
from datetime import datetime
from app.config import config
from app.storage import init_db
from app.tasks import main_task

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_all_feeds():
    """
    Procesa todos los feeds configurados de una vez.
    """
    logger.info("🚀 Iniciando procesamiento completo de todos los feeds...")
    
    # Inicializar base de datos
    init_db()
    logger.info("✅ Base de datos inicializada")
    
    # Obtener feeds configurados
    feeds = config.get('feeds', {})
    if isinstance(feeds, list):
        feed_names = [feed['name'] if isinstance(feed, dict) else str(feed) for feed in feeds]
    else:
        feed_names = list(feeds.keys())
    
    logger.info(f"📊 Feeds configurados: {len(feed_names)}")
    for feed_name in feed_names:
        logger.info(f"  - {feed_name}")
    
    # Procesar todos los feeds
    start_time = datetime.now()
    logger.info(f"⏰ Iniciando procesamiento a las {start_time}")
    
    try:
        main_task()
        logger.info("✅ Procesamiento de feeds completado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error durante el procesamiento: {e}")
        raise
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"⏱️ Procesamiento completado en {duration}")
    
    # Mostrar estadísticas finales
    from app.storage import get_db_connection
    conn = get_db_connection()
    
    # Contar artículos por feed
    cursor = conn.execute("""
        SELECT site, COUNT(*) as count
        FROM articles 
        GROUP BY site 
        ORDER BY count DESC
    """)
    articles_by_feed = cursor.fetchall()
    
    # Contar menciones por feed
    cursor = conn.execute("""
        SELECT a.site, COUNT(h.id) as hits_count
        FROM articles a
        LEFT JOIN hits h ON a.id = h.article_id
        GROUP BY a.site
        ORDER BY hits_count DESC
    """)
    hits_by_feed = cursor.fetchall()
    
    conn.close()
    
    logger.info("\n📊 ESTADÍSTICAS FINALES:")
    logger.info("\n📰 ARTÍCULOS POR FEED:")
    total_articles = 0
    for site, count in articles_by_feed:
        logger.info(f"  {site}: {count} artículos")
        total_articles += count
    
    logger.info(f"\n📊 TOTAL DE ARTÍCULOS: {total_articles}")
    
    logger.info("\n🎯 MENCIONES POR FEED:")
    total_hits = 0
    for site, hits_count in hits_by_feed:
        logger.info(f"  {site}: {hits_count} menciones")
        total_hits += hits_count
    
    logger.info(f"\n🎯 TOTAL DE MENCIONES: {total_hits}")
    logger.info("\n🎉 ¡Sistema completamente actualizado!")

if __name__ == "__main__":
    process_all_feeds()
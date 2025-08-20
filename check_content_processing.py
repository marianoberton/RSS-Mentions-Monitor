import sqlite3
import logging
from app.config import config
from app.storage import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_content_processing():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener el total de artículos
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    
    # Obtener artículos procesados
    cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
    processed_articles = cursor.fetchone()[0]
    
    # Obtener artículos no procesados
    cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
    unprocessed_articles = cursor.fetchone()[0]
    
    # Obtener artículos con contenido completo
    cursor.execute("SELECT COUNT(*) FROM articles WHERE full_content IS NOT NULL")
    articles_with_content = cursor.fetchone()[0]
    
    # Obtener hits
    cursor.execute("SELECT COUNT(*) FROM hits")
    total_hits = cursor.fetchone()[0]
    
    # Obtener hits por palabra clave
    hits_by_keyword = {}
    for keyword in config["keywords"]:
        cursor.execute("SELECT COUNT(*) FROM hits WHERE keyword = ?", (keyword,))
        hits_by_keyword[keyword] = cursor.fetchone()[0]
    
    # Obtener hits por ubicación
    cursor.execute("SELECT where_found, COUNT(*) FROM hits GROUP BY where_found")
    hits_by_location = dict(cursor.fetchall())
    
    # Mostrar resultados
    logger.info("===== ESTADO DE PROCESAMIENTO DE CONTENIDO =====")
    logger.info(f"Total de artículos: {total_articles}")
    logger.info(f"Artículos procesados: {processed_articles}")
    logger.info(f"Artículos no procesados: {unprocessed_articles}")
    logger.info(f"Artículos con contenido completo: {articles_with_content}")
    logger.info("\n===== HITS POR PALABRA CLAVE =====")
    logger.info(f"Total de hits: {total_hits}")
    for keyword, count in hits_by_keyword.items():
        logger.info(f"- {keyword}: {count} hits")
    
    logger.info("\n===== HITS POR UBICACIÓN =====")
    for location, count in hits_by_location.items():
        logger.info(f"- {location}: {count} hits")
    
    # Mostrar algunos ejemplos de artículos con contenido completo
    if articles_with_content > 0:
        logger.info("\n===== EJEMPLOS DE ARTÍCULOS CON CONTENIDO COMPLETO =====")
        cursor.execute("SELECT id, site, title, link, full_content FROM articles WHERE full_content IS NOT NULL LIMIT 2")
        for row in cursor.fetchall():
            article_id, site, title, link, full_content = row
            logger.info(f"ID: {article_id}")
            logger.info(f"Sitio: {site}")
            logger.info(f"Título: {title}")
            logger.info(f"Enlace: {link}")
            logger.info(f"Extracto de contenido: {full_content[:200]}..." if full_content else "Sin contenido")
            logger.info("-" * 80)
    
    conn.close()

if __name__ == "__main__":
    check_content_processing()
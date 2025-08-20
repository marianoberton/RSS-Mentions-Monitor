import sqlite3
import logging
from app.config import config
from app.storage import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_keyword_hits(keyword):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener hits para la palabra clave específica
    cursor.execute("""
    SELECT h.article_id, h.where_found, h.detected_utc, a.site, a.title, a.link 
    FROM hits h 
    JOIN articles a ON h.article_id = a.id 
    WHERE h.keyword = ? 
    ORDER BY h.detected_utc DESC
    """, (keyword,))
    
    hits = cursor.fetchall()
    
    logger.info(f"===== HITS PARA LA PALABRA CLAVE '{keyword}' =====")
    logger.info(f"Total de hits encontrados: {len(hits)}")
    
    if hits:
        logger.info("\nDetalles de los hits:")
        for hit in hits:
            article_id, where_found, detected_utc, site, title, link = hit
            logger.info("-" * 80)
            logger.info(f"ID: {article_id}")
            logger.info(f"Sitio: {site}")
            logger.info(f"Título: {title}")
            logger.info(f"Enlace: {link}")
            logger.info(f"Encontrado en: {where_found}")
            logger.info(f"Fecha de detección: {detected_utc}")
            
            # Si se encontró en el contenido completo, mostrar un extracto
            if where_found == 'content':
                cursor.execute("SELECT full_content FROM articles WHERE id = ?", (article_id,))
                content = cursor.fetchone()[0]
                if content:
                    # Buscar la posición aproximada de la palabra clave en el contenido
                    keyword_pos = content.lower().find(keyword.lower())
                    if keyword_pos >= 0:
                        # Mostrar un extracto alrededor de la palabra clave
                        start = max(0, keyword_pos - 100)
                        end = min(len(content), keyword_pos + len(keyword) + 100)
                        extract = content[start:end]
                        logger.info(f"Extracto: ...{extract}...")
    else:
        logger.info("No se encontraron hits para esta palabra clave.")
    
    conn.close()

if __name__ == "__main__":
    # Verificar hits para "Javier Milei"
    check_keyword_hits("Javier Milei")
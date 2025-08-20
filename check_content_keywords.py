import sqlite3
import logging
import re
from app.config import config
from app.storage import get_db_connection
from app.matcher import normalize_text, find_keyword

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_content_for_keywords():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener artículos con contenido completo
    cursor.execute("""
    SELECT id, site, title, link, full_content 
    FROM articles 
    WHERE content_processed = 1 AND full_content IS NOT NULL
    """)
    
    articles = cursor.fetchall()
    
    logger.info(f"===== VERIFICACIÓN DE PALABRAS CLAVE EN CONTENIDO COMPLETO =====")
    logger.info(f"Total de artículos con contenido completo: {len(articles)}")
    
    keywords = config["keywords"]
    logger.info(f"Palabras clave a buscar: {keywords}")
    
    # Verificar cada artículo para cada palabra clave
    found_in_content = 0
    for article in articles:
        article_id, site, title, link, content = article
        
        # Verificar si ya existe un hit para este artículo con where_found='content'
        cursor.execute("""
        SELECT COUNT(*) FROM hits 
        WHERE article_id = ? AND where_found = 'content'
        """, (article_id,))
        
        has_content_hit = cursor.fetchone()[0] > 0
        
        # Buscar palabras clave en el contenido
        for keyword in keywords:
            if find_keyword(content, [keyword]):
                found_in_content += 1
                logger.info("-" * 80)
                logger.info(f"Palabra clave '{keyword}' encontrada en el contenido de:")
                logger.info(f"ID: {article_id}")
                logger.info(f"Sitio: {site}")
                logger.info(f"Título: {title}")
                logger.info(f"Enlace: {link}")
                logger.info(f"Ya registrado como hit de contenido: {'Sí' if has_content_hit else 'No'}")
                
                # Buscar la posición aproximada de la palabra clave en el contenido
                keyword_pos = content.lower().find(keyword.lower())
                if keyword_pos >= 0:
                    # Mostrar un extracto alrededor de la palabra clave
                    start = max(0, keyword_pos - 100)
                    end = min(len(content), keyword_pos + len(keyword) + 100)
                    extract = content[start:end]
                    logger.info(f"Extracto: ...{extract}...")
                break
    
    if found_in_content == 0:
        logger.info("No se encontraron palabras clave en el contenido de los artículos procesados.")
    else:
        logger.info(f"\nTotal de artículos con palabras clave en el contenido: {found_in_content}")
    
    conn.close()

if __name__ == "__main__":
    check_content_for_keywords()
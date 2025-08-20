#!/usr/bin/env python
"""
Script para procesar artículos pendientes utilizando Playwright.

Este script procesa artículos pendientes que no pudieron ser procesados
correctamente con el método tradicional, utilizando Playwright como alternativa.

Ejecución: python process_with_playwright.py [--limit N] [--site sitio.com]
"""

import logging
import click
import sqlite3
import sys
from app.improved_extractor import extract_with_retry, playwright_available
from app.config import config
from app.matcher import find_keyword
from app.storage import get_db_connection

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--limit', default=50, help='Límite de artículos a procesar')
@click.option('--site', default=None, help='Filtrar por sitio específico (ej: diario3.com.ar)')
def main(limit, site):
    if not playwright_available:
        logger.error("Playwright no está disponible. Instálalo con: python install_playwright.py")
        sys.exit(1)
    
    # Conectar a la base de datos
    conn = sqlite3.connect(config["db_path"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Consultar artículos pendientes
    query = """
    SELECT id, url, title, site, content_processed, content 
    FROM articles 
    WHERE content_processed = 0 AND error IS NULL
    """
    
    params = []
    if site:
        query += " AND site LIKE ?"
        params.append(f"%{site}%")
    
    query += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    articles = cursor.fetchall()
    
    if not articles:
        logger.info("No hay artículos pendientes para procesar.")
        return
    
    logger.info(f"Procesando {len(articles)} artículos pendientes con Playwright...")
    
    # Procesar cada artículo
    processed_count = 0
    success_count = 0
    
    for article in articles:
        article_id = article['id']
        url = article['url']
        title = article['title']
        site = article['site']
        
        logger.info(f"Procesando artículo {article_id}: {title} ({site})")
        
        # Extraer contenido con Playwright
        content = extract_with_retry(url)
        
        if content and len(content) > 200:
            # Actualizar contenido en la base de datos
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE articles SET full_content = ? WHERE id = ?",
                (content, article_id)
            )
            
            # Buscar palabras clave en el contenido
            keywords = config.get('keywords', [])
            keyword_found = find_keyword(content, keywords) or find_keyword(title, keywords)
            
            if keyword_found:
                # Guardar hit encontrado
                now_utc = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                    (article_id, keyword_found, "content", now_utc)
                )
                logger.info(f"✅ Artículo {article_id} procesado con éxito. Se encontró la palabra clave: {keyword_found}")
            else:
                logger.info(f"✅ Artículo {article_id} procesado con éxito. No se encontraron palabras clave.")
            
            # Marcar como procesado
            cursor.execute(
                "UPDATE articles SET content_processed = 1 WHERE id = ?",
                (article_id,)
            )
            
            conn.commit()
            success_count += 1
        else:
            logger.warning(f"❌ No se pudo extraer contenido suficiente para el artículo {article_id}")
        
        processed_count += 1
    
    conn.close()
    
    logger.info(f"Procesamiento completado: {success_count}/{processed_count} artículos procesados con éxito.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script para probar la funcionalidad FTS5.
"""

import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection, search_articles_fts, search_mentions_fts
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_fts_query():
    """Prueba consulta FTS5 directa."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("=== PRUEBA CONSULTA DIRECTA FTS5 ===")
    
    # Probar búsqueda simple en FTS5
    cursor.execute("SELECT COUNT(*) FROM articles_fts WHERE articles_fts MATCH 'Milei'")
    count = cursor.fetchone()[0]
    logger.info(f"Artículos que contienen 'Milei': {count}")
    
    # Obtener algunos resultados
    cursor.execute("""
        SELECT fts.article_id, a.title, a.site
        FROM articles_fts fts
        JOIN articles a ON fts.article_id = a.id
        WHERE articles_fts MATCH 'Milei'
        LIMIT 3
    """)
    
    results = cursor.fetchall()
    logger.info(f"Primeros 3 resultados:")
    for i, (article_id, title, site) in enumerate(results, 1):
        logger.info(f"  {i}. [{site}] {title[:60]}...")
    
    conn.close()

def test_mentions_query():
    """Prueba consulta de menciones con FTS5."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("\n=== PRUEBA CONSULTA MENCIONES ===")
    
    # Verificar que hay hits para artículos que contienen 'Milei'
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles_fts fts
        JOIN articles a ON fts.article_id = a.id
        JOIN hits h ON h.article_id = a.id
        WHERE articles_fts MATCH 'Milei'
    """)
    
    count = cursor.fetchone()[0]
    logger.info(f"Hits en artículos que contienen 'Milei': {count}")
    
    if count > 0:
        # Obtener algunos resultados
        cursor.execute("""
            SELECT h.keyword, h.where_found, h.score, a.title, a.site, p.name
            FROM articles_fts fts
            JOIN articles a ON fts.article_id = a.id
            JOIN hits h ON h.article_id = a.id
            JOIN persons p ON h.person_id = p.id
            WHERE articles_fts MATCH 'Milei'
            ORDER BY h.score DESC
            LIMIT 3
        """)
        
        results = cursor.fetchall()
        logger.info(f"Primeras 3 menciones:")
        for i, (keyword, where_found, score, title, site, person_name) in enumerate(results, 1):
            logger.info(f"  {i}. {person_name} ({keyword}) - Score: {score:.2f} - [{site}] {title[:40]}...")
    
    conn.close()

def test_search_functions():
    """Prueba las funciones de búsqueda."""
    logger.info("\n=== PRUEBA FUNCIONES DE BÚSQUEDA ===")
    
    # Probar search_articles_fts
    logger.info("\nProbando search_articles_fts:")
    articles = search_articles_fts('Milei', limit=3)
    logger.info(f"Encontrados {len(articles)} artículos")
    for i, article in enumerate(articles, 1):
        logger.info(f"  {i}. [{article[2]}] {article[1][:50]}...")
    
    # Probar search_mentions_fts
    logger.info("\nProbando search_mentions_fts:")
    mentions = search_mentions_fts('Milei', limit=3)
    logger.info(f"Encontradas {len(mentions)} menciones")
    for i, mention in enumerate(mentions, 1):
        logger.info(f"  {i}. {mention[8]} ({mention[1]}) - Score: {mention[3]:.2f}")

def main():
    """Función principal de pruebas."""
    logger.info("Iniciando pruebas de FTS5...")
    
    test_direct_fts_query()
    test_mentions_query()
    test_search_functions()
    
    logger.info("\n✅ Pruebas de FTS5 completadas.")

if __name__ == "__main__":
    main()
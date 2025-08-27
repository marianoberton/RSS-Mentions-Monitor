#!/usr/bin/env python3
"""
Script para inicializar FTS5 y poblar la tabla con artículos existentes.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import init_db, populate_fts_table, search_articles_fts, get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fts_search():
    """Prueba la funcionalidad de búsqueda FTS5."""
    logger.info("\n===== PRUEBAS DE BÚSQUEDA FTS5 =====")
    
    # Pruebas de búsqueda
    test_queries = [
        "Milei",
        "elecciones",
        "política",
        "economía",
        "gobierno"
    ]
    
    for query in test_queries:
        logger.info(f"\nBuscando: '{query}'")
        results = search_articles_fts(query, limit=5)
        
        if results:
            logger.info(f"Encontrados {len(results)} resultados:")
            for i, (article_id, title, site, link, published_utc, content, rank) in enumerate(results, 1):
                logger.info(f"  {i}. [{site}] {title[:60]}...")
                logger.info(f"     Rank: {rank}, Fecha: {published_utc}")
        else:
            logger.info("No se encontraron resultados")

def show_fts_stats():
    """Muestra estadísticas de la tabla FTS5."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contar artículos en FTS5
    cursor.execute("SELECT COUNT(*) FROM articles_fts")
    fts_count = cursor.fetchone()[0]
    
    # Contar artículos totales
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_count = cursor.fetchone()[0]
    
    # Verificar que los triggers funcionan
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='trigger' AND name LIKE 'articles_fts_%'
    """)
    triggers = cursor.fetchall()
    
    conn.close()
    
    logger.info(f"\n===== ESTADÍSTICAS FTS5 =====")
    logger.info(f"Artículos en FTS5: {fts_count}")
    logger.info(f"Artículos totales: {total_count}")
    logger.info(f"Cobertura: {(fts_count/total_count*100):.1f}%" if total_count > 0 else "Cobertura: 0%")
    logger.info(f"Triggers activos: {len(triggers)}")
    
    for trigger in triggers:
        logger.info(f"  - {trigger[0]}")

def main():
    """Función principal de inicialización FTS5."""
    logger.info("Iniciando configuración de FTS5...")
    
    # Inicializar base de datos (crea tabla FTS5 y triggers)
    logger.info("Inicializando base de datos...")
    init_db()
    
    # Poblar tabla FTS5 con artículos existentes
    logger.info("Poblando tabla FTS5 con artículos existentes...")
    populated_count = populate_fts_table()
    logger.info(f"Se poblaron {populated_count} artículos en la tabla FTS5")
    
    # Mostrar estadísticas
    show_fts_stats()
    
    # Probar búsquedas
    test_fts_search()
    
    logger.info("\n✅ Configuración de FTS5 completada. El sistema ahora soporta búsqueda rápida.")
    logger.info("\nFunciones disponibles:")
    logger.info("  - search_articles_fts(query, limit=50, person_id=None)")
    logger.info("  - search_mentions_fts(query, person_id=None, limit=50)")
    logger.info("  - populate_fts_table() # Para repoblar si es necesario")

if __name__ == "__main__":
    main()
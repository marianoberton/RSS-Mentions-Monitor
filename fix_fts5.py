#!/usr/bin/env python3
"""
Script para corregir la configuración de FTS5.
"""

import sys
import os
import sqlite3

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_fts5():
    """Corrige la configuración de FTS5."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar tabla FTS5 existente si hay problemas
        logger.info("Eliminando tabla FTS5 existente...")
        cursor.execute("DROP TABLE IF EXISTS articles_fts")
        
        # Eliminar triggers existentes
        logger.info("Eliminando triggers existentes...")
        cursor.execute("DROP TRIGGER IF EXISTS articles_fts_insert")
        cursor.execute("DROP TRIGGER IF EXISTS articles_fts_delete")
        cursor.execute("DROP TRIGGER IF EXISTS articles_fts_update")
        
        # Crear tabla FTS5 sin content_rowid ya que el ID es TEXT
        logger.info("Creando tabla FTS5...")
        cursor.execute("""
            CREATE VIRTUAL TABLE articles_fts USING fts5(
                article_id UNINDEXED,
                title, 
                content, 
                site
            )
        """)
        
        # Crear triggers corregidos
        logger.info("Creando triggers...")
        cursor.execute("""
            CREATE TRIGGER articles_fts_insert AFTER INSERT ON articles BEGIN
                INSERT INTO articles_fts(article_id, title, content, site) 
                VALUES (new.id, new.title, COALESCE(new.full_content, ''), new.site);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER articles_fts_delete AFTER DELETE ON articles BEGIN
                DELETE FROM articles_fts WHERE article_id = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER articles_fts_update AFTER UPDATE ON articles BEGIN
                DELETE FROM articles_fts WHERE article_id = old.id;
                INSERT INTO articles_fts(article_id, title, content, site) 
                VALUES (new.id, new.title, COALESCE(new.full_content, ''), new.site);
            END
        """)
        
        # Poblar tabla FTS5
        logger.info("Poblando tabla FTS5...")
        cursor.execute("""
            INSERT INTO articles_fts(article_id, title, content, site)
            SELECT id, title, COALESCE(full_content, ''), site
            FROM articles
        """)
        
        populated_count = cursor.rowcount
        
        conn.commit()
        
        logger.info(f"\n===== FTS5 CONFIGURADO CORRECTAMENTE =====")
        logger.info(f"Artículos poblados: {populated_count}")
        
        # Verificar que funciona
        logger.info("\nProbando búsqueda...")
        cursor.execute("SELECT COUNT(*) FROM articles_fts WHERE articles_fts MATCH 'Milei'")
        milei_count = cursor.fetchone()[0]
        logger.info(f"Artículos que mencionan 'Milei': {milei_count}")
        
        # Mostrar algunos resultados
        if milei_count > 0:
            cursor.execute("""
                SELECT fts.article_id, a.title, a.site 
                FROM articles_fts fts
                JOIN articles a ON fts.article_id = a.id
                WHERE articles_fts MATCH 'Milei'
                LIMIT 3
            """)
            
            results = cursor.fetchall()
            logger.info("\nEjemplos de resultados:")
            for i, (article_id, title, site) in enumerate(results, 1):
                logger.info(f"  {i}. [{site}] {title[:60]}...")
        
        # Probar otras búsquedas
        test_queries = ['política', 'elecciones', 'gobierno']
        for query in test_queries:
            cursor.execute(f"SELECT COUNT(*) FROM articles_fts WHERE articles_fts MATCH '{query}'")
            count = cursor.fetchone()[0]
            logger.info(f"Artículos que mencionan '{query}': {count}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error configurando FTS5: {e}")
        raise
    finally:
        conn.close()

def main():
    """Función principal."""
    logger.info("Corrigiendo configuración de FTS5...")
    fix_fts5()
    logger.info("\n✅ FTS5 configurado correctamente.")

if __name__ == "__main__":
    main()
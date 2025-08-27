#!/usr/bin/env python3
"""
Script para depurar la búsqueda de menciones FTS5.
"""

import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_mentions_search():
    """Depura paso a paso la búsqueda de menciones."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("=== DEPURACIÓN BÚSQUEDA MENCIONES ===")
    
    # 1. Verificar que hay artículos con 'Milei' en FTS5
    cursor.execute("SELECT COUNT(*) FROM articles_fts WHERE articles_fts MATCH 'Milei'")
    fts_count = cursor.fetchone()[0]
    logger.info(f"1. Artículos en FTS5 que contienen 'Milei': {fts_count}")
    
    # 2. Verificar que hay hits en general
    cursor.execute("SELECT COUNT(*) FROM hits")
    hits_count = cursor.fetchone()[0]
    logger.info(f"2. Total de hits en la base: {hits_count}")
    
    # 3. Verificar que hay artículos en la tabla articles
    cursor.execute("SELECT COUNT(*) FROM articles")
    articles_count = cursor.fetchone()[0]
    logger.info(f"3. Total de artículos: {articles_count}")
    
    # 4. Verificar el JOIN entre FTS5 y articles
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles_fts fts
        JOIN articles a ON fts.article_id = a.id
        WHERE articles_fts MATCH 'Milei'
    """)
    join_count = cursor.fetchone()[0]
    logger.info(f"4. JOIN FTS5 + articles con 'Milei': {join_count}")
    
    # 5. Verificar el JOIN con hits
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles_fts fts
        JOIN articles a ON fts.article_id = a.id
        JOIN hits h ON h.article_id = a.id
        WHERE articles_fts MATCH 'Milei'
    """)
    hits_join_count = cursor.fetchone()[0]
    logger.info(f"5. JOIN FTS5 + articles + hits con 'Milei': {hits_join_count}")
    
    # 6. Verificar el JOIN completo con persons
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles_fts fts
        JOIN articles a ON fts.article_id = a.id
        JOIN hits h ON h.article_id = a.id
        JOIN persons p ON h.person_id = p.id
        WHERE articles_fts MATCH 'Milei'
    """)
    full_join_count = cursor.fetchone()[0]
    logger.info(f"6. JOIN completo con 'Milei': {full_join_count}")
    
    # 7. Si hay resultados, mostrar algunos
    if full_join_count > 0:
        logger.info("\n7. Primeros 3 resultados del JOIN completo:")
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
        for i, (keyword, where_found, score, title, site, person_name) in enumerate(results, 1):
            logger.info(f"   {i}. {person_name} ({keyword}) - Score: {score:.2f}")
            logger.info(f"      [{site}] {title[:60]}...")
    
    # 8. Verificar algunos IDs específicos
    logger.info("\n8. Verificando IDs de artículos:")
    cursor.execute("SELECT article_id FROM articles_fts WHERE articles_fts MATCH 'Milei' LIMIT 3")
    fts_ids = [row[0] for row in cursor.fetchall()]
    logger.info(f"   IDs en FTS5: {fts_ids}")
    
    if fts_ids:
        cursor.execute(f"SELECT id FROM articles WHERE id IN ({','.join(['?' for _ in fts_ids])})", fts_ids)
        article_ids = [row[0] for row in cursor.fetchall()]
        logger.info(f"   IDs en articles: {article_ids}")
        
        cursor.execute(f"SELECT DISTINCT article_id FROM hits WHERE article_id IN ({','.join(['?' for _ in fts_ids])})", fts_ids)
        hit_article_ids = [row[0] for row in cursor.fetchall()]
        logger.info(f"   IDs con hits: {hit_article_ids}")
    
    conn.close()

def main():
    """Función principal de depuración."""
    logger.info("Iniciando depuración de búsqueda de menciones...")
    debug_mentions_search()
    logger.info("\n✅ Depuración completada.")

if __name__ == "__main__":
    main()
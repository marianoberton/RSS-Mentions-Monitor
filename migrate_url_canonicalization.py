#!/usr/bin/env python3
"""
Script para migrar artículos existentes agregando canonicalización de URL y content_hash.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from app.url_utils import canonicalize_url, calculate_content_hash
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_articles():
    """Migra artículos existentes agregando canonicalización y content_hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener artículos sin canonicalización
        cursor.execute("""
            SELECT id, title, link, full_content 
            FROM articles 
            WHERE canonical_url IS NULL OR content_hash IS NULL
        """)
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        
        if total_articles == 0:
            logger.info("No hay artículos para migrar.")
            return
            
        logger.info(f"Migrando {total_articles} artículos...")
        
        updated_count = 0
        duplicates_found = 0
        
        for i, (article_id, title, link, full_content) in enumerate(articles, 1):
            try:
                # Canonicalizar URL
                canonical_url = canonicalize_url(link)
                
                # Calcular content hash
                content_hash = calculate_content_hash(title, full_content)
                
                # Verificar si ya existe un artículo con la misma URL canónica y content hash
                cursor.execute("""
                    SELECT id FROM articles 
                    WHERE canonical_url = ? AND content_hash = ? AND id != ?
                    LIMIT 1
                """, (canonical_url, content_hash, article_id))
                
                existing_duplicate = cursor.fetchone()
                
                if existing_duplicate:
                    duplicates_found += 1
                    logger.warning(f"Duplicado encontrado: artículo {article_id} es duplicado de {existing_duplicate[0]}")
                
                # Actualizar el artículo con los nuevos campos
                cursor.execute("""
                    UPDATE articles 
                    SET canonical_url = ?, content_hash = ?
                    WHERE id = ?
                """, (canonical_url, content_hash, article_id))
                
                updated_count += 1
                
                if i % 100 == 0:
                    logger.info(f"Progreso: {i}/{total_articles} artículos procesados")
                    conn.commit()  # Commit periódico
                    
            except Exception as e:
                logger.error(f"Error procesando artículo {article_id}: {e}")
                continue
        
        conn.commit()
        
        logger.info(f"\n===== MIGRACIÓN COMPLETADA =====")
        logger.info(f"Artículos actualizados: {updated_count}")
        logger.info(f"Duplicados encontrados: {duplicates_found}")
        
        # Mostrar estadísticas de duplicados
        cursor.execute("""
            SELECT canonical_url, content_hash, COUNT(*) as count
            FROM articles 
            WHERE canonical_url IS NOT NULL AND content_hash IS NOT NULL
            GROUP BY canonical_url, content_hash
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        
        duplicate_groups = cursor.fetchall()
        
        if duplicate_groups:
            logger.info(f"\n===== TOP 10 GRUPOS DE DUPLICADOS =====")
            for canonical_url, content_hash, count in duplicate_groups:
                logger.info(f"URL: {canonical_url[:80]}... - {count} duplicados")
        
        # Crear índices únicos si no existen
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_canonical_content ON articles(canonical_url, content_hash)")
            logger.info("Índice único creado para prevenir futuros duplicados")
        except Exception as e:
            logger.warning(f"No se pudo crear índice único (puede que ya existan duplicados): {e}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error durante la migración: {e}")
        raise
    finally:
        conn.close()

def clean_duplicates():
    """Limpia artículos duplicados manteniendo el más reciente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        logger.info("Identificando y limpiando duplicados...")
        
        # Encontrar duplicados y mantener solo el más reciente
        cursor.execute("""
            DELETE FROM articles 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM articles 
                WHERE canonical_url IS NOT NULL AND content_hash IS NOT NULL
                GROUP BY canonical_url, content_hash
            )
            AND canonical_url IS NOT NULL 
            AND content_hash IS NOT NULL
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"Artículos duplicados eliminados: {deleted_count}")
        
        # Ahora intentar crear el índice único
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_canonical_content ON articles(canonical_url, content_hash)")
            logger.info("✅ Índice único creado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error creando índice único: {e}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error limpiando duplicados: {e}")
        raise
    finally:
        conn.close()

def main():
    """Función principal de migración."""
    logger.info("Iniciando migración de canonicalización de URLs...")
    
    # Paso 1: Migrar artículos existentes
    migrate_articles()
    
    # Paso 2: Preguntar si limpiar duplicados
    response = input("\n¿Deseas limpiar artículos duplicados? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'sí', 's']:
        clean_duplicates()
    else:
        logger.info("Limpieza de duplicados omitida. Puedes ejecutarla más tarde si es necesario.")
    
    logger.info("\n✅ Migración completada. El sistema ahora usa canonicalización de URLs y deduplicación.")

if __name__ == "__main__":
    main()
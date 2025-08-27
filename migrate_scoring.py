#!/usr/bin/env python3
"""
Script para migrar hits existentes y calcular sus scores.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection, init_db
from app.scoring import calculate_mention_score, get_person_keywords_map
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_hit_scores():
    """Migra hits existentes calculando sus scores."""
    # Asegurar que la base de datos esté inicializada
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener hits sin score o con score 0
        cursor.execute("""
            SELECT h.id, h.article_id, h.person_id, h.keyword, h.where_found,
                   a.site, a.title, a.published_utc
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            WHERE h.score IS NULL OR h.score = 0.0
        """)
        
        hits = cursor.fetchall()
        total_hits = len(hits)
        
        if total_hits == 0:
            logger.info("No hay hits para migrar.")
            return
            
        logger.info(f"Migrando {total_hits} hits...")
        
        updated_count = 0
        
        for i, (hit_id, article_id, person_id, keyword, where_found, 
                site, title, published_utc) in enumerate(hits, 1):
            try:
                # Preparar datos para el cálculo de score
                article_data = {
                    'site': site,
                    'title': title,
                    'published_utc': published_utc
                }
                
                hit_data = {
                    'keyword': keyword,
                    'where_found': where_found,
                    'person_id': person_id
                }
                
                # Obtener keywords de la persona
                person_keywords = get_person_keywords_map(person_id) if person_id else {}
                
                # Calcular score
                score = calculate_mention_score(article_data, hit_data, person_keywords)
                
                # Actualizar score
                cursor.execute("UPDATE hits SET score = ? WHERE id = ?", (score, hit_id))
                
                updated_count += 1
                
                if i % 100 == 0:
                    logger.info(f"Progreso: {i}/{total_hits} hits procesados")
                    conn.commit()  # Commit periódico
                    
            except Exception as e:
                logger.error(f"Error procesando hit {hit_id}: {e}")
                continue
        
        conn.commit()
        
        logger.info(f"\n===== MIGRACIÓN DE SCORES COMPLETADA =====")
        logger.info(f"Hits actualizados: {updated_count}")
        
        # Mostrar estadísticas de scores
        cursor.execute("""
            SELECT 
                COUNT(*) as total_hits,
                AVG(score) as avg_score,
                MIN(score) as min_score,
                MAX(score) as max_score,
                COUNT(CASE WHEN score >= 7.0 THEN 1 END) as high_score_hits,
                COUNT(CASE WHEN score >= 5.0 AND score < 7.0 THEN 1 END) as medium_score_hits,
                COUNT(CASE WHEN score < 5.0 THEN 1 END) as low_score_hits
            FROM hits
            WHERE score IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        
        if stats:
            logger.info(f"\n===== ESTADÍSTICAS DE SCORES =====")
            logger.info(f"Total hits: {stats[0]}")
            logger.info(f"Score promedio: {stats[1]:.2f}")
            logger.info(f"Score mínimo: {stats[2]:.2f}")
            logger.info(f"Score máximo: {stats[3]:.2f}")
            logger.info(f"Hits de alto score (≥7.0): {stats[4]}")
            logger.info(f"Hits de score medio (5.0-6.9): {stats[5]}")
            logger.info(f"Hits de score bajo (<5.0): {stats[6]}")
        
        # Mostrar top 10 hits por score
        cursor.execute("""
            SELECT h.score, h.keyword, h.where_found, a.title, a.site, p.name
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            JOIN persons p ON h.person_id = p.id
            WHERE h.score IS NOT NULL
            ORDER BY h.score DESC
            LIMIT 10
        """)
        
        top_hits = cursor.fetchall()
        
        if top_hits:
            logger.info(f"\n===== TOP 10 HITS POR SCORE =====")
            for score, keyword, where_found, title, site, person_name in top_hits:
                logger.info(f"Score: {score:.2f} | {person_name} ({keyword}) en {where_found} | {title[:50]}...")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error durante la migración: {e}")
        raise
    finally:
        conn.close()

def main():
    """Función principal de migración."""
    logger.info("Iniciando migración de scores para hits...")
    
    migrate_hit_scores()
    
    logger.info("\n✅ Migración de scores completada. El sistema ahora calcula scores automáticamente.")

if __name__ == "__main__":
    main()
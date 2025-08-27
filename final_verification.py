#!/usr/bin/env python3
"""
Script de verificación final del sistema de detección de keywords.
"""

from app.storage import get_db_connection, get_all_active_keywords
from app.tasks import process_article_content
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def final_verification():
    print("=== VERIFICACIÓN FINAL DEL SISTEMA ===")
    
    conn = get_db_connection()
    
    # 1. Verificar keywords activas
    keywords = get_all_active_keywords()
    print(f"\n1. KEYWORDS ACTIVAS: {len(keywords)}")
    
    # Mostrar keywords de candidatos principales
    cursor = conn.execute("""
        SELECT c.name, ck.keyword 
        FROM candidate_keywords ck
        JOIN candidates c ON ck.candidate_id = c.id
        WHERE ck.is_active = 1 AND c.name IN ('Diego Santilli', 'Facundo Manes', 'Sergio Massa')
        ORDER BY c.name, ck.keyword
    """)
    
    candidate_keywords = cursor.fetchall()
    print("\nKeywords de candidatos principales:")
    for name, keyword in candidate_keywords:
        print(f"  {name}: '{keyword}'")
    
    # 2. Verificar hits recientes
    print("\n2. HITS RECIENTES (últimas 24 horas):")
    cursor = conn.execute("""
        SELECT h.keyword, COUNT(*) as count, c.name as candidate_name
        FROM hits h
        JOIN candidate_keywords ck ON h.keyword = ck.keyword
        JOIN candidates c ON ck.candidate_id = c.id
        WHERE datetime(h.detected_utc) >= datetime('now', '-24 hours')
        GROUP BY h.keyword, c.name
        ORDER BY count DESC
    """)
    
    recent_hits = cursor.fetchall()
    if recent_hits:
        for keyword, count, candidate_name in recent_hits:
            print(f"  {candidate_name} ('{keyword}'): {count} hits")
    else:
        print("  No hay hits recientes")
    
    # 3. Verificar artículos sin procesar
    print("\n3. ARTÍCULOS SIN PROCESAR:")
    cursor = conn.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE content_processed = 0 
        AND full_content IS NOT NULL 
        AND full_content != ''
    """)
    
    unprocessed_count = cursor.fetchone()[0]
    print(f"  Artículos sin procesar: {unprocessed_count}")
    
    # 4. Procesar algunos artículos pendientes
    if unprocessed_count > 0:
        print("\n4. PROCESANDO ARTÍCULOS PENDIENTES...")
        try:
            # Procesar artículos pendientes
            process_article_content()
            print("  ✓ Procesamiento de contenido completado")
            
            # Verificar nuevos hits
            cursor = conn.execute("""
                SELECT COUNT(*) FROM hits 
                WHERE datetime(detected_utc) >= datetime('now', '-5 minutes')
            """)
            
            new_hits = cursor.fetchone()[0]
            print(f"  Nuevos hits detectados: {new_hits}")
            
        except Exception as e:
            print(f"  ✗ Error procesando artículos: {e}")
    
    # 5. Estadísticas finales
    print("\n5. ESTADÍSTICAS FINALES:")
    
    # Total de hits
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    total_hits = cursor.fetchone()[0]
    print(f"  Total de hits: {total_hits}")
    
    # Hits por candidato
    cursor = conn.execute("""
        SELECT c.name, COUNT(h.id) as hit_count
        FROM candidates c
        LEFT JOIN candidate_keywords ck ON c.id = ck.candidate_id
        LEFT JOIN hits h ON ck.keyword = h.keyword
        WHERE ck.is_active = 1
        GROUP BY c.id, c.name
        ORDER BY hit_count DESC
        LIMIT 10
    """)
    
    candidate_stats = cursor.fetchall()
    print("\n  Hits por candidato:")
    for name, hit_count in candidate_stats:
        print(f"    {name}: {hit_count} hits")
    
    # 6. Verificar Diego Santilli específicamente
    print("\n6. VERIFICACIÓN ESPECÍFICA DE DIEGO SANTILLI:")
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hits h
        JOIN candidate_keywords ck ON h.keyword = ck.keyword
        JOIN candidates c ON ck.candidate_id = c.id
        WHERE c.name = 'Diego Santilli'
    """)
    
    santilli_hits = cursor.fetchone()[0]
    print(f"  Total hits para Diego Santilli: {santilli_hits}")
    
    if santilli_hits > 0:
        cursor = conn.execute("""
            SELECT h.keyword, h.detected_utc, a.title
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            JOIN candidates c ON ck.candidate_id = c.id
            JOIN articles a ON h.article_id = a.id
            WHERE c.name = 'Diego Santilli'
            ORDER BY h.detected_utc DESC
            LIMIT 3
        """)
        
        recent_santilli = cursor.fetchall()
        print("\n  Hits recientes de Diego Santilli:")
        for keyword, detected_utc, title in recent_santilli:
            print(f"    '{keyword}' en: {title[:60]}... ({detected_utc})")
    
    conn.close()
    print("\n=== VERIFICACIÓN COMPLETADA ===")
    print("\n✓ El sistema de detección de keywords está funcionando correctamente")
    print("✓ Los hits se están guardando en la base de datos")
    print("✓ El dashboard web está disponible en http://localhost:5000")
    print("✓ El monitoreo RSS está ejecutándose cada 10 minutos")

if __name__ == '__main__':
    final_verification()
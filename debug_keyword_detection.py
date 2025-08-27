#!/usr/bin/env python3
"""
Script de diagnóstico detallado para la detección de keywords de candidatos.
"""

import sqlite3
from app.storage import get_db_connection, get_all_active_keywords
from app.tasks import process_article_content
import re
from datetime import datetime, timedelta

def debug_keyword_detection():
    print("=== DIAGNÓSTICO DE DETECCIÓN DE KEYWORDS ===")
    
    # 1. Verificar keywords activas
    keywords = get_all_active_keywords()
    print(f"\n1. Keywords activas: {len(keywords)}")
    
    candidate_keywords = []
    config_keywords = []
    
    conn = get_db_connection()
    
    # Separar keywords por origen
    with conn:
        cursor = conn.execute("SELECT keyword FROM candidate_keywords WHERE is_active = 1")
        candidate_keywords = [row[0] for row in cursor.fetchall()]
        
    # Keywords de config (asumiendo que son las que no están en candidate_keywords)
    config_keywords = [k for k in keywords if k not in candidate_keywords]
    
    print(f"   - Keywords de config: {len(config_keywords)} -> {config_keywords}")
    print(f"   - Keywords de candidatos: {len(candidate_keywords)}")
    
    # 2. Verificar candidatos específicos
    target_candidates = ['Diego Santilli', 'Facundo Manes', 'Sergio Massa']
    
    print(f"\n2. Keywords para candidatos objetivo:")
    for candidate_name in target_candidates:
        with conn:
            cursor = conn.execute("""
                SELECT ck.keyword 
                FROM candidate_keywords ck
                JOIN candidates c ON ck.candidate_id = c.id
                WHERE c.name = ? AND ck.is_active = 1
            """, (candidate_name,))
            candidate_kws = [row[0] for row in cursor.fetchall()]
            print(f"   - {candidate_name}: {candidate_kws}")
    
    # 3. Buscar artículos que contengan estas keywords
    print(f"\n3. Artículos que contienen keywords de candidatos objetivo:")
    
    search_terms = {
        'Diego Santilli': ['santilli', 'diego santilli'],
        'Facundo Manes': ['manes', 'facundo manes', 'facundo'],
        'Sergio Massa': ['massa', 'sergio massa']
    }
    
    for candidate_name, terms in search_terms.items():
        print(f"\n   {candidate_name}:")
        
        for term in terms:
            with conn:
                # Buscar en títulos
                cursor = conn.execute("""
                    SELECT COUNT(*), MIN(published_utc), MAX(published_utc)
                    FROM articles 
                    WHERE LOWER(title) LIKE ? AND published_utc > ?
                """, (f'%{term.lower()}%', (datetime.now() - timedelta(days=7)).isoformat()))
                title_count, min_date, max_date = cursor.fetchone()
                
                # Buscar en contenido
                cursor = conn.execute("""
                    SELECT COUNT(*), MIN(published_utc), MAX(published_utc)
                    FROM articles 
                    WHERE LOWER(full_content) LIKE ? AND published_utc > ? AND full_content IS NOT NULL AND full_content != ''
                """, (f'%{term.lower()}%', (datetime.now() - timedelta(days=7)).isoformat()))
                content_count, min_date_content, max_date_content = cursor.fetchone()
                
                print(f"     '{term}' -> Títulos: {title_count}, Contenido: {content_count}")
                if title_count > 0:
                    print(f"       Fechas en títulos: {min_date} a {max_date}")
                if content_count > 0:
                    print(f"       Fechas en contenido: {min_date_content} a {max_date_content}")
    
    # 4. Verificar hits existentes
    print(f"\n4. Hits existentes para candidatos objetivo:")
    
    for candidate_name in target_candidates:
        with conn:
            cursor = conn.execute("""
                SELECT COUNT(*), h.keyword, MIN(h.detected_utc), MAX(h.detected_utc)
                FROM hits h
                JOIN candidate_keywords ck ON h.keyword = ck.keyword
                JOIN candidates c ON ck.candidate_id = c.id
                WHERE c.name = ?
                GROUP BY h.keyword
            """, (candidate_name,))
            hits = cursor.fetchall()
            
            if hits:
                print(f"   {candidate_name}:")
                for count, keyword, min_date, max_date in hits:
                    print(f"     '{keyword}': {count} hits ({min_date} a {max_date})")
            else:
                print(f"   {candidate_name}: Sin hits")
    
    # 5. Probar detección manual
    print(f"\n5. Prueba de detección manual:")
    
    # Tomar un artículo reciente que contenga 'santilli'
    with conn:
        cursor = conn.execute("""
            SELECT id, title, full_content, link, published_utc
            FROM articles 
            WHERE LOWER(full_content) LIKE '%santilli%' 
            AND published_utc > ?
            AND full_content IS NOT NULL AND full_content != ''
            ORDER BY published_utc DESC
            LIMIT 1
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))
        
        article = cursor.fetchone()
        
        if article:
            article_id, title, content, url, published_utc = article
            print(f"   Artículo de prueba: {title[:100]}...")
            print(f"   URL: {url}")
            print(f"   Fecha: {published_utc}")
            
            # Verificar si ya tiene hits
            cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE article_id = ?", (article_id,))
            existing_hits = cursor.fetchone()[0]
            print(f"   Hits existentes: {existing_hits}")
            
            # Buscar 'santilli' en el contenido manualmente
            if content:
                santilli_matches = len(re.findall(r'santilli', content.lower()))
                print(f"   Ocurrencias de 'santilli' en contenido: {santilli_matches}")
                
                # Mostrar contexto de las primeras menciones
                if santilli_matches > 0:
                    for i, match in enumerate(re.finditer(r'.{0,50}santilli.{0,50}', content.lower())):
                        if i < 3:  # Solo las primeras 3
                            print(f"     Contexto {i+1}: ...{match.group()}...")
            
            # Intentar procesar este artículo específicamente
            print(f"   Procesando artículo manualmente...")
            try:
                process_article_content(article_id)
                
                # Verificar hits después del procesamiento
                cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE article_id = ?", (article_id,))
                new_hits = cursor.fetchone()[0]
                print(f"   Hits después del procesamiento: {new_hits}")
                
                if new_hits > existing_hits:
                    cursor = conn.execute("""
                        SELECT keyword, where_found, detected_utc
                        FROM hits 
                        WHERE article_id = ?
                        ORDER BY detected_utc DESC
                        LIMIT 5
                    """, (article_id,))
                    recent_hits = cursor.fetchall()
                    print(f"   Nuevos hits detectados:")
                    for keyword, where_found, detected_utc in recent_hits:
                        print(f"     '{keyword}' en {where_found}: {detected_utc}")
                        
            except Exception as e:
                print(f"   Error al procesar artículo: {e}")
        else:
            print(f"   No se encontraron artículos recientes con 'santilli'")
    
    conn.close()
    print(f"\n=== DIAGNÓSTICO COMPLETADO ===")

if __name__ == '__main__':
    debug_keyword_detection()
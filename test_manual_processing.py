#!/usr/bin/env python3
"""
Script para probar el procesamiento manual de un artículo específico que contiene 'santilli'.
"""

import sqlite3
from app.storage import get_db_connection, get_all_active_keywords, save_article_and_hit
from app.matcher import find_keyword
from app.utils import get_utc_now
from app.improved_extractor import extract_with_retry
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_manual_processing():
    print("=== PRUEBA DE PROCESAMIENTO MANUAL ===")
    
    # 1. Obtener keywords activas
    keywords = get_all_active_keywords()
    print(f"Keywords activas: {len(keywords)}")
    
    # Verificar keywords de candidatos específicos
    candidate_keywords = []
    conn = get_db_connection()
    
    with conn:
        cursor = conn.execute("""
            SELECT c.name, ck.keyword 
            FROM candidate_keywords ck
            JOIN candidates c ON ck.candidate_id = c.id
            WHERE ck.is_active = 1 AND c.name IN ('Diego Santilli', 'Facundo Manes', 'Sergio Massa')
            ORDER BY c.name, ck.keyword
        """)
        candidate_keywords = cursor.fetchall()
    
    print(f"\nKeywords de candidatos objetivo:")
    for name, keyword in candidate_keywords:
        print(f"  {name}: '{keyword}'")
    
    # 2. Buscar un artículo que contenga 'santilli'
    with conn:
        cursor = conn.execute("""
            SELECT id, title, full_content, link, published_utc, site
            FROM articles 
            WHERE LOWER(full_content) LIKE '%santilli%' 
            AND published_utc > ?
            AND full_content IS NOT NULL AND full_content != ''
            ORDER BY published_utc DESC
            LIMIT 1
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))
        
        article = cursor.fetchone()
    
    if not article:
        print("\nNo se encontró ningún artículo con 'santilli' en los últimos 7 días")
        return
    
    article_id, title, content, url, published_utc, site = article
    print(f"\n=== ARTÍCULO DE PRUEBA ===")
    print(f"ID: {article_id}")
    print(f"Título: {title}")
    print(f"URL: {url}")
    print(f"Sitio: {site}")
    print(f"Fecha: {published_utc}")
    print(f"Longitud del contenido: {len(content)} caracteres")
    
    # 3. Verificar hits existentes
    with conn:
        cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE article_id = ?", (article_id,))
        existing_hits = cursor.fetchone()[0]
    
    print(f"Hits existentes: {existing_hits}")
    
    # 4. Buscar keywords manualmente en el contenido
    print(f"\n=== BÚSQUEDA MANUAL DE KEYWORDS ===")
    
    # Buscar todas las keywords en el contenido
    found_keywords = []
    for keyword in keywords:
        if keyword.lower() in content.lower():
            found_keywords.append(keyword)
    
    print(f"Keywords encontradas manualmente: {found_keywords}")
    
    # 5. Usar la función find_keyword del sistema
    system_keyword = find_keyword(content, keywords)
    print(f"Keyword encontrada por el sistema: {system_keyword}")
    
    # 6. Si el sistema no encuentra keyword, investigar por qué
    if not system_keyword and found_keywords:
        print(f"\n¡PROBLEMA DETECTADO!")
        print(f"Se encontraron keywords manualmente pero el sistema no las detecta")
        print(f"Keywords encontradas manualmente: {found_keywords}")
        
        # Probar con la primera keyword encontrada
        test_keyword = found_keywords[0]
        print(f"\nProbando con keyword: '{test_keyword}'")
        
        # Verificar si está en la lista de keywords activas
        if test_keyword in keywords:
            print(f"✓ '{test_keyword}' está en la lista de keywords activas")
        else:
            print(f"✗ '{test_keyword}' NO está en la lista de keywords activas")
        
        # Buscar variaciones de case
        for kw in keywords:
            if kw.lower() == test_keyword.lower():
                print(f"Encontrada variación de case: '{kw}' vs '{test_keyword}'")
    
    # 7. Si el sistema encuentra una keyword, crear el hit
    if system_keyword:
        print(f"\n=== CREANDO HIT ===")
        
        now_utc = get_utc_now()
        hit = {
            "article_id": article_id,
            "keyword": system_keyword,
            "where_found": "content",
            "detected_utc": now_utc.isoformat(),
        }
        
        # Obtener detalles del artículo
        article_details = {
            "id": article_id,
            "site": site,
            "title": title,
            "link": url,
            "published_utc": published_utc,
            "inserted_utc": published_utc  # Usar published_utc como fallback
        }
        
        try:
            # Intentar guardar el hit
            save_article_and_hit(article_details, hit)
            print(f"✓ Hit creado exitosamente para keyword '{system_keyword}'")
            
            # Verificar que se guardó
            with conn:
                cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE article_id = ?", (article_id,))
                new_hits = cursor.fetchone()[0]
            
            print(f"Hits después de crear: {new_hits} (antes: {existing_hits})")
            
        except Exception as e:
            print(f"✗ Error al crear hit: {e}")
    
    # 8. Mostrar contexto de las menciones
    print(f"\n=== CONTEXTO DE MENCIONES ===")
    
    import re
    for keyword in found_keywords[:3]:  # Solo las primeras 3
        pattern = rf'.{{0,50}}{re.escape(keyword.lower())}.{{0,50}}'
        matches = re.finditer(pattern, content.lower())
        
        print(f"\nContextos para '{keyword}':")
        for i, match in enumerate(matches):
            if i < 2:  # Solo los primeros 2 contextos
                context = match.group()
                print(f"  {i+1}: ...{context}...")
    
    conn.close()
    print(f"\n=== PRUEBA COMPLETADA ===")

if __name__ == '__main__':
    test_manual_processing()
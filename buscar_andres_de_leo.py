#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection

print("=== BÚSQUEDA DE MENCIONES DE ANDRES DE LEO ===")
print("Buscando menciones existentes en la base de datos...\n")

conn = get_db_connection()
with conn:
    # Buscar en hits por keyword
    cursor = conn.execute("""
        SELECT h.id, a.title, h.keyword, h.where_found, h.detected_utc, a.link, a.site
        FROM hits h 
        JOIN articles a ON h.article_id = a.id 
        WHERE h.keyword LIKE '%Andres%' OR h.keyword LIKE '%de Leo%'
        ORDER BY h.detected_utc DESC 
        LIMIT 20
    """)
    
    mentions_hits = cursor.fetchall()
    
    # Buscar en títulos de artículos
    cursor = conn.execute("""
        SELECT id, title, site, link, published_utc
        FROM articles 
        WHERE title LIKE '%Andres de Leo%' OR title LIKE '%Andrés de Leo%'
        ORDER BY published_utc DESC 
        LIMIT 20
    """)
    
    mentions_titles = cursor.fetchall()
    
    # No buscar en contenido ya que la columna no existe
    mentions_content = []

print(f"📊 RESULTADOS DE BÚSQUEDA:")
print(f"• Menciones en hits (keywords): {len(mentions_hits)}")
print(f"• Menciones en títulos: {len(mentions_titles)}")
print(f"• Menciones en contenido: {len(mentions_content)}")

if mentions_hits:
    print("\n📰 MENCIONES EN HITS (KEYWORDS):")
    for i, mention in enumerate(mentions_hits, 1):
        hit_id, title, keyword, where_found, detected_utc, link, site = mention
        print(f"{i}. {title[:60]}... ({site})")
        print(f"   Keyword: {keyword} (en {where_found})")
        print(f"   Fecha: {detected_utc}")
        print(f"   Link: {link}")
        print()

if mentions_titles:
    print("\n📰 MENCIONES EN TÍTULOS:")
    for i, mention in enumerate(mentions_titles, 1):
        article_id, title, site, link, published_utc = mention
        print(f"{i}. {title} ({site})")
        print(f"   Fecha: {published_utc}")
        print(f"   Link: {link}")
        print()

if mentions_content:
    print("\n📰 MENCIONES EN CONTENIDO:")
    for i, mention in enumerate(mentions_content, 1):
        article_id, title, site, link, published_utc = mention
        print(f"{i}. {title} ({site})")
        print(f"   Fecha: {published_utc}")
        print(f"   Link: {link}")
        print()

if not mentions_hits and not mentions_titles and not mentions_content:
    print("\n❌ No se encontraron menciones previas de 'Andres de Leo' en la base de datos.")
    print("Esto es normal si es la primera vez que se agrega esta persona.")

print("\n=== BÚSQUEDA COMPLETADA ===")
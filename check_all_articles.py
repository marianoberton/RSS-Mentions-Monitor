#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection

def check_all_articles():
    """Verificar todos los artículos en la base de datos."""
    conn = get_db_connection()
    
    # Contar total de artículos
    cursor = conn.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    
    # Contar total de hits
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    total_hits = cursor.fetchone()[0]
    
    print(f"Total de artículos: {total_articles}")
    print(f"Total de hits: {total_hits}")
    print("=" * 50)
    
    # Mostrar últimos 10 artículos
    cursor = conn.execute("""
        SELECT title, site, published_utc, link
        FROM articles 
        ORDER BY published_utc DESC 
        LIMIT 10
    """)
    
    articles = cursor.fetchall()
    
    print("Últimos 10 artículos:")
    for i, row in enumerate(articles, 1):
        print(f"{i}. {row[0]}")
        print(f"   Sitio: {row[1]}")
        print(f"   Fecha: {row[2]}")
        print(f"   Link: {row[3]}")
        print("-" * 40)
    
    # Mostrar últimos hits
    cursor = conn.execute("""
        SELECT h.keyword, h.where_found, a.title, a.site, h.detected_utc
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        ORDER BY h.detected_utc DESC
        LIMIT 10
    """)
    
    hits = cursor.fetchall()
    
    print("\nÚltimos 10 hits:")
    for i, row in enumerate(hits, 1):
        print(f"{i}. Palabra: {row[0]}")
        print(f"   Encontrado en: {row[1]}")
        print(f"   Artículo: {row[2]}")
        print(f"   Sitio: {row[3]}")
        print(f"   Fecha: {row[4]}")
        print("-" * 40)
    
    # Buscar cualquier mención de "Liberman" (case insensitive)
    cursor = conn.execute("""
        SELECT h.keyword, h.where_found, a.title, a.site, h.detected_utc
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        WHERE LOWER(h.keyword) LIKE '%liberman%' 
           OR LOWER(a.title) LIKE '%liberman%'
        ORDER BY h.detected_utc DESC
    """)
    
    liberman_hits = cursor.fetchall()
    
    print(f"\nBúsqueda de 'Liberman' (case insensitive): {len(liberman_hits)} resultados")
    for i, row in enumerate(liberman_hits, 1):
        print(f"{i}. Palabra: {row[0]}")
        print(f"   Encontrado en: {row[1]}")
        print(f"   Artículo: {row[2]}")
        print(f"   Sitio: {row[3]}")
        print(f"   Fecha: {row[4]}")
        print("-" * 40)
    
    conn.close()

if __name__ == "__main__":
    check_all_articles()
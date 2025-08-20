#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection

def search_liberman_articles():
    """Buscar artículos que mencionen a Liberman."""
    conn = get_db_connection()
    
    # Buscar artículos que mencionen a Liberman
    cursor = conn.execute("""
        SELECT a.title, a.site, a.link, a.published_utc, h.keyword, h.where_found
        FROM articles a 
        JOIN hits h ON a.id = h.article_id 
        WHERE h.keyword LIKE '%Liberman%' 
        ORDER BY a.published_utc DESC
    """)
    
    results = cursor.fetchall()
    
    print(f"Artículos que mencionan Liberman: {len(results)}")
    print("=" * 50)
    
    for i, row in enumerate(results, 1):
        print(f"{i}. {row[0]}")
        print(f"   Sitio: {row[1]}")
        print(f"   Fecha: {row[3]}")
        print(f"   Palabra clave: {row[4]}")
        print(f"   Encontrado en: {row[5]}")
        print(f"   Link: {row[2]}")
        print("-" * 40)
    
    conn.close()

if __name__ == "__main__":
    search_liberman_articles()
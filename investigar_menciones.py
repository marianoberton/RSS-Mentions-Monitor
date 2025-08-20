#!/usr/bin/env python3

from app.storage import get_db_connection
from app.matcher import find_keyword
from app.config import config
import random

def investigar_menciones():
    """Investiga por qué no se están detectando menciones en los artículos procesados."""
    print("🔍 INVESTIGACIÓN DE DETECCIÓN DE MENCIONES")
    print("=" * 60)
    
    keywords = config["keywords"]
    print(f"📋 Palabras clave configuradas: {keywords}")
    
    conn = get_db_connection()
    
    # Estadísticas generales
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
    processed_articles = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    total_hits = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1 AND (full_content IS NOT NULL AND full_content != '')")
    articles_with_content = cursor.fetchone()[0]
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Artículos procesados: {processed_articles}")
    print(f"   Artículos con contenido: {articles_with_content}")
    print(f"   Total de menciones encontradas: {total_hits}")
    print(f"   Tasa de detección: {(total_hits/articles_with_content*100):.2f}%" if articles_with_content > 0 else "   Tasa de detección: 0%")
    
    # Analizar algunos artículos con contenido para ver si deberían tener menciones
    print(f"\n🔍 ANÁLISIS DE MUESTRA (10 artículos aleatorios):")
    cursor = conn.execute("""
        SELECT id, site, title, full_content, LENGTH(full_content) as content_length
        FROM articles 
        WHERE content_processed = 1 
        AND full_content IS NOT NULL 
        AND full_content != ''
        ORDER BY RANDOM()
        LIMIT 10
    """)
    
    sample_articles = cursor.fetchall()
    
    for i, article in enumerate(sample_articles, 1):
        article_id, site, title, content, content_length = article
        print(f"\n--- ARTÍCULO {i} ---")
        print(f"ID: {article_id}")
        print(f"Site: {site}")
        print(f"Title: {title[:80]}...")
        print(f"Content length: {content_length} caracteres")
        
        # Verificar si ya tiene hits
        cursor_hits = conn.execute("SELECT keyword, where_found FROM hits WHERE article_id = ?", (article_id,))
        existing_hits = cursor_hits.fetchall()
        
        if existing_hits:
            print(f"✅ Ya tiene menciones: {[f'{hit[0]} ({hit[1]})' for hit in existing_hits]}")
        else:
            print(f"❌ Sin menciones detectadas")
            
            # Buscar manualmente cada palabra clave
            print(f"🔍 Búsqueda manual:")
            for keyword in keywords:
                found = find_keyword(content, [keyword])
                if found:
                    print(f"   ✅ '{keyword}' ENCONTRADA en contenido")
                    # Mostrar contexto
                    keyword_lower = keyword.lower()
                    content_lower = content.lower()
                    pos = content_lower.find(keyword_lower)
                    if pos != -1:
                        start = max(0, pos - 50)
                        end = min(len(content), pos + len(keyword) + 50)
                        context = content[start:end]
                        print(f"      📝 Contexto: ...{context}...")
                else:
                    # Verificar en título
                    title_found = find_keyword(title, [keyword])
                    if title_found:
                        print(f"   ✅ '{keyword}' ENCONTRADA en título")
                    else:
                        print(f"   ❌ '{keyword}' no encontrada")
        
        print("-" * 50)
    
    # Verificar si hay problemas con la función find_keyword
    print(f"\n🧪 PRUEBA DE FUNCIÓN find_keyword:")
    test_content = "Este es un texto de prueba que menciona a Javier Milei y también habla de política."
    for keyword in keywords:
        result = find_keyword(test_content, [keyword])
        print(f"   Buscando '{keyword}' en texto de prueba: {'✅ ENCONTRADA' if result else '❌ NO ENCONTRADA'}")
    
    # Verificar artículos que deberían tener menciones pero no las tienen
    print(f"\n🎯 ARTÍCULOS QUE PODRÍAN TENER MENCIONES:")
    for keyword in keywords:
        cursor = conn.execute("""
            SELECT COUNT(*) 
            FROM articles 
            WHERE content_processed = 1 
            AND (full_content LIKE ? OR title LIKE ?)
            AND id NOT IN (SELECT article_id FROM hits WHERE keyword = ?)
        """, (f'%{keyword}%', f'%{keyword}%', keyword))
        
        potential_matches = cursor.fetchone()[0]
        if potential_matches > 0:
            print(f"   📰 '{keyword}': {potential_matches} artículos potenciales sin menciones detectadas")
    
    conn.close()

if __name__ == "__main__":
    investigar_menciones()
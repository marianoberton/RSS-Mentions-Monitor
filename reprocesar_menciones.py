#!/usr/bin/env python3

from app.storage import get_db_connection
from app.matcher import find_keyword
from app.config import config
from app.utils import get_utc_now
import time

def reprocesar_menciones_faltantes():
    """Reprocesa artículos que deberían tener menciones pero no las tienen detectadas."""
    print("🔄 REPROCESAMIENTO DE MENCIONES FALTANTES")
    print("=" * 60)
    
    keywords = config["keywords"]
    print(f"📋 Palabras clave: {keywords}")
    
    conn = get_db_connection()
    
    total_menciones_agregadas = 0
    
    for keyword in keywords:
        print(f"\n🔍 Procesando palabra clave: '{keyword}'")
        
        # Buscar artículos que contienen la palabra clave pero no tienen hits
        cursor = conn.execute("""
            SELECT id, title, full_content, site
            FROM articles 
            WHERE content_processed = 1 
            AND (full_content LIKE ? OR title LIKE ?)
            AND id NOT IN (SELECT article_id FROM hits WHERE keyword = ?)
        """, (f'%{keyword}%', f'%{keyword}%', keyword))
        
        articles_to_process = cursor.fetchall()
        print(f"   📰 Encontrados {len(articles_to_process)} artículos potenciales")
        
        menciones_agregadas = 0
        
        for article in articles_to_process:
            article_id, title, content, site = article
            
            # Verificar en título
            if find_keyword(title, [keyword]):
                print(f"   ✅ Agregando mención en título: {title[:60]}...")
                now_utc = get_utc_now()
                conn.execute(
                    "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                    (article_id, keyword, "title", now_utc.isoformat())
                )
                menciones_agregadas += 1
                continue
            
            # Verificar en contenido
            if content and find_keyword(content, [keyword]):
                print(f"   ✅ Agregando mención en contenido: {title[:60]}...")
                now_utc = get_utc_now()
                conn.execute(
                    "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                    (article_id, keyword, "content", now_utc.isoformat())
                )
                menciones_agregadas += 1
        
        print(f"   📈 Menciones agregadas para '{keyword}': {menciones_agregadas}")
        total_menciones_agregadas += menciones_agregadas
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ REPROCESAMIENTO COMPLETADO")
    print(f"   🎯 Total de menciones agregadas: {total_menciones_agregadas}")
    
    return total_menciones_agregadas

def verificar_mejora_efectividad():
    """Verifica la mejora en la efectividad después del reprocesamiento."""
    print(f"\n📊 VERIFICANDO MEJORA EN EFECTIVIDAD")
    print("=" * 60)
    
    conn = get_db_connection()
    
    # Estadísticas actualizadas
    cursor = conn.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    total_mentions = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
    processed_articles = cursor.fetchone()[0]
    
    efectividad = (total_mentions / total_articles * 100) if total_articles > 0 else 0
    
    print(f"   📰 Total de artículos: {total_articles}")
    print(f"   ✅ Artículos procesados: {processed_articles}")
    print(f"   🎯 Total de menciones: {total_mentions}")
    print(f"   📈 Efectividad actual: {efectividad:.1f}%")
    
    # Menciones por palabra clave
    print(f"\n📋 MENCIONES POR PALABRA CLAVE:")
    for keyword in config["keywords"]:
        cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword = ?", (keyword,))
        count = cursor.fetchone()[0]
        print(f"   - {keyword}: {count} menciones")
    
    conn.close()
    
    return efectividad

if __name__ == "__main__":
    # Verificar efectividad inicial
    efectividad_inicial = verificar_mejora_efectividad()
    
    # Reprocesar menciones faltantes
    menciones_agregadas = reprocesar_menciones_faltantes()
    
    if menciones_agregadas > 0:
        # Verificar efectividad final
        efectividad_final = verificar_mejora_efectividad()
        mejora = efectividad_final - efectividad_inicial
        
        print(f"\n🎉 RESUMEN DE MEJORA:")
        print(f"   📊 Efectividad inicial: {efectividad_inicial:.1f}%")
        print(f"   📊 Efectividad final: {efectividad_final:.1f}%")
        print(f"   📈 Mejora obtenida: +{mejora:.1f}%")
    else:
        print(f"\n💡 No se encontraron menciones faltantes para agregar.")
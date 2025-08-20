#!/usr/bin/env python3

from app.storage import get_db_connection
from app.tasks import extract_article_content
from app.improved_extractor import extract_with_retry
import time

print("🔍 ANÁLISIS DETALLADO DE PROCESAMIENTO")
print("=" * 50)

# Obtener artículos sin procesar
conn = get_db_connection()
cursor = conn.execute("""
    SELECT id, title, link, site, full_content
    FROM articles 
    WHERE content_processed = 0 
    LIMIT 3
""")
articles = cursor.fetchall()

print(f"\n📊 Analizando {len(articles)} artículos sin procesar:")

for i, article in enumerate(articles, 1):
    article_id, title, link, site, full_content = article
    print(f"\n--- ARTÍCULO {i} ---")
    print(f"ID: {article_id}")
    print(f"Site: {site}")
    print(f"Title: {title[:80]}...")
    print(f"Link: {link}")
    print(f"Current content length: {len(full_content) if full_content else 0}")
    
    # Intentar extraer contenido
    print("\n🔄 Intentando extraer contenido...")
    start_time = time.time()
    
    try:
        content = extract_with_retry(link)
        extraction_time = time.time() - start_time
        
        if content:
            print(f"✅ Extracción exitosa en {extraction_time:.2f}s")
            print(f"📝 Contenido extraído: {len(content)} caracteres")
            print(f"📄 Primeros 200 caracteres: {content[:200]}...")
        else:
            print(f"❌ Extracción falló en {extraction_time:.2f}s")
            print("🔍 Contenido vacío o None")
            
    except Exception as e:
        extraction_time = time.time() - start_time
        print(f"💥 Error en extracción ({extraction_time:.2f}s): {e}")
        import traceback
        traceback.print_exc()
    
    print("-" * 40)

conn.close()

print("\n🔍 VERIFICANDO CONFIGURACIÓN DE FEEDS")
print("=" * 50)

# Verificar si hay límites en el procesamiento
conn = get_db_connection()
cursor = conn.execute("""
    SELECT site, 
           COUNT(*) as total,
           SUM(CASE WHEN content_processed = 0 THEN 1 ELSE 0 END) as unprocessed,
           SUM(CASE WHEN content_processed = 1 THEN 1 ELSE 0 END) as processed,
           SUM(CASE WHEN content_processed = 2 THEN 1 ELSE 0 END) as failed
    FROM articles 
    GROUP BY site
    HAVING unprocessed > 0
    ORDER BY unprocessed DESC
""")

results = cursor.fetchall()
print("\nEstado por feed:")
for site, total, unprocessed, processed, failed in results:
    print(f"📰 {site}:")
    print(f"   Total: {total}, Sin procesar: {unprocessed}, Procesados: {processed}, Fallidos: {failed}")
    
conn.close()
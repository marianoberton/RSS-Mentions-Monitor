#!/usr/bin/env python3

from app.tasks import process_article_content
from app.storage import get_db_connection
import time

print("🔍 Verificando artículos sin procesar antes del procesamiento...")
conn = get_db_connection()
cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
count_before = cursor.fetchone()[0]
print(f"Artículos sin procesar: {count_before}")

# Obtener algunos ejemplos de artículos sin procesar
cursor = conn.execute("""
    SELECT id, title, link, site 
    FROM articles 
    WHERE content_processed = 0 
    LIMIT 5
""")
articles = cursor.fetchall()
print("\nEjemplos de artículos sin procesar:")
for article in articles:
    print(f"- ID: {article[0]}, Site: {article[3]}, Title: {article[1][:50]}...")

conn.close()

print("\n🚀 Ejecutando procesamiento de contenido de artículos...")
start_time = time.time()

try:
    process_article_content()
    print("✅ Procesamiento completado exitosamente")
except Exception as e:
    print(f"❌ Error durante el procesamiento: {e}")
    import traceback
    traceback.print_exc()

end_time = time.time()
print(f"⏱️ Tiempo de procesamiento: {end_time - start_time:.2f} segundos")

print("\n🔍 Verificando artículos sin procesar después del procesamiento...")
conn = get_db_connection()
cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
count_after = cursor.fetchone()[0]
print(f"Artículos sin procesar: {count_after}")
print(f"Artículos procesados en esta ejecución: {count_before - count_after}")

# Verificar artículos que fallaron en el procesamiento
cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 2")
failed_count = cursor.fetchone()[0]
print(f"Artículos con fallo de extracción: {failed_count}")

conn.close()
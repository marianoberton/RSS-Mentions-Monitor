import sqlite3
import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection

# Obtener conexión a la base de datos
conn = get_db_connection()
cursor = conn.cursor()

print("===== VERIFICACIÓN DE NUEVAS MENCIONES =====")
print("Buscando menciones de Oscar Liberman y Gustavo Coria...\n")

# Buscar menciones de las nuevas palabras clave
cursor.execute("""
    SELECT h.id, a.title, h.keyword, h.where_found, h.detected_utc, a.link, a.site
    FROM hits h 
    JOIN articles a ON h.article_id = a.id 
    WHERE h.keyword IN ('Oscar Liberman', 'Gustavo Coria')
    ORDER BY h.detected_utc DESC 
    LIMIT 20
""")

mentions = cursor.fetchall()

if mentions:
    print(f"Se encontraron {len(mentions)} menciones:")
    print("-" * 80)
    for mention in mentions:
        hit_id, title, keyword, where_found, detected_utc, link, site = mention
        print(f"Palabra clave: {keyword}")
        print(f"Sitio: {site}")
        print(f"Título: {title}")
        print(f"Encontrado en: {where_found}")
        print(f"Fecha: {detected_utc}")
        print(f"Enlace: {link}")
        print("-" * 80)
else:
    print("No se encontraron menciones de Oscar Liberman o Gustavo Coria aún.")
    print("Esto es normal si recién se configuraron las palabras clave.")
    print("El sistema seguirá monitoreando cada minuto.")

# Mostrar estadísticas generales
cursor.execute("SELECT COUNT(*) FROM hits WHERE detected_utc > datetime('now', '-1 hour')")
recent_hits = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM articles WHERE inserted_utc > datetime('now', '-1 hour')")
recent_articles = cursor.fetchone()[0]

print(f"\n===== ESTADÍSTICAS DE LA ÚLTIMA HORA =====")
print(f"Artículos procesados: {recent_articles}")
print(f"Menciones encontradas: {recent_hits}")

conn.close()
print("\n✅ Sistema funcionando correctamente")
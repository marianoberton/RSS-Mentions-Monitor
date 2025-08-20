import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Añadir el directorio actual al path para poder importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.feeds import get_enabled_feeds
from app.fetch import fetch_feed
from app.matcher import find_keyword
from app.storage import get_db_connection, init_db

# Inicializar la base de datos
init_db()

# Obtener la conexión a la base de datos
conn = get_db_connection()
cursor = conn.cursor()

# Mostrar la configuración actual
print("\n===== CONFIGURACIÓN ACTUAL =====")
print(f"Feeds habilitados: {len(get_enabled_feeds())}")
print(f"Palabras clave: {config.get('keywords', [])}")
print(f"Intervalo de verificación: {config.get('interval_minutes', 60)} minutos")
print(f"Zona horaria: {config.get('timezone', 'UTC')}")

# Mostrar estadísticas de la base de datos
print("\n===== ESTADÍSTICAS DE LA BASE DE DATOS =====")
cursor.execute("SELECT COUNT(*) FROM articles")
articles_count = cursor.fetchone()[0]
print(f"Total de artículos: {articles_count}")

cursor.execute("SELECT COUNT(*) FROM hits")
hits_count = cursor.fetchone()[0]
print(f"Total de menciones encontradas: {hits_count}")

# Mostrar las últimas 10 menciones
print("\n===== ÚLTIMAS 10 MENCIONES =====")
cursor.execute("""
    SELECT h.id, a.title, h.keyword, h.where_found, h.detected_utc, a.link 
    FROM hits h 
    JOIN articles a ON h.article_id = a.id 
    ORDER BY h.detected_utc DESC 
    LIMIT 10
""")
hits = cursor.fetchall()

if hits:
    for hit in hits:
        hit_id, title, keyword, where_found, detected_utc, link = hit
        print(f"ID: {hit_id}")
        print(f"Título: {title}")
        print(f"Palabra clave: {keyword}")
        print(f"Campo: {where_found}")
        print(f"Fecha: {detected_utc}")
        print(f"Enlace: {link}")
        print("-" * 50)
else:
    print("No se encontraron menciones en la base de datos.")

# Probar la funcionalidad de búsqueda de palabras clave
print("\n===== PRUEBA DE BÚSQUEDA DE PALABRAS CLAVE =====")
test_text = """El presidente Javier Milei anunció nuevas medidas económicas. 
El gobernador Axel Kicillof criticó las políticas del gobierno nacional.
Cristina Fernández de Kirchner (CFK) también se pronunció al respecto.
Patricia Bullrich defendió la gestión actual."""

print("Texto de prueba:")
print(test_text)
print("\nResultados de la búsqueda:")

for keyword in config.get('keywords', []):
    result = find_keyword(test_text, [keyword])
    if result:
        print(f"✓ Palabra clave '{keyword}' encontrada")
    else:
        print(f"✗ Palabra clave '{keyword}' no encontrada")

# Probar la funcionalidad de obtención de feeds
print("\n===== PRUEBA DE OBTENCIÓN DE FEEDS =====")
feeds = get_enabled_feeds()
for feed in feeds:
    print(f"Probando feed: {feed['name']} - {feed['url']}")
    try:
        feed_data = fetch_feed(feed)
        entries = feed_data.entries
        print(f"  ✓ Feed obtenido correctamente. {len(entries)} artículos encontrados.")
        if entries:
            print(f"  Último artículo: {entries[0].get('title', 'Sin título')}")
    except Exception as e:
        print(f"  ✗ Error al obtener el feed: {str(e)}")

# Cerrar la conexión a la base de datos
conn.close()

print("\n===== PRUEBAS COMPLETADAS =====")
print("El sistema parece estar funcionando correctamente.")
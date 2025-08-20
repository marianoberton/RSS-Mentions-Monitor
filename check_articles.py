import sqlite3
import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from app.config import config

# Obtener conexión a la base de datos
conn = get_db_connection()
cursor = conn.cursor()

print("===== VERIFICACIÓN DE ARTÍCULOS PROCESADOS =====")

# Verificar artículos en la base de datos
cursor.execute("SELECT COUNT(*) FROM articles")
articles_count = cursor.fetchone()[0]

print(f"Total de artículos en la base de datos: {articles_count}")

if articles_count > 0:
    # Mostrar los últimos 5 artículos
    cursor.execute("""
        SELECT id, site, title, link, published_utc, inserted_utc
        FROM articles
        ORDER BY inserted_utc DESC
        LIMIT 5
    """)
    
    articles = cursor.fetchall()
    
    print("\nÚltimos 5 artículos procesados:")
    print("-" * 80)
    
    for article in articles:
        article_id, site, title, link, published_utc, inserted_utc = article
        print(f"ID: {article_id}")
        print(f"Sitio: {site}")
        print(f"Título: {title}")
        print(f"Enlace: {link}")
        print(f"Fecha publicación: {published_utc}")
        print(f"Fecha procesamiento: {inserted_utc}")
        print("-" * 80)
else:
    print("\nNo hay artículos en la base de datos.")
    print("Esto puede indicar un problema con el procesamiento de feeds.")

# Mostrar la configuración actual
print("\n===== CONFIGURACIÓN ACTUAL =====")
print(f"Feeds habilitados: {len([f for f in config['feeds'] if f['enabled']])}")
print(f"Palabras clave: {config.get('keywords', [])}")
print(f"Intervalo de verificación: {config.get('interval_minutes', 60)} minutos")

conn.close()
import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.feeds import get_enabled_feeds
from app.fetch import fetch_feed
from app.matcher import find_keyword
from app.storage import save_article_and_hit, get_db_connection, init_db
from app.utils import get_utc_now, generate_article_id

# Inicializar la base de datos
init_db()

# Obtener la conexión a la base de datos
conn = get_db_connection()
cursor = conn.cursor()

# Función para procesar un feed y guardar todos los artículos (sin filtrar por palabras clave)
def debug_process_feed(feed):
    print(f"\nProcesando feed: {feed['name']} - {feed['url']}")
    try:
        parsed_feed = fetch_feed(feed)
        print(f"  ✓ Feed obtenido correctamente. {len(parsed_feed.entries)} artículos encontrados.")
        
        for i, entry in enumerate(parsed_feed.entries[:5]):  # Procesar solo los primeros 5 artículos para debug
            article_id = generate_article_id(entry)
            now_utc = get_utc_now()
            published_utc_str = entry.get("published", now_utc.isoformat())
            
            article = {
                "id": article_id,
                "site": feed['name'],
                "title": entry.title,
                "link": entry.link,
                "published_utc": published_utc_str,
                "inserted_utc": now_utc.isoformat(),
            }
            
            print(f"\nGuardando artículo {i+1}:")
            print(f"  ID: {article_id}")
            print(f"  Título: {entry.title}")
            print(f"  Enlace: {entry.link}")
            
            # Intentar guardar el artículo sin verificar palabras clave
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO articles (id, site, title, link, published_utc, inserted_utc) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        article["id"],
                        article["site"],
                        article["title"],
                        article["link"],
                        article["published_utc"],
                        article["inserted_utc"],
                    ),
                )
                conn.commit()
                
                # Verificar si se guardó correctamente
                cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
                if cursor.fetchone():
                    print("  ✓ Artículo guardado correctamente en la base de datos.")
                else:
                    print("  ✗ Error: El artículo no se guardó en la base de datos.")
                
                # Verificar palabras clave
                keywords = config["keywords"]
                keyword_found = False
                
                # Verificar en título
                keyword = find_keyword(entry.title, keywords)
                if keyword:
                    print(f"  ✓ Palabra clave '{keyword}' encontrada en el título.")
                    keyword_found = True
                
                # Verificar en resumen
                if hasattr(entry, 'summary'):
                    keyword = find_keyword(entry.summary, keywords)
                    if keyword:
                        print(f"  ✓ Palabra clave '{keyword}' encontrada en el resumen.")
                        keyword_found = True
                
                if not keyword_found:
                    print("  ✗ No se encontraron palabras clave en este artículo.")
                
            except Exception as e:
                print(f"  ✗ Error al guardar el artículo: {e}")
        
    except Exception as e:
        print(f"  ✗ Error al obtener el feed: {e}")

# Procesar cada feed habilitado
print("===== DEPURACIÓN DE PROCESAMIENTO DE FEEDS =====")
print(f"Palabras clave configuradas: {config['keywords']}")

feeds = get_enabled_feeds()
print(f"Feeds habilitados: {len(feeds)}")

for feed in feeds:
    debug_process_feed(feed)

# Verificar artículos en la base de datos después del procesamiento
cursor.execute("SELECT COUNT(*) FROM articles")
articles_count = cursor.fetchone()[0]
print(f"\nTotal de artículos en la base de datos después del procesamiento: {articles_count}")

# Cerrar la conexión
conn.close()

print("\n===== DEPURACIÓN COMPLETADA =====")
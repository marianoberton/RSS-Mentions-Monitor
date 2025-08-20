import os
import sys
import logging
import yaml
import feedparser
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos de la aplicación
from app.config import config
from app.matcher import find_keyword
from app.storage import save_article_and_hit, get_db_connection
from app.utils import get_utc_now, format_date, generate_article_id
from app.improved_extractor import extract_article_content_improved, extract_with_retry
from app.feed_extractor import extraer_contenido_feed, tiene_contenido_completo
from app.notifier import send_telegram_notification

# Cargar configuración
def cargar_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error al cargar la configuración: {e}")
        return None

# Función para procesar un feed deshabilitado
def procesar_feed_deshabilitado(feed, keywords):
    logger.info(f"Procesando feed deshabilitado: {feed['name']} - {feed['url']}")
    try:
        # Parsear el feed
        parsed_feed = feedparser.parse(feed['url'])
        
        if not parsed_feed.entries:
            logger.warning(f"No se encontraron entradas en el feed {feed['name']}")
            return 0
        
        articulos_procesados = 0
        hits_encontrados = 0
        
        # Procesar cada entrada del feed
        for entry in parsed_feed.entries:
            article_id = generate_article_id(entry)
            now_utc = get_utc_now()
            published_utc_str = entry.get("published", now_utc.isoformat())
            
            # Verificar si podemos extraer el contenido directamente del feed
            content_processed = 0
            full_content = None
            
            if tiene_contenido_completo(feed['name']):
                full_content = extraer_contenido_feed(entry, feed['name'])
                if full_content and len(full_content) > 100:  # Verificar que el contenido sea sustancial
                    content_processed = 1  # Marcar como procesado
                    logger.info(f"Contenido extraído directamente del feed para {feed['name']} - {entry.title}")
            
            # Guardar el artículo independientemente de si contiene palabras clave
            article = {
                "id": article_id,
                "site": feed['name'],
                "title": entry.title,
                "link": entry.link,
                "published_utc": published_utc_str,
                "inserted_utc": now_utc.isoformat(),
                "content_processed": content_processed,
                "full_content": full_content
            }
            
            # Verificar palabras clave en el título
            keyword = find_keyword(entry.title, keywords)
            if keyword:
                hit = {
                    "article_id": article_id,
                    "keyword": keyword,
                    "where_found": "title",
                    "detected_utc": now_utc.isoformat(),
                }
                save_article_and_hit(article, hit)
                notification_details = {
                    **article,
                    **hit,
                    "published_local": format_date(now_utc, config["TZ"])
                }
                send_telegram_notification(notification_details)
                hits_encontrados += 1
                logger.info(f"¡Palabra clave '{keyword}' encontrada en el título del artículo: {entry.title}")
                continue
            
            # Verificar palabras clave en el resumen
            if hasattr(entry, 'summary'):
                keyword = find_keyword(entry.summary, keywords)
                if keyword:
                    hit = {
                        "article_id": article_id,
                        "keyword": keyword,
                        "where_found": "summary",
                        "detected_utc": now_utc.isoformat(),
                    }
                    save_article_and_hit(article, hit)
                    notification_details = {
                        **article,
                        **hit,
                        "published_local": format_date(now_utc, config["TZ"])
                    }
                    send_telegram_notification(notification_details)
                    hits_encontrados += 1
                    logger.info(f"¡Palabra clave '{keyword}' encontrada en el resumen del artículo: {entry.title}")
                    continue
            
            # Si no se encontraron palabras clave en título o resumen, extraer contenido completo
            if not full_content:
                # Intentar extraer con BeautifulSoup primero
                full_content = extract_article_content_improved(entry.link)
                
                if not full_content or len(full_content) < 100:
                    # Si BeautifulSoup falla, intentar con extract_with_retry (que puede usar Playwright)
                    full_content = extract_with_retry(entry.link)
                
                if full_content and len(full_content) > 100:
                    content_processed = 1
                    article["full_content"] = full_content
                    article["content_processed"] = content_processed
                    
                    # Buscar palabras clave en el contenido
                    keyword = find_keyword(full_content, keywords)
                    if keyword:
                        hit = {
                            "article_id": article_id,
                            "keyword": keyword,
                            "where_found": "content",
                            "detected_utc": now_utc.isoformat(),
                        }
                        save_article_and_hit(article, hit)
                        notification_details = {
                            **article,
                            **hit,
                            "published_local": format_date(now_utc, config["TZ"])
                        }
                        send_telegram_notification(notification_details)
                        hits_encontrados += 1
                        logger.info(f"¡Palabra clave '{keyword}' encontrada en el contenido del artículo: {entry.title}")
                        continue
            
            # Si no se encontraron palabras clave, guardar solo el artículo
            try:
                conn = get_db_connection()
                with conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO articles (id, site, title, link, published_utc, inserted_utc, content_processed, full_content) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            article["id"],
                            article["site"],
                            article["title"],
                            article["link"],
                            article["published_utc"],
                            article["inserted_utc"],
                            article["content_processed"],
                            article["full_content"]
                        ),
                    )
                articulos_procesados += 1
            except Exception as e:
                logger.error(f"Error al guardar el artículo {article_id}: {e}")
        
        logger.info(f"Feed {feed['name']}: {articulos_procesados} artículos procesados, {hits_encontrados} hits encontrados")
        return articulos_procesados
    except Exception as e:
        logger.error(f"Error al procesar el feed {feed['name']}: {e}")
        return 0

# Función principal
def main():
    logger.info("Iniciando procesamiento de feeds deshabilitados")
    
    # Cargar configuración
    config_data = cargar_config()
    if not config_data:
        logger.error("No se pudo cargar la configuración.")
        return
    
    # Obtener feeds deshabilitados
    feeds_deshabilitados = [feed for feed in config_data.get('feeds', []) if not feed.get('enabled', True)]
    
    if not feeds_deshabilitados:
        logger.error("No hay feeds deshabilitados en la configuración.")
        return
    
    logger.info(f"Se procesarán {len(feeds_deshabilitados)} feeds deshabilitados.")
    
    # Obtener palabras clave
    keywords = config_data.get('keywords', [])
    if not keywords:
        logger.error("No hay palabras clave definidas en la configuración.")
        return
    
    logger.info(f"Palabras clave a buscar: {', '.join(keywords)}")
    
    # Procesar cada feed deshabilitado
    total_articulos = 0
    for feed in feeds_deshabilitados:
        articulos = procesar_feed_deshabilitado(feed, keywords)
        total_articulos += articulos
    
    logger.info(f"Procesamiento completado. Total de artículos procesados: {total_articulos}")

if __name__ == "__main__":
    main()
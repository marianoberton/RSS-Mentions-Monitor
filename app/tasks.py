import logging
import requests
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from app.config import config
from app.feeds import get_enabled_feeds
from app.fetch import fetch_feed
from app.matcher import find_keyword
from app.storage import save_article_and_hit, get_db_connection, get_unprocessed_articles, update_article_content, get_hourly_stats, get_important_hits
from app.notifier import send_telegram_notification, send_hourly_summary, send_important_hits_notifications
from app.utils import get_utc_now, format_date, generate_article_id
from app.feed_extractor import extraer_contenido_feed, tiene_contenido_completo

logger = logging.getLogger(__name__)

def process_feed(feed: Dict[str, Any], keywords: List[str]):
    """Processes a single RSS feed."""
    logger.info(f"Fetching feed: {feed['name']}")
    try:
        parsed_feed = fetch_feed(feed)
    except Exception as e:
        logger.error(f"Failed to fetch feed {feed['name']}: {e}")
        return

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
            
            # No enviar notificaciones individuales para ninguna palabra clave
            # Las notificaciones de Liberman y Coria se envían en el resumen horario
            # Las de Milei solo aparecen en estadísticas del resumen horario
            pass
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
                
                # No enviar notificaciones individuales para ninguna palabra clave
                # Las notificaciones de Liberman y Coria se envían en el resumen horario
                # Las de Milei solo aparecen en estadísticas del resumen horario
                pass
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
        except Exception as e:
            logger.error(f"Failed to save article {article_id}: {e}")

# Función save_and_notify eliminada - ya no se envían notificaciones individuales
# Todas las notificaciones se manejan en el resumen horario

# Importar el extractor mejorado
from app.improved_extractor import extract_article_content_improved, extract_with_retry

def extract_article_content(url: str) -> str:
    """Extrae el contenido de un artículo a partir de su URL.
    Esta función ahora utiliza el extractor mejorado."""
    return extract_with_retry(url, max_retries=3)

def process_article_content():
    """Procesa artículos pendientes para extraer su contenido y buscar palabras clave."""
    logger.info("Starting article content processing task.")
    keywords = config["keywords"]
    enabled_feeds = [feed["name"] for feed in get_enabled_feeds()]
    unprocessed_articles = get_unprocessed_articles(limit=10)
    
    for article in unprocessed_articles:
        try:
            article_id = article["id"]
            url = article["link"]
            site = article["site"]
            
            # Verificar si el feed está habilitado
            if site not in enabled_feeds:
                logger.info(f"Omitiendo artículo {article_id} de {site} porque el feed está deshabilitado")
                # Marcar como procesado para evitar procesarlo nuevamente
                update_article_content(article_id, "", content_processed=3)
                continue
            
            # Verificar si ya tenemos el contenido (podría haber sido extraído directamente del feed)
            conn = get_db_connection()
            with conn:
                cursor = conn.execute(
                    "SELECT full_content, site FROM articles WHERE id = ?",
                    (article_id,)
                )
                result = cursor.fetchone()
                existing_content = result['full_content'] if result and result['full_content'] else None
                site = result['site'] if result else ''
            
            # Si ya tenemos contenido del feed, usarlo directamente
            if existing_content and len(existing_content) > 100:
                content = existing_content
                logger.info(f"Usando contenido ya extraído para artículo {article_id} de {site}")
            else:
                # Extraer el contenido completo con métodos alternativos
                content = extract_article_content(url)
                logger.info(f"Contenido extraído con métodos alternativos para artículo {article_id} de {site}")
            
            if content:
                # Buscar palabras clave en el contenido
                keyword = find_keyword(content, keywords)
                
                if keyword:
                    # Si se encuentra una palabra clave, crear un hit
                    now_utc = get_utc_now()
                    hit = {
                        "article_id": article_id,
                        "keyword": keyword,
                        "where_found": "content",
                        "detected_utc": now_utc.isoformat(),
                    }
                    
                    # Obtener detalles del artículo para la notificación
                    conn = get_db_connection()
                    with conn:
                        cursor = conn.execute(
                            "SELECT id, site, title, link, published_utc, inserted_utc FROM articles WHERE id = ?",
                            (article_id,)
                        )
                        article_details = dict(cursor.fetchone())
                        
                    # Guardar el hit en la base de datos
                    conn = get_db_connection()
                    with conn:
                        conn.execute(
                            "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                            (hit["article_id"], hit["keyword"], hit["where_found"], hit["detected_utc"]),
                        )
                    
                    # No enviar notificaciones individuales para ninguna palabra clave
                    # Las notificaciones de Liberman y Coria se envían en el resumen horario
                    # Las de Milei solo aparecen en estadísticas del resumen horario
                    pass
                
                # Actualizar el artículo con el contenido y marcarlo como procesado
                # Solo actualizar si no teníamos contenido previo
                if not existing_content:
                    update_article_content(article_id, content)
                    logger.info(f"Actualizado artículo {article_id} con nuevo contenido")
                else:
                    # Marcar como procesado sin sobrescribir el contenido existente
                    conn = get_db_connection()
                    with conn:
                        conn.execute(
                            "UPDATE articles SET content_processed = 1 WHERE id = ?",
                            (article_id,)
                        )
                    logger.info(f"Artículo {article_id} marcado como procesado (ya tenía contenido)")
            else:
                # Si no se pudo extraer contenido, marcar como procesado para evitar intentos repetidos
                update_article_content(article_id, "", content_processed=2)
                logger.warning(f"Could not extract content for article {article_id}")
                
        except Exception as e:
            logger.error(f"Error processing article content for {article['id']}: {e}")
    
    logger.info("Article content processing task finished.")

def main_task():
    """The main task to be run by the scheduler."""
    logger.info("Starting RSS mention monitoring task.")
    feeds = get_enabled_feeds()
    keywords = config["keywords"]

    for feed in feeds:
        process_feed(feed, keywords)
    
    # Procesar artículos pendientes para extraer su contenido
    # Esto asegura que todos los artículos, incluso de feeds deshabilitados,
    # sean procesados para la búsqueda de palabras clave
    process_article_content()
    
    # Enviar resumen horario
    try:
        hourly_summary()
    except Exception as e:
        logger.error(f"Error al generar resumen horario: {e}")

    logger.info("RSS mention monitoring task finished.")

def hourly_summary():
    """Genera y envía un resumen horario de las menciones encontradas."""
    logger.info("Generando resumen horario")
    
    # Obtener estadísticas de la última hora
    stats = get_hourly_stats()
    
    # Enviar resumen general por Telegram (solo estadísticas de Milei)
    send_hourly_summary(stats)
    
    # Obtener y enviar notificaciones específicas para menciones importantes (Liberman, Coria y Andres de Leo)
    important_hits = get_important_hits(hours=1)
    if important_hits["liberman"] or important_hits["coria"] or important_hits["andres_de_leo"]:
        send_important_hits_notifications(important_hits)
        logger.info(f"Notificaciones importantes enviadas. Liberman: {len(important_hits['liberman'])}, Coria: {len(important_hits['coria'])}, Andres de Leo: {len(important_hits['andres_de_leo'])}")
    
    logger.info(f"Resumen horario enviado. Artículos: {stats['total_articles']}, Menciones a Milei: {stats['milei_mentions']}")


def daily_summary():
    """Sends a daily summary of mentions."""
    # This is a placeholder for the daily summary logic
    logger.info("Generating daily summary.")
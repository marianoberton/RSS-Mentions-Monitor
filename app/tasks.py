import logging
import requests
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from app.config import config
from app.feeds import get_enabled_feeds, get_feeds_for_processing
from app.fetch import fetch_feed, fetch_feed_with_cache, FeedNotModifiedException
from app.storage import update_feed_state
from app.matcher import find_keyword
from app.storage import save_article_and_hit, get_db_connection, get_unprocessed_articles, update_article_content, get_hourly_stats, get_important_hits, get_all_active_keywords
from app.notifier import send_telegram_notification, send_hourly_summary, send_important_hits_notifications, send_immediate_important_notification, send_candidate_notification, get_candidate_id_by_keyword
from app.utils import get_utc_now, format_date, generate_article_id
from app.feed_extractor import extraer_contenido_feed, tiene_contenido_completo

logger = logging.getLogger(__name__)

def process_feed(feed: Dict[str, Any], keywords: List[str]):
    """Processes a single RSS feed with ETag/Last-Modified support."""
    logger.info(f"Fetching feed: {feed['name']}")
    
    try:
        # Intentar fetch con cache headers
        parsed_feed, etag, last_modified = fetch_feed_with_cache(feed)
        
        # Actualizar estado del feed como exitoso
        update_feed_state(feed['name'], success=True, etag=etag, last_modified=last_modified)
        
    except FeedNotModifiedException:
        # Feed no modificado, actualizar estado sin procesar artículos
        logger.info(f"Feed {feed['name']} no modificado, saltando procesamiento")
        update_feed_state(feed['name'], success=True)
        return
        
    except Exception as e:
        logger.error(f"Failed to fetch feed {feed['name']}: {e}")
        update_feed_state(feed['name'], success=False, error_msg=str(e))
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
            
            # Enviar notificación inmediata usando el nuevo sistema de candidatos
            candidate_id = get_candidate_id_by_keyword(keyword)
            if candidate_id:
                send_candidate_notification(candidate_id, article, hit, 'mention')
            else:
                # Fallback al sistema anterior para compatibilidad
                if any(name in keyword.lower() for name in ['liberman', 'coria', 'andres de leo']):
                    send_immediate_important_notification(article, hit)
            
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
                
                # Enviar notificación inmediata usando el nuevo sistema de candidatos
                candidate_id = get_candidate_id_by_keyword(keyword)
                if candidate_id:
                    send_candidate_notification(candidate_id, article, hit, 'mention')
                else:
                    # Fallback al sistema anterior para compatibilidad
                    if any(name in keyword.lower() for name in ['liberman', 'coria', 'andres de leo']):
                        send_immediate_important_notification(article, hit)
                
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
    keywords = get_all_active_keywords()  # Usar función que incluye keywords de candidatos
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
                        
                    # Guardar el hit usando la función segura que previene duplicados
                    save_article_and_hit(article_details, hit)
                    
                    # Enviar notificación usando el nuevo sistema de candidatos
                    candidate_id = get_candidate_id_by_keyword(keyword)
                    if candidate_id:
                        send_candidate_notification(candidate_id, article_details, hit, 'mention')
                    else:
                        # Fallback: no enviar notificaciones individuales para palabras clave sin candidato asociado
                        # Las notificaciones se envían en el resumen horario
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
    """The main task to be run by the scheduler with adaptive scheduling."""
    logger.info("Starting RSS mention monitoring task.")
    
    # Obtener feeds listos para procesamiento según su schedule
    feeds = get_feeds_for_processing()
    keywords = get_all_active_keywords()  # Usar función que incluye keywords de candidatos
    
    if not feeds:
        logger.info("No hay feeds listos para procesar en este momento")
        return
    
    logger.info(f"Procesando {len(feeds)} feeds listos con {len(keywords)} keywords activas")
    
    for feed in feeds:
        process_feed(feed, keywords)
    
    # Procesar artículos pendientes para extraer su contenido
    # Esto asegura que todos los artículos, incluso de feeds deshabilitados,
    # sean procesados para la búsqueda de palabras clave
    process_article_content()
    
    # Las notificaciones inmediatas ya se envían en process_feed
    # El resumen se envía cada 6 horas por el scheduler

    logger.info("RSS mention monitoring task finished.")

def six_hourly_summary():
    """Obtiene estadísticas de las últimas 6 horas y envía un resumen por Telegram."""
    from app.storage import get_stats_for_hours
    
    # Obtener estadísticas de las últimas 6 horas
    stats = get_stats_for_hours(6)
    send_hourly_summary(stats)  # Reutilizamos la función existente
    
    logger.info(f"Resumen de 6 horas enviado. Artículos: {stats['total_articles']}, Menciones a Milei: {stats['milei_mentions']}")


def daily_summary():
    """Sends a daily summary of mentions."""
    # This is a placeholder for the daily summary logic
    logger.info("Generating daily summary.")

def send_candidate_digests():
    """Envía resúmenes diarios a todos los candidatos con suscripciones activas."""
    from app.storage import get_db_connection
    from app.notifier import send_candidate_digest
    from datetime import datetime, timedelta
    
    logger.info("Iniciando envío de digests diarios de candidatos")
    
    try:
        conn = get_db_connection()
        with conn:
            # Obtener todos los candidatos activos
            cursor = conn.execute("""
                SELECT DISTINCT c.id, c.name
                FROM candidates c
                JOIN candidate_subscriptions cs ON c.id = cs.candidate_id
                WHERE c.is_active = 1 AND cs.is_active = 1
                AND cs.notification_types IN ('all', 'digest')
            """)
            candidates = cursor.fetchall()
            
            # Calcular fecha de ayer para el resumen
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            
            for candidate_id, candidate_name in candidates:
                try:
                    # Obtener estadísticas de menciones del candidato para ayer
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_mentions,
                            COUNT(DISTINCT a.site) as sites_count
                        FROM hits h
                        JOIN articles a ON h.article_id = a.id
                        JOIN candidate_keywords ck ON h.keyword = ck.keyword
                        WHERE ck.candidate_id = ? 
                        AND DATE(h.detected_utc) = ?
                        AND ck.is_active = 1
                    """, (candidate_id, yesterday_str))
                    
                    stats = cursor.fetchone()
                    total_mentions = stats[0] if stats else 0
                    
                    if total_mentions == 0:
                        logger.info(f"No hay menciones para {candidate_name} en {yesterday_str}, omitiendo digest")
                        continue
                    
                    # Obtener sitios con más menciones
                    cursor = conn.execute("""
                        SELECT a.site, COUNT(*) as mention_count
                        FROM hits h
                        JOIN articles a ON h.article_id = a.id
                        JOIN candidate_keywords ck ON h.keyword = ck.keyword
                        WHERE ck.candidate_id = ? 
                        AND DATE(h.detected_utc) = ?
                        AND ck.is_active = 1
                        GROUP BY a.site
                        ORDER BY mention_count DESC
                        LIMIT 5
                    """, (candidate_id, yesterday_str))
                    
                    top_sites = cursor.fetchall()
                    
                    # Obtener menciones recientes
                    cursor = conn.execute("""
                        SELECT DISTINCT a.title, a.link, a.site, h.detected_utc
                        FROM hits h
                        JOIN articles a ON h.article_id = a.id
                        JOIN candidate_keywords ck ON h.keyword = ck.keyword
                        WHERE ck.candidate_id = ? 
                        AND DATE(h.detected_utc) = ?
                        AND ck.is_active = 1
                        ORDER BY h.detected_utc DESC
                        LIMIT 5
                    """, (candidate_id, yesterday_str))
                    
                    recent_mentions = [{
                        'title': row[0],
                        'link': row[1],
                        'site': row[2],
                        'detected_utc': row[3]
                    } for row in cursor.fetchall()]
                    
                    # Crear resumen
                    mentions_summary = {
                        'total_mentions': total_mentions,
                        'top_sites': top_sites,
                        'recent_mentions': recent_mentions,
                        'date': yesterday_str
                    }
                    
                    # Enviar digest
                    send_candidate_digest(candidate_id, mentions_summary)
                    logger.info(f"Digest enviado para {candidate_name}: {total_mentions} menciones")
                    
                except Exception as e:
                    logger.error(f"Error enviando digest para candidato {candidate_name} (ID: {candidate_id}): {e}")
            
            logger.info(f"Proceso de digests completado. {len(candidates)} candidatos procesados")
            
    except Exception as e:
        logger.error(f"Error en send_candidate_digests: {e}")
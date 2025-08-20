import sqlite3
import logging
import requests
from bs4 import BeautifulSoup
import time
import random

from app.config import config
from app.storage import get_db_connection, update_article_content
from app.matcher import find_keyword
from app.notifier import send_telegram_notification
from app.utils import get_utc_now, format_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_failed_extraction_articles(limit=20):
    """Obtiene artículos que no tienen contenido completo o que fallaron en la extracción."""
    conn = get_db_connection()
    articles = []
    with conn:
        cursor = conn.execute(
            "SELECT id, link FROM articles WHERE content_processed = 2 OR (content_processed = 1 AND full_content = '') LIMIT ?",
            (limit,)
        )
        for row in cursor:
            articles.append({"id": row["id"], "link": row["link"]})
    return articles

def extract_article_content_improved(url: str) -> str:
    """Versión mejorada de extracción de contenido con más selectores y manejo de errores."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=config["request_timeout_sec"])
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Eliminar elementos no deseados
        for element in soup.select('script, style, nav, header, footer, iframe, .ads, .banner, .comments, .social, .related, .sidebar'):
            element.decompose()
        
        # Lista ampliada de selectores para encontrar el contenido principal
        content_selectors = [
            'article', '.article-content', '.post-content', '.entry-content', 
            '.content', '#content', 'main', '.main-content', '.story-body',
            '.article-body', '.post-body', '.entry-body', '.news-content',
            '.article__content', '.post__content', '.news__content',
            '.article-text', '.post-text', '.news-text',
            '#article-content', '#post-content', '#news-content',
            '.nota', '.nota-contenido', '.nota-texto',
            '.articulo', '.articulo-contenido', '.articulo-texto',
            '.article', '.article-container', '.post', '.post-container'
        ]
        
        article_content = ""
        
        # Intentar con cada selector
        for selector in content_selectors:
            content = soup.select(selector)
            if content:
                article_content = ' '.join([elem.get_text(strip=True, separator=' ') for elem in content])
                if len(article_content) > 200:  # Si encontramos contenido sustancial
                    break
        
        # Si no se encontró contenido con los selectores, intentar con párrafos
        if not article_content or len(article_content) < 200:
            paragraphs = soup.find_all('p')
            if paragraphs:
                article_content = ' '.join([p.get_text(strip=True, separator=' ') for p in paragraphs])
        
        # Si aún no hay contenido, usar el body
        if not article_content or len(article_content) < 100:
            article_content = soup.body.get_text(strip=True, separator=' ')
        
        return article_content
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return ""

def reprocess_failed_articles():
    """Reprocesa artículos que fallaron en la extracción de contenido."""
    logger.info("Starting reprocessing of failed article extractions.")
    keywords = config["keywords"]
    failed_articles = get_failed_extraction_articles()
    
    logger.info(f"Found {len(failed_articles)} articles to reprocess.")
    
    for article in failed_articles:
        try:
            article_id = article["id"]
            url = article["link"]
            
            logger.info(f"Reprocessing article {article_id} from {url}")
            
            # Añadir un pequeño retraso aleatorio para evitar sobrecarga
            time.sleep(random.uniform(1, 3))
            
            # Extraer el contenido con el método mejorado
            content = extract_article_content_improved(url)
            
            if content and len(content) > 200:  # Verificar que el contenido sea sustancial
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
                    
                    # Guardar el hit y enviar notificación
                    conn.execute(
                        "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                        (hit["article_id"], hit["keyword"], hit["where_found"], hit["detected_utc"]),
                    )
                    
                    notification_details = {
                        **article_details,
                        **hit,
                        "published_local": format_date(get_utc_now(), config["TZ"])
                    }
                    send_telegram_notification(notification_details)
                    logger.info(f"Found keyword '{keyword}' in article {article_id}")
                
                # Actualizar el artículo con el contenido y marcarlo como procesado correctamente
                update_article_content(article_id, content, content_processed=1)
                logger.info(f"Successfully reprocessed article {article_id}")
            else:
                # Si no se pudo extraer contenido sustancial, marcar como fallido definitivo
                update_article_content(article_id, "", content_processed=3)  # 3 = fallido definitivo
                logger.warning(f"Could not extract substantial content for article {article_id}")
                
        except Exception as e:
            logger.error(f"Error reprocessing article {article['id']}: {e}")
    
    logger.info("Reprocessing of failed articles finished.")

def check_extraction_stats():
    """Muestra estadísticas sobre la extracción de contenido."""
    conn = get_db_connection()
    with conn:
        cursor = conn.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
        not_processed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1 AND full_content IS NOT NULL AND full_content != ''")
        success = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 2 OR (content_processed = 1 AND full_content = '')")
        failed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 3")
        permanently_failed = cursor.fetchone()[0]
        
        logger.info("===== ESTADÍSTICAS DE EXTRACCIÓN DE CONTENIDO =====")
        logger.info(f"Total de artículos: {total}")
        logger.info(f"Artículos no procesados: {not_processed}")
        logger.info(f"Artículos procesados con éxito: {success}")
        logger.info(f"Artículos con extracción fallida: {failed}")
        logger.info(f"Artículos con fallo permanente: {permanently_failed}")
        
        success_rate = (success / (success + failed + permanently_failed)) * 100 if (success + failed + permanently_failed) > 0 else 0
        logger.info(f"Tasa de éxito: {success_rate:.2f}%")

if __name__ == "__main__":
    # Mostrar estadísticas antes del reprocesamiento
    logger.info("Estadísticas antes del reprocesamiento:")
    check_extraction_stats()
    
    # Reprocesar artículos fallidos
    reprocess_failed_articles()
    
    # Mostrar estadísticas después del reprocesamiento
    logger.info("\nEstadísticas después del reprocesamiento:")
    check_extraction_stats()
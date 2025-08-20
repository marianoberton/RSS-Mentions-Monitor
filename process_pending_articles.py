import logging
import time
import random
import sqlite3

from app.config import config
from app.storage import get_db_connection, update_article_content
from app.tasks import extract_article_content
from app.matcher import find_keyword
from app.notifier import send_telegram_notification
from app.utils import get_utc_now, format_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_unprocessed_articles_safe(limit=10):
    """Obtiene artículos que aún no han sido procesados para extraer su contenido completo.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            articles = []
            with conn:
                cursor = conn.execute(
                    "SELECT id, link FROM articles WHERE content_processed = 0 LIMIT ?",
                    (limit,)
                )
                for row in cursor:
                    articles.append({"id": row["id"], "link": row["link"]})
            return articles
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Base de datos bloqueada, reintentando en {retry_delay} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            else:
                logger.error(f"Error accediendo a la base de datos después de {attempt+1} intentos: {e}")
                raise
    return []

def update_article_content_safe(article_id, full_content, content_processed=1):
    """Actualiza el contenido completo de un artículo y lo marca como procesado.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            with conn:
                conn.execute(
                    "UPDATE articles SET full_content = ?, content_processed = ? WHERE id = ?",
                    (full_content, content_processed, article_id)
                )
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Base de datos bloqueada, reintentando en {retry_delay} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            else:
                logger.error(f"Error actualizando la base de datos después de {attempt+1} intentos: {e}")
                raise
    return False

def save_hit_safe(hit):
    """Guarda un hit en la base de datos.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            with conn:
                conn.execute(
                    "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                    (hit["article_id"], hit["keyword"], hit["where_found"], hit["detected_utc"]),
                )
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Base de datos bloqueada, reintentando en {retry_delay} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            else:
                logger.error(f"Error guardando hit después de {attempt+1} intentos: {e}")
                raise
    return False

def get_article_details_safe(article_id):
    """Obtiene los detalles de un artículo.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            with conn:
                cursor = conn.execute(
                    "SELECT id, site, title, link, published_utc, inserted_utc FROM articles WHERE id = ?",
                    (article_id,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Base de datos bloqueada, reintentando en {retry_delay} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            else:
                logger.error(f"Error obteniendo detalles del artículo después de {attempt+1} intentos: {e}")
                raise
    return None

def process_pending_articles(batch_size=5, max_articles=20):
    """Procesa artículos pendientes para extraer su contenido y buscar palabras clave.
    Versión mejorada que maneja bloqueos de base de datos."""
    logger.info("Iniciando procesamiento manual de artículos pendientes.")
    keywords = config["keywords"]
    processed_count = 0
    success_count = 0
    failed_count = 0
    hits_found = 0
    
    while processed_count < max_articles:
        try:
            unprocessed_articles = get_unprocessed_articles_safe(limit=batch_size)
            if not unprocessed_articles:
                logger.info("No hay más artículos pendientes para procesar.")
                break
            
            for article in unprocessed_articles:
                try:
                    article_id = article["id"]
                    url = article["link"]
                    
                    logger.info(f"Procesando artículo {article_id} desde {url}")
                    
                    # Añadir un pequeño retraso aleatorio para evitar sobrecarga
                    time.sleep(random.uniform(2, 5))
                    
                    # Extraer el contenido completo
                    content = extract_article_content(url)
                    
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
                            article_details = get_article_details_safe(article_id)
                            if article_details:
                                # Guardar el hit
                                if save_hit_safe(hit):
                                    notification_details = {
                                        **article_details,
                                        **hit,
                                        "published_local": format_date(get_utc_now(), config["TZ"])
                                    }
                                    try:
                                        send_telegram_notification(notification_details)
                                    except Exception as e:
                                        logger.error(f"Error enviando notificación: {e}")
                                    
                                    logger.info(f"Encontrada palabra clave '{keyword}' en artículo {article_id}")
                                    hits_found += 1
                        
                        # Actualizar el artículo con el contenido y marcarlo como procesado correctamente
                        if update_article_content_safe(article_id, content, content_processed=1):
                            logger.info(f"Artículo {article_id} procesado exitosamente")
                            success_count += 1
                        else:
                            logger.warning(f"No se pudo actualizar el artículo {article_id} en la base de datos")
                            failed_count += 1
                    else:
                        # Si no se pudo extraer contenido sustancial, marcar como fallido
                        if update_article_content_safe(article_id, "", content_processed=2):
                            logger.warning(f"No se pudo extraer contenido sustancial para el artículo {article_id}")
                            failed_count += 1
                        else:
                            logger.warning(f"No se pudo marcar como fallido el artículo {article_id}")
                            failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error procesando artículo {article['id']}: {e}")
                    # Marcar como fallido para evitar intentos repetidos
                    try:
                        update_article_content_safe(article['id'], "", content_processed=2)
                    except Exception as e2:
                        logger.error(f"Error adicional al marcar como fallido: {e2}")
                    failed_count += 1
                
                processed_count += 1
                if processed_count >= max_articles:
                    break
                
                # Pausa entre artículos para evitar bloqueos
                time.sleep(1)
            
            logger.info(f"Procesados {processed_count} artículos hasta ahora. Continuando...")
            
            # Pausa entre lotes para evitar bloqueos
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Error en el procesamiento del lote: {e}")
            time.sleep(5)  # Esperar un poco más si hay un error general
    
    logger.info(f"Procesamiento manual finalizado. Resultados:")
    logger.info(f"Total de artículos procesados: {processed_count}")
    logger.info(f"Artículos procesados con éxito: {success_count}")
    logger.info(f"Artículos fallidos: {failed_count}")
    logger.info(f"Palabras clave encontradas: {hits_found}")

def check_processing_stats():
    """Muestra estadísticas sobre el procesamiento de artículos.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            with conn:
                cursor = conn.execute("SELECT COUNT(*) FROM articles")
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
                not_processed = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1 AND full_content IS NOT NULL AND full_content != ''")
                success = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 2")
                failed = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM hits")
                total_hits = cursor.fetchone()[0]
                
                cursor.execute("SELECT keyword, COUNT(*) FROM hits GROUP BY keyword")
                keyword_hits = {row[0]: row[1] for row in cursor.fetchall()}
                
                cursor.execute("SELECT where_found, COUNT(*) FROM hits GROUP BY where_found")
                where_found = {row[0]: row[1] for row in cursor.fetchall()}
            
            logger.info("===== ESTADÍSTICAS DE PROCESAMIENTO DE ARTÍCULOS =====")
            logger.info(f"Total de artículos: {total}")
            logger.info(f"Artículos no procesados: {not_processed}")
            logger.info(f"Artículos procesados con éxito: {success}")
            logger.info(f"Artículos fallidos: {failed}")
            logger.info(f"Total de hits: {total_hits}")
            logger.info(f"Hits por palabra clave: {keyword_hits}")
            logger.info(f"Hits por ubicación: {where_found}")
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Base de datos bloqueada, reintentando en {retry_delay} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            else:
                logger.error(f"Error obteniendo estadísticas después de {attempt+1} intentos: {e}")
                raise

if __name__ == "__main__":
    try:
        # Mostrar estadísticas antes del procesamiento
        logger.info("Estadísticas antes del procesamiento:")
        check_processing_stats()
        
        # Procesar artículos pendientes (procesar hasta 20 artículos en lotes de 5)
        # Reducimos el tamaño del lote y el total para evitar bloqueos
        process_pending_articles(batch_size=5, max_articles=20)
        
        # Mostrar estadísticas después del procesamiento
        logger.info("\nEstadísticas después del procesamiento:")
        check_processing_stats()
    except Exception as e:
        logger.error(f"Error general en la ejecución del script: {e}")
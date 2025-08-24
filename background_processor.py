import logging
import time
import random
import sqlite3
import sys
import os
from datetime import datetime, timedelta

# Configurar el path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.storage import get_db_connection
from app.improved_extractor import extract_article_content_improved
from app.matcher import find_keyword
from app.notifier import send_telegram_notification
from app.utils import get_utc_now, format_date

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='background_processor.log',
                   filemode='a')
logger = logging.getLogger(__name__)

# También mostrar logs en consola
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def get_unprocessed_articles_safe(limit=5):
    """Obtiene artículos que aún no han sido procesados para extraer su contenido completo.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            articles = []
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
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error cerrando conexión: {e}")
    return []

def update_article_content_safe(article_id, full_content, content_processed=1):
    """Actualiza el contenido completo de un artículo y lo marca como procesado.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            conn.execute(
                "UPDATE articles SET full_content = ?, content_processed = ? WHERE id = ?",
                (full_content, content_processed, article_id)
            )
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Base de datos bloqueada, reintentando en {retry_delay} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            else:
                logger.error(f"Error actualizando la base de datos después de {attempt+1} intentos: {e}")
                raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error cerrando conexión: {e}")
    return False

def save_hit_safe(hit):
    """Guarda un hit en la base de datos.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT OR IGNORE INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                (hit["article_id"], hit["keyword"], hit["where_found"], hit["detected_utc"]),
            )
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Base de datos bloqueada, reintentando en {retry_delay} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            else:
                logger.error(f"Error guardando hit después de {attempt+1} intentos: {e}")
                raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error cerrando conexión: {e}")
    return False

def get_article_details_safe(article_id):
    """Obtiene los detalles de un artículo.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
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
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error cerrando conexión: {e}")
    return None

def process_pending_articles(batch_size=5, max_articles=None):
    """Procesa artículos pendientes para extraer su contenido y buscar palabras clave.
    Versión mejorada que maneja bloqueos de base de datos.
    
    Args:
        batch_size: Tamaño del lote de artículos a procesar en cada iteración
        max_articles: Número máximo de artículos a procesar en total. Si es None, procesa todos los pendientes.
    """
    logger.info("Iniciando procesamiento automático de artículos pendientes.")
    keywords = config["keywords"]
    processed_count = 0
    success_count = 0
    failed_count = 0
    hits_found = 0
    
    while True:
        try:
            # Verificar si hemos alcanzado el límite de artículos a procesar
            if max_articles is not None and processed_count >= max_articles:
                break
                
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
                    
                    # Extraer el contenido completo usando el extractor mejorado
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
                            article_details = get_article_details_safe(article_id)
                            if article_details:
                                # Guardar el hit
                                try:
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
                                except Exception as e:
                                    logger.error(f"Error guardando hit: {e}")
                        
                        # Actualizar el artículo con el contenido y marcarlo como procesado correctamente
                        try:
                            if update_article_content_safe(article_id, content, content_processed=1):
                                logger.info(f"Artículo {article_id} procesado exitosamente")
                                success_count += 1
                            else:
                                logger.warning(f"No se pudo actualizar el artículo {article_id} en la base de datos")
                                failed_count += 1
                        except Exception as e:
                            logger.error(f"Error actualizando artículo: {e}")
                            failed_count += 1
                    else:
                        # Si no se pudo extraer contenido sustancial, marcar como fallido
                        try:
                            if update_article_content_safe(article_id, "", content_processed=2):
                                logger.warning(f"No se pudo extraer contenido sustancial para el artículo {article_id}")
                                failed_count += 1
                            else:
                                logger.warning(f"No se pudo marcar como fallido el artículo {article_id}")
                                failed_count += 1
                        except Exception as e:
                            logger.error(f"Error marcando artículo como fallido: {e}")
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
                if max_articles is not None and processed_count >= max_articles:
                    break
                
                # Pausa entre artículos para evitar bloqueos
                time.sleep(random.uniform(1, 3))
            
            logger.info(f"Procesados {processed_count} artículos hasta ahora. Continuando...")
            
            # Pausa entre lotes para evitar bloqueos
            time.sleep(random.uniform(3, 6))
            
        except Exception as e:
            logger.error(f"Error en el procesamiento del lote: {e}")
            time.sleep(5)  # Esperar un poco más si hay un error general
    
    logger.info(f"Procesamiento automático finalizado. Resultados:")
    logger.info(f"Total de artículos procesados: {processed_count}")
    logger.info(f"Artículos procesados con éxito: {success_count}")
    logger.info(f"Artículos fallidos: {failed_count}")
    logger.info(f"Palabras clave encontradas: {hits_found}")

def check_processing_stats():
    """Muestra estadísticas sobre el procesamiento de artículos.
    Versión segura que maneja bloqueos de base de datos."""
    max_retries = 5
    retry_delay = 2
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
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
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error cerrando conexión: {e}")

def run_continuous_processing(process_all_first=True):
    """Ejecuta el procesamiento de artículos en un bucle continuo.
    
    Args:
        process_all_first: Si es True, procesa todos los artículos pendientes primero
                          antes de entrar en el bucle de procesamiento continuo.
    """
    logger.info("Iniciando procesamiento continuo de artículos en segundo plano.")
    
    try:
        # Si se solicita procesar todos los pendientes primero
        if process_all_first:
            logger.info("Procesando todos los artículos pendientes primero...")
            # Obtener el número total de artículos no procesados
            conn = get_db_connection()
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
                total_pending = cursor.fetchone()[0]
            finally:
                conn.close()
                
            logger.info(f"Total de artículos pendientes: {total_pending}")
            # Procesar todos los artículos pendientes con un tamaño de lote mayor
            process_pending_articles(batch_size=20, max_articles=None)
            logger.info("Procesamiento inicial de todos los artículos pendientes completado.")
            
        # Continuar con el procesamiento normal
        while True:
            # Mostrar estadísticas actuales
            check_processing_stats()
            
            # Procesar un lote de artículos (20 a la vez)
            process_pending_articles(batch_size=20, max_articles=20)
            
            # Esperar un tiempo antes de la siguiente ejecución
            wait_time = random.randint(60, 120)  # Entre 1 y 2 minutos
            logger.info(f"Esperando {wait_time} segundos antes de la siguiente ejecución...")
            time.sleep(wait_time)
    except KeyboardInterrupt:
        logger.info("Procesamiento detenido por el usuario.")
    except Exception as e:
        logger.error(f"Error en el procesamiento continuo: {e}")
        # Intentar reiniciar el procesamiento después de un error
        time.sleep(30)
        logger.info("Intentando reiniciar el procesamiento...")
        run_continuous_processing()

if __name__ == "__main__":
    # Mostrar estadísticas antes del procesamiento
    logger.info("Estadísticas antes del procesamiento:")
    check_processing_stats()
    
    # Ejecutar el procesamiento continuo
    run_continuous_processing()
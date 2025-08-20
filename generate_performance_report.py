import sqlite3
import logging
import time
from datetime import datetime

from app.config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(config.get("SQLITE_PATH", "data/mentions.db"))
    conn.row_factory = sqlite3.Row
    return conn

def generate_performance_report():
    """Genera un informe detallado del rendimiento del sistema."""
    start_time = time.time()
    
    conn = get_db_connection()
    try:
        # Estadísticas generales
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_articles,
                SUM(CASE WHEN content_processed = 1 THEN 1 ELSE 0 END) as processed_success,
                SUM(CASE WHEN content_processed = 0 THEN 1 ELSE 0 END) as unprocessed,
                SUM(CASE WHEN content_processed = -1 THEN 1 ELSE 0 END) as processed_failed
            FROM articles
        """)
        stats = cursor.fetchone()
        
        # Estadísticas de hits
        cursor = conn.execute("""
            SELECT 
                keyword, 
                COUNT(*) as count,
                where_found,
                GROUP_CONCAT(article_id) as article_ids
            FROM hits 
            GROUP BY keyword, where_found
        """)
        hits_stats = cursor.fetchall()
        
        # Rendimiento de procesamiento
        cursor = conn.execute("""
            SELECT 
                strftime('%Y-%m-%d', inserted_utc) as date,
                COUNT(*) as articles_count,
                SUM(CASE WHEN content_processed = 1 THEN 1 ELSE 0 END) as processed_success,
                SUM(CASE WHEN content_processed = -1 THEN 1 ELSE 0 END) as processed_failed
            FROM articles
            GROUP BY date
            ORDER BY date DESC
        """)
        daily_stats = cursor.fetchall()
        
        # Tiempo de consulta
        query_time = time.time() - start_time
        
        # Generar informe
        print("\n===== INFORME DE RENDIMIENTO DEL SISTEMA =====\n")
        print(f"Fecha y hora del informe: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tiempo de consulta: {query_time:.4f} segundos\n")
        
        print("===== ESTADÍSTICAS GENERALES =====")
        print(f"Total de artículos: {stats['total_articles']}")
        print(f"Artículos procesados con éxito: {stats['processed_success']} ({stats['processed_success']/stats['total_articles']*100:.1f}%)")
        print(f"Artículos no procesados: {stats['unprocessed']} ({stats['unprocessed']/stats['total_articles']*100:.1f}%)")
        print(f"Artículos fallidos: {stats['processed_failed']} ({stats['processed_failed']/stats['total_articles']*100:.1f}%)\n")
        
        print("===== ESTADÍSTICAS DE HITS =====")
        keywords = {}
        locations = {}
        for hit in hits_stats:
            keyword = hit['keyword']
            where = hit['where_found']
            count = hit['count']
            
            if keyword not in keywords:
                keywords[keyword] = 0
            keywords[keyword] += count
            
            if where not in locations:
                locations[where] = 0
            locations[where] += count
        
        print("Hits por palabra clave:")
        for keyword, count in keywords.items():
            print(f"  - {keyword}: {count}")
        
        print("\nHits por ubicación:")
        for location, count in locations.items():
            print(f"  - {location}: {count}")
        
        print("\n===== ESTADÍSTICAS DIARIAS =====")
        print("Fecha | Artículos | Procesados | Fallidos | Tasa de éxito")
        print("-" * 65)
        for day in daily_stats:
            date = day['date']
            total = day['articles_count']
            success = day['processed_success']
            failed = day['processed_failed']
            success_rate = (success / total * 100) if total > 0 else 0
            
            print(f"{date} | {total:9d} | {success:10d} | {failed:8d} | {success_rate:6.1f}%")
        
        print("\n===== CONFIGURACIÓN DE LA BASE DE DATOS =====")
        for pragma in ['journal_mode', 'synchronous', 'temp_store', 'cache_size', 'mmap_size']:
            cursor = conn.execute(f"PRAGMA {pragma}")
            value = cursor.fetchone()[0]
            print(f"{pragma}: {value}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    generate_performance_report()
import sqlite3
import logging
import sys
from datetime import datetime
from app.config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(config["SQLITE_PATH"])
    conn.row_factory = sqlite3.Row
    return conn

def verificar_estado():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar estructura de la base de datos
    logger.info("Verificando estructura de la base de datos...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    logger.info(f"Tablas en la base de datos: {[tabla['name'] for tabla in tablas]}")
    
    # Verificar columnas de la tabla articles
    logger.info("\nVerificando columnas de la tabla articles...")
    cursor.execute("PRAGMA table_info(articles);")
    columnas = cursor.fetchall()
    logger.info("Columnas de la tabla articles:")
    for col in columnas:
        logger.info(f"  - {col['name']} ({col['type']})")
    
    # Verificar columnas de la tabla hits
    logger.info("\nVerificando columnas de la tabla hits...")
    cursor.execute("PRAGMA table_info(hits);")
    columnas = cursor.fetchall()
    logger.info("Columnas de la tabla hits:")
    for col in columnas:
        logger.info(f"  - {col['name']} ({col['type']})")
    
    # Estadísticas de artículos
    logger.info("\nEstadísticas de artículos:")
    cursor.execute("SELECT COUNT(*) FROM articles;")
    total_articulos = cursor.fetchone()[0]
    logger.info(f"Total de artículos: {total_articulos}")
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1;")
    articulos_procesados = cursor.fetchone()[0]
    logger.info(f"Artículos procesados: {articulos_procesados}")
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0;")
    articulos_pendientes = cursor.fetchone()[0]
    logger.info(f"Artículos pendientes: {articulos_pendientes}")
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE full_content IS NOT NULL AND full_content != ''")
    articulos_con_contenido = cursor.fetchone()[0]
    logger.info(f"Artículos con contenido: {articulos_con_contenido}")
    
    # Estadísticas de hits
    logger.info("\nEstadísticas de hits:")
    cursor.execute("SELECT COUNT(*) FROM hits;")
    total_hits = cursor.fetchone()[0]
    logger.info(f"Total de hits: {total_hits}")
    
    cursor.execute("SELECT keyword, COUNT(*) as count FROM hits GROUP BY keyword ORDER BY count DESC;")
    hits_por_keyword = cursor.fetchall()
    logger.info("Hits por palabra clave:")
    for hit in hits_por_keyword:
        logger.info(f"  - {hit['keyword']}: {hit['count']}")
    
    cursor.execute("SELECT where_found, COUNT(*) as count FROM hits GROUP BY where_found ORDER BY count DESC;")
    hits_por_ubicacion = cursor.fetchall()
    logger.info("Hits por ubicación:")
    for hit in hits_por_ubicacion:
        logger.info(f"  - {hit['where_found']}: {hit['count']}")
    
    # Estadísticas por sitio
    logger.info("\nEstadísticas por sitio:")
    cursor.execute("""
    SELECT 
        site, 
        COUNT(*) as total, 
        SUM(CASE WHEN content_processed = 1 THEN 1 ELSE 0 END) as procesados,
        SUM(CASE WHEN full_content IS NOT NULL AND full_content != '' THEN 1 ELSE 0 END) as con_contenido
    FROM articles 
    GROUP BY site 
    ORDER BY total DESC;
    """)
    stats_por_sitio = cursor.fetchall()
    logger.info("Artículos por sitio:")
    for stat in stats_por_sitio:
        logger.info(f"  - {stat['site']}: {stat['total']} artículos, {stat['procesados']} procesados, {stat['con_contenido']} con contenido")
    
    # Mostrar algunos ejemplos de artículos con contenido
    logger.info("\nEjemplos de artículos con contenido:")
    cursor.execute("""
    SELECT id, title, site, length(full_content) as content_length 
    FROM articles 
    WHERE full_content IS NOT NULL AND full_content != '' 
    ORDER BY content_length DESC 
    LIMIT 5;
    """)
    ejemplos = cursor.fetchall()
    for ejemplo in ejemplos:
        logger.info(f"  - {ejemplo['title']} ({ejemplo['site']}): {ejemplo['content_length']} caracteres")
    
    conn.close()

if __name__ == "__main__":
    logger.info("Iniciando verificación del estado de la base de datos...")
    verificar_estado()
    logger.info("Verificación completada.")
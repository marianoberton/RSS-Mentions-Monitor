import sqlite3
import logging
from typing import Dict, Any, List, Tuple

from app.config import config

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(config["SQLITE_PATH"])
    conn.row_factory = sqlite3.Row
    # Configurar para usar el modo WAL y optimizar el rendimiento
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA mmap_size=30000000000")
    conn.execute("PRAGMA cache_size=-2000")
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            site TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            published_utc TEXT NOT NULL,
            inserted_utc TEXT NOT NULL,
            content_processed INTEGER DEFAULT 0,
            full_content TEXT
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            where_found TEXT NOT NULL,
            detected_utc TEXT NOT NULL,
            notification_sent INTEGER DEFAULT 0,
            FOREIGN KEY(article_id) REFERENCES articles(id)
        );
        """)
        
        # Agregar columna notification_sent si no existe (para bases de datos existentes)
        try:
            conn.execute("ALTER TABLE hits ADD COLUMN notification_sent INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
    logger.info("Database initialized.")

def save_article_and_hit(article: Dict[str, Any], hit: Dict[str, Any]):
    conn = get_db_connection()
    with conn:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO articles (id, site, title, link, published_utc, inserted_utc, content_processed, full_content) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    article["id"],
                    article["site"],
                    article["title"],
                    article["link"],
                    article["published_utc"],
                    article["inserted_utc"],
                    article.get("content_processed", 0),
                    article.get("full_content", None),
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                (hit["article_id"], hit["keyword"], hit["where_found"], hit["detected_utc"]),
            )
        except sqlite3.IntegrityError:
            logger.warning(f"Article with ID {article['id']} already exists.")

def update_article_content(article_id: str, full_content: str, content_processed: int = 1):
    """Actualiza el contenido completo de un artículo y lo marca como procesado."""
    conn = get_db_connection()
    with conn:
        conn.execute(
            "UPDATE articles SET full_content = ?, content_processed = ? WHERE id = ?",
            (full_content, content_processed, article_id)
        )

def get_unprocessed_articles(limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene artículos que aún no han sido procesados para extraer su contenido completo."""
    conn = get_db_connection()
    articles = []
    with conn:
        cursor = conn.execute(
            "SELECT id, link, site FROM articles WHERE content_processed = 0 LIMIT ?",
            (limit,)
        )
        for row in cursor:
            articles.append({"id": row["id"], "link": row["link"], "site": row["site"]})
    return articles

def get_hourly_stats() -> Dict[str, Any]:
    """Obtiene estadísticas de la última hora para el resumen horario."""
    conn = get_db_connection()
    stats = {
        "total_articles": 0,
        "processed_articles": 0,
        "total_hits": 0,
        "milei_mentions": 0,
        "liberman_mentions": 0,
        "coria_mentions": 0,
        "andres_de_leo_mentions": 0,
        "success_rate": 0
    }
    
    one_hour_ago = "datetime('now', '-1 hour')"
    
    with conn:
        # Total de artículos procesados en la última hora
        cursor = conn.execute(f"SELECT COUNT(*) FROM articles WHERE inserted_utc >= {one_hour_ago}")
        stats["total_articles"] = cursor.fetchone()[0]
        
        # Artículos procesados exitosamente
        cursor = conn.execute(f"SELECT COUNT(*) FROM articles WHERE inserted_utc >= {one_hour_ago} AND content_processed = 1")
        stats["processed_articles"] = cursor.fetchone()[0]
        
        # Total de menciones detectadas en la última hora
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {one_hour_ago}")
        stats["total_hits"] = cursor.fetchone()[0]
        
        # Calcular tasa de éxito
        if stats["total_articles"] > 0:
            stats["success_rate"] = (stats["processed_articles"] / stats["total_articles"]) * 100
        
        # Menciones a Javier Milei
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {one_hour_ago} AND keyword LIKE '%Milei%'")
        stats["milei_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Oscar Liberman
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {one_hour_ago} AND keyword LIKE '%Liberman%'")
        stats["liberman_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Gustavo Coria
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {one_hour_ago} AND keyword LIKE '%Coria%'")
        stats["coria_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Andres de Leo
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {one_hour_ago} AND (keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%')")
        stats["andres_de_leo_mentions"] = cursor.fetchone()[0]
    
    return stats

def get_global_stats() -> Dict[str, Any]:
    """Obtiene estadísticas globales de todo el sistema."""
    conn = get_db_connection()
    stats = {
        "total_articles": 0,
        "processed_articles": 0,
        "total_hits": 0,
        "milei_mentions": 0,
        "liberman_mentions": 0,
        "coria_mentions": 0,
        "andres_de_leo_mentions": 0,
        "success_rate": 0
    }
    
    with conn:
        # Total de artículos procesados
        cursor = conn.execute("SELECT COUNT(*) FROM articles")
        stats["total_articles"] = cursor.fetchone()[0]
        
        # Artículos procesados exitosamente
        cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
        stats["processed_articles"] = cursor.fetchone()[0]
        
        # Total de menciones detectadas
        cursor = conn.execute("SELECT COUNT(*) FROM hits")
        stats["total_hits"] = cursor.fetchone()[0]
        
        # Calcular tasa de éxito
        if stats["total_articles"] > 0:
            stats["success_rate"] = (stats["processed_articles"] / stats["total_articles"]) * 100
        
        # Menciones a Javier Milei
        cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Milei%'")
        stats["milei_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Oscar Liberman
        cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Liberman%'")
        stats["liberman_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Gustavo Coria
        cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Coria%'")
        stats["coria_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Andres de Leo
        cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE (keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%')")
        stats["andres_de_leo_mentions"] = cursor.fetchone()[0]
    
    return stats

def get_important_hits(hours: int = 1) -> Dict[str, List[Dict[str, Any]]]:
    """Obtiene los hits importantes (Liberman, Coria y Andres de Leo) de las últimas horas."""
    conn = get_db_connection()
    important_hits = {
        "liberman": [],
        "coria": [],
        "andres_de_leo": []
    }
    
    time_ago = f"datetime('now', '-{hours} hour')"
    
    with conn:
        # Obtener hits de Liberman que no han sido notificados
        cursor = conn.execute(f"""
            SELECT h.id, h.article_id, h.keyword, h.where_found, h.detected_utc, a.title, a.link, a.site, a.published_utc
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            WHERE h.detected_utc >= {time_ago}
            AND h.keyword LIKE '%Liberman%'
            AND h.notification_sent = 0
            ORDER BY h.detected_utc DESC
        """)
        
        for row in cursor:
            important_hits["liberman"].append({
                "id": row["id"],
                "article_id": row["article_id"],
                "keyword": row["keyword"],
                "where_found": row["where_found"],
                "detected_utc": row["detected_utc"],
                "title": row["title"],
                "link": row["link"],
                "site": row["site"],
                "published_utc": row["published_utc"]
            })
        
        # Obtener hits de Coria que no han sido notificados
        cursor = conn.execute(f"""
            SELECT h.id, h.article_id, h.keyword, h.where_found, h.detected_utc, a.title, a.link, a.site, a.published_utc
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            WHERE h.detected_utc >= {time_ago}
            AND h.keyword LIKE '%Coria%'
            AND h.notification_sent = 0
            ORDER BY h.detected_utc DESC
        """)
        
        for row in cursor:
            important_hits["coria"].append({
                "id": row["id"],
                "article_id": row["article_id"],
                "keyword": row["keyword"],
                "where_found": row["where_found"],
                "detected_utc": row["detected_utc"],
                "title": row["title"],
                "link": row["link"],
                "site": row["site"],
                "published_utc": row["published_utc"]
            })
        
        # Obtener hits de Andres de Leo que no han sido notificados
        cursor = conn.execute(f"""
            SELECT h.id, h.article_id, h.keyword, h.where_found, h.detected_utc, a.title, a.link, a.site, a.published_utc
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            WHERE h.detected_utc >= {time_ago}
            AND (h.keyword LIKE '%Andres de Leo%' OR h.keyword LIKE '%Andrés de Leo%')
            AND h.notification_sent = 0
            ORDER BY h.detected_utc DESC
        """)
        
        for row in cursor:
            important_hits["andres_de_leo"].append({
                "id": row["id"],
                "article_id": row["article_id"],
                "keyword": row["keyword"],
                "where_found": row["where_found"],
                "detected_utc": row["detected_utc"],
                "title": row["title"],
                "link": row["link"],
                "site": row["site"],
                "published_utc": row["published_utc"]
            })
    
    return important_hits


def mark_notification_sent(hit_id: int):
    """Marca una notificación como enviada para evitar duplicados."""
    conn = get_db_connection()
    with conn:
        conn.execute(
            "UPDATE hits SET notification_sent = 1 WHERE id = ?",
            (hit_id,)
        )
    logger.debug(f"Notificación marcada como enviada para hit ID: {hit_id}")

def remove_duplicate_hits() -> Dict[str, Any]:
    """Elimina hits duplicados y retorna estadísticas de la operación."""
    conn = get_db_connection()
    result = {
        "duplicates_found": 0,
        "hits_removed": 0,
        "groups_processed": 0,
        "success": False,
        "message": ""
    }
    
    try:
        with conn:
            # Buscar duplicados
            cursor = conn.execute("""
                SELECT article_id, keyword, where_found, COUNT(*) as count, 
                       GROUP_CONCAT(id ORDER BY detected_utc) as hit_ids
                FROM hits 
                GROUP BY article_id, keyword, where_found
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)
            
            duplicates = cursor.fetchall()
            result["duplicates_found"] = len(duplicates)
            
            if duplicates:
                # Eliminar duplicados manteniendo solo el más antiguo
                for dup in duplicates:
                    hit_ids = dup[4].split(',')
                    if len(hit_ids) > 1:
                        # Mantener el primer hit (más antiguo) y eliminar los demás
                        hits_to_delete = hit_ids[1:]
                        
                        for hit_id in hits_to_delete:
                            conn.execute("DELETE FROM hits WHERE id = ?", (int(hit_id),))
                            result["hits_removed"] += 1
                        
                        result["groups_processed"] += 1
                
                result["success"] = True
                result["message"] = f"Eliminados {result['hits_removed']} hits duplicados de {result['groups_processed']} grupos"
                logger.info(f"Duplicados eliminados: {result['hits_removed']} hits de {result['groups_processed']} grupos")
            else:
                result["success"] = True
                result["message"] = "No se encontraron duplicados para eliminar"
                
    except Exception as e:
        result["success"] = False
        result["message"] = f"Error al eliminar duplicados: {str(e)}"
        logger.error(f"Error eliminando duplicados: {e}")
    
    return result

def get_detailed_stats() -> Dict[str, Any]:
    """Obtiene estadísticas detalladas para diagnóstico."""
    conn = get_db_connection()
    stats = {
        "total_articles": 0,
        "processed_articles": 0,
        "total_hits": 0,
        "unique_articles_with_hits": 0,
        "avg_hits_per_article": 0,
        "duplicate_groups": 0,
        "keyword_breakdown": {},
        "articles_with_many_hits": []
    }
    
    try:
        with conn:
            # Estadísticas básicas
            cursor = conn.execute("SELECT COUNT(*) FROM articles")
            stats["total_articles"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
            stats["processed_articles"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM hits")
            stats["total_hits"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT article_id) FROM hits")
            stats["unique_articles_with_hits"] = cursor.fetchone()[0]
            
            if stats["unique_articles_with_hits"] > 0:
                stats["avg_hits_per_article"] = stats["total_hits"] / stats["unique_articles_with_hits"]
            
            # Buscar duplicados
            cursor = conn.execute("""
                SELECT COUNT(*) FROM (
                    SELECT article_id, keyword, where_found
                    FROM hits 
                    GROUP BY article_id, keyword, where_found
                    HAVING COUNT(*) > 1
                )
            """)
            stats["duplicate_groups"] = cursor.fetchone()[0]
            
            # Breakdown por keyword
            cursor = conn.execute("""
                SELECT keyword, COUNT(*) as count
                FROM hits
                GROUP BY keyword
                ORDER BY count DESC
            """)
            
            for row in cursor:
                stats["keyword_breakdown"][row[0]] = row[1]
            
            # Artículos con muchos hits
            cursor = conn.execute("""
                SELECT h.article_id, COUNT(*) as hit_count, a.title, a.site
                FROM hits h
                JOIN articles a ON h.article_id = a.id
                GROUP BY h.article_id
                HAVING COUNT(*) > 3
                ORDER BY hit_count DESC
                LIMIT 10
            """)
            
            for row in cursor:
                stats["articles_with_many_hits"].append({
                    "article_id": row[0],
                    "hit_count": row[1],
                    "title": row[2][:80] + "..." if len(row[2]) > 80 else row[2],
                    "site": row[3]
                })
                
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas detalladas: {e}")
    
    return stats
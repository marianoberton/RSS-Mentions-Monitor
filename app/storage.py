import sqlite3
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

from app.config import config
from app.url_utils import canonicalize_url, calculate_content_hash

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
            full_content TEXT,
            canonical_url TEXT,
            content_hash TEXT
        );
        """)
        
        # Tabla de personas políticas
        conn.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            full_name TEXT,
            description TEXT,
            position TEXT,
            political_party TEXT,
            importance_level INTEGER DEFAULT 1,
            created_utc TEXT NOT NULL,
            updated_utc TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        );
        """)
        
        # Tabla de keywords asociadas a personas
        conn.execute("""
        CREATE TABLE IF NOT EXISTS person_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            created_utc TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE,
            UNIQUE(person_id, keyword)
        );
        """)
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT NOT NULL,
            person_id INTEGER,
            keyword TEXT NOT NULL,
            where_found TEXT NOT NULL,
            detected_utc TEXT NOT NULL,
            notification_sent INTEGER DEFAULT 0,
            score REAL DEFAULT 0.0,
            FOREIGN KEY(article_id) REFERENCES articles(id),
            FOREIGN KEY(person_id) REFERENCES persons(id)
        );
        """)
        
        # Agregar columna notification_sent si no existe (para bases de datos existentes)
        try:
            conn.execute("ALTER TABLE hits ADD COLUMN notification_sent INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
            
        # Agregar columna person_id si no existe (para migración)
        try:
            conn.execute("ALTER TABLE hits ADD COLUMN person_id INTEGER REFERENCES persons(id)")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
            
        # Agregar columna score si no existe (para migración)
        try:
            conn.execute("ALTER TABLE hits ADD COLUMN score REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
            
        # Tabla para el estado y health de feeds
        conn.execute("""
        CREATE TABLE IF NOT EXISTS feed_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            etag TEXT,
            last_modified TEXT,
            last_fetch_utc TEXT,
            last_success_utc TEXT,
            error_count INTEGER DEFAULT 0,
            last_error TEXT,
            next_run_at TEXT,
            fetch_interval_minutes INTEGER DEFAULT 10,
            is_enabled INTEGER DEFAULT 1,
            created_utc TEXT NOT NULL,
            updated_utc TEXT NOT NULL
        );
        """)        
        
        # Agregar columnas a la tabla articles si no existen (para migración)
        try:
            conn.execute("ALTER TABLE articles ADD COLUMN canonical_url TEXT")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
            
        try:
            conn.execute("ALTER TABLE articles ADD COLUMN content_hash TEXT")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
        
        # Crear índices para mejorar el rendimiento (después de agregar columnas)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hits_person_id ON hits(person_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hits_article_person ON hits(article_id, person_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_person_keywords_person_id ON person_keywords(person_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_state_name ON feed_state(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_state_next_run ON feed_state(next_run_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_canonical_url ON articles(canonical_url)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_canonical_content ON articles(canonical_url, content_hash)")
        
        # Crear tabla FTS5 para búsqueda rápida
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                title, 
                content, 
                site,
                content=articles,
                content_rowid=id
            )
        """)
        
        # Crear triggers para mantener sincronizada la tabla FTS5
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_fts_insert AFTER INSERT ON articles BEGIN
                INSERT INTO articles_fts(rowid, title, content, site) 
                VALUES (new.id, new.title, COALESCE(new.full_content, ''), new.site);
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_fts_delete AFTER DELETE ON articles BEGIN
                DELETE FROM articles_fts WHERE rowid = old.id;
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_fts_update AFTER UPDATE ON articles BEGIN
                DELETE FROM articles_fts WHERE rowid = old.id;
                INSERT INTO articles_fts(rowid, title, content, site) 
                VALUES (new.id, new.title, COALESCE(new.full_content, ''), new.site);
            END
        """)
        
    logger.info("Database initialized with persons system.")

def save_article_and_hit(article: Dict[str, Any], hit: Dict[str, Any]):
    conn = get_db_connection()
    with conn:
        try:
            # Canonicalizar URL y calcular content hash
            canonical_url = canonicalize_url(article["link"])
            content_hash = calculate_content_hash(article["title"])
            
            # Verificar si ya existe un artículo con la misma URL canónica y content hash
            cursor = conn.execute(
                "SELECT id FROM articles WHERE canonical_url = ? AND content_hash = ? LIMIT 1",
                (canonical_url, content_hash)
            )
            existing_article = cursor.fetchone()
            
            if existing_article:
                article_id = existing_article[0]
                logger.debug(f"Artículo duplicado detectado: {canonical_url}")
            else:
                # Insertar nuevo artículo con canonicalización
                conn.execute(
                    "INSERT INTO articles (id, site, title, link, published_utc, inserted_utc, content_processed, full_content, canonical_url, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        article["id"],
                        article["site"],
                        article["title"],
                        article["link"],
                        article["published_utc"],
                        article["inserted_utc"],
                        article.get("content_processed", 0),
                        article.get("full_content", None),
                        canonical_url,
                        content_hash,
                    ),
                )
                article_id = article["id"]
            
            # Buscar el candidato asociado a esta keyword
            person_id = None
            cursor = conn.execute(
                "SELECT candidate_id FROM candidate_keywords WHERE keyword = ? AND is_active = 1",
                (hit["keyword"],)
            )
            result = cursor.fetchone()
            if result:
                person_id = result[0]
            
            # Verificar si ya existe este hit específico
            cursor = conn.execute(
                "SELECT id FROM hits WHERE article_id = ? AND person_id = ? AND keyword = ? AND where_found = ?",
                (article_id, person_id, hit["keyword"], hit["where_found"])
            )
            existing_hit = cursor.fetchone()
            
            if not existing_hit:
                # Insertar nuevo hit solo si no existe
                cursor = conn.execute(
                    "INSERT INTO hits (article_id, person_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?, ?)",
                    (article_id, person_id, hit["keyword"], hit["where_found"], hit["detected_utc"]),
                )
                
                # Calcular y actualizar score del hit
                hit_id = cursor.lastrowid
                try:
                    from app.scoring import calculate_mention_score, get_person_keywords_map
                    
                    article_data = {
                        'site': article["site"],
                        'title': article["title"],
                        'published_utc': article["published_utc"]
                    }
                    
                    hit_data = {
                        'keyword': hit["keyword"],
                        'where_found': hit["where_found"],
                        'person_id': person_id
                    }
                    
                    person_keywords = get_person_keywords_map(person_id) if person_id else {}
                    score = calculate_mention_score(article_data, hit_data, person_keywords)
                    
                    conn.execute("UPDATE hits SET score = ? WHERE id = ?", (score, hit_id))
                    
                except Exception as e:
                    logger.warning(f"Error calculando score para hit {hit_id}: {e}")
        except sqlite3.IntegrityError:
            logger.warning(f"Article with ID {article['id']} already exists.")

def update_article_content(article_id: str, full_content: str, content_processed: int = 1):
    """Actualiza el contenido completo de un artículo y lo marca como procesado."""
    conn = get_db_connection()
    with conn:
        # Obtener el título para recalcular el hash
        cursor = conn.execute("SELECT title FROM articles WHERE id = ?", (article_id,))
        result = cursor.fetchone()
        
        if result:
            title = result[0]
            # Recalcular content hash con título y contenido completo
            new_content_hash = calculate_content_hash(title, full_content)
            
            conn.execute(
                "UPDATE articles SET full_content = ?, content_processed = ?, content_hash = ? WHERE id = ?",
                (full_content, content_processed, new_content_hash, article_id)
            )
        else:
            # Si no se encuentra el artículo, actualizar sin cambiar el hash
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

def get_stats_for_hours(hours: int) -> Dict[str, Any]:
    """Obtiene estadísticas de las últimas N horas para el resumen."""
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
    
    time_ago = f"datetime('now', '-{hours} hour')"
    
    with conn:
        # Total de artículos procesados en las últimas N horas
        cursor = conn.execute(f"SELECT COUNT(*) FROM articles WHERE inserted_utc >= {time_ago}")
        stats["total_articles"] = cursor.fetchone()[0]
        
        # Artículos procesados exitosamente
        cursor = conn.execute(f"SELECT COUNT(*) FROM articles WHERE inserted_utc >= {time_ago} AND content_processed = 1")
        stats["processed_articles"] = cursor.fetchone()[0]
        
        # Total de menciones detectadas en las últimas N horas
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {time_ago}")
        stats["total_hits"] = cursor.fetchone()[0]
        
        # Calcular tasa de éxito
        if stats["total_articles"] > 0:
            stats["success_rate"] = (stats["processed_articles"] / stats["total_articles"]) * 100
        
        # Menciones a Javier Milei
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {time_ago} AND keyword LIKE '%Milei%'")
        stats["milei_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Oscar Liberman
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {time_ago} AND keyword LIKE '%Liberman%'")
        stats["liberman_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Gustavo Coria
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {time_ago} AND keyword LIKE '%Coria%'")
        stats["coria_mentions"] = cursor.fetchone()[0]
        
        # Menciones a Andres de Leo
        cursor = conn.execute(f"SELECT COUNT(*) FROM hits WHERE detected_utc >= {time_ago} AND (keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%')")
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
                SELECT article_id, keyword, where_found, COUNT(*) as count
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
                    article_id, keyword, where_found, count = dup
                    
                    # Obtener todos los IDs de este grupo duplicado, ordenados por fecha
                    hit_cursor = conn.execute("""
                        SELECT id FROM hits 
                        WHERE article_id = ? AND keyword = ? AND where_found = ?
                        ORDER BY detected_utc ASC
                    """, (article_id, keyword, where_found))
                    
                    hit_ids = [row[0] for row in hit_cursor.fetchall()]
                    
                    if len(hit_ids) > 1:
                        # Mantener el primer hit (más antiguo) y eliminar los demás
                        hits_to_delete = hit_ids[1:]
                        
                        for hit_id in hits_to_delete:
                            conn.execute("DELETE FROM hits WHERE id = ?", (hit_id,))
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


# ============================================================================
# FUNCIONES DE ALIANZAS ELECTORALES
# ============================================================================

def get_all_electoral_alliances() -> List[Dict[str, Any]]:
    """Obtener todas las alianzas electorales activas."""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT id, name, display_name, description, logo_url, 
                   primary_color, secondary_color, is_active
            FROM electoral_alliances 
            WHERE is_active = 1
            ORDER BY display_name
        """)
        
        alliances = []
        for row in cursor:
            alliances.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'logo_url': row[4],
                'primary_color': row[5],
                'secondary_color': row[6],
                'is_active': bool(row[7])
            })
        
        return alliances
        
    except Exception as e:
        logger.error(f"Error obteniendo alianzas electorales: {e}")
        return []
    finally:
        conn.close()


def create_electoral_alliance(name: str, display_name: str, description: str = None, 
                            logo_url: str = None, primary_color: str = '#007bff', 
                            secondary_color: str = '#6c757d') -> int:
    """Crear nueva alianza electoral."""
    from datetime import datetime
    
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            cursor = conn.execute("""
                INSERT INTO electoral_alliances (
                    name, display_name, description, logo_url, 
                    primary_color, secondary_color, is_active, created_utc, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (name, display_name, description, logo_url, primary_color, secondary_color, current_time, current_time))
            
            alliance_id = cursor.lastrowid
            logger.info(f"Alianza electoral '{display_name}' creada con ID {alliance_id}")
            return alliance_id
            
    except Exception as e:
        logger.error(f"Error creando alianza electoral '{display_name}': {e}")
        raise e
    finally:
        conn.close()


def update_electoral_alliance(alliance_id: int, **kwargs) -> bool:
    """Actualizar alianza electoral."""
    from datetime import datetime
    
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            # Construir query dinámicamente
            fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['name', 'display_name', 'description', 'logo_url', 'primary_color', 'secondary_color', 'is_active']:
                    fields.append(f"{field} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            fields.append("updated_utc = ?")
            values.append(current_time)
            values.append(alliance_id)
            
            query = f"UPDATE electoral_alliances SET {', '.join(fields)} WHERE id = ?"
            conn.execute(query, values)
            
            logger.info(f"Alianza electoral ID {alliance_id} actualizada")
            return True
            
    except Exception as e:
        logger.error(f"Error actualizando alianza electoral {alliance_id}: {e}")
        return False
    finally:
        conn.close()


def assign_candidate_to_alliance(candidate_id: int, alliance_id: int) -> bool:
    """Asignar candidato a una alianza electoral."""
    from datetime import datetime
    
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            conn.execute("""
                UPDATE candidates 
                SET alliance_id = ?, updated_utc = ?
                WHERE id = ?
            """, (alliance_id, current_time, candidate_id))
            
            logger.info(f"Candidato ID {candidate_id} asignado a alianza ID {alliance_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error asignando candidato {candidate_id} a alianza {alliance_id}: {e}")
        return False
    finally:
        conn.close()


def get_candidates_by_alliance(alliance_id: int = None) -> Dict[str, List[Dict[str, Any]]]:
    """Obtener candidatos agrupados por alianza."""
    conn = get_db_connection()
    
    try:
        if alliance_id:
            # Obtener candidatos de una alianza específica
            cursor = conn.execute("""
                SELECT c.id, c.name, c.full_name, c.political_party, c.legislative_position,
                       c.electoral_section, c.district, c.importance_level, c.is_active,
                       ea.id as alliance_id, ea.display_name as alliance_name, 
                       ea.primary_color, ea.secondary_color
                FROM candidates c
                LEFT JOIN electoral_alliances ea ON c.alliance_id = ea.id
                WHERE c.alliance_id = ? AND c.is_active = 1
                ORDER BY c.name
            """, (alliance_id,))
        else:
            # Obtener todos los candidatos con sus alianzas
            cursor = conn.execute("""
                SELECT c.id, c.name, c.full_name, c.political_party, c.legislative_position,
                       c.electoral_section, c.district, c.importance_level, c.is_active,
                       ea.id as alliance_id, ea.display_name as alliance_name, 
                       ea.primary_color, ea.secondary_color
                FROM candidates c
                LEFT JOIN electoral_alliances ea ON c.alliance_id = ea.id
                WHERE c.is_active = 1
                ORDER BY ea.display_name, c.name
            """)
        
        candidates_by_alliance = {}
        
        for row in cursor:
            alliance_name = row[10] if row[10] else 'Sin Alianza'
            
            if alliance_name not in candidates_by_alliance:
                candidates_by_alliance[alliance_name] = {
                    'alliance_info': {
                        'id': row[9],
                        'name': alliance_name,
                        'primary_color': row[11] if row[11] else '#6c757d',
                        'secondary_color': row[12] if row[12] else '#adb5bd'
                    },
                    'candidates': []
                }
            
            candidates_by_alliance[alliance_name]['candidates'].append({
                'id': row[0],
                'name': row[1],
                'full_name': row[2],
                'political_party': row[3],
                'legislative_position': row[4],
                'electoral_section': row[5],
                'district': row[6],
                'importance_level': row[7],
                'is_active': bool(row[8])
            })
        
        return candidates_by_alliance
        
    except Exception as e:
        logger.error(f"Error obteniendo candidatos por alianza: {e}")
        return {}
    finally:
        conn.close()

# ============================================================================
# FUNCIONES PARA GESTIÓN DE PERSONAS
# ============================================================================

def create_person(name: str, full_name: str = None, description: str = None, 
                 position: str = None, political_party: str = None, 
                 importance_level: int = 1) -> int:
    """Crear una nueva persona política."""
    from datetime import datetime
    
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            cursor = conn.execute("""
                INSERT INTO persons (name, full_name, description, position, 
                                   political_party, importance_level, created_utc, updated_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, full_name, description, position, political_party, 
                  importance_level, current_time, current_time))
            
            person_id = cursor.lastrowid
            logger.info(f"Persona creada: {name} (ID: {person_id})")
            return person_id
            
    except sqlite3.IntegrityError as e:
        logger.error(f"Error creando persona {name}: {e}")
        raise ValueError(f"La persona '{name}' ya existe")
    except Exception as e:
        logger.error(f"Error inesperado creando persona {name}: {e}")
        raise


def add_candidate_keyword(candidate_id: int, keyword: str, is_primary: bool = False) -> bool:
    """Agregar una keyword a un candidato."""
    from datetime import datetime
    
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            conn.execute("""
                INSERT OR IGNORE INTO candidate_keywords (candidate_id, keyword, is_primary, created_utc, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (candidate_id, keyword, 1 if is_primary else 0, current_time))
            
            logger.info(f"Keyword '{keyword}' agregada a candidato ID {candidate_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error agregando keyword '{keyword}' a candidato {candidate_id}: {e}")
        return False


def get_candidate_by_keyword(keyword: str) -> Dict[str, Any]:
    """Obtener información de candidato por keyword."""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT c.id, c.name, c.full_name, c.description, c.legislative_position, 
                   c.political_party, c.electoral_section, c.district, c.importance_level, c.is_active
            FROM candidates c
            JOIN candidate_keywords ck ON c.id = ck.candidate_id
            WHERE ck.keyword = ? AND c.is_active = 1
        """, (keyword,))
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "full_name": row[2],
                "description": row[3],
                "legislative_position": row[4],
                "political_party": row[5],
                "electoral_section": row[6],
                "district": row[7],
                "importance_level": row[8],
                "is_active": row[9]
            }
        return None
        
    except Exception as e:
        logger.error(f"Error buscando candidato por keyword '{keyword}': {e}")
        return None


def get_all_candidates() -> List[Dict[str, Any]]:
    """Obtener todos los candidatos activos con estadísticas."""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT c.id, c.name, c.full_name, c.description, c.legislative_position, 
                   c.political_party, c.electoral_section, c.district, c.importance_level, 
                   c.created_utc, c.is_active
            FROM candidates c
            WHERE c.is_active = 1
            ORDER BY c.electoral_section, c.importance_level DESC, c.name
        """)
        
        candidates = []
        for row in cursor:
            candidate_id = row[0]
            
            # Obtener estadísticas de menciones para cada candidato
            stats_cursor = conn.execute("""
                SELECT COUNT(*) as total_mentions,
                       COUNT(DISTINCT h.article_id) as unique_articles,
                       MIN(h.detected_utc) as first_mention,
                       MAX(h.detected_utc) as last_mention
                FROM hits h
                JOIN candidate_keywords ck ON h.keyword = ck.keyword
                WHERE ck.candidate_id = ? AND ck.is_active = 1
            """, (candidate_id,))
            
            stats = stats_cursor.fetchone()
            total_mentions = stats[0] if stats[0] else 0
            unique_articles = stats[1] if stats[1] else 0
            first_mention = stats[2]
            last_mention = stats[3]
            
            # Convertir importance_level a string para compatibilidad con templates
            importance_map = {1: 'low', 2: 'medium', 3: 'high'}
            importance_str = importance_map.get(row[8], 'low')
            
            candidates.append({
                "id": candidate_id,
                "name": row[1],
                "full_name": row[2],
                "description": row[3],
                "legislative_position": row[4],
                "political_party": row[5],
                "electoral_section": row[6],
                "district": row[7],
                "importance_level": importance_str,
                "importance_level_int": row[8],
                "created_utc": row[9],
                "is_active": row[10],
                "total_mentions": total_mentions,
                "unique_articles": unique_articles,
                "first_mention": datetime.fromisoformat(first_mention) if first_mention else None,
                "last_mention": datetime.fromisoformat(last_mention) if last_mention else None
            })
            
        return candidates
        
    except Exception as e:
        logger.error(f"Error obteniendo todos los candidatos: {e}")
        return []


def get_candidate_keywords(candidate_id: int) -> List[Dict[str, Any]]:
    """Obtener todas las keywords de un candidato."""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT keyword, is_primary, created_utc
            FROM candidate_keywords
            WHERE candidate_id = ? AND is_active = 1
            ORDER BY is_primary DESC, keyword
        """, (candidate_id,))
        
        keywords = []
        for row in cursor:
            keywords.append({
                "keyword": row[0],
                "is_primary": bool(row[1]),
                "created_utc": row[2]
            })
            
        return keywords
        
    except Exception as e:
        logger.error(f"Error obteniendo keywords de candidato {candidate_id}: {e}")
        return []


def get_all_active_keywords() -> List[str]:
    """Obtener todas las keywords activas del sistema (config + candidatos)."""
    keywords = []
    
    # Agregar keywords del config
    config_keywords = config.get("keywords", [])
    keywords.extend(config_keywords)
    
    # Agregar keywords de candidatos activos
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT ck.keyword
            FROM candidate_keywords ck
            JOIN candidates c ON ck.candidate_id = c.id
            WHERE ck.is_active = 1 AND c.is_active = 1
            ORDER BY ck.keyword
        """)
        
        candidate_keywords = [row[0] for row in cursor.fetchall()]
        keywords.extend(candidate_keywords)
        
    except Exception as e:
        logger.error(f"Error obteniendo keywords de candidatos: {e}")
    finally:
        conn.close()
    
    # Eliminar duplicados manteniendo el orden
    unique_keywords = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            unique_keywords.append(keyword)
            seen.add(keyword)
    
    logger.info(f"Keywords activas obtenidas: {len(unique_keywords)} ({len(config_keywords)} del config + {len(candidate_keywords)} de candidatos)")
    return unique_keywords


def get_person_stats(person_id: int, hours: int = 24) -> Dict[str, Any]:
    """Obtener estadísticas de menciones de una persona."""
    conn = get_db_connection()
    
    try:
        stats = {
            "person_id": person_id,
            "total_hits": 0,
            "unique_articles": 0,
            "recent_hits": 0,
            "keywords_breakdown": {},
            "recent_articles": []
        }
        
        # Total de hits para esta persona
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits WHERE person_id = ?
        """, (person_id,))
        stats["total_hits"] = cursor.fetchone()[0]
        
        # Artículos únicos
        cursor = conn.execute("""
            SELECT COUNT(DISTINCT article_id) FROM hits WHERE person_id = ?
        """, (person_id,))
        stats["unique_articles"] = cursor.fetchone()[0]
        
        # Calcular promedio de hits por artículo
        if stats["unique_articles"] > 0:
            stats["avg_hits_per_article"] = stats["total_hits"] / stats["unique_articles"]
        else:
            stats["avg_hits_per_article"] = 0
        
        # Hits recientes (últimas X horas)
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits 
            WHERE person_id = ? AND datetime(detected_utc) >= datetime('now', '-{} hours')
        """.format(hours), (person_id,))
        stats["recent_hits"] = cursor.fetchone()[0]
        
        # Primera y última mención
        cursor = conn.execute("""
            SELECT MIN(detected_utc) as first_mention, MAX(detected_utc) as last_mention
            FROM hits WHERE person_id = ?
        """, (person_id,))
        result = cursor.fetchone()
        stats["first_mention"] = result[0] if result[0] else None
        stats["last_mention"] = result[1] if result[1] else None
        
        # Breakdown por keyword
        cursor = conn.execute("""
            SELECT keyword, COUNT(*) as count
            FROM hits 
            WHERE person_id = ?
            GROUP BY keyword
            ORDER BY count DESC
        """, (person_id,))
        
        for row in cursor:
            stats["keywords_breakdown"][row[0]] = row[1]
        
        # Artículos recientes
        cursor = conn.execute("""
            SELECT DISTINCT a.title, a.site, a.link, h.detected_utc
            FROM articles a
            JOIN hits h ON a.id = h.article_id
            WHERE h.person_id = ?
            ORDER BY h.detected_utc DESC
            LIMIT 10
        """, (person_id,))
        
        for row in cursor:
            stats["recent_articles"].append({
                "title": row[0],
                "site": row[1],
                "link": row[2],
                "detected_utc": row[3]
            })
            
        return stats
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de persona {person_id}: {e}")
        return {"error": str(e)}


def create_candidate(name: str, political_party: str, electoral_section: int, 
                    legislative_position: str, full_name: str = None, 
                    description: str = None, district: str = None, 
                    list_number: int = None, list_position: int = None,
                    importance_level: int = 1, alliance_id: int = None) -> int:
    """Crear un nuevo candidato."""
    from datetime import datetime
    
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            cursor = conn.execute("""
                INSERT INTO candidates (
                    name, full_name, description, political_party, 
                    electoral_section, legislative_position, district,
                    list_number, list_position, importance_level, alliance_id,
                    created_utc, updated_utc, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (name, full_name, description, political_party, 
                  electoral_section, legislative_position, district,
                  list_number, list_position, importance_level, alliance_id,
                  current_time, current_time))
            
            candidate_id = cursor.lastrowid
            logger.info(f"Candidato creado: {name} (ID: {candidate_id})")
            return candidate_id
            
    except Exception as e:
        logger.error(f"Error creando candidato {name}: {e}")
        raise


def update_candidate(candidate_id: int, **kwargs) -> bool:
    """Actualizar información de un candidato."""
    from datetime import datetime
    
    allowed_fields = ['name', 'full_name', 'description', 'political_party',
                     'electoral_section', 'legislative_position', 'district',
                     'list_number', 'list_position', 'importance_level', 'alliance_id', 'is_active']
    
    # Filtrar solo campos permitidos
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
        
    # Agregar timestamp de actualización
    updates['updated_utc'] = datetime.utcnow().isoformat()
    
    # Construir query dinámicamente
    set_clause = ', '.join([f"{field} = ?" for field in updates.keys()])
    values = list(updates.values()) + [candidate_id]
    
    conn = get_db_connection()
    
    try:
        with conn:
            conn.execute(f"""
                UPDATE candidates 
                SET {set_clause}
                WHERE id = ?
            """, values)
            
            logger.info(f"Candidato {candidate_id} actualizado: {updates}")
            return True
            
    except Exception as e:
        logger.error(f"Error actualizando candidato {candidate_id}: {e}")
        return False


def get_candidate_stats(candidate_id: int, hours: int = 168) -> Dict[str, Any]:  # 168 horas = 7 días
    """Obtener estadísticas completas de un candidato para su página de perfil."""
    conn = get_db_connection()
    
    try:
        # Obtener información básica del candidato
        cursor = conn.execute("""
            SELECT id, name, full_name, description, legislative_position, 
                   political_party, electoral_section, district, 
                   list_number, list_position, importance_level, is_active
            FROM candidates 
            WHERE id = ?
        """, (candidate_id,))
        
        candidate_row = cursor.fetchone()
        if not candidate_row:
            return {"error": "Candidato no encontrado"}
        
        # Estructura de datos completa para el template
        candidate_data = {
            "basic_info": {
                "id": candidate_row[0],
                "name": candidate_row[1],
                "full_name": candidate_row[2],
                "description": candidate_row[3],
                "legislative_position": candidate_row[4],
                "political_party": candidate_row[5],
                "electoral_section": candidate_row[6],
                "district": candidate_row[7],
                "list_number": candidate_row[8],
                "list_position": candidate_row[9],
                "importance_level": candidate_row[10],
                "is_active": bool(candidate_row[11])
            },
            "stats": {},
            "keywords": [],
            "trends": [],
            "weekly_activity": [],
            "recent_articles": []
        }
        
        # Estadísticas principales
        cursor = conn.execute("""
            SELECT COUNT(*) as total_hits,
                   COUNT(DISTINCT h.article_id) as unique_articles
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
        """, (candidate_id,))
        
        stats_row = cursor.fetchone()
        total_hits = stats_row[0] if stats_row[0] else 0
        unique_articles = stats_row[1] if stats_row[1] else 0
        
        # Hits recientes (últimos 7 días)
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1 
            AND datetime(h.detected_utc) >= datetime('now', '-7 days')
        """, (candidate_id,))
        recent_hits_row = cursor.fetchone()
        recent_hits = recent_hits_row[0] if recent_hits_row else 0
        
        candidate_data["stats"] = {
            "total_hits": total_hits,
            "unique_articles": unique_articles,
            "avg_hits_per_article": total_hits / unique_articles if unique_articles > 0 else 0,
            "recent_hits": recent_hits
        }
        
        # Keywords con estadísticas
        cursor = conn.execute("""
            SELECT ck.keyword, ck.is_primary, COUNT(h.id) as hits_count
            FROM candidate_keywords ck
            LEFT JOIN hits h ON ck.keyword = h.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
            GROUP BY ck.keyword, ck.is_primary
            ORDER BY ck.is_primary DESC, hits_count DESC
        """, (candidate_id,))
        
        for row in cursor:
            candidate_data["keywords"].append({
                "keyword": row[0],
                "is_primary": bool(row[1]),
                "hits_count": row[2] if row[2] else 0
            })
        
        # Tendencias de los últimos 30 días
        cursor = conn.execute("""
            SELECT DATE(h.detected_utc) as date, COUNT(*) as hits_count
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
            AND datetime(h.detected_utc) >= datetime('now', '-30 days')
            GROUP BY DATE(h.detected_utc)
            ORDER BY date DESC
            LIMIT 30
        """, (candidate_id,))
        
        for row in cursor:
            candidate_data["trends"].append({
                "date": row[0],
                "hits_count": row[1]
            })
        
        # Actividad semanal (últimos 7 días)
        cursor = conn.execute("""
            SELECT DATE(h.detected_utc) as date, COUNT(*) as hits_count
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
            AND datetime(h.detected_utc) >= datetime('now', '-7 days')
            GROUP BY DATE(h.detected_utc)
            ORDER BY date DESC
        """, (candidate_id,))
        
        for row in cursor:
            candidate_data["weekly_activity"].append({
                "date": row[0],
                "hits_count": row[1]
            })
        
        # Artículos recientes con conteo de menciones
        cursor = conn.execute("""
            SELECT a.title, a.site, a.link, a.published_utc, COUNT(h.id) as hits_count
            FROM articles a
            JOIN hits h ON a.id = h.article_id
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
            GROUP BY a.id, a.title, a.site, a.link, a.published_utc
            ORDER BY a.published_utc DESC
            LIMIT 20
        """, (candidate_id,))
        
        for row in cursor:
            candidate_data["recent_articles"].append({
                "title": row[0],
                "site": row[1],
                "link": row[2],
                "published_utc": row[3],
                "hits_count": row[4]
            })
            
        return candidate_data
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de candidato {candidate_id}: {e}")
        return {"error": str(e)}


def init_feed_state_from_config():
    """Inicializa el estado de feeds desde la configuración si no existen."""
    from datetime import datetime
    conn = get_db_connection()
    
    with conn:
        for feed in config.get("feeds", []):
            # Verificar si el feed ya existe
            cursor = conn.execute(
                "SELECT COUNT(*) FROM feed_state WHERE name = ?",
                (feed["name"],)
            )
            if cursor.fetchone()[0] == 0:
                # Crear nuevo registro de estado
                now = datetime.utcnow().isoformat()
                conn.execute("""
                    INSERT INTO feed_state (
                        name, url, is_enabled, created_utc, updated_utc,
                        fetch_interval_minutes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    feed["name"],
                    feed["url"],
                    1 if feed.get("enabled", True) else 0,
                    now,
                    now,
                    config.get("interval_minutes", 10)
                ))
                logger.info(f"Inicializado estado para feed: {feed['name']}")


def get_feeds_ready_for_fetch():
    """Obtiene feeds que están listos para ser procesados según su schedule."""
    from datetime import datetime
    conn = get_db_connection()
    feeds = []
    
    with conn:
        cursor = conn.execute("""
            SELECT name, url, etag, last_modified, fetch_interval_minutes
            FROM feed_state 
            WHERE is_enabled = 1 
            AND (next_run_at IS NULL OR next_run_at <= datetime('now'))
            ORDER BY last_fetch_utc ASC NULLS FIRST
        """)
        
        for row in cursor:
            feeds.append({
                "name": row[0],
                "url": row[1],
                "etag": row[2],
                "last_modified": row[3],
                "fetch_interval_minutes": row[4]
            })
    
    return feeds


def update_feed_state(feed_name: str, success: bool, etag: str = None, 
                     last_modified: str = None, error_msg: str = None):
    """Actualiza el estado de un feed después del fetch."""
    from datetime import datetime, timedelta
    import random
    
    conn = get_db_connection()
    now = datetime.utcnow()
    
    with conn:
        if success:
            # Calcular próximo run con jitter adaptativo
            cursor = conn.execute(
                "SELECT fetch_interval_minutes, error_count FROM feed_state WHERE name = ?",
                (feed_name,)
            )
            result = cursor.fetchone()
            if result:
                base_interval = result[0]
                error_count = result[1]
                
                # Jitter: ±20% del intervalo base
                jitter = random.uniform(-0.2, 0.2) * base_interval
                next_interval = base_interval + jitter
                
                # Si había errores, resetear el contador
                if error_count > 0:
                    logger.info(f"Feed {feed_name} recuperado después de {error_count} errores")
                
                next_run = now + timedelta(minutes=next_interval)
                
                conn.execute("""
                    UPDATE feed_state SET
                        etag = ?, last_modified = ?, last_fetch_utc = ?,
                        last_success_utc = ?, error_count = 0, last_error = NULL,
                        next_run_at = ?, updated_utc = ?
                    WHERE name = ?
                """, (
                    etag, last_modified, now.isoformat(), now.isoformat(),
                    next_run.isoformat(), now.isoformat(), feed_name
                ))
        else:
            # Incrementar error count y aplicar backoff exponencial
            cursor = conn.execute(
                "SELECT error_count, fetch_interval_minutes FROM feed_state WHERE name = ?",
                (feed_name,)
            )
            result = cursor.fetchone()
            if result:
                error_count = result[0] + 1
                base_interval = result[1]
                
                # Backoff exponencial: 2^error_count * base_interval (máximo 4 horas)
                backoff_multiplier = min(2 ** error_count, 24)  # máximo 24x
                next_interval = min(base_interval * backoff_multiplier, 240)  # máximo 4 horas
                
                # Jitter para evitar thundering herd
                jitter = random.uniform(0.8, 1.2) * next_interval
                next_run = now + timedelta(minutes=jitter)
                
                conn.execute("""
                    UPDATE feed_state SET
                        last_fetch_utc = ?, error_count = ?, last_error = ?,
                        next_run_at = ?, updated_utc = ?
                    WHERE name = ?
                """, (
                    now.isoformat(), error_count, error_msg,
                    next_run.isoformat(), now.isoformat(), feed_name
                ))
                
                logger.warning(f"Feed {feed_name} falló (error #{error_count}). Próximo intento en {jitter:.1f} minutos")


def get_feed_health_stats():
    """Obtiene estadísticas de salud de todos los feeds."""
    conn = get_db_connection()
    stats = {
        "total_feeds": 0,
        "healthy_feeds": 0,
        "error_feeds": 0,
        "feeds": []
    }
    
    with conn:
        cursor = conn.execute("""
            SELECT name, url, last_success_utc, error_count, last_error,
                   next_run_at, is_enabled, fetch_interval_minutes
            FROM feed_state
            ORDER BY error_count DESC, last_success_utc ASC
        """)
        
        for row in cursor:
            feed_info = {
                "name": row[0],
                "url": row[1],
                "last_success_utc": row[2],
                "error_count": row[3],
                "last_error": row[4],
                "next_run_at": row[5],
                "is_enabled": bool(row[6]),
                "fetch_interval_minutes": row[7],
                "status": "healthy" if row[3] == 0 else "error"
            }
            
            stats["feeds"].append(feed_info)
            stats["total_feeds"] += 1
            
            if row[3] == 0:
                stats["healthy_feeds"] += 1
            else:
                stats["error_feeds"] += 1
    
    return stats


def get_top_mentions(person_id=None, limit=10, min_score=5.0):
    """Obtiene las menciones con mayor score.
    
    Args:
        person_id: ID de la persona (opcional, para filtrar)
        limit: Número máximo de resultados
        min_score: Score mínimo requerido
    
    Returns:
        Lista de tuplas con información de las menciones
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT h.score, h.keyword, h.where_found, a.title, a.site, 
               a.published_utc, p.name, a.link
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        JOIN persons p ON h.person_id = p.id
        WHERE h.score >= ?
    """
    
    params = [min_score]
    
    if person_id:
        query += " AND h.person_id = ?"
        params.append(person_id)
    
    query += " ORDER BY h.score DESC, a.published_utc DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    conn.close()
    return results


def search_articles_fts(query, limit=50, person_id=None):
    """Busca artículos usando FTS5.
    
    Args:
        query: Término de búsqueda
        limit: Número máximo de resultados
        person_id: ID de la persona (opcional, para filtrar por menciones)
    
    Returns:
        Lista de artículos que coinciden con la búsqueda
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if person_id:
        # Buscar artículos que mencionen a una persona específica
        sql = """
            SELECT DISTINCT a.id, a.title, a.site, a.link, a.published_utc, 
                   a.full_content, fts.rank
            FROM articles_fts fts
            JOIN articles a ON fts.article_id = a.id
            JOIN hits h ON h.article_id = a.id
            WHERE articles_fts MATCH ? AND h.person_id = ?
            ORDER BY fts.rank, a.published_utc DESC
            LIMIT ?
        """
        cursor.execute(sql, (query, person_id, limit))
    else:
        # Búsqueda general
        sql = """
            SELECT a.id, a.title, a.site, a.link, a.published_utc, 
                   a.full_content, fts.rank
            FROM articles_fts fts
            JOIN articles a ON fts.article_id = a.id
            WHERE articles_fts MATCH ?
            ORDER BY fts.rank, a.published_utc DESC
            LIMIT ?
        """
        cursor.execute(sql, (query, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return results


def search_mentions_fts(query, person_id=None, limit=50):
    """Busca menciones usando FTS5.
    
    Args:
        query: Término de búsqueda
        person_id: ID de la persona (opcional)
        limit: Número máximo de resultados
    
    Returns:
        Lista de menciones que coinciden con la búsqueda
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    base_query = """
        SELECT h.id, h.keyword, h.where_found, h.score, 
               a.title, a.site, a.link, a.published_utc, 
               p.name, 0 as rank
        FROM articles_fts fts
        JOIN articles a ON fts.article_id = a.id
        JOIN hits h ON h.article_id = a.id
        JOIN persons p ON h.person_id = p.id
        WHERE articles_fts MATCH ?
    """
    
    params = [query]
    
    if person_id:
        base_query += " AND h.person_id = ?"
        params.append(person_id)
    
    base_query += " ORDER BY h.score DESC, a.published_utc DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(base_query, params)
    results = cursor.fetchall()
    
    conn.close()
    return results


def populate_fts_table():
    """Puebla la tabla FTS5 con artículos existentes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Limpiar tabla FTS5
    cursor.execute("DELETE FROM articles_fts")
    
    # Insertar todos los artículos existentes
    cursor.execute("""
        INSERT INTO articles_fts(article_id, title, content, site)
        SELECT id, title, COALESCE(full_content, ''), site
        FROM articles
    """)
    
    conn.commit()
    conn.close()
    
    return cursor.rowcount
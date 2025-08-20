import sqlite3
import logging

from app.config import config
from app.storage import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_processed_articles():
    """Verifica los artículos procesados y muestra información sobre su contenido."""
    conn = get_db_connection()
    with conn:
        # Obtener estadísticas generales
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
        
        # Mostrar estadísticas
        print("===== ESTADÍSTICAS DE PROCESAMIENTO DE ARTÍCULOS =====")
        print(f"Total de artículos: {total}")
        print(f"Artículos no procesados: {not_processed}")
        print(f"Artículos procesados con éxito: {success}")
        print(f"Artículos fallidos: {failed}")
        print(f"Total de hits: {total_hits}")
        print(f"Hits por palabra clave: {keyword_hits}")
        print(f"Hits por ubicación: {where_found}")
        
        # Mostrar ejemplos de artículos procesados con contenido
        print("\n===== EJEMPLOS DE ARTÍCULOS CON CONTENIDO COMPLETO =====")
        cursor.execute(
            "SELECT id, site, title, link, LENGTH(full_content) as content_length FROM articles "
            "WHERE content_processed = 1 AND full_content IS NOT NULL AND full_content != '' "
            "ORDER BY content_length DESC LIMIT 5"
        )
        for row in cursor:
            print(f"ID: {row['id']}")
            print(f"Sitio: {row['site']}")
            print(f"Título: {row['title']}")
            print(f"Enlace: {row['link']}")
            print(f"Longitud del contenido: {row['content_length']} caracteres")
            print("---")
        
        # Mostrar ejemplos de hits encontrados en el contenido
        print("\n===== EJEMPLOS DE HITS ENCONTRADOS EN CONTENIDO =====")
        cursor.execute(
            "SELECT h.article_id, h.keyword, h.where_found, a.title, a.site "
            "FROM hits h JOIN articles a ON h.article_id = a.id "
            "WHERE h.where_found = 'content' "
            "ORDER BY h.detected_utc DESC LIMIT 5"
        )
        for row in cursor:
            print(f"ID: {row['article_id']}")
            print(f"Palabra clave: {row['keyword']}")
            print(f"Encontrado en: {row['where_found']}")
            print(f"Título: {row['title']}")
            print(f"Sitio: {row['site']}")
            print("---")
        
        # Mostrar un fragmento del contenido de un artículo con hit
        print("\n===== FRAGMENTO DE CONTENIDO CON KEYWORD =====")
        cursor.execute(
            "SELECT a.id, a.title, a.full_content, h.keyword "
            "FROM articles a JOIN hits h ON a.id = h.article_id "
            "WHERE h.where_found = 'content' AND a.full_content IS NOT NULL AND a.full_content != '' "
            "ORDER BY h.detected_utc DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            content = row['full_content']
            keyword = row['keyword']
            print(f"ID: {row['id']}")
            print(f"Título: {row['title']}")
            print(f"Palabra clave: {keyword}")
            
            # Encontrar la posición de la palabra clave en el contenido
            pos = content.lower().find(keyword.lower())
            if pos >= 0:
                # Mostrar un fragmento del contenido alrededor de la palabra clave
                start = max(0, pos - 100)
                end = min(len(content), pos + len(keyword) + 100)
                fragment = content[start:end]
                
                # Resaltar la palabra clave en el fragmento
                keyword_start = pos - start
                keyword_end = keyword_start + len(keyword)
                highlighted = fragment[:keyword_start] + "[" + fragment[keyword_start:keyword_end] + "]" + fragment[keyword_end:]
                
                print(f"Fragmento de contenido: ...{highlighted}...")
            else:
                print("No se pudo encontrar la palabra clave en el contenido.")
        else:
            print("No se encontraron hits en el contenido de los artículos.")

if __name__ == "__main__":
    check_processed_articles()
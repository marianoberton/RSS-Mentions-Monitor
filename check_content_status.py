import sqlite3
import sys
import os
from datetime import datetime

# Configurar el path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from app.config import config

def check_content_status():
    """Verifica el estado de procesamiento de los artículos y muestra estadísticas detalladas."""
    conn = get_db_connection()
    try:
        # Estadísticas generales
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
        
        print("\n===== ESTADÍSTICAS DE PROCESAMIENTO DE ARTÍCULOS =====")
        print(f"Total de artículos: {total}")
        print(f"Artículos no procesados: {not_processed}")
        print(f"Artículos procesados con éxito: {success}")
        print(f"Artículos fallidos: {failed}")
        print(f"Total de hits: {total_hits}")
        print(f"Hits por palabra clave: {keyword_hits}")
        print(f"Hits por ubicación: {where_found}")
        
        # Verificar si hay artículos con contenido pero sin procesar
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0 AND full_content IS NOT NULL AND full_content != ''")
        unprocessed_with_content = cursor.fetchone()[0]
        print(f"\nArtículos con contenido pero marcados como no procesados: {unprocessed_with_content}")
        
        # Verificar si hay artículos procesados pero sin contenido
        cursor.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1 AND (full_content IS NULL OR full_content = '')")
        processed_without_content = cursor.fetchone()[0]
        print(f"Artículos marcados como procesados pero sin contenido: {processed_without_content}")
        
        # Mostrar ejemplos de artículos procesados con éxito
        print("\n===== EJEMPLOS DE ARTÍCULOS PROCESADOS CON ÉXITO =====")
        cursor.execute(
            "SELECT id, site, title, link, published_utc, LENGTH(full_content) as content_length " 
            "FROM articles WHERE content_processed = 1 AND full_content IS NOT NULL AND full_content != '' "
            "ORDER BY published_utc DESC LIMIT 5"
        )
        for row in cursor.fetchall():
            print(f"ID: {row['id']}")
            print(f"Sitio: {row['site']}")
            print(f"Título: {row['title']}")
            print(f"Enlace: {row['link']}")
            print(f"Fecha: {row['published_utc']}")
            print(f"Longitud del contenido: {row['content_length']} caracteres")
            print("---")
        
        # Mostrar ejemplos de hits encontrados en el contenido
        print("\n===== EJEMPLOS DE HITS ENCONTRADOS EN CONTENIDO =====")
        cursor.execute(
            "SELECT h.article_id, h.keyword, h.where_found, a.site, a.title, a.link " 
            "FROM hits h JOIN articles a ON h.article_id = a.id "
            "WHERE h.where_found = 'content' "
            "ORDER BY h.detected_utc DESC LIMIT 5"
        )
        for row in cursor.fetchall():
            print(f"ID del artículo: {row['article_id']}")
            print(f"Palabra clave: {row['keyword']}")
            print(f"Encontrado en: {row['where_found']}")
            print(f"Sitio: {row['site']}")
            print(f"Título: {row['title']}")
            print(f"Enlace: {row['link']}")
            
            # Mostrar un fragmento del contenido con la palabra clave
            article_id = row['article_id']
            keyword = row['keyword']
            cursor.execute("SELECT full_content FROM articles WHERE id = ?", (article_id,))
            content_row = cursor.fetchone()
            if content_row and content_row['full_content']:
                content = content_row['full_content']
                keyword_pos = content.lower().find(keyword.lower())
                if keyword_pos >= 0:
                    start = max(0, keyword_pos - 100)
                    end = min(len(content), keyword_pos + len(keyword) + 100)
                    fragment = content[start:end]
                    # Resaltar la palabra clave
                    keyword_start = max(0, keyword_pos - start)
                    keyword_end = keyword_start + len(keyword)
                    highlighted = fragment[:keyword_start] + "[" + fragment[keyword_start:keyword_end] + "]" + fragment[keyword_end:]
                    print(f"Fragmento: ...{highlighted}...")
            print("---")
        
        # Verificar si hay hits sin artículos correspondientes
        cursor.execute(
            "SELECT COUNT(*) FROM hits h LEFT JOIN articles a ON h.article_id = a.id WHERE a.id IS NULL"
        )
        orphaned_hits = cursor.fetchone()[0]
        print(f"\nHits sin artículos correspondientes: {orphaned_hits}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_content_status()
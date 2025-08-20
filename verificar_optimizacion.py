import sqlite3
import os
import json
from collections import Counter

# Ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mentions.db')

def obtener_conexion_db():
    """Obtiene una conexión a la base de datos SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def verificar_metodos_extraccion():
    """Verifica los métodos de extracción utilizados para cada feed"""
    conn = obtener_conexion_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Verificar si existe la columna extraction_method
        cursor.execute("PRAGMA table_info(articles)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'extraction_method' not in columnas:
            print("La columna 'extraction_method' no existe en la tabla 'articles'.")
            print("Columnas disponibles:", columnas)
            return
        
        # Obtener estadísticas por sitio y método de extracción
        cursor.execute("""
        SELECT site, extraction_method, COUNT(*) as cantidad
        FROM articles
        WHERE extraction_method IS NOT NULL
        GROUP BY site, extraction_method
        ORDER BY site, extraction_method
        """)
        
        resultados = cursor.fetchall()
        
        if not resultados:
            print("No se encontraron artículos con método de extracción registrado.")
            return
        
        # Organizar resultados por sitio
        estadisticas_por_sitio = {}
        for row in resultados:
            site = row['site']
            metodo = row['extraction_method']
            cantidad = row['cantidad']
            
            if site not in estadisticas_por_sitio:
                estadisticas_por_sitio[site] = []
            
            estadisticas_por_sitio[site].append({
                'metodo': metodo,
                'cantidad': cantidad
            })
        
        # Mostrar resultados
        print("\nESTADÍSTICAS DE MÉTODOS DE EXTRACCIÓN POR SITIO:\n")
        for site, metodos in estadisticas_por_sitio.items():
            print(f"Sitio: {site}")
            for metodo_info in metodos:
                print(f"  - Método: {metodo_info['metodo']} - Cantidad: {metodo_info['cantidad']} artículos")
            print()
        
        # Verificar longitud de contenido por método
        cursor.execute("""
        SELECT extraction_method, 
               AVG(LENGTH(full_content)) as longitud_promedio,
               MIN(LENGTH(full_content)) as longitud_minima,
               MAX(LENGTH(full_content)) as longitud_maxima,
               COUNT(*) as cantidad
        FROM articles
        WHERE extraction_method IS NOT NULL
        GROUP BY extraction_method
        ORDER BY longitud_promedio DESC
        """)
        
        resultados_longitud = cursor.fetchall()
        
        print("\nLONGITUD DE CONTENIDO POR MÉTODO DE EXTRACCIÓN:\n")
        for row in resultados_longitud:
            print(f"Método: {row['extraction_method']}")
            print(f"  - Artículos: {row['cantidad']}")
            print(f"  - Longitud promedio: {int(row['longitud_promedio'])} caracteres")
            print(f"  - Longitud mínima: {row['longitud_minima']} caracteres")
            print(f"  - Longitud máxima: {row['longitud_maxima']} caracteres")
            print()
        
        # Mostrar ejemplos de contenido para cada método
        print("\nEJEMPLOS DE CONTENIDO POR MÉTODO DE EXTRACCIÓN:\n")
        for metodo in ['feed_directo', 'beautifulsoup', 'playwright']:
            cursor.execute("""
            SELECT site, title, LENGTH(full_content) as longitud, full_content
            FROM articles
            WHERE extraction_method = ?
            ORDER BY LENGTH(full_content) DESC
            LIMIT 1
            """, (metodo,))
            
            ejemplo = cursor.fetchone()
            if ejemplo:
                print(f"Método: {metodo} - Sitio: {ejemplo['site']} - Título: {ejemplo['title']}")
                print(f"Longitud: {ejemplo['longitud']} caracteres")
                print("Primeros 300 caracteres del contenido:")
                print(ejemplo['full_content'][:300] + "..." if len(ejemplo['full_content']) > 300 else ejemplo['full_content'])
                print("\n" + "-"*80 + "\n")
    
    except Exception as e:
        print(f"Error al verificar métodos de extracción: {e}")
    
    finally:
        conn.close()

def main():
    print("Verificando optimización de extracción de contenido...\n")
    verificar_metodos_extraccion()

if __name__ == "__main__":
    main()
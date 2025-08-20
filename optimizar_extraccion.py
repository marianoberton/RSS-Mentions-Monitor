import feedparser
import json
import os
import sys
import sqlite3
import datetime
from urllib.parse import urlparse

# Importar módulos condicionales
try:
    from bs4 import BeautifulSoup
    import requests
    BS4_DISPONIBLE = True
except ImportError:
    BS4_DISPONIBLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_DISPONIBLE = True
except ImportError:
    PLAYWRIGHT_DISPONIBLE = False

# Configuración
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mentions.db')

# Feeds que contienen el artículo completo en el RSS
FEEDS_CON_CONTENIDO_COMPLETO = {
    'infocielo': True,
    'labrujula24': True,
    'lanueva': True,
    'lpo': True,
    'letra_p': False,
    'diario3': False
}

def cargar_config():
    """Carga la configuración desde el archivo YAML"""
    import yaml
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error al cargar la configuración: {e}")
        return None

def obtener_conexion_db():
    """Obtiene una conexión a la base de datos SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def extraer_contenido_feed(entry, feed_name):
    """Extrae el contenido directamente del feed RSS"""
    contenido = ""
    
    # Intentar extraer del campo 'content' si existe
    if 'content' in entry:
        if isinstance(entry.content, list) and len(entry.content) > 0:
            contenido = entry.content[0].value
        else:
            contenido = str(entry.content)
    # Si no hay 'content', intentar con 'summary'
    elif 'summary' in entry:
        contenido = entry.summary
    
    # Limpiar el contenido si es necesario (eliminar etiquetas HTML no deseadas, etc.)
    # Aquí se podría implementar una limpieza específica para cada feed si fuera necesario
    
    return contenido

def extraer_con_beautifulsoup(url):
    """Extrae el contenido de un artículo usando BeautifulSoup"""
    if not BS4_DISPONIBLE:
        print("BeautifulSoup no está disponible. Instálalo con: pip install beautifulsoup4 requests")
        return ""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Intentar encontrar el contenido principal del artículo
        # Esta lógica puede necesitar ajustes según el sitio web específico
        article = soup.find('article') or soup.find('div', class_='article-body') or soup.find('div', class_='content')
        
        if article:
            # Extraer solo el texto de los párrafos
            paragraphs = article.find_all('p')
            content = '\n'.join([p.get_text().strip() for p in paragraphs])
            return content
        else:
            # Si no se encuentra una estructura específica, devolver el texto del body
            body = soup.find('body')
            if body:
                return body.get_text().strip()
            return ""
    
    except Exception as e:
        print(f"Error al extraer contenido con BeautifulSoup: {e}")
        return ""

def extraer_con_playwright(url):
    """Extrae el contenido de un artículo usando Playwright"""
    if not PLAYWRIGHT_DISPONIBLE:
        print("Playwright no está disponible. Instálalo con: pip install playwright")
        return ""
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            
            # Esperar a que el contenido se cargue
            page.wait_for_load_state('networkidle')
            
            # Intentar encontrar el contenido principal
            selectors = [
                'article', 
                '.article-body', 
                '.content', 
                '.nota-content',
                'main'
            ]
            
            content = ""
            for selector in selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        # Extraer el texto del elemento
                        content = element.inner_text()
                        break
                except:
                    continue
            
            # Si no se encontró contenido con los selectores, tomar el body
            if not content:
                body = page.query_selector('body')
                if body:
                    content = body.inner_text()
            
            browser.close()
            return content
    
    except Exception as e:
        print(f"Error al extraer contenido con Playwright: {e}")
        return ""

def procesar_feed(feed_info):
    """Procesa un feed RSS y extrae sus artículos"""
    print(f"Procesando feed: {feed_info['name']} - {feed_info['url']}")
    
    try:
        feed = feedparser.parse(feed_info['url'])
        
        if not feed.entries:
            print(f"  - No se encontraron entradas en el feed")
            return []
        
        articulos_procesados = []
        
        for entry in feed.entries:
            try:
                # Extraer información básica
                titulo = entry.title
                url = entry.link
                fecha_publicacion = None
                
                # Intentar obtener la fecha de publicación
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    fecha_publicacion = datetime.datetime(*entry.published_parsed[:6])
                
                # Determinar el método de extracción según el feed
                contenido = ""
                metodo_extraccion = ""
                
                if FEEDS_CON_CONTENIDO_COMPLETO.get(feed_info['name'], False):
                    # Extraer directamente del feed
                    contenido = extraer_contenido_feed(entry, feed_info['name'])
                    metodo_extraccion = "feed_directo"
                else:
                    # Intentar primero con BeautifulSoup
                    if BS4_DISPONIBLE:
                        contenido = extraer_con_beautifulsoup(url)
                        metodo_extraccion = "beautifulsoup"
                    
                    # Si BeautifulSoup no obtuvo contenido o no está disponible, intentar con Playwright
                    if (not contenido or len(contenido) < 100) and PLAYWRIGHT_DISPONIBLE:
                        contenido = extraer_con_playwright(url)
                        metodo_extraccion = "playwright"
                
                # Guardar el artículo procesado
                articulo = {
                    'titulo': titulo,
                    'url': url,
                    'fecha_publicacion': fecha_publicacion.isoformat() if fecha_publicacion else None,
                    'contenido': contenido[:500] + '...' if len(contenido) > 500 else contenido,  # Truncar para la salida
                    'longitud_contenido': len(contenido),
                    'feed': feed_info['name'],
                    'metodo_extraccion': metodo_extraccion
                }
                
                articulos_procesados.append(articulo)
                print(f"  - Artículo procesado: {titulo} - Método: {metodo_extraccion} - Longitud: {len(contenido)} caracteres")
                
            except Exception as e:
                print(f"  - Error al procesar entrada: {str(e)}")
        
        return articulos_procesados
        
    except Exception as e:
        print(f"  - Error al procesar el feed: {str(e)}")
        return []

def guardar_articulos_db(articulos):
    """Guarda los artículos procesados en la base de datos"""
    conn = obtener_conexion_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe, si no, crearla
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT,
            title TEXT,
            link TEXT UNIQUE,
            published_utc TEXT,
            inserted_utc TEXT,
            content_processed INTEGER DEFAULT 0,
            full_content TEXT,
            extraction_method TEXT
        )
        """)
        
        # Insertar artículos
        for articulo in articulos:
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO articles 
                (site, title, link, published_utc, inserted_utc, content_processed, full_content, extraction_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    articulo['feed'],
                    articulo['titulo'],
                    articulo['url'],
                    articulo['fecha_publicacion'],
                    datetime.datetime.utcnow().isoformat(),
                    1,  # Ya procesado
                    articulo['contenido'],
                    articulo['metodo_extraccion']
                ))
            except Exception as e:
                print(f"Error al insertar artículo: {e}")
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error al guardar artículos en la base de datos: {e}")
        return False
    
    finally:
        conn.close()

def main():
    # Cargar configuración
    config = cargar_config()
    if not config:
        print("No se pudo cargar la configuración. Saliendo.")
        return
    
    # Obtener feeds habilitados
    feeds_habilitados = [feed for feed in config.get('feeds', []) if feed.get('enabled', False)]
    
    if not feeds_habilitados:
        print("No hay feeds habilitados en la configuración.")
        return
    
    print(f"Se procesarán {len(feeds_habilitados)} feeds habilitados.")
    
    # Procesar cada feed
    todos_articulos = []
    for feed_info in feeds_habilitados:
        articulos = procesar_feed(feed_info)
        todos_articulos.extend(articulos)
    
    # Guardar artículos en la base de datos
    if todos_articulos:
        if guardar_articulos_db(todos_articulos):
            print(f"\nSe guardaron {len(todos_articulos)} artículos en la base de datos.")
        else:
            print("\nHubo un error al guardar los artículos en la base de datos.")
    else:
        print("\nNo se encontraron artículos para procesar.")

if __name__ == "__main__":
    main()
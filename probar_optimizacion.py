import os
import sys
import logging
import yaml
import feedparser
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos de la aplicación
from app.feed_extractor import extraer_contenido_feed, tiene_contenido_completo
from app.improved_extractor import extract_article_content_improved

# Intentar importar Playwright
try:
    from app.improved_extractor import extract_with_playwright
    import asyncio
    PLAYWRIGHT_DISPONIBLE = True
except ImportError:
    PLAYWRIGHT_DISPONIBLE = False
    logger.warning("Playwright no está disponible. La extracción con navegador no se realizará.")

# Cargar configuración
def cargar_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error al cargar la configuración: {e}")
        return None

# Función para extraer contenido con Playwright
async def extraer_con_playwright_async(url):
    if not PLAYWRIGHT_DISPONIBLE:
        return ""
    try:
        return await extract_with_playwright(url)
    except Exception as e:
        logger.error(f"Error al extraer con Playwright: {e}")
        return ""

# Función principal para probar la extracción
def probar_extraccion():
    config = cargar_config()
    if not config:
        logger.error("No se pudo cargar la configuración.")
        return
    
    # Obtener feeds habilitados
    feeds_habilitados = [feed for feed in config.get('feeds', []) if feed.get('enabled', True)]
    
    if not feeds_habilitados:
        logger.error("No hay feeds habilitados en la configuración.")
        return
    
    logger.info(f"Se probarán {len(feeds_habilitados)} feeds habilitados.")
    
    # Estadísticas
    estadisticas = {
        "total_articulos": 0,
        "articulos_con_contenido_feed": 0,
        "articulos_sin_contenido_feed": 0,
        "tiempo_promedio_feed": 0,
        "tiempo_promedio_bs4": 0,
        "tiempo_promedio_playwright": 0
    }
    
    # Procesar cada feed
    for feed_info in feeds_habilitados:
        logger.info(f"\nProcesando feed: {feed_info['name']} - {feed_info['url']}")
        
        try:
            # Parsear el feed
            feed = feedparser.parse(feed_info['url'])
            
            if not feed.entries:
                logger.warning(f"No se encontraron entradas en el feed {feed_info['name']}")
                continue
            
            # Verificar si este feed tiene contenido completo
            tiene_contenido = tiene_contenido_completo(feed_info['name'])
            logger.info(f"¿Feed con contenido completo? {'Sí' if tiene_contenido else 'No'}")
            
            # Procesar solo las primeras 3 entradas para la prueba
            for i, entry in enumerate(feed.entries[:3]):
                if i >= 3:  # Limitar a 3 artículos por feed
                    break
                    
                estadisticas["total_articulos"] += 1
                
                titulo = entry.title
                url = entry.link
                logger.info(f"\nArticulo {i+1}: {titulo}")
                logger.info(f"URL: {url}")
                
                # 1. Intentar extraer del feed
                inicio = datetime.now()
                contenido_feed = extraer_contenido_feed(entry, feed_info['name'])
                tiempo_feed = (datetime.now() - inicio).total_seconds()
                
                if contenido_feed and len(contenido_feed) > 100:
                    estadisticas["articulos_con_contenido_feed"] += 1
                    logger.info(f"✓ Contenido extraído del feed: {len(contenido_feed)} caracteres en {tiempo_feed:.2f} segundos")
                    logger.info(f"Primeros 150 caracteres: {contenido_feed[:150]}...")
                else:
                    estadisticas["articulos_sin_contenido_feed"] += 1
                    logger.info(f"✗ No se pudo extraer contenido del feed o es muy corto ({len(contenido_feed) if contenido_feed else 0} caracteres)")
                    
                    # 2. Intentar con BeautifulSoup
                    inicio = datetime.now()
                    contenido_bs4 = extract_article_content_improved(url)
                    tiempo_bs4 = (datetime.now() - inicio).total_seconds()
                    
                    if contenido_bs4 and len(contenido_bs4) > 100:
                        logger.info(f"✓ Contenido extraído con BeautifulSoup: {len(contenido_bs4)} caracteres en {tiempo_bs4:.2f} segundos")
                        logger.info(f"Primeros 150 caracteres: {contenido_bs4[:150]}...")
                    else:
                        logger.info(f"✗ No se pudo extraer contenido con BeautifulSoup o es muy corto ({len(contenido_bs4) if contenido_bs4 else 0} caracteres)")
                        
                        # 3. Intentar con Playwright si está disponible
                        if PLAYWRIGHT_DISPONIBLE:
                            inicio = datetime.now()
                            contenido_playwright = asyncio.run(extraer_con_playwright_async(url))
                            tiempo_playwright = (datetime.now() - inicio).total_seconds()
                            
                            if contenido_playwright and len(contenido_playwright) > 100:
                                logger.info(f"✓ Contenido extraído con Playwright: {len(contenido_playwright)} caracteres en {tiempo_playwright:.2f} segundos")
                                logger.info(f"Primeros 150 caracteres: {contenido_playwright[:150]}...")
                            else:
                                logger.info(f"✗ No se pudo extraer contenido con Playwright o es muy corto ({len(contenido_playwright) if contenido_playwright else 0} caracteres)")
                
                # Actualizar estadísticas de tiempo
                estadisticas["tiempo_promedio_feed"] += tiempo_feed
                if 'tiempo_bs4' in locals():
                    estadisticas["tiempo_promedio_bs4"] += tiempo_bs4
                if 'tiempo_playwright' in locals():
                    estadisticas["tiempo_promedio_playwright"] += tiempo_playwright
                
        except Exception as e:
            logger.error(f"Error al procesar el feed {feed_info['name']}: {e}")
    
    # Calcular promedios
    if estadisticas["total_articulos"] > 0:
        estadisticas["tiempo_promedio_feed"] /= estadisticas["total_articulos"]
        if estadisticas["articulos_sin_contenido_feed"] > 0:
            estadisticas["tiempo_promedio_bs4"] /= estadisticas["articulos_sin_contenido_feed"]
            if 'tiempo_promedio_playwright' in estadisticas and estadisticas["tiempo_promedio_playwright"] > 0:
                estadisticas["tiempo_promedio_playwright"] /= estadisticas["articulos_sin_contenido_feed"]
    
    # Mostrar estadísticas
    logger.info("\n" + "=" * 50)
    logger.info("ESTADÍSTICAS DE EXTRACCIÓN")
    logger.info("=" * 50)
    logger.info(f"Total de artículos procesados: {estadisticas['total_articulos']}")
    logger.info(f"Artículos con contenido en el feed: {estadisticas['articulos_con_contenido_feed']} ({estadisticas['articulos_con_contenido_feed']/estadisticas['total_articulos']*100:.1f}%)")
    logger.info(f"Artículos sin contenido en el feed: {estadisticas['articulos_sin_contenido_feed']} ({estadisticas['articulos_sin_contenido_feed']/estadisticas['total_articulos']*100:.1f}%)")
    logger.info(f"Tiempo promedio de extracción del feed: {estadisticas['tiempo_promedio_feed']:.2f} segundos")
    if estadisticas["articulos_sin_contenido_feed"] > 0:
        logger.info(f"Tiempo promedio de extracción con BeautifulSoup: {estadisticas['tiempo_promedio_bs4']:.2f} segundos")
        if 'tiempo_promedio_playwright' in estadisticas and estadisticas["tiempo_promedio_playwright"] > 0:
            logger.info(f"Tiempo promedio de extracción con Playwright: {estadisticas['tiempo_promedio_playwright']:.2f} segundos")
    
    # Conclusión
    logger.info("\nCONCLUSIÓN:")
    if estadisticas['articulos_con_contenido_feed'] > 0:
        logger.info(f"La extracción directa del feed es efectiva para {estadisticas['articulos_con_contenido_feed']} de {estadisticas['total_articulos']} artículos ({estadisticas['articulos_con_contenido_feed']/estadisticas['total_articulos']*100:.1f}%).")
        logger.info("Esto representa un ahorro significativo de recursos y tiempo de procesamiento.")
    else:
        logger.info("La extracción directa del feed no fue efectiva para ningún artículo.")
        logger.info("Se recomienda revisar la configuración de los feeds o los métodos de extracción.")

if __name__ == "__main__":
    probar_extraccion()
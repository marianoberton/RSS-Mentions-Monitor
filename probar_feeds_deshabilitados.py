import os
import sys
import logging
import yaml
import feedparser
from datetime import datetime
import asyncio

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
from app.improved_extractor import extract_article_content_improved, extract_with_playwright
from app.feed_extractor import extraer_contenido_feed

# Cargar configuración
def cargar_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error al cargar la configuración: {e}")
        return None

# Función principal para probar los feeds deshabilitados
def probar_feeds_deshabilitados():
    config = cargar_config()
    if not config:
        logger.error("No se pudo cargar la configuración.")
        return
    
    # Obtener feeds deshabilitados
    feeds_deshabilitados = [feed for feed in config.get('feeds', []) if not feed.get('enabled', True)]
    
    if not feeds_deshabilitados:
        logger.error("No hay feeds deshabilitados en la configuración.")
        return
    
    logger.info(f"Se probarán {len(feeds_deshabilitados)} feeds deshabilitados.")
    
    # Estadísticas
    estadisticas = {
        "total_articulos": 0,
        "articulos_con_contenido_feed": 0,
        "articulos_con_contenido_bs4": 0,
        "articulos_con_contenido_playwright": 0,
        "articulos_sin_contenido": 0
    }
    
    # Procesar cada feed
    for feed_info in feeds_deshabilitados:
        logger.info(f"\nProcesando feed: {feed_info['name']} - {feed_info['url']}")
        
        try:
            # Parsear el feed
            feed = feedparser.parse(feed_info['url'])
            
            if not feed.entries:
                logger.warning(f"No se encontraron entradas en el feed {feed_info['name']}")
                continue
            
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
                contenido_feed = extraer_contenido_feed(entry, feed_info['name'])
                
                if contenido_feed and len(contenido_feed) > 100:
                    estadisticas["articulos_con_contenido_feed"] += 1
                    logger.info(f"✓ Contenido extraído del feed: {len(contenido_feed)} caracteres")
                    logger.info(f"Primeros 150 caracteres: {contenido_feed[:150]}...")
                else:
                    logger.info(f"✗ No se pudo extraer contenido del feed o es muy corto ({len(contenido_feed) if contenido_feed else 0} caracteres)")
                    
                    # 2. Intentar con BeautifulSoup
                    contenido_bs4 = extract_article_content_improved(url)
                    
                    if contenido_bs4 and len(contenido_bs4) > 100:
                        estadisticas["articulos_con_contenido_bs4"] += 1
                        logger.info(f"✓ Contenido extraído con BeautifulSoup: {len(contenido_bs4)} caracteres")
                        logger.info(f"Primeros 150 caracteres: {contenido_bs4[:150]}...")
                    else:
                        logger.info(f"✗ No se pudo extraer contenido con BeautifulSoup o es muy corto ({len(contenido_bs4) if contenido_bs4 else 0} caracteres)")
                        
                        # 3. Intentar con Playwright
                        try:
                            contenido_playwright = asyncio.run(extract_with_playwright(url))
                            
                            if contenido_playwright and len(contenido_playwright) > 100:
                                estadisticas["articulos_con_contenido_playwright"] += 1
                                logger.info(f"✓ Contenido extraído con Playwright: {len(contenido_playwright)} caracteres")
                                logger.info(f"Primeros 150 caracteres: {contenido_playwright[:150]}...")
                            else:
                                estadisticas["articulos_sin_contenido"] += 1
                                logger.info(f"✗ No se pudo extraer contenido con Playwright o es muy corto ({len(contenido_playwright) if contenido_playwright else 0} caracteres)")
                        except Exception as e:
                            estadisticas["articulos_sin_contenido"] += 1
                            logger.error(f"Error al extraer con Playwright: {e}")
                
        except Exception as e:
            logger.error(f"Error al procesar el feed {feed_info['name']}: {e}")
    
    # Mostrar estadísticas
    logger.info("\n" + "=" * 50)
    logger.info("ESTADÍSTICAS DE EXTRACCIÓN PARA FEEDS DESHABILITADOS")
    logger.info("=" * 50)
    logger.info(f"Total de artículos procesados: {estadisticas['total_articulos']}")
    logger.info(f"Artículos con contenido en el feed: {estadisticas['articulos_con_contenido_feed']} ({estadisticas['articulos_con_contenido_feed']/estadisticas['total_articulos']*100:.1f}% si hay alguno)")
    logger.info(f"Artículos con contenido extraído con BeautifulSoup: {estadisticas['articulos_con_contenido_bs4']} ({estadisticas['articulos_con_contenido_bs4']/estadisticas['total_articulos']*100:.1f}%)")
    logger.info(f"Artículos con contenido extraído con Playwright: {estadisticas['articulos_con_contenido_playwright']} ({estadisticas['articulos_con_contenido_playwright']/estadisticas['total_articulos']*100:.1f}%)")
    logger.info(f"Artículos sin contenido extraído: {estadisticas['articulos_sin_contenido']} ({estadisticas['articulos_sin_contenido']/estadisticas['total_articulos']*100:.1f}% si hay alguno)")
    
    # Conclusión
    logger.info("\nCONCLUSIÓN:")
    exito_total = estadisticas['articulos_con_contenido_feed'] + estadisticas['articulos_con_contenido_bs4'] + estadisticas['articulos_con_contenido_playwright']
    logger.info(f"Se pudo extraer contenido para {exito_total} de {estadisticas['total_articulos']} artículos ({exito_total/estadisticas['total_articulos']*100:.1f}%).")
    
    if estadisticas['articulos_sin_contenido'] > 0:
        logger.info(f"No se pudo extraer contenido para {estadisticas['articulos_sin_contenido']} artículos ({estadisticas['articulos_sin_contenido']/estadisticas['total_articulos']*100:.1f}%).")
        logger.info("Se recomienda revisar estos feeds para implementar métodos de extracción específicos.")
    else:
        logger.info("¡Excelente! Se pudo extraer contenido para todos los artículos probados.")

if __name__ == "__main__":
    probar_feeds_deshabilitados()
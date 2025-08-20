import requests
import logging
import time
import random
import asyncio
import os
import sys
from bs4 import BeautifulSoup

from app.config import config

logger = logging.getLogger(__name__)

# Variable para controlar si Playwright está disponible
playwright_available = False

# Intentar importar Playwright, pero no fallar si no está instalado
try:
    from playwright.async_api import async_playwright
    playwright_available = True
    logger.info("Playwright está disponible para extracción de contenido avanzada")
except ImportError:
    logger.warning("Playwright no está instalado. La extracción avanzada con navegador no estará disponible.")
    logger.warning("Para instalar: pip install playwright && playwright install chromium")

def extract_article_content_improved(url: str) -> str:
    """Versión mejorada de extracción de contenido con más selectores y manejo de errores."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=config["request_timeout_sec"])
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Eliminar elementos no deseados
        for element in soup.select('script, style, nav, header, footer, iframe, .ads, .banner, .comments, .social, .related, .sidebar'):
            element.decompose()
        
        # Lista ampliada de selectores para encontrar el contenido principal
        content_selectors = [
            'article', '.article-content', '.post-content', '.entry-content', 
            '.content', '#content', 'main', '.main-content', '.story-body',
            '.article-body', '.post-body', '.entry-body', '.news-content',
            '.article__content', '.post__content', '.news__content',
            '.article-text', '.post-text', '.news-text',
            '#article-content', '#post-content', '#news-content',
            '.nota', '.nota-contenido', '.nota-texto',
            '.articulo', '.articulo-contenido', '.articulo-texto',
            '.article', '.article-container', '.post', '.post-container'
        ]
        
        article_content = ""
        
        # Intentar con cada selector
        for selector in content_selectors:
            content = soup.select(selector)
            if content:
                article_content = ' '.join([elem.get_text(strip=True, separator=' ') for elem in content])
                if len(article_content) > 200:  # Si encontramos contenido sustancial
                    break
        
        # Si no se encontró contenido con los selectores, intentar con párrafos
        if not article_content or len(article_content) < 200:
            paragraphs = soup.find_all('p')
            if paragraphs:
                article_content = ' '.join([p.get_text(strip=True, separator=' ') for p in paragraphs])
        
        # Si aún no hay contenido, usar el body
        if not article_content or len(article_content) < 100:
            article_content = soup.body.get_text(strip=True, separator=' ')
        
        return article_content
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return ""

async def extract_with_playwright(url: str) -> str:
    """Extrae el contenido de un artículo usando Playwright (navegador headless)."""
    if not playwright_available:
        logger.warning("Playwright no está disponible para la extracción avanzada")
        return ""
    
    try:
        logger.info(f"Intentando extracción con Playwright para: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Configurar el user agent para simular un navegador normal
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
            # Navegar a la URL con timeout
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Esperar a que el contenido se cargue
            await page.wait_for_load_state("domcontentloaded")
            
            # Intentar extraer el contenido con los mismos selectores que usamos en BeautifulSoup
            content_selectors = [
                'article', '.article-content', '.post-content', '.entry-content', 
                '.content', '#content', 'main', '.main-content', '.story-body',
                '.article-body', '.post-body', '.entry-body', '.news-content',
                '.article__content', '.post__content', '.news__content',
                '.article-text', '.post-text', '.news-text',
                '#article-content', '#post-content', '#news-content',
                '.nota', '.nota-contenido', '.nota-texto',
                '.articulo', '.articulo-contenido', '.articulo-texto',
                '.article', '.article-container', '.post', '.post-container'
            ]
            
            article_content = ""
            
            # Intentar con cada selector
            for selector in content_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        texts = [await element.text_content() for element in elements]
                        article_content = ' '.join([text.strip() for text in texts if text.strip()])
                        if len(article_content) > 200:  # Si encontramos contenido sustancial
                            break
                except Exception as e:
                    logger.debug(f"Error al procesar selector {selector}: {e}")
            
            # Si no se encontró contenido con los selectores, intentar con párrafos
            if not article_content or len(article_content) < 200:
                try:
                    paragraphs = await page.query_selector_all('p')
                    if paragraphs:
                        texts = [await p.text_content() for p in paragraphs]
                        article_content = ' '.join([text.strip() for text in texts if text.strip()])
                except Exception as e:
                    logger.debug(f"Error al procesar párrafos: {e}")
            
            # Si aún no hay contenido, usar el body
            if not article_content or len(article_content) < 100:
                try:
                    body = await page.query_selector('body')
                    if body:
                        article_content = await body.text_content()
                except Exception as e:
                    logger.debug(f"Error al procesar body: {e}")
            
            await browser.close()
            
            return article_content.strip()
    except Exception as e:
        logger.error(f"Error al extraer contenido con Playwright de {url}: {e}")
        return ""

def extract_with_retry(url: str, max_retries: int = 3) -> str:
    """Extrae el contenido de un artículo con reintentos en caso de fallo.
    Si el método tradicional falla, intenta con Playwright como alternativa."""
    retry_delay = 2
    
    # Primer intento con el método tradicional
    for attempt in range(max_retries):
        try:
            content = extract_article_content_improved(url)
            if content and len(content) > 200:
                return content
            
            if attempt < max_retries - 1:
                # Añadir un retraso aleatorio antes de reintentar
                sleep_time = retry_delay * (1 + random.random())
                logger.warning(f"Contenido insuficiente, reintentando en {sleep_time:.2f} segundos... (intento {attempt+1}/{max_retries})")
                time.sleep(sleep_time)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            elif playwright_available:  # Si llegamos al último intento y Playwright está disponible
                logger.info(f"Método tradicional falló después de {max_retries} intentos. Probando con Playwright...")
                break
        except Exception as e:
            if attempt < max_retries - 1:
                sleep_time = retry_delay * (1 + random.random())
                logger.warning(f"Error en la extracción, reintentando en {sleep_time:.2f} segundos... (intento {attempt+1}/{max_retries}): {e}")
                time.sleep(sleep_time)
                retry_delay *= 1.5  # Incrementar el tiempo de espera exponencialmente
            elif playwright_available:  # Si llegamos al último intento y Playwright está disponible
                logger.info(f"Método tradicional falló con error después de {max_retries} intentos. Probando con Playwright...")
                break
            else:
                logger.error(f"Error final en la extracción después de {attempt+1} intentos: {e}")
    
    # Si el método tradicional falló y Playwright está disponible, intentar con Playwright
    if playwright_available:
        try:
            # Ejecutar la función asíncrona en un bucle de eventos
            content = asyncio.run(extract_with_playwright(url))
            if content and len(content) > 200:
                logger.info(f"Extracción exitosa con Playwright para: {url}")
                return content
            else:
                logger.warning(f"Extracción con Playwright no produjo contenido suficiente para: {url}")
        except Exception as e:
            logger.error(f"Error al ejecutar extracción con Playwright: {e}")
    
    return ""
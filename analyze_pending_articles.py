import sqlite3
import logging
import requests
import time
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Configurar el path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.storage import get_db_connection
from app.improved_extractor import extract_article_content_improved
from app.utils import get_utc_now, format_date

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_pending_articles():
    """Obtiene todos los artículos pendientes de procesamiento."""
    conn = None
    try:
        conn = get_db_connection()
        articles = []
        cursor = conn.execute(
            "SELECT id, link, title, site, published_utc FROM articles WHERE content_processed = 0"
        )
        for row in cursor:
            articles.append({
                "id": row["id"],
                "link": row["link"],
                "title": row["title"],
                "site": row["site"],
                "published_utc": row["published_utc"]
            })
        return articles
    except sqlite3.OperationalError as e:
        logger.error(f"Error accediendo a la base de datos: {e}")
        return []
    finally:
        if conn:
            conn.close()

def check_url_accessibility(url):
    """Verifica si una URL es accesible."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=config["request_timeout_sec"])
        return {
            "accessible": response.status_code == 200,
            "status_code": response.status_code,
            "content_length": len(response.content) if response.status_code == 200 else 0,
            "error": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "accessible": False,
            "status_code": None,
            "content_length": 0,
            "error": str(e)
        }

def analyze_article_content(url):
    """Analiza el contenido de un artículo para determinar posibles problemas."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=config["request_timeout_sec"])
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Verificar si hay contenido en los selectores principales
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
        
        selector_results = {}
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text = ' '.join([elem.get_text(strip=True, separator=' ') for elem in elements])
                selector_results[selector] = len(text)
        
        # Verificar párrafos
        paragraphs = soup.find_all('p')
        paragraph_count = len(paragraphs)
        paragraph_text_length = sum(len(p.get_text(strip=True)) for p in paragraphs)
        
        # Verificar si hay paywall o login
        paywall_indicators = [
            'paywall', 'subscribe', 'subscription', 'premium', 'member', 'membership',
            'login', 'sign in', 'signin', 'register', 'suscripción', 'suscribirse', 'premium',
            'iniciar sesión', 'ingresar', 'registrarse'
        ]
        
        paywall_detected = False
        for indicator in paywall_indicators:
            if indicator.lower() in response.text.lower():
                paywall_detected = True
                break
        
        # Verificar si hay JavaScript requerido
        js_required = 'noscript' in response.text.lower() or len(soup.find_all('noscript')) > 0
        
        return {
            "selector_results": selector_results,
            "paragraph_count": paragraph_count,
            "paragraph_text_length": paragraph_text_length,
            "paywall_detected": paywall_detected,
            "js_required": js_required,
            "content_extraction_result": extract_article_content_improved(url),
            "content_extraction_length": len(extract_article_content_improved(url))
        }
    except Exception as e:
        logger.error(f"Error analizando contenido: {e}")
        return {
            "error": str(e),
            "selector_results": {},
            "paragraph_count": 0,
            "paragraph_text_length": 0,
            "paywall_detected": False,
            "js_required": False,
            "content_extraction_result": "",
            "content_extraction_length": 0
        }

def analyze_pending_articles(sample_size=10):
    """Analiza una muestra de artículos pendientes para determinar por qué no se han procesado."""
    pending_articles = get_pending_articles()
    
    if not pending_articles:
        logger.info("No hay artículos pendientes para analizar.")
        return
    
    logger.info(f"Total de artículos pendientes: {len(pending_articles)}")
    
    # Agrupar artículos por sitio
    sites = {}
    for article in pending_articles:
        site = article['site']
        if site not in sites:
            sites[site] = []
        sites[site].append(article)
    
    # Mostrar distribución por sitio
    logger.info("\n===== DISTRIBUCIÓN DE ARTÍCULOS PENDIENTES POR SITIO =====\n")
    for site, articles in sorted(sites.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f"{site}: {len(articles)} artículos ({len(articles)/len(pending_articles)*100:.1f}%)")
    
    # Tomar una muestra aleatoria si hay más artículos que el tamaño de muestra
    import random
    if len(pending_articles) > sample_size:
        # Asegurar que la muestra incluya artículos de diferentes sitios
        sample = []
        sites_list = list(sites.keys())
        # Distribuir la muestra proporcionalmente entre los sitios
        for site in sites_list:
            site_count = len(sites[site])
            site_proportion = site_count / len(pending_articles)
            site_sample_size = max(1, int(sample_size * site_proportion))
            if site_sample_size > site_count:
                site_sample_size = site_count
            site_sample = random.sample(sites[site], site_sample_size)
            sample.extend(site_sample)
        # Si no llegamos al tamaño de muestra deseado, completar aleatoriamente
        if len(sample) < sample_size:
            remaining = [a for a in pending_articles if a not in sample]
            additional = random.sample(remaining, min(sample_size - len(sample), len(remaining)))
            sample.extend(additional)
    else:
        sample = pending_articles
    
    logger.info(f"\nAnalizando {len(sample)} artículos de {len(pending_articles)} pendientes...\n")
    
    results = []
    for i, article in enumerate(sample, 1):
        logger.info(f"Analizando artículo {i}/{len(sample)}: {article['id']} - {article['title']}")
        
        # Verificar accesibilidad de la URL
        accessibility = check_url_accessibility(article['link'])
        
        # Si la URL es accesible, analizar el contenido
        content_analysis = None
        if accessibility['accessible']:
            content_analysis = analyze_article_content(article['link'])
        
        results.append({
            "article": article,
            "accessibility": accessibility,
            "content_analysis": content_analysis
        })
        
        # Pausa para no sobrecargar los servidores
        time.sleep(2)
    
    # Analizar resultados
    inaccessible_count = sum(1 for r in results if not r['accessibility']['accessible'])
    paywall_count = sum(1 for r in results if r['content_analysis'] and r['content_analysis']['paywall_detected'])
    js_required_count = sum(1 for r in results if r['content_analysis'] and r['content_analysis']['js_required'])
    short_content_count = sum(1 for r in results if r['content_analysis'] and r['content_analysis']['content_extraction_length'] < 200)
    
    # Agrupar problemas por sitio
    site_issues = {}
    for result in results:
        site = result['article']['site']
        if site not in site_issues:
            site_issues[site] = {
                "total": 0,
                "inaccessible": 0,
                "paywall": 0,
                "js_required": 0,
                "short_content": 0
            }
        
        site_issues[site]["total"] += 1
        
        if not result['accessibility']['accessible']:
            site_issues[site]["inaccessible"] += 1
        
        if result['content_analysis']:
            if result['content_analysis']['paywall_detected']:
                site_issues[site]["paywall"] += 1
            
            if result['content_analysis']['js_required']:
                site_issues[site]["js_required"] += 1
            
            if result['content_analysis']['content_extraction_length'] < 200:
                site_issues[site]["short_content"] += 1
    
    # Mostrar resultados generales
    logger.info("\n===== ANÁLISIS DE ARTÍCULOS PENDIENTES =====\n")
    logger.info(f"Total de artículos analizados: {len(results)}")
    logger.info(f"URLs inaccesibles: {inaccessible_count} ({inaccessible_count/len(results)*100:.1f}%)")
    logger.info(f"Posible paywall detectado: {paywall_count} ({paywall_count/len(results)*100:.1f}%)")
    logger.info(f"JavaScript posiblemente requerido: {js_required_count} ({js_required_count/len(results)*100:.1f}%)")
    logger.info(f"Contenido extraído demasiado corto: {short_content_count} ({short_content_count/len(results)*100:.1f}%)")
    
    # Mostrar problemas por sitio
    logger.info("\n===== PROBLEMAS POR SITIO =====\n")
    logger.info("Sitio | Total | Inaccesibles | Paywall | JS Requerido | Contenido Corto")
    logger.info("-" * 80)
    
    for site, issues in sorted(site_issues.items(), key=lambda x: x[1]['total'], reverse=True):
        inaccesible_pct = issues['inaccessible']/issues['total']*100 if issues['total'] > 0 else 0
        paywall_pct = issues['paywall']/issues['total']*100 if issues['total'] > 0 else 0
        js_pct = issues['js_required']/issues['total']*100 if issues['total'] > 0 else 0
        short_pct = issues['short_content']/issues['total']*100 if issues['total'] > 0 else 0
        
        logger.info(f"{site:10} | {issues['total']:5} | {issues['inaccessible']:2} ({inaccesible_pct:4.1f}%) | {issues['paywall']:2} ({paywall_pct:4.1f}%) | {issues['js_required']:2} ({js_pct:4.1f}%) | {issues['short_content']:2} ({short_pct:4.1f}%)")
    
    # Análisis de problemas específicos por sitio
    logger.info("\n===== ANÁLISIS DE PROBLEMAS POR SITIO =====\n")
    
    for site, issues in sorted(site_issues.items(), key=lambda x: x[1]['total'], reverse=True):
        logger.info(f"Sitio: {site} (Total analizado: {issues['total']})")
        
        # Calcular el problema principal para este sitio
        problems = [
            ("URLs inaccesibles", issues['inaccessible']),
            ("Posible paywall", issues['paywall']),
            ("JavaScript requerido", issues['js_required']),
            ("Contenido corto", issues['short_content'])
        ]
        
        main_problems = sorted(problems, key=lambda x: x[1], reverse=True)
        
        if issues['total'] > 0:
            logger.info("  Problemas detectados:")
            for problem, count in main_problems:
                if count > 0:
                    logger.info(f"    - {problem}: {count} ({count/issues['total']*100:.1f}%)")
            
            # Recomendaciones específicas por sitio
            logger.info("  Recomendaciones:")
            
            if issues['inaccessible'] > 0 and issues['inaccessible']/issues['total'] > 0.5:
                logger.info("    - Verificar si el sitio tiene restricciones de acceso o limitaciones de tasa")
            
            if issues['paywall'] > 0 and issues['paywall']/issues['total'] > 0.5:
                logger.info("    - El sitio probablemente tiene un paywall que limita el acceso al contenido")
                logger.info("    - Considerar implementar técnicas específicas para este sitio o excluirlo")
            
            if issues['js_required'] > 0 and issues['js_required']/issues['total'] > 0.5:
                logger.info("    - El sitio probablemente requiere JavaScript para cargar el contenido")
                logger.info("    - Considerar usar un navegador headless como Selenium o Playwright")
            
            if issues['short_content'] > 0 and issues['short_content']/issues['total'] > 0.5:
                logger.info("    - Los selectores actuales no están extrayendo correctamente el contenido")
                logger.info("    - Implementar selectores específicos para este sitio")
        
        logger.info("")
    
    # Detalles de cada artículo
    logger.info("\n===== DETALLES DE ARTÍCULOS ANALIZADOS =====\n")
    for i, result in enumerate(results, 1):
        article = result['article']
        accessibility = result['accessibility']
        content_analysis = result['content_analysis']
        
        logger.info(f"Artículo {i}: {article['id']}")
        logger.info(f"Título: {article['title']}")
        logger.info(f"Sitio: {article['site']}")
        logger.info(f"URL: {article['link']}")
        logger.info(f"Fecha de publicación: {article['published_utc']}")
        
        if not accessibility['accessible']:
            logger.info(f"Estado: URL inaccesible (Error: {accessibility['error']})")
        elif content_analysis:
            logger.info(f"Estado: URL accesible (Código: {accessibility['status_code']})")
            logger.info(f"Longitud del contenido extraído: {content_analysis['content_extraction_length']} caracteres")
            
            if content_analysis['paywall_detected']:
                logger.info("Posible paywall detectado")
            
            if content_analysis['js_required']:
                logger.info("JavaScript posiblemente requerido")
            
            if content_analysis['content_extraction_length'] < 200:
                logger.info("Contenido extraído demasiado corto")
            
            # Mostrar los selectores que funcionaron mejor
            if content_analysis['selector_results']:
                best_selectors = sorted(content_analysis['selector_results'].items(), key=lambda x: x[1], reverse=True)[:3]
                logger.info(f"Mejores selectores: {best_selectors}")
            
            logger.info(f"Párrafos encontrados: {content_analysis['paragraph_count']} (longitud total: {content_analysis['paragraph_text_length']})")
        
        logger.info("---")

if __name__ == "__main__":
    # Analizar una muestra de artículos pendientes
    sample_size = 10
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        sample_size = int(sys.argv[1])
    
    analyze_pending_articles(sample_size)
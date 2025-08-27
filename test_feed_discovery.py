#!/usr/bin/env python3
"""
Script para probar y mejorar el autodescubrimiento de feeds RSS
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

def discover_feeds_enhanced(url):
    """Versión mejorada del autodescubrimiento de feeds"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    feeds = []
    
    try:
        # Headers más realistas para evitar bloqueos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print(f"🔍 Analizando: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Buscar enlaces RSS/Atom en el HTML
        rss_links = soup.find_all('link', {'type': re.compile(r'application/(rss|atom)\+xml', re.I)})
        for link in rss_links:
            href = link.get('href')
            if href:
                feed_url = urljoin(url, href)
                title = link.get('title', 'RSS Feed')
                feeds.append({'url': feed_url, 'title': title, 'type': 'link_tag'})
                print(f"  📡 Encontrado en <link>: {title} - {feed_url}")
        
        # 2. Buscar enlaces RSS en el contenido
        rss_anchors = soup.find_all('a', href=re.compile(r'(rss|feed|atom)', re.I))
        for anchor in rss_anchors:
            href = anchor.get('href')
            if href:
                feed_url = urljoin(url, href)
                title = anchor.get_text(strip=True) or 'RSS Feed'
                feeds.append({'url': feed_url, 'title': title, 'type': 'anchor_tag'})
                print(f"  📡 Encontrado en <a>: {title} - {feed_url}")
        
        # 3. Probar URLs comunes de RSS
        common_paths = [
            '/rss',
            '/rss.xml',
            '/feed',
            '/feed.xml',
            '/feeds',
            '/feeds.xml',
            '/atom.xml',
            '/index.xml',
            '/rss/index.xml',
            '/feed/index.xml',
            '/blog/rss',
            '/blog/feed',
            '/news/rss',
            '/news/feed',
            '/noticias/rss',
            '/noticias/feed'
        ]
        
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        for path in common_paths:
            test_url = base_url + path
            try:
                print(f"  🔍 Probando: {test_url}")
                test_response = requests.head(test_url, headers=headers, timeout=5)
                if test_response.status_code == 200:
                    content_type = test_response.headers.get('content-type', '').lower()
                    if any(ct in content_type for ct in ['xml', 'rss', 'atom']):
                        feeds.append({'url': test_url, 'title': f'RSS Feed ({path})', 'type': 'common_path'})
                        print(f"  ✅ Feed válido encontrado: {test_url}")
                    else:
                        # Verificar contenido si el content-type no es claro
                        test_get = requests.get(test_url, headers=headers, timeout=5)
                        if any(tag in test_get.text[:500].lower() for tag in ['<rss', '<feed', '<atom']):
                            feeds.append({'url': test_url, 'title': f'RSS Feed ({path})', 'type': 'common_path'})
                            print(f"  ✅ Feed válido encontrado: {test_url}")
            except requests.RequestException:
                continue
            
            time.sleep(0.1)  # Pequeña pausa para no sobrecargar
        
        # 4. Buscar en robots.txt
        try:
            robots_url = base_url + '/robots.txt'
            robots_response = requests.get(robots_url, headers=headers, timeout=5)
            if robots_response.status_code == 200:
                for line in robots_response.text.split('\n'):
                    if 'rss' in line.lower() or 'feed' in line.lower():
                        # Extraer URL del robots.txt
                        match = re.search(r'(https?://[^\s]+|/[^\s]+)', line)
                        if match:
                            potential_feed = match.group(1)
                            if not potential_feed.startswith('http'):
                                potential_feed = base_url + potential_feed
                            feeds.append({'url': potential_feed, 'title': 'RSS Feed (robots.txt)', 'type': 'robots_txt'})
                            print(f"  📡 Encontrado en robots.txt: {potential_feed}")
        except requests.RequestException:
            pass
        
        # 5. Buscar en sitemap.xml
        try:
            sitemap_url = base_url + '/sitemap.xml'
            sitemap_response = requests.get(sitemap_url, headers=headers, timeout=5)
            if sitemap_response.status_code == 200:
                sitemap_soup = BeautifulSoup(sitemap_response.content, 'xml')
                for loc in sitemap_soup.find_all('loc'):
                    url_text = loc.get_text()
                    if any(keyword in url_text.lower() for keyword in ['rss', 'feed', 'atom']):
                        feeds.append({'url': url_text, 'title': 'RSS Feed (sitemap)', 'type': 'sitemap'})
                        print(f"  📡 Encontrado en sitemap: {url_text}")
        except requests.RequestException:
            pass
        
    except requests.RequestException as e:
        print(f"❌ Error al acceder a {url}: {e}")
        return []
    
    # Eliminar duplicados
    unique_feeds = []
    seen_urls = set()
    for feed in feeds:
        if feed['url'] not in seen_urls:
            unique_feeds.append(feed)
            seen_urls.add(feed['url'])
    
    return unique_feeds

def validate_feed(feed_url):
    """Validar que un feed RSS es válido"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Verificar que contiene elementos RSS/Atom
        content = response.text.lower()
        if any(tag in content for tag in ['<rss', '<feed', '<atom', '<channel>', '<item>', '<entry>']):
            # Contar items aproximadamente
            item_count = content.count('<item>') + content.count('<entry>')
            return True, item_count
        else:
            return False, 0
            
    except Exception as e:
        return False, 0

def test_infobae():
    """Probar específicamente con Infobae"""
    print("\n" + "="*60)
    print("🧪 PRUEBA ESPECÍFICA: www.infobae.com")
    print("="*60)
    
    feeds = discover_feeds_enhanced('www.infobae.com')
    
    print(f"\n📊 RESULTADOS: {len(feeds)} feeds encontrados")
    print("-" * 40)
    
    valid_feeds = []
    for i, feed in enumerate(feeds, 1):
        print(f"\n{i}. {feed['title']}")
        print(f"   URL: {feed['url']}")
        print(f"   Método: {feed['type']}")
        
        # Validar el feed
        is_valid, item_count = validate_feed(feed['url'])
        if is_valid:
            print(f"   ✅ VÁLIDO - {item_count} artículos")
            valid_feeds.append(feed)
        else:
            print(f"   ❌ INVÁLIDO")
    
    print(f"\n🎯 RESUMEN: {len(valid_feeds)} de {len(feeds)} feeds son válidos")
    
    if valid_feeds:
        print("\n✅ FEEDS RECOMENDADOS PARA INFOBAE:")
        for feed in valid_feeds:
            print(f"   • {feed['url']} ({feed['title']})")
    else:
        print("\n❌ No se encontraron feeds válidos para Infobae")
    
    return valid_feeds

def test_other_sites():
    """Probar con otros sitios conocidos"""
    test_sites = [
        'clarin.com',
        'lanacion.com.ar',
        'pagina12.com.ar',
        'ambito.com'
    ]
    
    print("\n" + "="*60)
    print("🧪 PRUEBAS ADICIONALES")
    print("="*60)
    
    for site in test_sites:
        print(f"\n🔍 Probando: {site}")
        feeds = discover_feeds_enhanced(site)
        valid_count = 0
        
        for feed in feeds:
            is_valid, _ = validate_feed(feed['url'])
            if is_valid:
                valid_count += 1
        
        print(f"   📊 {len(feeds)} feeds encontrados, {valid_count} válidos")

def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBAS DE AUTODESCUBRIMIENTO DE FEEDS")
    print("=" * 60)
    
    # Probar Infobae específicamente
    infobae_feeds = test_infobae()
    
    # Probar otros sitios
    test_other_sites()
    
    print("\n" + "="*60)
    print("🏁 PRUEBAS COMPLETADAS")
    print("="*60)
    
    if infobae_feeds:
        print(f"\n✅ Infobae: {len(infobae_feeds)} feeds válidos encontrados")
        print("\n💡 RECOMENDACIÓN: Actualizar la función de autodescubrimiento")
        print("   en web_app.py con las mejoras implementadas en este script.")
    else:
        print("\n❌ Infobae: No se encontraron feeds válidos")
        print("\n💡 POSIBLES CAUSAS:")
        print("   • El sitio bloquea bots/scrapers")
        print("   • Los feeds están en subdominios o rutas no estándar")
        print("   • Requiere autenticación o cookies")
        print("   • Usa JavaScript para cargar el contenido")

if __name__ == "__main__":
    main()
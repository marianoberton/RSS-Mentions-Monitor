from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import yaml
import os
from datetime import datetime, timedelta
from app.storage import get_db_connection, get_hourly_stats, get_global_stats, remove_duplicate_hits, get_detailed_stats, get_feed_health_stats
from app.tasks import main_task, process_feed
from app.feeds import get_enabled_feeds
from app.config import config
# Removed person_profiles import as it's no longer used
import threading
import logging
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ejecutar migraciones automáticamente al iniciar la aplicación web
try:
    from migrate_db import main as run_migrations
    logger.info("Ejecutando migraciones de base de datos...")
    if run_migrations():
        logger.info("Migraciones completadas exitosamente")
    else:
        logger.error("Error en migraciones")
except Exception as e:
    logger.error(f"Error ejecutando migraciones: {e}")

@app.route('/')
def dashboard():
    """Dashboard principal con estadísticas."""
    try:
        # Obtener estadísticas globales y de la última hora
        stats = get_global_stats()
        hourly_stats = get_hourly_stats()
        
        # Combinar estadísticas para el dashboard
        stats['hourly_hits'] = hourly_stats['total_hits']
        stats['hourly_articles'] = hourly_stats['total_articles']
        
        # Obtener feeds habilitados
        enabled_feeds = get_enabled_feeds()
        
        # Obtener estadísticas de salud de feeds
        feed_health = get_feed_health_stats()
        
        # Obtener últimas menciones y keywords activas
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("""
                SELECT h.keyword, h.where_found, h.detected_utc, 
                       a.title, a.site, a.link, a.published_utc
                FROM hits h
                JOIN articles a ON h.article_id = a.id
                ORDER BY h.detected_utc DESC
                LIMIT 20
            """)
            recent_hits = [dict(row) for row in cursor.fetchall()]
            
            # Obtener keywords activas de candidatos
            cursor = conn.execute("""
                SELECT DISTINCT ck.keyword
                FROM candidate_keywords ck
                JOIN candidates c ON ck.candidate_id = c.id
                WHERE ck.is_active = 1 AND c.is_active = 1
                ORDER BY ck.keyword
            """)
            active_keywords = [row[0] for row in cursor.fetchall()]
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             enabled_feeds=enabled_feeds,
                             feed_health=feed_health,
                             recent_hits=recent_hits,
                             keywords=active_keywords,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        flash(f"Error al cargar dashboard: {e}", 'error')
        return render_template('dashboard.html', 
                             stats={}, 
                             enabled_feeds=[],
                             feed_health={'total_feeds': 0, 'healthy_feeds': 0, 'error_feeds': 0, 'feeds': []},
                             recent_hits=[],
                             keywords=[],
                             current_time=datetime.now())

@app.route('/feeds')
def feeds_management():
    """Gestión de feeds RSS."""
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return render_template('feeds.html', feeds=config_data['feeds'], current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar feeds: {e}")
        flash(f"Error al cargar feeds: {e}", 'error')
        return render_template('feeds.html', feeds=[], current_time=datetime.now())

@app.route('/feeds/toggle/<feed_name>', methods=['POST'])
def toggle_feed(feed_name):
    """Habilitar/deshabilitar un feed."""
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Buscar y cambiar el estado del feed
        for feed in config_data['feeds']:
            if feed['name'] == feed_name:
                feed['enabled'] = not feed.get('enabled', True)
                break
        
        # Guardar cambios
        with open('config.yml', 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        
        flash(f"Feed {feed_name} {'habilitado' if feed['enabled'] else 'deshabilitado'} exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al cambiar estado del feed: {e}")
        flash(f"Error al cambiar estado del feed: {e}", 'error')
    
    return redirect(url_for('feeds_management'))

@app.route('/feeds/add', methods=['POST'])
def add_feed():
    """Agregar nuevo feed RSS."""
    try:
        name = request.form.get('name')
        url = request.form.get('url')
        enabled = request.form.get('enabled') == 'on'
        
        if not name or not url:
            flash('Nombre y URL son requeridos', 'error')
            return redirect(url_for('feeds_management'))
        
        with open('config.yml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Verificar si el feed ya existe
        for feed in config_data['feeds']:
            if feed['name'] == name:
                flash('Ya existe un feed con ese nombre', 'error')
                return redirect(url_for('feeds_management'))
        
        # Agregar nuevo feed
        new_feed = {
            'name': name,
            'url': url,
            'enabled': enabled
        }
        config_data['feeds'].append(new_feed)
        
        # Guardar cambios
        with open('config.yml', 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        
        flash(f"Feed {name} agregado exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al agregar feed: {e}")
        flash(f"Error al agregar feed: {e}", 'error')
    
    return redirect(url_for('feeds_management'))

@app.route('/feeds/remove/<feed_name>', methods=['POST'])
def remove_feed(feed_name):
    """Eliminar feed RSS."""
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Buscar y eliminar el feed
        original_count = len(config_data['feeds'])
        config_data['feeds'] = [feed for feed in config_data['feeds'] if feed['name'] != feed_name]
        
        if len(config_data['feeds']) == original_count:
            flash(f'Feed {feed_name} no encontrado', 'error')
            return redirect(url_for('feeds_management'))
        
        # Guardar cambios
        with open('config.yml', 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        
        flash(f"Feed {feed_name} eliminado exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al eliminar feed: {e}")
        flash(f"Error al eliminar feed: {e}", 'error')
    
    return redirect(url_for('feeds_management'))

@app.route('/feeds/validate', methods=['POST'])
def validate_feed():
    """Validar feed RSS antes de agregarlo."""
    try:
        import feedparser
        import requests
        from urllib.parse import urljoin, urlparse
        
        url = request.form.get('url')
        if not url:
            return jsonify({'valid': False, 'error': 'URL requerida'})
        
        # Validar formato de URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return jsonify({'valid': False, 'error': 'URL inválida'})
        except Exception:
            return jsonify({'valid': False, 'error': 'Formato de URL inválido'})
        
        # Intentar acceder al feed
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'RSS Mentions Monitor/1.0'
            })
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return jsonify({'valid': False, 'error': f'Error al acceder al feed: {str(e)}'})
        
        # Parsear el feed
        try:
            feed = feedparser.parse(response.content)
            
            if feed.bozo and feed.bozo_exception:
                return jsonify({
                    'valid': False, 
                    'error': f'Feed RSS inválido: {str(feed.bozo_exception)}'
                })
            
            if not feed.entries:
                return jsonify({
                    'valid': False, 
                    'error': 'El feed no contiene artículos'
                })
            
            # Extraer información del feed
            feed_info = {
                'title': getattr(feed.feed, 'title', 'Sin título'),
                'description': getattr(feed.feed, 'description', 'Sin descripción'),
                'entries_count': len(feed.entries),
                'last_updated': getattr(feed.feed, 'updated', 'Desconocido')
            }
            
            return jsonify({
                'valid': True, 
                'feed_info': feed_info
            })
            
        except Exception as e:
            return jsonify({'valid': False, 'error': f'Error al parsear el feed: {str(e)}'})
            
    except Exception as e:
        logger.error(f"Error en validación de feed: {e}")
        return jsonify({'valid': False, 'error': 'Error interno del servidor'})

@app.route('/feeds/autodiscover', methods=['POST'])
def autodiscover_feeds():
    """Autodescubrir feeds RSS desde una URL de sitio web (versión mejorada)."""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        from urllib.parse import urljoin, urlparse
        import time
        
        # Obtener URL del request JSON o form
        if request.is_json:
            site_url = request.json.get('url')
        else:
            site_url = request.form.get('site_url')
            
        if not site_url:
            return jsonify({'success': False, 'error': 'URL del sitio requerida'})
        
        # Validar y normalizar URL
        if not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
            
        try:
            parsed = urlparse(site_url)
            if not parsed.netloc:
                return jsonify({'success': False, 'error': 'URL inválida'})
        except Exception:
            return jsonify({'success': False, 'error': 'Formato de URL inválido'})
        
        discovered_feeds = []
        
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
            
            # Obtener la página principal
            response = requests.get(site_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. Buscar enlaces RSS/Atom en el HTML usando regex más flexible
            rss_links = soup.find_all('link', {'type': re.compile(r'application/(rss|atom)\+xml', re.I)})
            for link in rss_links:
                href = link.get('href')
                if href:
                    feed_url = urljoin(site_url, href)
                    title = link.get('title', 'RSS Feed')
                    discovered_feeds.append({
                        'url': feed_url,
                        'title': title,
                        'type': link.get('type', 'application/rss+xml')
                    })
            
            # 2. Buscar enlaces RSS en el contenido (anchors)
            rss_anchors = soup.find_all('a', href=re.compile(r'(rss|feed|atom)', re.I))
            for anchor in rss_anchors:
                href = anchor.get('href')
                if href:
                    feed_url = urljoin(site_url, href)
                    title = anchor.get_text(strip=True) or 'RSS Feed'
                    # Verificar si ya está en la lista
                    if not any(f['url'] == feed_url for f in discovered_feeds):
                        discovered_feeds.append({
                            'url': feed_url,
                            'title': title,
                            'type': 'application/rss+xml'
                        })
            
            # 3. Probar URLs comunes de RSS (expandida)
            common_feed_paths = [
                '/rss', '/rss.xml', '/feed', '/feed.xml', '/feeds', '/feeds.xml',
                '/atom.xml', '/index.xml', '/rss/index.xml', '/feed/index.xml',
                '/blog/rss', '/blog/feed', '/news/rss', '/news/feed',
                '/noticias/rss', '/noticias/feed', '/feeds/all.atom.xml'
            ]
            
            base_url = f"{urlparse(site_url).scheme}://{urlparse(site_url).netloc}"
            
            for path in common_feed_paths:
                test_url = base_url + path
                try:
                    test_response = requests.head(test_url, headers=headers, timeout=5)
                    if test_response.status_code == 200:
                        content_type = test_response.headers.get('content-type', '').lower()
                        if any(ct in content_type for ct in ['xml', 'rss', 'atom']):
                            # Verificar si ya está en la lista
                            if not any(f['url'] == test_url for f in discovered_feeds):
                                discovered_feeds.append({
                                    'url': test_url,
                                    'title': f'RSS Feed ({path})',
                                    'type': 'application/rss+xml'
                                })
                        else:
                            # Verificar contenido si el content-type no es claro
                            try:
                                test_get = requests.get(test_url, headers=headers, timeout=5)
                                if any(tag in test_get.text[:500].lower() for tag in ['<rss', '<feed', '<atom']):
                                    if not any(f['url'] == test_url for f in discovered_feeds):
                                        discovered_feeds.append({
                                            'url': test_url,
                                            'title': f'RSS Feed ({path})',
                                            'type': 'application/rss+xml'
                                        })
                            except:
                                pass
                except requests.RequestException:
                    continue
                
                time.sleep(0.05)  # Pequeña pausa para no sobrecargar
            
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
                                # Verificar si ya está en la lista
                                if not any(f['url'] == potential_feed for f in discovered_feeds):
                                    discovered_feeds.append({
                                        'url': potential_feed,
                                        'title': 'RSS Feed (robots.txt)',
                                        'type': 'application/rss+xml'
                                    })
            except requests.RequestException:
                pass
            
            # Validar feeds encontrados
            valid_feeds = []
            for feed in discovered_feeds:
                try:
                    # Validación rápida del feed
                    feed_response = requests.get(feed['url'], headers=headers, timeout=8)
                    if feed_response.status_code == 200:
                        content = feed_response.text.lower()
                        if any(tag in content for tag in ['<rss', '<feed', '<atom', '<channel>', '<item>', '<entry>']):
                            valid_feeds.append(feed)
                except:
                    continue
            
            return jsonify({
                'success': True, 
                'feeds': valid_feeds,
                'count': len(valid_feeds)
            })
            
        except requests.exceptions.RequestException as e:
            return jsonify({'success': False, 'error': f'Error al acceder al sitio: {str(e)}'})
            
    except Exception as e:
        logger.error(f"Error en autodiscovery: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'})

@app.route('/keywords')
def keywords_management():
    """Gestión de palabras clave de candidatos."""
    try:
        conn = get_db_connection()
        with conn:
            # Obtener todas las keywords de candidatos con información del candidato
            cursor = conn.execute("""
                SELECT ck.keyword, c.name, c.full_name, c.political_party, 
                       c.importance_level, ck.is_primary, ck.created_utc,
                       COUNT(h.id) as hits_count
                FROM candidate_keywords ck
                JOIN candidates c ON ck.candidate_id = c.id
                LEFT JOIN hits h ON ck.keyword = h.keyword
                WHERE ck.is_active = 1 AND c.is_active = 1
                GROUP BY ck.keyword, c.id
                ORDER BY c.importance_level DESC, ck.is_primary DESC, ck.keyword
            """)
            
            keywords_data = []
            importance_map = {1: 'low', 2: 'medium', 3: 'high'}
            
            for row in cursor.fetchall():
                keywords_data.append({
                    'keyword': row[0],
                    'candidate_name': row[1],
                    'candidate_full_name': row[2],
                    'political_party': row[3],
                    'importance_level': importance_map.get(row[4], 'low'),
                    'is_primary': bool(row[5]),
                    'created_utc': row[6],
                    'hits_count': row[7] or 0
                })
        
        return render_template('keywords.html', keywords=keywords_data, current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar palabras clave de candidatos: {e}")
        flash(f"Error al cargar palabras clave de candidatos: {e}", 'error')
        return render_template('keywords.html', keywords=[], current_time=datetime.now())

@app.route('/keywords/add', methods=['POST'])
def add_keyword():
    """Agregar nueva palabra clave."""
    try:
        keyword = request.form.get('keyword')
        
        if not keyword:
            flash('La palabra clave es requerida', 'error')
            return redirect(url_for('keywords_management'))
        
        with open('config.yml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Verificar si la palabra clave ya existe
        if keyword in config_data['keywords']:
            flash('La palabra clave ya existe', 'error')
            return redirect(url_for('keywords_management'))
        
        # Agregar nueva palabra clave
        config_data['keywords'].append(keyword)
        
        # Guardar cambios
        with open('config.yml', 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        
        flash(f"Palabra clave '{keyword}' agregada exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al agregar palabra clave: {e}")
        flash(f"Error al agregar palabra clave: {e}", 'error')
    
    return redirect(url_for('keywords_management'))

@app.route('/keywords/remove/<keyword>', methods=['POST'])
def remove_keyword(keyword):
    """Eliminar palabra clave."""
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Eliminar palabra clave
        if keyword in config_data['keywords']:
            config_data['keywords'].remove(keyword)
            
            # Guardar cambios
            with open('config.yml', 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            flash(f"Palabra clave '{keyword}' eliminada exitosamente", 'success')
        else:
            flash('Palabra clave no encontrada', 'error')
    except Exception as e:
        logger.error(f"Error al eliminar palabra clave: {e}")
        flash(f"Error al eliminar palabra clave: {e}", 'error')
    
    return redirect(url_for('keywords_management'))

@app.route('/candidates')
def candidates_dashboard():
    """Dashboard de candidatos políticos."""
    try:
        # Obtener resumen de todos los candidatos
        from app.storage import get_all_candidates, get_all_electoral_alliances
        candidates_summary = get_all_candidates()
        alliances = get_all_electoral_alliances()
        
        return render_template('candidates.html', 
                             candidates=candidates_summary,
                             alliances=alliances,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar dashboard de candidatos: {e}")
        flash(f"Error al cargar dashboard de candidatos: {e}", 'error')
        return render_template('candidates.html', 
                             candidates=[],
                             alliances=[],
                             current_time=datetime.now())

@app.route('/candidates/<int:candidate_id>')
def candidate_profile(candidate_id):
    """Perfil detallado de un candidato."""
    try:
        # Obtener datos del candidato
        from app.storage import get_candidate_stats
        candidate_stats = get_candidate_stats(candidate_id)
        
        return render_template('candidate_detail.html',
                             candidate=candidate_stats,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar perfil de candidato {candidate_id}: {e}")
        flash(f"Error al cargar perfil de candidato: {e}", 'error')
        return redirect(url_for('candidates_dashboard'))

@app.route('/candidates/<int:candidate_id>/mentions')
def candidate_mentions(candidate_id):
    """Página para ver todas las menciones de un candidato específico."""
    page = request.args.get('page', 1, type=int)
    feed_filter = request.args.get('feed', '')
    per_page = 20  # Menciones por página
    
    conn = get_db_connection()
    
    try:
        # Obtener información básica del candidato
        cursor = conn.execute("""
            SELECT name, full_name, political_party, electoral_section
            FROM candidates 
            WHERE id = ?
        """, (candidate_id,))
        
        candidate_row = cursor.fetchone()
        if not candidate_row:
            flash('Candidato no encontrado', 'error')
            return redirect(url_for('candidates_dashboard'))
        
        candidate_info = {
            'id': candidate_id,
            'name': candidate_row[0],
            'full_name': candidate_row[1],
            'political_party': candidate_row[2],
            'electoral_section': candidate_row[3]
        }
        
        # Obtener lista de feeds disponibles para este candidato
        cursor = conn.execute("""
            SELECT DISTINCT a.site 
            FROM articles a
            JOIN hits h ON a.id = h.article_id
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
            ORDER BY a.site
        """, (candidate_id,))
        available_feeds = [row[0] for row in cursor.fetchall()]
        
        # Construir consulta con filtros opcionales
        where_conditions = ["ck.candidate_id = ?", "ck.is_active = 1"]
        params = [candidate_id]
        
        if feed_filter:
            where_conditions.append("a.site = ?")
            params.append(feed_filter)
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Contar total de menciones (con filtros si aplican)
        count_query = f"""
            SELECT COUNT(*) 
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            {where_clause}
        """
        cursor = conn.execute(count_query, params)
        total_mentions = cursor.fetchone()[0]
        
        # Calcular offset
        offset = (page - 1) * per_page
        
        # Obtener menciones con paginación y filtros
        mentions_query = f"""
            SELECT h.keyword, h.where_found, h.detected_utc,
                   a.title, a.site, a.link, a.published_utc
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            {where_clause}
            ORDER BY h.detected_utc DESC 
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        cursor = conn.execute(mentions_query, params)
        
        mentions = [{
            'keyword': row[0],
            'where_found': row[1],
            'detected_utc': row[2],
            'article_title': row[3],
            'site': row[4],
            'article_link': row[5],
            'published_utc': row[6]
        } for row in cursor.fetchall()]
        
        # Calcular información de paginación
        total_pages = (total_mentions + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('candidate_mentions.html', 
                             candidate=candidate_info,
                             mentions=mentions,
                             page=page,
                             total_pages=total_pages,
                             total_mentions=total_mentions,
                             has_prev=has_prev,
                             has_next=has_next,
                             available_feeds=available_feeds,
                             current_feed=feed_filter,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar menciones de candidato {candidate_id}: {e}")
        flash(f"Error al cargar menciones de candidato: {e}", 'error')
        return redirect(url_for('candidate_profile', candidate_id=candidate_id))
    finally:
        conn.close()

@app.route('/api/candidates')
def api_candidates():
    """API endpoint para obtener datos de candidatos en formato JSON."""
    try:
        from app.storage import get_all_candidates
        candidates_summary = get_all_candidates()
        return jsonify({
            'success': True,
            'data': candidates_summary,
            'total': len(candidates_summary)
        })
    except Exception as e:
        logger.error(f"Error en API de candidatos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/candidates/<int:candidate_id>')
def api_candidate_profile(candidate_id):
    """API endpoint para obtener perfil de candidato específico."""
    try:
        from app.storage import get_candidate_stats
        candidate_data = get_candidate_stats(candidate_id)
        
        return jsonify({
            'success': True,
            'data': candidate_data
        })
    except Exception as e:
        logger.error(f"Error en API de perfil de candidato {candidate_id}: {e}")
        return jsonify({
             'success': False,
             'error': str(e)
         }), 500

@app.route('/candidates/manage')
def manage_candidates():
    """Página de gestión de candidatos."""
    try:
        # Obtener todos los candidatos para gestión
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("""
                SELECT c.id, c.name, c.full_name, c.description, c.political_party, 
                       c.electoral_section, c.legislative_position, c.district,
                       c.list_number, c.list_position, c.importance_level, c.is_active,
                       c.alliance_id, ea.display_name as alliance_name, ea.primary_color as alliance_color,
                       ea.logo_url as alliance_logo_url
                FROM candidates c
                LEFT JOIN electoral_alliances ea ON c.alliance_id = ea.id
                ORDER BY c.name
            """)
            candidates = [dict(row) for row in cursor.fetchall()]
            
            # Obtener keywords para cada candidato y convertir importance_level
            importance_map = {1: 'low', 2: 'medium', 3: 'high'}
            for candidate in candidates:
                # Convertir importance_level a string
                candidate['importance_level'] = importance_map.get(candidate['importance_level'], 'low')
                
                # Obtener keywords
                cursor = conn.execute("""
                    SELECT keyword 
                    FROM candidate_keywords 
                    WHERE candidate_id = ? AND is_active = 1
                """, (candidate['id'],))
                candidate['keywords'] = [row[0] for row in cursor.fetchall()]
        
        # Obtener alianzas para el formulario
        from app.storage import get_all_electoral_alliances
        alliances = get_all_electoral_alliances()
        
        return render_template('manage_candidates.html', 
                             candidates=candidates,
                             alliances=alliances,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar gestión de candidatos: {e}")
        flash(f"Error al cargar gestión de candidatos: {e}", 'error')
        
        # Obtener alianzas para el formulario incluso en caso de error
        try:
            from app.storage import get_all_electoral_alliances
            alliances = get_all_electoral_alliances()
        except:
            alliances = []
        
        return render_template('manage_candidates.html', 
                             candidates=[],
                             alliances=alliances,
                             current_time=datetime.now())

@app.route('/candidates/add', methods=['POST'])
def add_candidate():
    """Agregar nuevo candidato."""
    try:
        name = request.form.get('name')
        full_name = request.form.get('full_name')
        description = request.form.get('description')
        political_party = request.form.get('political_party')
        electoral_section = int(request.form.get('electoral_section', 1))
        legislative_position = request.form.get('legislative_position')
        district = request.form.get('district', 'Buenos Aires')
        list_number = request.form.get('list_number')
        list_position = request.form.get('list_position')
        importance_level = request.form.get('importance_level', 'medium')
        alliance_id = request.form.get('alliance_id')
        keywords = request.form.get('keywords', '').split(',')
        
        if not name or not political_party or not legislative_position:
            flash('El nombre, partido político y cargo legislativo son requeridos', 'error')
            return redirect(url_for('manage_candidates'))
        
        # Convertir importance_level de string a int
        importance_map = {'low': 1, 'medium': 2, 'high': 3}
        importance_int = importance_map.get(importance_level, 2)
        
        from app.storage import create_candidate, add_candidate_keyword
        
        # Crear candidato usando la función de storage
        candidate_id = create_candidate(
            name=name,
            political_party=political_party,
            electoral_section=electoral_section,
            legislative_position=legislative_position,
            full_name=full_name,
            description=description,
            district=district,
            list_number=int(list_number) if list_number else None,
            list_position=int(list_position) if list_position else None,
            importance_level=importance_int,
            alliance_id=int(alliance_id) if alliance_id else None
        )
        
        # Generar keywords automáticas basadas en el nombre
        auto_keywords = set()
        
        # Agregar el nombre completo como keyword principal
        if name:
            auto_keywords.add(name.strip())
        
        # Agregar el nombre completo si es diferente al nombre
        if full_name and full_name.strip() != name.strip():
            auto_keywords.add(full_name.strip())
        
        # NO agregar partes individuales del nombre para evitar keywords separadas
        # Solo usar el nombre completo como keyword
        
        # Combinar keywords automáticas con las manuales
        manual_keywords = [kw.strip() for kw in keywords if kw.strip()]
        all_keywords = list(auto_keywords) + manual_keywords
        
        # Eliminar duplicados manteniendo el orden
        unique_keywords = []
        seen = set()
        for keyword in all_keywords:
            if keyword and keyword.lower() not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword.lower())
        
        # Agregar todas las keywords
        for keyword in unique_keywords:
            add_candidate_keyword(candidate_id, keyword)
        
        # Informar al usuario sobre las keywords generadas y próxima búsqueda
        auto_count = len(auto_keywords)
        manual_count = len(manual_keywords)
        total_keywords = len(unique_keywords)
        
        flash(f"✅ Candidato '{name}' agregado exitosamente con {total_keywords} keywords ({auto_count} automáticas, {manual_count} manuales)", 'success')
        flash(f"🔍 Las menciones de este candidato se buscarán automáticamente en el próximo procesamiento de feeds. Usa 'Ejecutar Todo' en Herramientas para buscar inmediatamente.", 'info')
    except Exception as e:
        logger.error(f"Error al agregar candidato: {e}")
        flash(f"Error al agregar candidato: {e}", 'error')
    
    return redirect(url_for('manage_candidates'))

@app.route('/candidates/<int:candidate_id>/edit', methods=['POST'])
def edit_candidate(candidate_id):
    """Editar candidato existente."""
    try:
        name = request.form.get('name')
        full_name = request.form.get('full_name')
        description = request.form.get('description')
        political_party = request.form.get('political_party')
        electoral_section = int(request.form.get('electoral_section', 1))
        legislative_position = request.form.get('legislative_position')
        district = request.form.get('district', 'Buenos Aires')
        list_number = request.form.get('list_number')
        list_position = request.form.get('list_position')
        importance_level = request.form.get('importance_level', 'medium')
        alliance_id = request.form.get('alliance_id')
        is_active = request.form.get('is_active') == 'on'
        keywords = request.form.get('keywords', '').split(',')
        
        if not name or not political_party or not legislative_position:
            flash('El nombre, partido político y cargo legislativo son requeridos', 'error')
            return redirect(url_for('manage_candidates'))
        
        # Convertir importance_level de string a int
        importance_map = {'low': 1, 'medium': 2, 'high': 3}
        importance_int = importance_map.get(importance_level, 2)
        
        from app.storage import update_candidate
        
        # Actualizar candidato
        update_candidate(candidate_id,
            name=name,
            full_name=full_name,
            description=description,
            political_party=political_party,
            electoral_section=electoral_section,
            legislative_position=legislative_position,
            district=district,
            list_number=int(list_number) if list_number else None,
            list_position=int(list_position) if list_position else None,
            importance_level=importance_int,
            alliance_id=int(alliance_id) if alliance_id else None,
            is_active=is_active
        )
        
        # Actualizar keywords
        conn = get_db_connection()
        with conn:
            # Desactivar keywords existentes
            conn.execute("""
                UPDATE candidate_keywords 
                SET is_active = 0 
                WHERE candidate_id = ?
            """, (candidate_id,))
            
            # Agregar nuevas keywords
            for keyword in keywords:
                keyword = keyword.strip()
                if keyword:
                    # Verificar si ya existe
                    cursor = conn.execute("""
                        SELECT id FROM candidate_keywords 
                        WHERE candidate_id = ? AND keyword = ?
                    """, (candidate_id, keyword))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Reactivar keyword existente
                        conn.execute("""
                            UPDATE candidate_keywords 
                            SET is_active = 1 
                            WHERE id = ?
                        """, (existing[0],))
                    else:
                        # Crear nueva keyword
                        conn.execute("""
                            INSERT INTO candidate_keywords (candidate_id, keyword, created_utc, is_active)
                            VALUES (?, ?, ?, 1)
                        """, (candidate_id, keyword, datetime.utcnow().isoformat()))
        
        flash(f"Candidato '{name}' actualizado exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al editar candidato: {e}")
        flash(f"Error al editar candidato: {e}", 'error')
    
    return redirect(url_for('manage_candidates'))

@app.route('/candidates/<int:candidate_id>/delete', methods=['POST'])
def delete_candidate(candidate_id):
    """Eliminar candidato completamente."""
    try:
        conn = get_db_connection()
        with conn:
            # Obtener nombre del candidato
            cursor = conn.execute("SELECT name FROM candidates WHERE id = ?", (candidate_id,))
            candidate = cursor.fetchone()
            
            if not candidate:
                flash('Candidato no encontrado', 'error')
                return redirect(url_for('manage_candidates'))
            
            # Eliminar completamente las keywords del candidato
            conn.execute("""
                DELETE FROM candidate_keywords 
                WHERE candidate_id = ?
            """, (candidate_id,))
            
            # Eliminar completamente el candidato
            conn.execute("""
                DELETE FROM candidates 
                WHERE id = ?
            """, (candidate_id,))
        
        flash(f"Candidato '{candidate[0]}' eliminado exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al eliminar candidato: {e}")
        flash(f"Error al eliminar candidato: {e}", 'error')
    
    return redirect(url_for('manage_candidates'))

@app.route('/test')
def test_page():
    """Página de testing."""
    try:
        enabled_feeds = get_enabled_feeds()
        return render_template('test.html', enabled_feeds=enabled_feeds, keywords=config['keywords'], current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar página de test: {e}")
        flash(f"Error al cargar página de test: {e}", 'error')
        return render_template('test.html', enabled_feeds=[], keywords=[], current_time=datetime.now())

@app.route('/test-delete')
def test_delete_ui():
    """Página de prueba para eliminación de candidatos."""
    with open('test_delete_ui.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/articles')
def articles():
    """Página para ver todos los artículos procesados."""
    page = request.args.get('page', 1, type=int)
    feed_filter = request.args.get('feed', '')
    per_page = 20  # Artículos por página
    
    conn = get_db_connection()
    
    # Obtener lista de feeds disponibles
    cursor = conn.execute("SELECT DISTINCT site FROM articles ORDER BY site")
    available_feeds = [row[0] for row in cursor.fetchall()]
    
    # Construir consulta con filtro opcional
    where_clause = ""
    params = []
    if feed_filter:
        where_clause = "WHERE site = ?"
        params.append(feed_filter)
    
    # Contar total de artículos (con filtro si aplica)
    count_query = f"SELECT COUNT(*) FROM articles {where_clause}"
    cursor = conn.execute(count_query, params)
    total_articles = cursor.fetchone()[0]
    
    # Calcular offset
    offset = (page - 1) * per_page
    
    # Obtener artículos con paginación y filtro
    articles_query = f"""
        SELECT id, title, site, published_utc, link
        FROM articles {where_clause}
        ORDER BY published_utc DESC 
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    cursor = conn.execute(articles_query, params)
    
    articles = cursor.fetchall()
    
    # Obtener hits para cada artículo
    articles_with_hits = []
    for article in articles:
        cursor = conn.execute("""
            SELECT keyword, where_found
            FROM hits 
            WHERE article_id = ?
        """, (article[0],))
        hits = cursor.fetchall()
        
        articles_with_hits.append({
            'id': article[0],
            'title': article[1],
            'site': article[2],
            'published_utc': article[3],
            'link': article[4],
            'hits': hits
        })
    
    conn.close()
    
    # Calcular información de paginación
    total_pages = (total_articles + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('articles.html', 
                         articles=articles_with_hits,
                         page=page,
                         total_pages=total_pages,
                         total_articles=total_articles,
                         has_prev=has_prev,
                         has_next=has_next,
                         available_feeds=available_feeds,
                         current_feed=feed_filter,
                         current_time=datetime.now())

@app.route('/mentions')
def mentions():
    """Página para ver todas las menciones filtradas por feed."""
    page = request.args.get('page', 1, type=int)
    feed_filter = request.args.get('feed', '')
    keyword_filter = request.args.get('keyword', '')
    per_page = 20  # Menciones por página
    
    conn = get_db_connection()
    
    # Obtener lista de feeds y keywords disponibles
    cursor = conn.execute("SELECT DISTINCT a.site FROM articles a JOIN hits h ON a.id = h.article_id ORDER BY a.site")
    available_feeds = [row[0] for row in cursor.fetchall()]
    
    cursor = conn.execute("SELECT DISTINCT keyword FROM hits ORDER BY keyword")
    available_keywords = [row[0] for row in cursor.fetchall()]
    
    # Construir consulta con filtros opcionales
    where_conditions = []
    params = []
    
    if feed_filter:
        where_conditions.append("a.site = ?")
        params.append(feed_filter)
    
    if keyword_filter:
        where_conditions.append("h.keyword = ?")
        params.append(keyword_filter)
    
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    # Contar total de menciones (con filtros si aplican)
    count_query = f"""
        SELECT COUNT(*) 
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        {where_clause}
    """
    cursor = conn.execute(count_query, params)
    total_mentions = cursor.fetchone()[0]
    
    # Calcular offset
    offset = (page - 1) * per_page
    
    # Obtener menciones con paginación y filtros
    mentions_query = f"""
        SELECT h.keyword, h.where_found, h.detected_utc,
               a.title, a.site, a.link, a.published_utc
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        {where_clause}
        ORDER BY h.detected_utc DESC 
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    cursor = conn.execute(mentions_query, params)
    
    mentions = [{
        'keyword': row[0],
        'where_found': row[1],
        'detected_utc': row[2],
        'article_title': row[3],
        'site': row[4],
        'article_link': row[5],
        'published_utc': row[6]
    } for row in cursor.fetchall()]
    
    conn.close()
    
    # Calcular información de paginación
    total_pages = (total_mentions + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('mentions.html', 
                         mentions=mentions,
                         page=page,
                         total_pages=total_pages,
                         total_mentions=total_mentions,
                         has_prev=has_prev,
                         has_next=has_next,
                         available_feeds=available_feeds,
                         available_keywords=available_keywords,
                         current_feed=feed_filter,
                         current_keyword=keyword_filter,
                         current_time=datetime.now())

@app.route('/test/run', methods=['POST'])
def run_test():
    """Ejecutar test manual del sistema."""
    try:
        test_type = request.form.get('test_type')
        
        if test_type == 'main_task':
            # Ejecutar tarea principal en un hilo separado
            def run_main_task():
                try:
                    main_task()
                    logger.info("Test de tarea principal completado")
                except Exception as e:
                    logger.error(f"Error en test de tarea principal: {e}")
            
            thread = threading.Thread(target=run_main_task)
            thread.daemon = True
            thread.start()
            
            flash('Test de tarea principal iniciado. Revisa los logs para ver el progreso.', 'info')
        
        elif test_type == 'single_feed':
            feed_name = request.form.get('feed_name')
            if not feed_name:
                flash('Selecciona un feed para testear', 'error')
                return redirect(url_for('test_page'))
            
            # Buscar el feed específico
            feeds = get_enabled_feeds()
            target_feed = None
            for feed in feeds:
                if feed['name'] == feed_name:
                    target_feed = feed
                    break
            
            if not target_feed:
                flash('Feed no encontrado o deshabilitado', 'error')
                return redirect(url_for('test_page'))
            
            # Ejecutar test del feed en un hilo separado
            def run_feed_test():
                try:
                    process_feed(target_feed, config['keywords'])
                    logger.info(f"Test del feed {feed_name} completado")
                except Exception as e:
                    logger.error(f"Error en test del feed {feed_name}: {e}")
            
            thread = threading.Thread(target=run_feed_test)
            thread.daemon = True
            thread.start()
            
            flash(f'Test del feed {feed_name} iniciado. Revisa los logs para ver el progreso.', 'info')
        
    except Exception as e:
        logger.error(f"Error al ejecutar test: {e}")
        flash(f"Error al ejecutar test: {e}", 'error')
    
    return redirect(url_for('test_page'))

@app.route('/api/stats')
def api_stats():
    """API endpoint para obtener estadísticas en tiempo real."""
    try:
        stats = get_global_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs')
def view_logs():
    """Ver logs del sistema."""
    try:
        # Leer últimas líneas del log (si existe)
        log_lines = []
        log_file = 'logs/app.log'  # Ruta correcta al archivo de logs
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    log_lines = lines[-100:]  # Últimas 100 líneas
            except UnicodeDecodeError:
                # Intentar con codificación latin-1 si utf-8 falla
                try:
                    with open(log_file, 'r', encoding='latin-1') as f:
                        lines = f.readlines()
                        log_lines = lines[-100:]  # Últimas 100 líneas
                except Exception:
                    log_lines = ['Error al leer el archivo de logs debido a problemas de codificación']
        
        return render_template('logs.html', log_lines=log_lines, current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al leer logs: {e}")
        flash(f"Error al leer logs: {e}", 'error')
        return render_template('logs.html', log_lines=[], current_time=datetime.now())

@app.route('/health')
def health_check():
    """Endpoint de health check para monitoreo."""
    try:
        # Verificar conexión a base de datos
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'RSS Mentions Monitor',
            'version': '2.0.0'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status')
def status():
    """Página de estado del sistema en tiempo real."""
    try:
        conn = get_db_connection()
        
        # Estadísticas generales
        with conn:
            # Contar feeds activos
            cursor = conn.execute("SELECT COUNT(*) FROM rss_feeds WHERE is_active = 1")
            feeds_activos = cursor.fetchone()[0]
            
            # Contar candidatos activos
            cursor = conn.execute("SELECT COUNT(*) FROM candidates WHERE is_active = 1")
            candidatos_activos = cursor.fetchone()[0]
            
            # Contar artículos totales y recientes (últimas 24h)
            cursor = conn.execute("SELECT COUNT(*) FROM articles")
            total_articulos = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            articulos_24h = cursor.fetchone()[0]
            
            # Contar menciones totales y recientes
            cursor = conn.execute("SELECT COUNT(*) FROM mentions")
            total_menciones = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM mentions 
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            menciones_24h = cursor.fetchone()[0]
            
            # Último procesamiento de feeds
            cursor = conn.execute("""
                SELECT name, last_processed 
                FROM rss_feeds 
                WHERE last_processed IS NOT NULL 
                ORDER BY last_processed DESC 
                LIMIT 1
            """)
            ultimo_feed = cursor.fetchone()
            
            # Últimas menciones encontradas
            cursor = conn.execute("""
                SELECT m.created_at, c.name as candidate_name, a.title, m.context
                FROM mentions m
                JOIN candidates c ON m.candidate_id = c.id
                JOIN articles a ON m.article_id = a.id
                ORDER BY m.created_at DESC
                LIMIT 5
            """)
            ultimas_menciones = [dict(row) for row in cursor.fetchall()]
        
        status_data = {
            'feeds_activos': feeds_activos,
            'candidatos_activos': candidatos_activos,
            'total_articulos': total_articulos,
            'articulos_24h': articulos_24h,
            'total_menciones': total_menciones,
            'menciones_24h': menciones_24h,
            'ultimo_feed': dict(ultimo_feed) if ultimo_feed else None,
            'ultimas_menciones': ultimas_menciones,
            'timestamp': datetime.now()
        }
        
        return render_template('status.html', status=status_data, current_time=datetime.now())
        
    except Exception as e:
        logger.error(f"Error en página de estado: {e}")
        flash(f"Error al cargar estado del sistema: {e}", 'error')
        return render_template('status.html', status={}, current_time=datetime.now())

@app.route('/tools')
def tools_dashboard():
    """Dashboard de herramientas y diagnósticos."""
    try:
        # Definir las herramientas disponibles
        tools = [
            {
                'name': 'Verificar Efectividad',
                'description': 'Analiza la efectividad del sistema de detección de menciones',
                'script': 'verificar_efectividad.py',
                'category': 'diagnostico',
                'icon': '📊'
            },
            {
                'name': 'Verificar Estado',
                'description': 'Revisa el estado general del sistema y base de datos',
                'script': 'verificar_estado.py',
                'category': 'diagnostico',
                'icon': '🔍'
            },
            {
                'name': 'Generar Reporte de Rendimiento',
                'description': 'Crea un reporte detallado del rendimiento del sistema',
                'script': 'generate_performance_report.py',
                'category': 'reporte',
                'icon': '📈'
            },
            {
                'name': 'Verificar Solución',
                'description': 'Ejecuta verificaciones post-despliegue',
                'script': 'verificar_solucion.py',
                'category': 'diagnostico',
                'icon': '✅'
            },
            {
                'name': 'Procesar Artículos Pendientes',
                'description': 'Procesa todos los artículos pendientes en la cola',
                'script': 'process_pending_articles.py',
                'category': 'procesamiento',
                'icon': '⚙️'
            },
            {
                'name': 'Procesar Todos los Feeds',
                'description': 'Ejecuta procesamiento inmediato de todos los feeds',
                'script': 'process_all_feeds_now.py',
                'category': 'procesamiento',
                'icon': '🔄'
            },
            {
                'name': 'Verificar Andres de Leo',
                'description': 'Analiza específicamente las menciones de Andres de Leo',
                'script': 'verificar_andres_de_leo.py',
                'category': 'diagnostico',
                'icon': '👤'
            },
            {
                'name': 'Verificar Optimización',
                'description': 'Revisa el estado de las optimizaciones implementadas',
                'script': 'verificar_optimizacion.py',
                'category': 'diagnostico',
                'icon': '🚀'
            },
            {
                'name': 'Analizar Efectividad',
                'description': 'Análisis profundo de la efectividad del sistema',
                'script': 'analizar_efectividad.py',
                'category': 'analisis',
                'icon': '🔬'
            },
            {
                'name': 'Verificar Estado de Contenido',
                'description': 'Revisa el estado del procesamiento de contenido',
                'script': 'check_content_status.py',
                'category': 'diagnostico',
                'icon': '📄'
            },
            {
                'name': 'Migrar Base de Datos',
                'description': 'Actualiza la estructura de la base de datos con las últimas migraciones',
                'script': 'migrate_db.py',
                'category': 'mantenimiento',
                'icon': '🗄️'
            },
            {
                'name': 'Debug APIs Candidatos',
                'description': 'Verifica el estado de las APIs y base de datos para el formulario de candidatos',
                'script': 'debug_api_endpoints.py',
                'category': 'diagnostico',
                'icon': '🐛'
            },
            {
                'name': 'Debug Frontend Candidatos',
                'description': 'Verifica la estructura HTML y JavaScript del formulario de candidatos',
                'script': 'debug_frontend.py',
                'category': 'diagnostico',
                'icon': '🔍'
            },
            {
                'name': 'Solucionar Dropdowns Candidatos',
                'description': 'Diagnóstico completo y soluciones para opciones faltantes en formulario',
                'script': 'fix_candidate_dropdowns.py',
                'category': 'diagnostico',
                'icon': '🔧'
            },
            {
                'name': 'Ejecutar Todo',
                'description': 'Procesa todos los feeds, guarda artículos y busca menciones con estadísticas detalladas',
                'script': 'ejecutar_todo.py',
                'category': 'procesamiento',
                'icon': '🚀'
            }
        ]
        
        return render_template('tools.html', tools=tools, current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error en tools dashboard: {e}")
        flash(f"Error al cargar herramientas: {e}", 'error')
        return render_template('tools.html', tools=[], current_time=datetime.now())

@app.route('/tools/run/<script_name>', methods=['POST'])
def run_tool(script_name):
    """Ejecutar una herramienta específica."""
    import subprocess
    import sys
    
    try:
        # Lista de scripts permitidos por seguridad
        allowed_scripts = [
            'verificar_efectividad.py',
            'verificar_estado.py', 
            'generate_performance_report.py',
            'verificar_solucion.py',
            'process_pending_articles.py',
            'process_all_feeds_now.py',
            'verificar_andres_de_leo.py',
            'verificar_optimizacion.py',
            'analizar_efectividad.py',
            'check_content_status.py',
            'migrate_db.py',
            'debug_api_endpoints.py',
            'debug_frontend.py',
            'fix_candidate_dropdowns.py',
            'ejecutar_todo.py'
        ]
        
        if script_name not in allowed_scripts:
            return jsonify({
                'success': False,
                'error': f'Script {script_name} no está permitido'
            }), 400
        
        # Ejecutar el script
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos máximo
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'return_code': result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'El script excedió el tiempo límite de 5 minutos'
        }), 408
    except Exception as e:
        logger.error(f"Error ejecutando {script_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/favicon.ico')
def favicon():
    """Servir favicon para evitar 404s."""
    return '', 204

@app.route('/@vite/client')
def vite_client():
    """Manejar solicitudes de vite client para evitar 404s."""
    return '', 404

@app.route('/api/remove-duplicates', methods=['POST'])
def remove_duplicates():
    """Elimina hits duplicados de la base de datos."""
    try:
        result = remove_duplicate_hits()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al eliminar duplicados: {str(e)}'
        }), 500

@app.route('/api/detailed-stats')
def detailed_stats():
    """Obtiene estadísticas detalladas del sistema."""
    try:
        stats = get_detailed_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}'
        }), 500

# === RUTAS DE SUSCRIPCIONES ===

@app.route('/subscriptions')
def subscriptions_dashboard():
    """Dashboard de suscripciones por candidato."""
    try:
        from add_candidate_subscriptions import get_all_subscriptions
        
        # Obtener todas las suscripciones activas
        subscriptions = get_all_subscriptions()
        
        # Obtener candidatos disponibles para nuevas suscripciones
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("""
                SELECT id, name, political_party, electoral_section
                FROM candidates 
                WHERE is_active = 1
                ORDER BY name
            """)
            candidates = [dict(row) for row in cursor.fetchall()]
        
        return render_template('subscriptions.html', 
                             subscriptions=subscriptions,
                             candidates=candidates,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar dashboard de suscripciones: {e}")
        flash(f"Error al cargar dashboard de suscripciones: {e}", 'error')
        return render_template('subscriptions.html', 
                             subscriptions=[],
                             candidates=[],
                             current_time=datetime.now())

@app.route('/subscriptions/add', methods=['POST'])
def add_subscription():
    """Agregar nueva suscripción de Telegram para un candidato."""
    try:
        from add_candidate_subscriptions import add_subscription as add_sub
        
        candidate_id = int(request.form.get('candidate_id'))
        telegram_chat_id = request.form.get('telegram_chat_id').strip()
        subscriber_name = request.form.get('subscriber_name', '').strip()
        subscriber_username = request.form.get('subscriber_username', '').strip()
        notification_types = request.form.get('notification_types', 'all')
        
        if not candidate_id or not telegram_chat_id:
            flash('El candidato y el Chat ID de Telegram son requeridos', 'error')
            return redirect(url_for('subscriptions_dashboard'))
        
        # Validar formato de chat_id (debe ser numérico o empezar con -)
        if not (telegram_chat_id.isdigit() or (telegram_chat_id.startswith('-') and telegram_chat_id[1:].isdigit())):
            flash('El Chat ID de Telegram debe ser numérico (ej: 123456789 o -123456789)', 'error')
            return redirect(url_for('subscriptions_dashboard'))
        
        add_sub(candidate_id, telegram_chat_id, subscriber_name, subscriber_username, notification_types)
        
        flash('Suscripción agregada exitosamente', 'success')
    except Exception as e:
        logger.error(f"Error al agregar suscripción: {e}")
        flash(f"Error al agregar suscripción: {e}", 'error')
    
    return redirect(url_for('subscriptions_dashboard'))

@app.route('/subscriptions/remove', methods=['POST'])
def remove_subscription():
    """Remover suscripción de Telegram."""
    try:
        from add_candidate_subscriptions import remove_subscription as remove_sub
        
        candidate_id = int(request.form.get('candidate_id'))
        telegram_chat_id = request.form.get('telegram_chat_id')
        
        if not candidate_id or not telegram_chat_id:
            flash('Datos de suscripción inválidos', 'error')
            return redirect(url_for('subscriptions_dashboard'))
        
        remove_sub(candidate_id, telegram_chat_id)
        
        flash('Suscripción removida exitosamente', 'success')
    except Exception as e:
        logger.error(f"Error al remover suscripción: {e}")
        flash(f"Error al remover suscripción: {e}", 'error')
    
    return redirect(url_for('subscriptions_dashboard'))

@app.route('/api/subscriptions/<int:candidate_id>')
def api_candidate_subscriptions(candidate_id):
    """API endpoint para obtener suscripciones de un candidato específico."""
    try:
        from add_candidate_subscriptions import get_candidate_subscriptions
        
        subscriptions = get_candidate_subscriptions(candidate_id)
        
        return jsonify({
            'success': True,
            'candidate_id': candidate_id,
            'subscriptions': [{
                'telegram_chat_id': sub[0],
                'subscriber_name': sub[1],
                'notification_types': sub[2]
            } for sub in subscriptions]
        })
    except Exception as e:
        logger.error(f"Error en API de suscripciones para candidato {candidate_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/electoral-sections')
def api_electoral_sections():
    """API endpoint para obtener todas las secciones electorales."""
    try:
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("""
                SELECT id, numero, nombre, descripcion, municipios
                FROM electoral_sections 
                ORDER BY numero
            """)
            sections = []
            for row in cursor.fetchall():
                section = dict(row)
                # Parsear municipios JSON
                if section['municipios']:
                    try:
                        section['municipios'] = json.loads(section['municipios'])
                    except:
                        section['municipios'] = []
                sections.append(section)
        
        return jsonify({
            'success': True,
            'sections': sections
        })
    except Exception as e:
        logger.error(f"Error en API de secciones electorales: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/political-positions')
def api_political_positions():
    """API endpoint para obtener todos los cargos políticos."""
    try:
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("""
                SELECT id, nombre, nivel, tipo, descripcion
                FROM political_positions 
                WHERE is_active = 1
                ORDER BY nivel, tipo, nombre
            """)
            positions = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'positions': positions
        })
    except Exception as e:
        logger.error(f"Error en API de cargos políticos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/alliances')
def manage_alliances():
    """Página de gestión de alianzas electorales."""
    try:
        from app.storage import get_all_electoral_alliances
        alliances = get_all_electoral_alliances()
        return render_template('manage_alliances.html', alliances=alliances)
    except Exception as e:
        logger.error(f"Error al cargar alianzas: {e}")
        flash(f"Error al cargar alianzas: {e}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/alliances')
def api_alliances():
    """API para obtener todas las alianzas electorales."""
    try:
        from app.storage import get_all_electoral_alliances
        alliances = get_all_electoral_alliances()
        return jsonify({
            'success': True,
            'alliances': alliances
        })
    except Exception as e:
        logger.error(f"Error en API de alianzas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/alliances/add', methods=['POST'])
def add_alliance():
    """Agregar nueva alianza electoral."""
    try:
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        description = request.form.get('description')
        primary_color = request.form.get('primary_color')
        secondary_color = request.form.get('secondary_color')
        logo_url = request.form.get('logo_url')
        
        if not name or not display_name:
            flash('El nombre y nombre de visualización son requeridos', 'error')
            return redirect(url_for('manage_alliances'))
        
        from app.storage import create_electoral_alliance
        
        alliance_id = create_electoral_alliance(
            name=name,
            display_name=display_name,
            description=description,
            primary_color=primary_color,
            secondary_color=secondary_color,
            logo_url=logo_url
        )
        
        flash(f"Alianza '{display_name}' creada exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al agregar alianza: {e}")
        flash(f"Error al agregar alianza: {e}", 'error')
    
    return redirect(url_for('manage_alliances'))

@app.route('/alliances/<int:alliance_id>/edit', methods=['POST'])
def edit_alliance(alliance_id):
    """Editar alianza electoral existente."""
    try:
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        description = request.form.get('description')
        primary_color = request.form.get('primary_color')
        secondary_color = request.form.get('secondary_color')
        logo_url = request.form.get('logo_url')
        is_active = request.form.get('is_active') == 'on'
        
        if not name or not display_name:
            flash('El nombre y nombre de visualización son requeridos', 'error')
            return redirect(url_for('manage_alliances'))
        
        from app.storage import update_electoral_alliance
        
        update_electoral_alliance(alliance_id,
            name=name,
            display_name=display_name,
            description=description,
            primary_color=primary_color,
            secondary_color=secondary_color,
            logo_url=logo_url,
            is_active=is_active
        )
        
        flash(f"Alianza '{display_name}' actualizada exitosamente", 'success')
    except Exception as e:
        logger.error(f"Error al editar alianza: {e}")
        flash(f"Error al editar alianza: {e}", 'error')
    
    return redirect(url_for('manage_alliances'))

if __name__ == '__main__':
    # Para desarrollo local
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import yaml
import os
from datetime import datetime, timedelta
from app.storage import get_db_connection, get_hourly_stats, get_global_stats, remove_duplicate_hits, get_detailed_stats
from app.tasks import main_task, process_feed
from app.feeds import get_enabled_feeds
from app.config import config
import threading
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Obtener últimas menciones
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
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             enabled_feeds=enabled_feeds,
                             recent_hits=recent_hits,
                             keywords=config['keywords'],
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        flash(f"Error al cargar dashboard: {e}", 'error')
        return render_template('dashboard.html', 
                             stats={}, 
                             enabled_feeds=[],
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

@app.route('/keywords')
def keywords_management():
    """Gestión de palabras clave."""
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return render_template('keywords.html', keywords=config_data['keywords'], current_time=datetime.now())
    except Exception as e:
        logger.error(f"Error al cargar palabras clave: {e}")
        flash(f"Error al cargar palabras clave: {e}", 'error')
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
        stats = get_hourly_stats()
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
            'check_content_status.py'
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

if __name__ == '__main__':
    # Para desarrollo local
    app.run(debug=True, host='0.0.0.0', port=5000)
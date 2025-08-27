#!/usr/bin/env python3
"""
Script de prueba para buscar keywords y probar notificaciones
después de agregar candidatos.

Este script permite:
1. Verificar que los candidatos están en la base de datos
2. Buscar keywords específicas en artículos
3. Probar el sistema de notificaciones
4. Verificar que no se envían notificaciones duplicadas
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from app.storage import get_db_connection
from app.tasks import main_task
from app.notifier import send_telegram_notification
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def check_candidates():
    """Verificar que hay candidatos en la base de datos."""
    logger.info("Verificando candidatos en la base de datos...")
    
    conn = get_db_connection()
    with conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM persons")
        count = cursor.fetchone()['count']
        
        if count == 0:
            logger.warning("No hay candidatos en la base de datos")
            return False
        
        logger.info(f"Encontrados {count} candidatos")
        
        # Mostrar algunos candidatos
        cursor = conn.execute("""
            SELECT name, position, political_party 
            FROM persons 
            LIMIT 5
        """)
        candidates = cursor.fetchall()
        
        logger.info("Primeros 5 candidatos:")
        for candidate in candidates:
            party = candidate['political_party'] or 'Sin partido'
            position = candidate['position'] or 'Sin posición'
            logger.info(f"  - {candidate['name']} ({position}) - {party}")
        
        return True

def check_keywords():
    """Verificar keywords asociadas a candidatos."""
    logger.info("Verificando keywords de candidatos...")
    
    conn = get_db_connection()
    with conn:
        cursor = conn.execute("""
            SELECT p.name, pk.keyword 
            FROM persons p
            JOIN person_keywords pk ON p.id = pk.person_id
            LIMIT 10
        """)
        keywords = cursor.fetchall()
        
        if not keywords:
            logger.warning("No hay keywords asociadas a candidatos")
            return False
        
        logger.info(f"Encontradas {len(keywords)} keywords:")
        for kw in keywords:
            logger.info(f"  - {kw['name']}: '{kw['keyword']}'")
        
        return True

def search_test_keywords(test_keywords=None):
    """Buscar keywords específicas para prueba."""
    if test_keywords is None:
        test_keywords = ["candidato", "elecciones", "política", "congreso"]
    
    logger.info(f"Buscando keywords de prueba: {test_keywords}")
    
    conn = get_db_connection()
    results = {}
    
    with conn:
        for keyword in test_keywords:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM articles 
                WHERE title LIKE ? OR full_content LIKE ?
            """, (f"%{keyword}%", f"%{keyword}%"))
            
            count = cursor.fetchone()['count']
            results[keyword] = count
            logger.info(f"  - '{keyword}': {count} artículos encontrados")
    
    return results

def test_notification_system():
    """Probar el sistema de notificaciones."""
    logger.info("Probando sistema de notificaciones...")
    
    # Verificar configuración de notificaciones
    from app.config import config
    
    if not config.get('TELEGRAM_BOT_TOKEN') or not config.get('TELEGRAM_CHAT_ID'):
        logger.warning("Configuración de Telegram no encontrada")
        return False
    
    # Enviar notificación de prueba
    try:
        # Crear detalles de prueba en el formato esperado por send_telegram_notification
        test_hit_details = {
            'site': 'Sistema de Pruebas',
            'title': f'Prueba del sistema de notificaciones - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'link': 'https://example.com/test',
            'keyword': 'test',
            'where_found': 'sistema',
            'published_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'published_utc': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        send_telegram_notification(test_hit_details)
        logger.info("✅ Notificación de prueba enviada exitosamente")
        return True
            
    except Exception as e:
        logger.error(f"Error en sistema de notificaciones: {e}")
        return False

def check_recent_hits():
    """Verificar hits recientes en la base de datos."""
    logger.info("Verificando hits recientes...")
    
    conn = get_db_connection()
    with conn:
        cursor = conn.execute("""
            SELECT h.keyword, h.where_found, h.detected_utc,
                   a.title, a.site, p.name as person_name
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            LEFT JOIN persons p ON h.person_id = p.id
            ORDER BY h.detected_utc DESC
            LIMIT 10
        """)
        
        hits = cursor.fetchall()
        
        if not hits:
            logger.info("No hay hits recientes")
            return False
        
        logger.info(f"Últimos {len(hits)} hits:")
        for hit in hits:
            person_info = f" ({hit['person_name']})" if hit['person_name'] else ""
            logger.info(f"  - '{hit['keyword']}'{person_info} en {hit['site']} - {hit['detected_utc']}")
        
        return True

def run_feed_processing():
    """Ejecutar procesamiento de feeds para generar nuevos hits."""
    logger.info("Ejecutando procesamiento de feeds...")
    
    try:
        # Ejecutar la tarea principal
        main_task()
        logger.info("✅ Procesamiento de feeds completado")
        return True
    except Exception as e:
        logger.error(f"❌ Error en procesamiento de feeds: {e}")
        return False

def check_notification_duplicates():
    """Verificar que no hay notificaciones duplicadas."""
    logger.info("Verificando duplicados de notificaciones...")
    
    conn = get_db_connection()
    with conn:
        # Verificar si existe la tabla de notificaciones
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='notifications'
        """)
        
        if not cursor.fetchone():
            logger.warning("Tabla 'notifications' no existe")
            return False
        
        # Buscar notificaciones duplicadas por article_id
        cursor = conn.execute("""
            SELECT article_id, COUNT(*) as count
            FROM notifications
            GROUP BY article_id
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            logger.warning(f"Encontradas {len(duplicates)} notificaciones duplicadas:")
            for dup in duplicates:
                logger.warning(f"  - Article ID {dup['article_id']}: {dup['count']} notificaciones")
            return False
        else:
            # También verificar usando la columna notification_sent de hits
            cursor = conn.execute("""
                SELECT COUNT(*) as total_hits,
                       SUM(CASE WHEN notification_sent = 1 THEN 1 ELSE 0 END) as notified_hits
                FROM hits
            """)
            
            stats = cursor.fetchone()
            logger.info(f"✅ Estadísticas de notificaciones: {stats['notified_hits']}/{stats['total_hits']} hits notificados")
            logger.info("✅ No se encontraron notificaciones duplicadas")
            return True

def main():
    """Función principal del script de prueba."""
    logger.info("=== INICIANDO PRUEBAS DE KEYWORDS Y NOTIFICACIONES ===")
    
    results = {
        'candidates_check': False,
        'keywords_check': False,
        'keyword_search': False,
        'notification_test': False,
        'recent_hits': False,
        'feed_processing': False,
        'duplicate_check': False
    }
    
    # 1. Verificar candidatos
    results['candidates_check'] = check_candidates()
    
    # 2. Verificar keywords
    results['keywords_check'] = check_keywords()
    
    # 3. Buscar keywords de prueba
    search_results = search_test_keywords()
    results['keyword_search'] = any(count > 0 for count in search_results.values())
    
    # 4. Verificar hits recientes
    results['recent_hits'] = check_recent_hits()
    
    # 5. Ejecutar procesamiento de feeds
    if input("\n¿Ejecutar procesamiento de feeds? (y/N): ").lower() == 'y':
        results['feed_processing'] = run_feed_processing()
        
        # Esperar un poco y verificar nuevos hits
        time.sleep(2)
        logger.info("\nVerificando nuevos hits después del procesamiento...")
        check_recent_hits()
    
    # 6. Probar sistema de notificaciones
    if input("\n¿Probar sistema de notificaciones? (y/N): ").lower() == 'y':
        results['notification_test'] = test_notification_system()
    
    # 7. Verificar duplicados
    results['duplicate_check'] = check_notification_duplicates()
    
    # Resumen final
    logger.info("\n=== RESUMEN DE PRUEBAS ===")
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    logger.info(f"\nResultado: {passed_tests}/{total_tests} pruebas pasaron")
    
    if passed_tests == total_tests:
        logger.info("🎉 ¡Todas las pruebas pasaron!")
        return True
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} pruebas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
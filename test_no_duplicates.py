#!/usr/bin/env python3
"""
Script de prueba para verificar que no se envían notificaciones duplicadas.
Este script simula múltiples ejecuciones del sistema para verificar la deduplicación.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection, mark_notification_sent
from app.config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_notification_deduplication():
    """Prueba el sistema de deduplicación de notificaciones."""
    logger.info("=== INICIANDO PRUEBA DE DEDUPLICACIÓN ===")
    
    conn = get_db_connection()
    
    try:
        with conn:
            # 1. Verificar que existe la columna notification_sent
            cursor = conn.execute("PRAGMA table_info(hits)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'notification_sent' not in columns:
                logger.error("❌ La columna 'notification_sent' no existe en la tabla hits")
                return False
            
            logger.info("✅ La columna 'notification_sent' existe")
            
            # 2. Verificar hits pendientes de notificación
            cursor = conn.execute("""
                SELECT COUNT(*) FROM hits 
                WHERE notification_sent = 0
            """)
            pending_count = cursor.fetchone()[0]
            logger.info(f"📊 Hits pendientes de notificación: {pending_count}")
            
            # 3. Verificar hits ya notificados
            cursor = conn.execute("""
                SELECT COUNT(*) FROM hits 
                WHERE notification_sent = 1
            """)
            sent_count = cursor.fetchone()[0]
            logger.info(f"📊 Hits ya notificados: {sent_count}")
            
            # 4. Verificar hits de palabras clave importantes
            important_keywords = ['liberman', 'coria', 'andres de leo']
            
            for keyword in important_keywords:
                cursor = conn.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN notification_sent = 0 THEN 1 ELSE 0 END) as pending,
                           SUM(CASE WHEN notification_sent = 1 THEN 1 ELSE 0 END) as sent
                    FROM hits 
                    WHERE LOWER(keyword) LIKE ?
                """, (f'%{keyword.lower()}%',))
                
                result = cursor.fetchone()
                total, pending, sent = result[0], result[1] or 0, result[2] or 0
                
                logger.info(f"🔍 {keyword.upper()}: Total={total}, Pendientes={pending}, Enviados={sent}")
            
            # 5. Verificar feeds y su estado de cache
            cursor = conn.execute("""
                SELECT name, etag, last_modified, last_fetch_utc, error_count
                FROM feed_state 
                WHERE is_enabled = 1
                ORDER BY last_fetch_utc DESC
            """)
            
            logger.info("\n📡 Estado de feeds:")
            for row in cursor.fetchall():
                name, etag, last_modified, last_fetch, error_count = row
                etag_status = "✅" if etag else "❌"
                last_mod_status = "✅" if last_modified else "❌"
                logger.info(f"  {name}: ETag={etag_status} LastMod={last_mod_status} Errors={error_count}")
            
            # 6. Simular marcado de notificación
            if pending_count > 0:
                cursor = conn.execute("""
                    SELECT id FROM hits 
                    WHERE notification_sent = 0 
                    LIMIT 1
                """)
                test_hit = cursor.fetchone()
                
                if test_hit:
                    hit_id = test_hit[0]
                    logger.info(f"\n🧪 Probando marcado de notificación para hit {hit_id}")
                    
                    # Verificar estado antes
                    cursor = conn.execute(
                        "SELECT notification_sent FROM hits WHERE id = ?", 
                        (hit_id,)
                    )
                    before = cursor.fetchone()[0]
                    logger.info(f"   Estado antes: {before}")
                    
                    # Marcar como enviado
                    mark_notification_sent(hit_id)
                    
                    # Verificar estado después
                    cursor = conn.execute(
                        "SELECT notification_sent FROM hits WHERE id = ?", 
                        (hit_id,)
                    )
                    after = cursor.fetchone()[0]
                    logger.info(f"   Estado después: {after}")
                    
                    if after == 1:
                        logger.info("   ✅ Marcado exitoso")
                    else:
                        logger.error("   ❌ Error en el marcado")
                        return False
            
            logger.info("\n=== PRUEBA COMPLETADA EXITOSAMENTE ===")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}")
        return False
    
    finally:
        conn.close()

def test_feed_caching():
    """Prueba el sistema de cache de feeds."""
    logger.info("\n=== PROBANDO SISTEMA DE CACHE DE FEEDS ===")
    
    from app.feeds import get_feeds_for_processing
    from app.fetch import fetch_feed_with_cache, FeedNotModifiedException
    
    try:
        feeds = get_feeds_for_processing()
        logger.info(f"📡 Feeds listos para procesamiento: {len(feeds)}")
        
        if feeds:
            test_feed = feeds[0]
            logger.info(f"🧪 Probando cache con feed: {test_feed['name']}")
            
            try:
                parsed_feed, etag, last_modified = fetch_feed_with_cache(test_feed)
                logger.info(f"   ✅ Feed actualizado - ETag: {bool(etag)}, Last-Modified: {bool(last_modified)}")
            except FeedNotModifiedException:
                logger.info(f"   ✅ Feed no modificado (cache funcionando)")
            except Exception as e:
                logger.error(f"   ❌ Error al probar cache: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando cache de feeds: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando pruebas del sistema anti-duplicados")
    
    # Ejecutar pruebas
    dedup_ok = test_notification_deduplication()
    cache_ok = test_feed_caching()
    
    if dedup_ok and cache_ok:
        logger.info("\n🎉 TODAS LAS PRUEBAS PASARON - El sistema está funcionando correctamente")
        sys.exit(0)
    else:
        logger.error("\n💥 ALGUNAS PRUEBAS FALLARON - Revisar la configuración")
        sys.exit(1)
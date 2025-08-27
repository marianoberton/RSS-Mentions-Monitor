import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_candidate_subscriptions():
    """Agregar tabla de suscripciones por candidato con múltiples telegram_chat_id."""
    logger.info("Agregando sistema de suscripciones por candidato...")
    
    conn = sqlite3.connect('data/mentions.db')
    
    try:
        with conn:
            # 1. Crear tabla candidate_subscriptions
            logger.info("Creando tabla candidate_subscriptions...")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                telegram_chat_id TEXT NOT NULL,
                subscriber_name TEXT,
                subscriber_username TEXT,
                notification_types TEXT DEFAULT 'all',
                is_active INTEGER DEFAULT 1,
                created_utc TEXT NOT NULL,
                updated_utc TEXT NOT NULL,
                FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
                UNIQUE(candidate_id, telegram_chat_id)
            );
            """)
            
            # 2. Crear índices para mejorar el rendimiento
            logger.info("Creando índices...")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_subscriptions_candidate_id ON candidate_subscriptions(candidate_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_subscriptions_chat_id ON candidate_subscriptions(telegram_chat_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_subscriptions_active ON candidate_subscriptions(is_active)")
            
            # 3. Migrar configuración actual de Telegram si existe
            logger.info("Verificando configuración actual de Telegram...")
            
            # Verificar si existe la tabla candidates
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='candidates'
            """)
            
            if cursor.fetchone():
                logger.info("Tabla candidates encontrada. Verificando candidatos activos...")
                
                # Obtener candidatos activos
                candidates_cursor = conn.execute("""
                    SELECT id, name FROM candidates WHERE is_active = 1
                """)
                candidates = candidates_cursor.fetchall()
                
                logger.info(f"Encontrados {len(candidates)} candidatos activos")
                
                # Si hay candidatos pero no suscripciones, crear una suscripción por defecto
                # usando el TELEGRAM_CHAT_ID de la configuración
                if candidates:
                    subs_cursor = conn.execute("SELECT COUNT(*) FROM candidate_subscriptions")
                    subs_count = subs_cursor.fetchone()[0]
                    
                    if subs_count == 0:
                        logger.info("No hay suscripciones existentes. Se pueden agregar manualmente desde la interfaz web.")
            else:
                logger.info("Tabla candidates no encontrada. Ejecutar primero migrate_to_candidates.py")
            
            logger.info("Sistema de suscripciones agregado exitosamente")
            
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        raise
    finally:
        conn.close()

def get_candidate_subscriptions(candidate_id):
    """Obtener todas las suscripciones activas para un candidato."""
    conn = sqlite3.connect('data/mentions.db')
    try:
        cursor = conn.execute("""
            SELECT telegram_chat_id, subscriber_name, notification_types
            FROM candidate_subscriptions 
            WHERE candidate_id = ? AND is_active = 1
        """, (candidate_id,))
        return cursor.fetchall()
    finally:
        conn.close()

def add_subscription(candidate_id, telegram_chat_id, subscriber_name=None, subscriber_username=None, notification_types='all'):
    """Agregar una nueva suscripción para un candidato."""
    conn = sqlite3.connect('data/mentions.db')
    try:
        with conn:
            now_utc = datetime.utcnow().isoformat()
            conn.execute("""
                INSERT OR REPLACE INTO candidate_subscriptions 
                (candidate_id, telegram_chat_id, subscriber_name, subscriber_username, 
                 notification_types, created_utc, updated_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (candidate_id, telegram_chat_id, subscriber_name, subscriber_username, 
                  notification_types, now_utc, now_utc))
            logger.info(f"Suscripción agregada: candidato {candidate_id} -> chat {telegram_chat_id}")
    finally:
        conn.close()

def remove_subscription(candidate_id, telegram_chat_id):
    """Remover una suscripción específica."""
    conn = sqlite3.connect('data/mentions.db')
    try:
        with conn:
            conn.execute("""
                UPDATE candidate_subscriptions 
                SET is_active = 0, updated_utc = ?
                WHERE candidate_id = ? AND telegram_chat_id = ?
            """, (datetime.utcnow().isoformat(), candidate_id, telegram_chat_id))
            logger.info(f"Suscripción removida: candidato {candidate_id} -> chat {telegram_chat_id}")
    finally:
        conn.close()

def get_all_subscriptions():
    """Obtener todas las suscripciones activas con información del candidato."""
    conn = sqlite3.connect('data/mentions.db')
    try:
        cursor = conn.execute("""
            SELECT 
                cs.id,
                cs.candidate_id,
                c.name as candidate_name,
                c.political_party,
                cs.telegram_chat_id,
                cs.subscriber_name,
                cs.notification_types,
                cs.created_utc
            FROM candidate_subscriptions cs
            JOIN candidates c ON cs.candidate_id = c.id
            WHERE cs.is_active = 1 AND c.is_active = 1
            ORDER BY c.name, cs.created_utc
        """)
        return cursor.fetchall()
    finally:
        conn.close()

if __name__ == "__main__":
    add_candidate_subscriptions()
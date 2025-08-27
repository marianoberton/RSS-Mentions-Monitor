#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de migración automática de base de datos
Detecta automáticamente qué migraciones necesita aplicar y las ejecuta
"""

import sqlite3
import logging
import os
from datetime import datetime
from app.config import config
from app.storage import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.db_path = config.get("SQLITE_PATH", "data/mentions.db")
        self.migrations_applied = []
        
    def get_db_version(self):
        """Obtiene la versión actual de la base de datos"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Crear tabla de versiones si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)
            
            # Obtener migraciones aplicadas
            cursor.execute("SELECT migration_name FROM db_migrations ORDER BY id")
            applied = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return applied
            
        except Exception as e:
            logger.error(f"Error obteniendo versión de BD: {e}")
            return []
    
    def mark_migration_applied(self, migration_name):
        """Marca una migración como aplicada"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR IGNORE INTO db_migrations (migration_name, applied_at) VALUES (?, ?)",
                (migration_name, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Migración marcada como aplicada: {migration_name}")
            
        except Exception as e:
            logger.error(f"Error marcando migración: {e}")
    
    def check_table_exists(self, table_name):
        """Verifica si una tabla existe"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            exists = cursor.fetchone() is not None
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"Error verificando tabla {table_name}: {e}")
            return False
    
    def check_column_exists(self, table_name, column_name):
        """Verifica si una columna existe en una tabla"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            
            return column_name in columns
            
        except Exception as e:
            logger.error(f"Error verificando columna {column_name} en {table_name}: {e}")
            return False
    
    def check_index_exists(self, index_name):
        """Verifica si un índice existe"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                (index_name,)
            )
            exists = cursor.fetchone() is not None
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"Error verificando índice {index_name}: {e}")
            return False
    
    def migration_001_create_base_tables(self):
        """Migración 001: Crear tablas base del sistema"""
        migration_name = "001_create_base_tables"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 001: Crear tablas base")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tabla articles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    site TEXT NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    published_utc TEXT NOT NULL,
                    inserted_utc TEXT NOT NULL,
                    content_processed INTEGER DEFAULT 0,
                    full_content TEXT,
                    canonical_url TEXT,
                    content_hash TEXT
                )
            """)
            
            # Tabla hits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    where_found TEXT NOT NULL,
                    detected_utc TEXT NOT NULL,
                    notification_sent INTEGER DEFAULT 0,
                    FOREIGN KEY(article_id) REFERENCES articles(id)
                )
            """)
            
            # Tabla feed_state
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feed_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    url TEXT NOT NULL,
                    etag TEXT,
                    last_modified TEXT,
                    last_fetch_utc TEXT,
                    last_success_utc TEXT,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    next_run_at TEXT,
                    fetch_interval_minutes INTEGER DEFAULT 10,
                    is_enabled INTEGER DEFAULT 1,
                    created_utc TEXT NOT NULL,
                    updated_utc TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 001: {e}")
            raise
    
    def migration_002_add_persons_system(self):
        """Migración 002: Agregar sistema de personas"""
        migration_name = "002_add_persons_system"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 002: Sistema de personas")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tabla persons
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    full_name TEXT,
                    description TEXT,
                    position TEXT,
                    political_party TEXT,
                    importance_level INTEGER DEFAULT 1,
                    created_utc TEXT NOT NULL,
                    updated_utc TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Tabla person_keywords
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS person_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    is_primary INTEGER DEFAULT 0,
                    created_utc TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE,
                    UNIQUE(person_id, keyword)
                )
            """)
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 002: {e}")
            raise
    
    def migration_003_add_missing_columns(self):
        """Migración 003: Agregar columnas faltantes"""
        migration_name = "003_add_missing_columns"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 003: Columnas faltantes")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Agregar person_id a hits si no existe
            if not self.check_column_exists("hits", "person_id"):
                cursor.execute("ALTER TABLE hits ADD COLUMN person_id INTEGER REFERENCES persons(id)")
                logger.info("Agregada columna person_id a tabla hits")
            
            # Agregar score a hits si no existe
            if not self.check_column_exists("hits", "score"):
                cursor.execute("ALTER TABLE hits ADD COLUMN score REAL DEFAULT 0.0")
                logger.info("Agregada columna score a tabla hits")
            
            # Agregar canonical_url a articles si no existe
            if not self.check_column_exists("articles", "canonical_url"):
                cursor.execute("ALTER TABLE articles ADD COLUMN canonical_url TEXT")
                logger.info("Agregada columna canonical_url a tabla articles")
            
            # Agregar content_hash a articles si no existe
            if not self.check_column_exists("articles", "content_hash"):
                cursor.execute("ALTER TABLE articles ADD COLUMN content_hash TEXT")
                logger.info("Agregada columna content_hash a tabla articles")
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 003: {e}")
            raise
    
    def migration_004_create_indexes(self):
        """Migración 004: Crear índices para rendimiento"""
        migration_name = "004_create_indexes"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 004: Índices de rendimiento")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            indexes = [
                ("idx_hits_person_id", "CREATE INDEX IF NOT EXISTS idx_hits_person_id ON hits(person_id)"),
                ("idx_hits_article_person", "CREATE INDEX IF NOT EXISTS idx_hits_article_person ON hits(article_id, person_id)"),
                ("idx_person_keywords_person_id", "CREATE INDEX IF NOT EXISTS idx_person_keywords_person_id ON person_keywords(person_id)"),
                ("idx_persons_name", "CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name)"),
                ("idx_feed_state_name", "CREATE INDEX IF NOT EXISTS idx_feed_state_name ON feed_state(name)"),
                ("idx_feed_state_next_run", "CREATE INDEX IF NOT EXISTS idx_feed_state_next_run ON feed_state(next_run_at)"),
                ("idx_articles_canonical_url", "CREATE INDEX IF NOT EXISTS idx_articles_canonical_url ON articles(canonical_url)"),
                ("idx_articles_content_hash", "CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash)"),
                ("idx_articles_canonical_content", "CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_canonical_content ON articles(canonical_url, content_hash)")
            ]
            
            for index_name, sql in indexes:
                if not self.check_index_exists(index_name):
                    cursor.execute(sql)
                    logger.info(f"Creado índice: {index_name}")
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 004: {e}")
            raise
    
    def migration_005_create_fts_tables(self):
        """Migración 005: Crear tablas FTS5 para búsqueda"""
        migration_name = "005_create_fts_tables"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 005: Tablas FTS5")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Crear tabla FTS5
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                    title, 
                    content, 
                    site,
                    content=articles,
                    content_rowid=id
                )
            """)
            
            # Crear triggers
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS articles_fts_insert AFTER INSERT ON articles BEGIN
                    INSERT INTO articles_fts(rowid, title, content, site) 
                    VALUES (new.id, new.title, COALESCE(new.full_content, ''), new.site);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS articles_fts_delete AFTER DELETE ON articles BEGIN
                    DELETE FROM articles_fts WHERE rowid = old.id;
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS articles_fts_update AFTER UPDATE ON articles BEGIN
                    DELETE FROM articles_fts WHERE rowid = old.id;
                    INSERT INTO articles_fts(rowid, title, content, site) 
                    VALUES (new.id, new.title, COALESCE(new.full_content, ''), new.site);
                END
            """)
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 005: {e}")
            raise
    
    def run_all_migrations(self):
        """Ejecuta todas las migraciones necesarias"""
        logger.info("Iniciando proceso de migración de base de datos")
        
        # Obtener migraciones ya aplicadas
        self.migrations_applied = self.get_db_version()
        logger.info(f"Migraciones aplicadas: {self.migrations_applied}")
        
        # Ejecutar migraciones en orden
        migrations = [
            self.migration_001_create_base_tables,
            self.migration_002_add_persons_system,
            self.migration_003_add_missing_columns,
            self.migration_004_create_indexes,
            self.migration_005_create_fts_tables
        ]
        
        for migration in migrations:
            try:
                migration()
            except Exception as e:
                logger.error(f"Error ejecutando migración {migration.__name__}: {e}")
                raise
        
        logger.info("Proceso de migración completado exitosamente")
    
    def verify_database_integrity(self):
        """Verifica la integridad de la base de datos después de las migraciones"""
        logger.info("Verificando integridad de la base de datos")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar que las tablas principales existen
            required_tables = ['articles', 'hits', 'feed_state', 'persons', 'person_keywords', 'articles_fts']
            
            for table in required_tables:
                if self.check_table_exists(table):
                    logger.info(f"✅ Tabla {table} existe")
                else:
                    logger.error(f"❌ Tabla {table} no existe")
                    return False
            
            # Verificar columnas críticas
            critical_columns = [
                ('hits', 'notification_sent'),
                ('hits', 'person_id'),
                ('hits', 'score'),
                ('articles', 'canonical_url'),
                ('articles', 'content_hash')
            ]
            
            for table, column in critical_columns:
                if self.check_column_exists(table, column):
                    logger.info(f"✅ Columna {table}.{column} existe")
                else:
                    logger.error(f"❌ Columna {table}.{column} no existe")
                    return False
            
            # Verificar índices críticos
            critical_indexes = [
                'idx_hits_person_id',
                'idx_articles_canonical_content'
            ]
            
            for index in critical_indexes:
                if self.check_index_exists(index):
                    logger.info(f"✅ Índice {index} existe")
                else:
                    logger.warning(f"⚠️ Índice {index} no existe")
            
            conn.close()
            logger.info("Verificación de integridad completada")
            return True
            
        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
            return False

def main():
    """Función principal para ejecutar migraciones"""
    try:
        # Crear directorio de datos si no existe
        os.makedirs(os.path.dirname(config.get("SQLITE_PATH", "data/mentions.db")), exist_ok=True)
        
        migrator = DatabaseMigrator()
        
        # Ejecutar migraciones
        migrator.run_all_migrations()
        
        # Verificar integridad
        if migrator.verify_database_integrity():
            logger.info("🎉 Base de datos migrada y verificada exitosamente")
            return True
        else:
            logger.error("❌ Falló la verificación de integridad")
            return False
            
    except Exception as e:
        logger.error(f"Error en proceso de migración: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
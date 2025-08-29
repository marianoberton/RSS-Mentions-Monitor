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
    
    def migration_006_create_candidates_system(self):
        """Migración 006: Crear sistema de candidatos"""
        migration_name = "006_create_candidates_system"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 006: Sistema de candidatos")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tabla candidates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    full_name TEXT,
                    description TEXT,
                    political_party TEXT NOT NULL,
                    electoral_section INTEGER NOT NULL CHECK (electoral_section BETWEEN 1 AND 8),
                    legislative_position TEXT NOT NULL,
                    district TEXT,
                    list_number INTEGER,
                    list_position INTEGER,
                    importance_level INTEGER DEFAULT 1,
                    alliance_id INTEGER,
                    created_utc TEXT NOT NULL,
                    updated_utc TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    UNIQUE(name, political_party, electoral_section)
                )
            """)
            
            # Tabla candidate_keywords
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidate_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    is_primary INTEGER DEFAULT 0,
                    created_utc TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
                    UNIQUE(candidate_id, keyword)
                )
            """)
            
            # Tabla electoral_alliances
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS electoral_alliances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    display_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    logo_url TEXT,
                    primary_color TEXT DEFAULT '#007bff',
                    secondary_color TEXT DEFAULT '#6c757d',
                    created_utc TEXT NOT NULL,
                    updated_utc TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Tabla notifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    FOREIGN KEY(article_id) REFERENCES articles(id)
                )
            """)
            
            # Índices para mejorar rendimiento
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_keywords_candidate_id ON candidate_keywords(candidate_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate_keywords_keyword ON candidate_keywords(keyword)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_electoral_section ON candidates(electoral_section)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_article_id ON notifications(article_id)")
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 006: {e}")
            raise
    
    def migration_007_fix_electoral_alliances(self):
        """Migración 007: Agregar columnas faltantes a electoral_alliances"""
        migration_name = "007_fix_electoral_alliances"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 007: Corrigiendo tabla electoral_alliances")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar si las columnas ya existen
            cursor.execute("PRAGMA table_info(electoral_alliances)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Agregar columna 'name' si no existe
            if 'name' not in columns:
                cursor.execute("ALTER TABLE electoral_alliances ADD COLUMN name TEXT")
                # Actualizar registros existentes para que name = display_name
                cursor.execute("UPDATE electoral_alliances SET name = display_name WHERE name IS NULL")
                logger.info("✅ Columna 'name' agregada a electoral_alliances")
            
            # Agregar columna 'logo_url' si no existe
            if 'logo_url' not in columns:
                cursor.execute("ALTER TABLE electoral_alliances ADD COLUMN logo_url TEXT")
                logger.info("✅ Columna 'logo_url' agregada a electoral_alliances")
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 007: {e}")
            raise

    def migration_008_create_electoral_data_tables(self):
        """Migración 008: Crear tablas de datos electorales (political_positions y electoral_sections)"""
        migration_name = "008_create_electoral_data_tables"
        
        if migration_name in self.migrations_applied:
            return
            
        logger.info("Aplicando migración 008: Crear tablas de datos electorales")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Tabla de secciones electorales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS electoral_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero INTEGER NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    provincia TEXT DEFAULT 'Buenos Aires',
                    municipios TEXT, -- JSON string con lista de municipios
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de catálogo de cargos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS political_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    nivel TEXT NOT NULL, -- Nacional, Provincial, Municipal
                    tipo TEXT NOT NULL, -- Ejecutivo, Legislativo, Judicial, etc.
                    descripcion TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para optimizar consultas
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_electoral_sections_numero ON electoral_sections(numero)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_electoral_sections_provincia ON electoral_sections(provincia)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_political_positions_nivel ON political_positions(nivel)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_political_positions_tipo ON political_positions(tipo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_political_positions_active ON political_positions(is_active)")
            
            # Poblar con datos iniciales
            self._seed_electoral_sections(cursor)
            self._seed_political_positions(cursor)
            
            conn.commit()
            conn.close()
            
            self.mark_migration_applied(migration_name)
            
        except Exception as e:
            logger.error(f"Error en migración 008: {e}")
            raise
    
    def _seed_electoral_sections(self, cursor):
        """Poblar tabla de secciones electorales con datos de PBA"""
        import json
        
        # Verificar si ya existen datos
        cursor.execute("SELECT COUNT(*) FROM electoral_sections")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"Ya existen {existing_count} secciones electorales")
            return
        
        # Datos de secciones electorales de PBA
        secciones = [
            {"numero": 1, "nombre": "Primera Sección Electoral", "descripcion": "Zona Norte del Gran Buenos Aires", "municipios": ["Vicente López", "San Isidro", "San Fernando", "Tigre", "Escobar", "Pilar", "José C. Paz", "Malvinas Argentinas", "San Miguel", "Hurlingham", "Ituzaingó", "Tres de Febrero", "Morón", "General San Martín"]},
            {"numero": 2, "nombre": "Segunda Sección Electoral", "descripcion": "Zona Oeste del Gran Buenos Aires", "municipios": ["La Matanza", "Merlo", "Moreno", "General Rodríguez", "Luján", "Marcos Paz"]},
            {"numero": 3, "nombre": "Tercera Sección Electoral", "descripcion": "Zona Sur del Gran Buenos Aires", "municipios": ["Almirante Brown", "Avellaneda", "Berazategui", "Esteban Echeverría", "Ezeiza", "Florencio Varela", "Lanús", "Lomas de Zamora", "Quilmes"]},
            {"numero": 4, "nombre": "Cuarta Sección Electoral", "descripcion": "Zona Centro-Este", "municipios": ["Berisso", "Brandsen", "Ensenada", "La Plata", "Magdalena", "Presidente Perón", "San Vicente"]},
            {"numero": 5, "nombre": "Quinta Sección Electoral", "descripcion": "Zona Centro-Norte", "municipios": ["Campana", "Exaltación de la Cruz", "San Antonio de Areco", "San Andrés de Giles", "Zárate", "Baradero", "Ramallo", "San Pedro", "Arrecifes", "Capitán Sarmiento", "Carmen de Areco", "Pergamino", "Rojas", "Salto", "Colón", "San Nicolás"]},
            {"numero": 6, "nombre": "Sexta Sección Electoral", "descripcion": "Zona Centro-Oeste", "municipios": ["25 de Mayo", "9 de Julio", "Alberti", "Bragado", "Carlos Casares", "Carlos Tejedor", "Chivilcoy", "General Arenales", "General Pinto", "General Viamonte", "General Villegas", "Junín", "Leandro N. Alem", "Lincoln", "Mercedes", "Pehuajó", "Rivadavia", "Trenque Lauquen"]},
            {"numero": 7, "nombre": "Séptima Sección Electoral", "descripcion": "Zona Sur-Oeste", "municipios": ["Adolfo Alsina", "Bahía Blanca", "Coronel de Marina Leonardo Rosales", "Coronel Dorrego", "Coronel Pringles", "Coronel Suárez", "Daireaux", "Guaminí", "Hipólito Yrigoyen", "Monte Hermoso", "Patagones", "Pellegrini", "Puán", "Saavedra", "Tornquist", "Tres Lomas", "Villarino"]},
            {"numero": 8, "nombre": "Octava Sección Electoral", "descripcion": "Zona Centro-Sur", "municipios": ["Ayacucho", "Azul", "Benito Juárez", "Bolívar", "Castelli", "Chascomús", "Dolores", "General Alvarado", "General Belgrano", "General Guido", "General Juan Madariaga", "General La Madrid", "General Lavalle", "General Paz", "Laprida", "Las Flores", "Lobería", "Lobos", "Maipú", "Mar Chiquita", "Monte", "Necochea", "Olavarría", "Partido de la Costa", "Pinamar", "Punta Indio", "Rauch", "Roque Pérez", "Saladillo", "San Cayetano", "Tandil", "Tapalqué", "Tordillo", "Villa Gesell"]}
        ]
        
        # Insertar secciones electorales
        for seccion in secciones:
            municipios_json = json.dumps(seccion['municipios'], ensure_ascii=False)
            cursor.execute("""
                INSERT INTO electoral_sections (numero, nombre, descripcion, municipios)
                VALUES (?, ?, ?, ?)
            """, (seccion['numero'], seccion['nombre'], seccion['descripcion'], municipios_json))
        
        logger.info(f"Insertadas {len(secciones)} secciones electorales de PBA")
    
    def _seed_political_positions(self, cursor):
        """Poblar tabla de cargos políticos"""
        # Verificar si ya existen datos
        cursor.execute("SELECT COUNT(*) FROM political_positions")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"Ya existen {existing_count} cargos políticos")
            return
        
        # Catálogo de cargos políticos
        cargos = [
            {"nombre": "Diputado Provincial", "nivel": "Provincial", "tipo": "Legislativo", "descripcion": "Miembro de la Legislatura Provincial"},
            {"nombre": "Diputado Nacional", "nivel": "Nacional", "tipo": "Legislativo", "descripcion": "Miembro de la Cámara de Diputados de la Nación"},
            {"nombre": "Senador Provincial", "nivel": "Provincial", "tipo": "Legislativo", "descripcion": "Miembro del Senado Provincial (donde existe)"}
        ]
        
        # Insertar cargos políticos
        for cargo in cargos:
            cursor.execute("""
                INSERT INTO political_positions (nombre, nivel, tipo, descripcion)
                VALUES (?, ?, ?, ?)
            """, (cargo['nombre'], cargo['nivel'], cargo['tipo'], cargo['descripcion']))
        
        logger.info(f"Insertados {len(cargos)} cargos políticos")
    
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
            self.migration_005_create_fts_tables,
            self.migration_006_create_candidates_system,
            self.migration_007_fix_electoral_alliances,
            self.migration_008_create_electoral_data_tables
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
            required_tables = ['articles', 'hits', 'feed_state', 'persons', 'person_keywords', 'articles_fts', 'candidates', 'candidate_keywords', 'electoral_alliances', 'notifications', 'political_positions', 'electoral_sections']
            
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
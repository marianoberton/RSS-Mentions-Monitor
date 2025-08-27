import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_electoral_alliances_system():
    """Crear sistema de alianzas electorales."""
    logger.info("Creando sistema de alianzas electorales...")
    
    conn = sqlite3.connect('data/mentions.db')
    
    try:
        with conn:
            # 1. Crear tabla de alianzas electorales
            logger.info("Creando tabla electoral_alliances...")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS electoral_alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                description TEXT,
                logo_url TEXT,
                primary_color TEXT DEFAULT '#007bff',
                secondary_color TEXT DEFAULT '#6c757d',
                is_active INTEGER DEFAULT 1,
                created_utc TEXT NOT NULL,
                updated_utc TEXT NOT NULL
            );
            """)
            
            # 2. Agregar columna alliance_id a la tabla candidates si no existe
            logger.info("Agregando columna alliance_id a tabla candidates...")
            try:
                conn.execute("""
                ALTER TABLE candidates 
                ADD COLUMN alliance_id INTEGER 
                REFERENCES electoral_alliances(id) ON DELETE SET NULL
                """)
                logger.info("Columna alliance_id agregada exitosamente")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("Columna alliance_id ya existe")
                else:
                    raise e
            
            # 3. Insertar las tres alianzas principales
            current_time = datetime.utcnow().isoformat()
            
            alliances = [
                {
                    'name': 'fuerza_patria',
                    'display_name': 'Fuerza Patria',
                    'description': 'Alianza electoral Fuerza Patria',
                    'primary_color': '#1e3a8a',  # Azul oscuro
                    'secondary_color': '#3b82f6'  # Azul claro
                },
                {
                    'name': 'la_libertad_avanza',
                    'display_name': 'La Libertad Avanza',
                    'description': 'Alianza electoral La Libertad Avanza',
                    'primary_color': '#7c3aed',  # Violeta
                    'secondary_color': '#a855f7'  # Violeta claro
                },
                {
                    'name': 'somos',
                    'display_name': 'Somos',
                    'description': 'Alianza electoral Somos',
                    'primary_color': '#dc2626',  # Rojo
                    'secondary_color': '#ef4444'  # Rojo claro
                }
            ]
            
            for alliance in alliances:
                conn.execute("""
                    INSERT OR IGNORE INTO electoral_alliances (
                        name, display_name, description, primary_color, secondary_color,
                        is_active, created_utc, updated_utc
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """, (
                    alliance['name'],
                    alliance['display_name'],
                    alliance['description'],
                    alliance['primary_color'],
                    alliance['secondary_color'],
                    current_time,
                    current_time
                ))
                
                logger.info(f"Alianza '{alliance['display_name']}' creada/actualizada")
            
            # 4. Crear índices para optimizar consultas
            logger.info("Creando índices...")
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_candidates_alliance_id 
                ON candidates(alliance_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_electoral_alliances_name 
                ON electoral_alliances(name)
            """)
            
            logger.info("Sistema de alianzas electorales creado exitosamente")
            
    except Exception as e:
        logger.error(f"Error creando sistema de alianzas: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    create_electoral_alliances_system()
    print("✅ Sistema de alianzas electorales creado exitosamente")
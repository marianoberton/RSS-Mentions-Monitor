import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_to_candidates():
    """Migrar de sistema de personas a sistema de candidatos."""
    logger.info("Iniciando migración a sistema de candidatos...")
    
    conn = sqlite3.connect('data/mentions.db')
    
    try:
        with conn:
            # 1. Crear nueva tabla candidates con estructura específica
            logger.info("Creando tabla candidates...")
            conn.execute("""
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
                created_utc TEXT NOT NULL,
                updated_utc TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                UNIQUE(name, political_party, electoral_section)
            );
            """)
            
            # 2. Crear nueva tabla candidate_keywords
            logger.info("Creando tabla candidate_keywords...")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                is_primary INTEGER DEFAULT 0,
                created_utc TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
                UNIQUE(candidate_id, keyword)
            );
            """)
            
            # 3. Migrar datos existentes de persons a candidates
            logger.info("Migrando datos existentes...")
            cursor = conn.execute("SELECT * FROM persons WHERE is_active = 1")
            persons = cursor.fetchall()
            
            for person in persons:
                # Convertir persona a candidato con valores por defecto
                conn.execute("""
                    INSERT OR IGNORE INTO candidates (
                        name, full_name, description, political_party, 
                        electoral_section, legislative_position, district,
                        importance_level, created_utc, updated_utc, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    person[1],  # name
                    person[2],  # full_name
                    person[3],  # description
                    person[5] or 'Sin Partido',  # political_party
                    1,  # electoral_section (por defecto)
                    'Diputado Provincial',  # legislative_position (por defecto)
                    'Buenos Aires',  # district
                    person[6],  # importance_level
                    person[7],  # created_utc
                    person[8],  # updated_utc
                    person[9]   # is_active
                ))
                
                # Obtener ID del candidato recién creado
                candidate_id = cursor.lastrowid
                if candidate_id:
                    # Migrar keywords
                    keyword_cursor = conn.execute(
                        "SELECT keyword, is_primary, created_utc FROM person_keywords WHERE person_id = ? AND is_active = 1",
                        (person[0],)
                    )
                    keywords = keyword_cursor.fetchall()
                    
                    for keyword in keywords:
                        conn.execute("""
                            INSERT OR IGNORE INTO candidate_keywords (
                                candidate_id, keyword, is_primary, created_utc, is_active
                            ) VALUES (?, ?, ?, ?, 1)
                        """, (candidate_id, keyword[0], keyword[1], keyword[2]))
                    
                    logger.info(f"Migrado: {person[1]} -> Candidato ID {candidate_id}")
            
            logger.info("Migración completada exitosamente")
            
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_to_candidates()
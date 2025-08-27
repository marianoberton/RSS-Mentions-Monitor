#!/usr/bin/env python3
"""
Script de migración para convertir el sistema de keywords a un sistema de personas.
Este script:
1. Crea personas para las keywords existentes
2. Asocia las keywords con las personas
3. Actualiza los hits existentes para referenciar personas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import (
    init_db, get_db_connection, create_person, add_person_keyword,
    get_all_persons, get_person_by_keyword
)
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Definir las personas políticas conocidas
POLITICAL_PERSONS = {
    "Javier Milei": {
        "full_name": "Javier Gerardo Milei",
        "description": "Presidente de la República Argentina",
        "position": "Presidente",
        "political_party": "La Libertad Avanza",
        "importance_level": 5,
        "keywords": ["Milei", "Javier Milei", "Presidente Milei"]
    },
    "Oscar Liberman": {
        "full_name": "Oscar Liberman",
        "description": "Político y empresario argentino",
        "position": "Empresario",
        "political_party": None,
        "importance_level": 3,
        "keywords": ["Liberman", "Oscar Liberman"]
    },
    "Gustavo Coria": {
        "full_name": "Gustavo Coria",
        "description": "Político argentino",
        "position": "Político",
        "political_party": None,
        "importance_level": 3,
        "keywords": ["Coria", "Gustavo Coria"]
    },
    "Andrés de Leo": {
        "full_name": "Andrés de Leo",
        "description": "Político argentino",
        "position": "Político",
        "political_party": None,
        "importance_level": 3,
        "keywords": ["Andres de Leo", "Andrés de Leo"]
    }
}

def migrate_persons():
    """Migrar keywords existentes a sistema de personas."""
    logger.info("Iniciando migración a sistema de personas...")
    
    # Inicializar base de datos con nuevas tablas
    init_db()
    
    conn = get_db_connection()
    
    try:
        # 1. Crear personas
        logger.info("Creando personas...")
        person_mapping = {}  # keyword -> person_id
        
        for name, data in POLITICAL_PERSONS.items():
            try:
                person_id = create_person(
                    name=name,
                    full_name=data["full_name"],
                    description=data["description"],
                    position=data["position"],
                    political_party=data["political_party"],
                    importance_level=data["importance_level"]
                )
                
                # 2. Agregar keywords para esta persona
                for i, keyword in enumerate(data["keywords"]):
                    is_primary = (i == 0)  # Primera keyword es primaria
                    add_person_keyword(person_id, keyword, is_primary)
                    person_mapping[keyword] = person_id
                    
                logger.info(f"Persona creada: {name} (ID: {person_id}) con {len(data['keywords'])} keywords")
                
            except ValueError as e:
                logger.warning(f"Persona {name} ya existe: {e}")
                # Si ya existe, obtener su ID
                existing_person = get_person_by_keyword(data["keywords"][0])
                if existing_person:
                    person_id = existing_person["id"]
                    for keyword in data["keywords"]:
                        person_mapping[keyword] = person_id
        
        # 3. Actualizar hits existentes para asociarlos con personas
        logger.info("Actualizando hits existentes...")
        
        with conn:
            # Obtener todos los hits que no tienen person_id
            cursor = conn.execute("""
                SELECT id, keyword FROM hits WHERE person_id IS NULL
            """)
            
            hits_to_update = cursor.fetchall()
            logger.info(f"Encontrados {len(hits_to_update)} hits para actualizar")
            
            updated_count = 0
            for hit_id, keyword in hits_to_update:
                if keyword in person_mapping:
                    person_id = person_mapping[keyword]
                    conn.execute("""
                        UPDATE hits SET person_id = ? WHERE id = ?
                    """, (person_id, hit_id))
                    updated_count += 1
            
            logger.info(f"Actualizados {updated_count} hits con person_id")
        
        # 4. Mostrar estadísticas de migración
        logger.info("Generando estadísticas de migración...")
        
        with conn:
            # Total de hits por persona
            cursor = conn.execute("""
                SELECT p.name, COUNT(h.id) as hit_count
                FROM persons p
                LEFT JOIN hits h ON p.id = h.person_id
                GROUP BY p.id, p.name
                ORDER BY hit_count DESC
            """)
            
            logger.info("\n=== ESTADÍSTICAS DE MIGRACIÓN ===")
            for row in cursor:
                logger.info(f"{row[0]}: {row[1]} hits")
            
            # Hits sin persona asignada
            cursor = conn.execute("""
                SELECT COUNT(*) FROM hits WHERE person_id IS NULL
            """)
            orphan_hits = cursor.fetchone()[0]
            logger.info(f"\nHits sin persona asignada: {orphan_hits}")
            
            if orphan_hits > 0:
                # Mostrar keywords sin persona
                cursor = conn.execute("""
                    SELECT keyword, COUNT(*) as count
                    FROM hits 
                    WHERE person_id IS NULL
                    GROUP BY keyword
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                logger.info("\nKeywords sin persona (top 10):")
                for row in cursor:
                    logger.info(f"  {row[0]}: {row[1]} hits")
        
        logger.info("\n¡Migración completada exitosamente!")
        
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        raise
    finally:
        conn.close()

def verify_migration():
    """Verificar que la migración se completó correctamente."""
    logger.info("\n=== VERIFICACIÓN DE MIGRACIÓN ===")
    
    conn = get_db_connection()
    
    try:
        with conn:
            # Verificar que todas las personas fueron creadas
            cursor = conn.execute("SELECT COUNT(*) FROM persons")
            person_count = cursor.fetchone()[0]
            logger.info(f"Personas creadas: {person_count}")
            
            # Verificar keywords
            cursor = conn.execute("SELECT COUNT(*) FROM person_keywords")
            keyword_count = cursor.fetchone()[0]
            logger.info(f"Keywords asociadas: {keyword_count}")
            
            # Verificar hits con persona
            cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE person_id IS NOT NULL")
            hits_with_person = cursor.fetchone()[0]
            logger.info(f"Hits con persona asignada: {hits_with_person}")
            
            # Verificar hits sin persona
            cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE person_id IS NULL")
            hits_without_person = cursor.fetchone()[0]
            logger.info(f"Hits sin persona: {hits_without_person}")
            
            # Mostrar resumen por persona
            cursor = conn.execute("""
                SELECT p.name, p.importance_level, COUNT(h.id) as hits,
                       COUNT(DISTINCT h.article_id) as articles
                FROM persons p
                LEFT JOIN hits h ON p.id = h.person_id
                GROUP BY p.id, p.name, p.importance_level
                ORDER BY p.importance_level DESC, hits DESC
            """)
            
            logger.info("\nResumen por persona:")
            for row in cursor:
                logger.info(f"  {row[0]} (nivel {row[1]}): {row[2]} hits en {row[3]} artículos")
                
    except Exception as e:
        logger.error(f"Error durante la verificación: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        migrate_persons()
        verify_migration()
        
        print("\n✅ Migración completada exitosamente!")
        print("\nEl sistema ahora usa personas en lugar de keywords simples.")
        print("Puedes usar las nuevas funciones en storage.py para gestionar personas.")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        sys.exit(1)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar candidatos de ejemplo con los nuevos datos electorales.
"""

import sqlite3
import logging
from datetime import datetime
from app.storage import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Candidatos de ejemplo para diferentes secciones electorales
CANDIDATOS_EJEMPLO = [
    {
        "name": "Axel Kicillof",
        "full_name": "Axel Kicillof",
        "description": "Gobernador de la Provincia de Buenos Aires",
        "legislative_position": "Gobernador Provincial",
        "electoral_section": 1,  # Primera Sección
        "district": "Buenos Aires",
        "political_party": "Frente de Todos",
        "importance_level": "high",
        "keywords": ["Kicillof", "Axel Kicillof", "Gobernador"]
    },
    {
        "name": "María Eugenia Vidal",
        "full_name": "María Eugenia Vidal",
        "description": "Ex Gobernadora de Buenos Aires, Diputada Nacional",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 2,  # Segunda Sección
        "district": "Buenos Aires",
        "political_party": "Juntos por el Cambio",
        "importance_level": "high",
        "keywords": ["Vidal", "María Eugenia Vidal", "Diputada"]
    },
    {
        "name": "Sergio Massa",
        "full_name": "Sergio Tomás Massa",
        "description": "Ministro de Economía, Diputado Nacional por Buenos Aires",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 3,  # Tercera Sección
        "district": "Buenos Aires",
        "political_party": "Frente de Todos",
        "importance_level": "high",
        "keywords": ["Massa", "Sergio Massa", "Ministro Economía"]
    },
    {
        "name": "Diego Santilli",
        "full_name": "Diego Santilli",
        "description": "Diputado Nacional por Buenos Aires",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 1,  # Primera Sección
        "district": "Buenos Aires",
        "political_party": "Juntos por el Cambio",
        "list_number": "2021",
        "list_position": 1,
        "importance_level": "medium",
        "keywords": ["Santilli", "Diego Santilli"]
    },
    {
        "name": "Victoria Tolosa Paz",
        "full_name": "Victoria Tolosa Paz",
        "description": "Diputada Nacional por Buenos Aires",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 4,  # Cuarta Sección
        "district": "Buenos Aires",
        "political_party": "Frente de Todos",
        "list_number": "2021",
        "list_position": 2,
        "importance_level": "medium",
        "keywords": ["Tolosa Paz", "Victoria Tolosa Paz"]
    },
    {
        "name": "Facundo Manes",
        "full_name": "Facundo Manes",
        "description": "Diputado Nacional por Buenos Aires, Neurocientífico",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 5,  # Quinta Sección
        "district": "Buenos Aires",
        "political_party": "Juntos por el Cambio",
        "importance_level": "medium",
        "keywords": ["Manes", "Facundo Manes", "Neurocientífico"]
    },
    {
        "name": "Florencio Randazzo",
        "full_name": "Florencio Randazzo",
        "description": "Ex Ministro del Interior, Diputado Nacional",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 6,  # Sexta Sección
        "district": "Buenos Aires",
        "political_party": "Vamos con Vos",
        "importance_level": "medium",
        "keywords": ["Randazzo", "Florencio Randazzo"]
    },
    {
        "name": "Cristian Ritondo",
        "full_name": "Cristian Ritondo",
        "description": "Diputado Nacional por Buenos Aires",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 7,  # Séptima Sección
        "district": "Buenos Aires",
        "political_party": "Juntos por el Cambio",
        "importance_level": "medium",
        "keywords": ["Ritondo", "Cristian Ritondo"]
    },
    {
        "name": "Máximo Kirchner",
        "full_name": "Máximo Carlos Kirchner",
        "description": "Diputado Nacional por Buenos Aires",
        "legislative_position": "Diputado Nacional",
        "electoral_section": 8,  # Octava Sección
        "district": "Buenos Aires",
        "political_party": "Frente de Todos",
        "importance_level": "high",
        "keywords": ["Máximo Kirchner", "Máximo", "Kirchner hijo"]
    },
    {
        "name": "Jorge Macri",
        "full_name": "Jorge Macri",
        "description": "Intendente de Vicente López",
        "legislative_position": "Intendente Municipal",
        "electoral_section": 1,  # Primera Sección
        "district": "Vicente López",
        "political_party": "Juntos por el Cambio",
        "importance_level": "medium",
        "keywords": ["Jorge Macri", "Intendente Vicente López"]
    }
]

def get_political_position_id(position_name):
    """Obtiene el ID de un cargo político por su nombre."""
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute(
                "SELECT id FROM political_positions WHERE nombre = ?",
                (position_name,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    finally:
        conn.close()

def get_electoral_section_id(section_number):
    """Obtiene el ID de una sección electoral por su número."""
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute(
                "SELECT id FROM electoral_sections WHERE numero = ?",
                (section_number,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    finally:
        conn.close()

def add_sample_candidates():
    """Agrega candidatos de ejemplo a la base de datos."""
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            # Verificar si ya existen candidatos
            cursor = conn.execute("SELECT COUNT(*) FROM candidates")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                logger.info(f"Ya existen {existing_count} candidatos. Agregando candidatos de ejemplo...")
            
            added_count = 0
            
            for candidato in CANDIDATOS_EJEMPLO:
                # Verificar si el candidato ya existe
                cursor = conn.execute(
                    "SELECT id FROM candidates WHERE name = ?",
                    (candidato['name'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"Candidato {candidato['name']} ya existe, saltando...")
                    continue
                
                # Obtener IDs de referencias
                political_position_id = get_political_position_id(candidato['legislative_position'])
                electoral_section_id = get_electoral_section_id(candidato['electoral_section'])
                
                # Insertar candidato
                cursor = conn.execute("""
                    INSERT INTO candidates (
                        name, full_name, description, legislative_position, 
                        electoral_section, district, political_party, 
                        list_number, list_position, importance_level, 
                        is_active, political_position_id, electoral_section_id,
                        created_utc, updated_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    candidato['name'],
                    candidato['full_name'],
                    candidato['description'],
                    candidato['legislative_position'],
                    candidato['electoral_section'],
                    candidato['district'],
                    candidato['political_party'],
                    candidato.get('list_number'),
                    candidato.get('list_position'),
                    candidato['importance_level'],
                    1,  # is_active
                    political_position_id,
                    electoral_section_id,
                    current_time,
                    current_time
                ))
                
                candidate_id = cursor.lastrowid
                
                # Insertar keywords en tabla separada
                for keyword in candidato['keywords']:
                    conn.execute("""
                        INSERT INTO candidate_keywords (
                            candidate_id, keyword, is_primary, created_utc, is_active
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        candidate_id,
                        keyword,
                        1 if keyword == candidato['keywords'][0] else 0,  # Primera keyword es primaria
                        current_time,
                        1
                    ))
                
                added_count += 1
                logger.info(f"Agregado candidato: {candidato['name']}")
            
            logger.info(f"Se agregaron {added_count} candidatos de ejemplo")
            
    except Exception as e:
        logger.error(f"Error agregando candidatos de ejemplo: {e}")
        raise
    finally:
        conn.close()

def show_candidates_summary():
    """Muestra un resumen de los candidatos en la base de datos."""
    conn = get_db_connection()
    
    try:
        with conn:
            # Contar candidatos por sección electoral
            cursor = conn.execute("""
                SELECT es.nombre, COUNT(c.id) as cantidad
                FROM electoral_sections es
                LEFT JOIN candidates c ON es.numero = c.electoral_section
                GROUP BY es.id, es.nombre
                ORDER BY es.numero
            """)
            
            print("\n" + "="*60)
            print("CANDIDATOS POR SECCIÓN ELECTORAL")
            print("="*60)
            
            for row in cursor.fetchall():
                print(f"📍 {row[0]}: {row[1]} candidatos")
            
            # Contar candidatos por cargo
            cursor = conn.execute("""
                SELECT legislative_position, COUNT(*) as cantidad
                FROM candidates
                GROUP BY legislative_position
                ORDER BY cantidad DESC
            """)
            
            print("\n🏛️  CANDIDATOS POR CARGO:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} candidatos")
            
            # Contar candidatos por partido
            cursor = conn.execute("""
                SELECT political_party, COUNT(*) as cantidad
                FROM candidates
                GROUP BY political_party
                ORDER BY cantidad DESC
            """)
            
            print("\n🎯 CANDIDATOS POR PARTIDO:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} candidatos")
            
            # Total de candidatos
            cursor = conn.execute("SELECT COUNT(*) FROM candidates")
            total = cursor.fetchone()[0]
            
            print(f"\n✅ Total de candidatos registrados: {total}")
            
    except Exception as e:
        logger.error(f"Error mostrando resumen de candidatos: {e}")
    finally:
        conn.close()

def main():
    """Función principal para agregar candidatos de ejemplo."""
    logger.info("Iniciando carga de candidatos de ejemplo")
    
    try:
        # Agregar candidatos de ejemplo
        add_sample_candidates()
        
        # Mostrar resumen
        show_candidates_summary()
        
        logger.info("Carga de candidatos de ejemplo completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en el proceso de carga de candidatos: {e}")
        raise

if __name__ == "__main__":
    main()
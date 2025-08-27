#!/usr/bin/env python3
"""
Script para recrear las personas basándose en los hits existentes.
"""

import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def recreate_persons():
    """Recrea las personas basándose en los keywords de los hits."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("=== RECREANDO PERSONAS ===")
    
    # Obtener todos los person_id únicos y sus keywords
    cursor.execute("""
        SELECT DISTINCT person_id, keyword
        FROM hits
        ORDER BY person_id, keyword
    """)
    
    hits_data = cursor.fetchall()
    logger.info(f"Encontrados {len(hits_data)} combinaciones person_id/keyword")
    
    # Agrupar keywords por person_id
    persons_data = {}
    for person_id, keyword in hits_data:
        if person_id not in persons_data:
            persons_data[person_id] = set()
        persons_data[person_id].add(keyword)
    
    logger.info(f"Encontrados {len(persons_data)} person_id únicos")
    
    # Recrear las personas
    for person_id, keywords in persons_data.items():
        # Usar el keyword más común o el primero alfabéticamente como nombre
        main_keyword = sorted(keywords)[0]  # Primer keyword alfabéticamente
        
        logger.info(f"Recreando persona {person_id}: {main_keyword} (keywords: {len(keywords)})")
        
        # Insertar la persona
        cursor.execute("""
            INSERT OR REPLACE INTO persons (id, name, full_name, description, importance_level, created_utc, updated_utc, is_active)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1)
        """, (person_id, main_keyword, main_keyword, '|'.join(sorted(keywords)), 5))
    
    conn.commit()
    
    # Verificar el resultado
    cursor.execute("SELECT id, name, description FROM persons ORDER BY id")
    persons = cursor.fetchall()
    
    logger.info(f"\n✅ Personas recreadas: {len(persons)}")
    for person_id, name, description in persons:
        logger.info(f"  {person_id}. {name} (keywords: {description})")
    
    conn.close()

def test_mentions_after_fix():
    """Prueba la búsqueda de menciones después de la corrección."""
    logger.info("\n=== PROBANDO BÚSQUEDA DESPUÉS DE LA CORRECCIÓN ===")
    
    from app.storage import search_mentions_fts
    
    mentions = search_mentions_fts('Milei', limit=5)
    logger.info(f"Encontradas {len(mentions)} menciones con 'Milei'")
    
    for i, mention in enumerate(mentions, 1):
        logger.info(f"  {i}. {mention[8]} ({mention[1]}) - Score: {mention[3]:.2f}")
        logger.info(f"     [{mention[5]}] {mention[4][:50]}...")

def main():
    """Función principal."""
    logger.info("Iniciando corrección de personas...")
    
    recreate_persons()
    test_mentions_after_fix()
    
    logger.info("\n✅ Corrección completada.")

if __name__ == "__main__":
    main()
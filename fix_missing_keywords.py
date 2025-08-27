#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection
from datetime import datetime

def add_missing_keywords():
    """Agregar keywords faltantes para candidatos que tienen menciones pero no keywords."""
    conn = get_db_connection()
    current_time = datetime.utcnow().isoformat()
    
    try:
        with conn:
            # Agregar keywords para Javier Milei (ID: 1)
            print("Agregando keywords para Javier Milei...")
            conn.execute("""
                INSERT INTO candidate_keywords (candidate_id, keyword, is_primary, created_utc, is_active)
                VALUES (1, 'Javier Milei', 1, ?, 1)
            """, (current_time,))
            
            conn.execute("""
                INSERT INTO candidate_keywords (candidate_id, keyword, is_primary, created_utc, is_active)
                VALUES (1, 'Milei', 0, ?, 1)
            """, (current_time,))
            
            # Agregar keywords para Oscar Liberman (ID: 2)
            print("Agregando keywords para Oscar Liberman...")
            conn.execute("""
                INSERT INTO candidate_keywords (candidate_id, keyword, is_primary, created_utc, is_active)
                VALUES (2, 'Oscar Liberman', 1, ?, 1)
            """, (current_time,))
            
            conn.execute("""
                INSERT INTO candidate_keywords (candidate_id, keyword, is_primary, created_utc, is_active)
                VALUES (2, 'Liberman', 0, ?, 1)
            """, (current_time,))
            
            # Agregar keywords para Andres de Leo (ID: 3)
            print("Agregando keywords para Andres de Leo...")
            conn.execute("""
                INSERT INTO candidate_keywords (candidate_id, keyword, is_primary, created_utc, is_active)
                VALUES (3, 'Andres de Leo', 1, ?, 1)
            """, (current_time,))
            
            conn.execute("""
                INSERT INTO candidate_keywords (candidate_id, keyword, is_primary, created_utc, is_active)
                VALUES (3, 'de Leo', 0, ?, 1)
            """, (current_time,))
            
            print("Keywords agregadas exitosamente!")
            
    except Exception as e:
        print(f"Error agregando keywords: {e}")
    finally:
        conn.close()

def verify_keywords():
    """Verificar que las keywords se agregaron correctamente."""
    conn = get_db_connection()
    
    print("\n=== VERIFICACIÓN DE KEYWORDS AGREGADAS ===")
    cursor = conn.execute("""
        SELECT c.name, ck.keyword, ck.is_primary
        FROM candidates c
        JOIN candidate_keywords ck ON c.id = ck.candidate_id
        WHERE c.id IN (1, 2, 3) AND ck.is_active = 1
        ORDER BY c.name, ck.is_primary DESC
    """)
    
    current_candidate = None
    for row in cursor:
        candidate_name, keyword, is_primary = row
        if current_candidate != candidate_name:
            print(f"\n{candidate_name}:")
            current_candidate = candidate_name
        
        primary_text = " (PRIMARIA)" if is_primary else ""
        print(f"  - {keyword}{primary_text}")
    
    conn.close()

if __name__ == "__main__":
    add_missing_keywords()
    verify_keywords()
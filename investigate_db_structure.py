#!/usr/bin/env python3
"""
Script para investigar la estructura de la base de datos y el problema con los hits.
"""

import sqlite3
from app.storage import get_db_connection

def investigate_db_structure():
    print("=== INVESTIGACIÓN DE ESTRUCTURA DE BASE DE DATOS ===")
    
    conn = get_db_connection()
    
    # 1. Listar todas las tablas
    print("\n1. TABLAS EXISTENTES:")
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        print(f"  - {table}")
    
    # 2. Estructura de candidate_keywords
    if 'candidate_keywords' in tables:
        print("\n2. ESTRUCTURA DE candidate_keywords:")
        cursor = conn.execute("PRAGMA table_info(candidate_keywords)")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        # Contenido de candidate_keywords
        print("\n3. CONTENIDO DE candidate_keywords (primeros 10):")
        cursor = conn.execute("SELECT * FROM candidate_keywords LIMIT 10")
        for row in cursor.fetchall():
            print(f"  {row}")
    
    # 3. Estructura de person_keywords (si existe)
    if 'person_keywords' in tables:
        print("\n4. ESTRUCTURA DE person_keywords:")
        cursor = conn.execute("PRAGMA table_info(person_keywords)")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        # Contenido de person_keywords
        print("\n5. CONTENIDO DE person_keywords (primeros 10):")
        cursor = conn.execute("SELECT * FROM person_keywords LIMIT 10")
        for row in cursor.fetchall():
            print(f"  {row}")
    else:
        print("\n4. TABLA person_keywords NO EXISTE")
    
    # 4. Estructura de hits
    if 'hits' in tables:
        print("\n6. ESTRUCTURA DE hits:")
        cursor = conn.execute("PRAGMA table_info(hits)")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        # Contenido de hits
        print("\n7. CONTENIDO DE hits (últimos 5):")
        cursor = conn.execute("SELECT * FROM hits ORDER BY detected_utc DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        # Contar hits totales
        cursor = conn.execute("SELECT COUNT(*) FROM hits")
        total_hits = cursor.fetchone()[0]
        print(f"\n8. TOTAL DE HITS: {total_hits}")
    
    # 5. Verificar si hay hits para Diego Santilli
    print("\n9. HITS PARA 'Diego Santilli':")
    cursor = conn.execute("SELECT * FROM hits WHERE keyword = 'Diego Santilli' ORDER BY detected_utc DESC LIMIT 5")
    santilli_hits = cursor.fetchall()
    if santilli_hits:
        for hit in santilli_hits:
            print(f"  {hit}")
    else:
        print("  No se encontraron hits para 'Diego Santilli'")
    
    # 6. Verificar la relación entre candidate_keywords y hits
    print("\n10. VERIFICACIÓN DE RELACIÓN candidate_keywords -> hits:")
    cursor = conn.execute("""
        SELECT ck.candidate_id, ck.keyword, COUNT(h.id) as hit_count
        FROM candidate_keywords ck
        LEFT JOIN hits h ON ck.keyword = h.keyword
        WHERE ck.is_active = 1
        GROUP BY ck.candidate_id, ck.keyword
        ORDER BY hit_count DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        candidate_id, keyword, hit_count = row
        print(f"  Candidato {candidate_id}, keyword '{keyword}': {hit_count} hits")
    
    # 7. Verificar si existe la columna person_id en hits
    print("\n11. VERIFICACIÓN DE COLUMNA person_id EN hits:")
    cursor = conn.execute("PRAGMA table_info(hits)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'person_id' in columns:
        print("  ✓ Columna person_id existe en hits")
        
        # Verificar valores de person_id
        cursor = conn.execute("SELECT DISTINCT person_id FROM hits WHERE person_id IS NOT NULL LIMIT 10")
        person_ids = cursor.fetchall()
        print(f"  person_ids encontrados: {[row[0] for row in person_ids]}")
    else:
        print("  ✗ Columna person_id NO existe en hits")
    
    conn.close()
    print("\n=== INVESTIGACIÓN COMPLETADA ===")

if __name__ == '__main__':
    investigate_db_structure()
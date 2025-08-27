#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection

def check_hits_structure():
    """Verificar la estructura de la tabla hits."""
    conn = get_db_connection()
    
    print("=== ESTRUCTURA DE TABLA HITS ===")
    cursor = conn.execute('PRAGMA table_info(hits)')
    for row in cursor:
        print(f"  {row[1]} ({row[2]})")
    
    print("\n=== EJEMPLO DE DATOS EN HITS ===")
    cursor = conn.execute('SELECT * FROM hits LIMIT 3')
    for row in cursor:
        print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    check_hits_structure()
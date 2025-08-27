#!/usr/bin/env python3
"""
Script para verificar candidatos activos
"""

import sqlite3
import os

def check_candidates():
    """Verificar candidatos en la base de datos correcta"""
    db_file = 'data/mentions.db'
    
    if not os.path.exists(db_file):
        print(f"Archivo {db_file} no encontrado")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        
        # Verificar estructura de la tabla candidates
        print("=== ESTRUCTURA DE LA TABLA CANDIDATES ===")
        cursor = conn.execute("PRAGMA table_info(candidates)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Columna: {col[1]}, Tipo: {col[2]}, Not Null: {col[3]}, Default: {col[4]}, PK: {col[5]}")
        
        # Obtener candidatos activos
        print("\n=== CANDIDATOS ACTIVOS ===")
        cursor = conn.execute("""
            SELECT id, name, is_active
            FROM candidates 
            WHERE is_active = 1
            ORDER BY id
        """)
        
        active_candidates = cursor.fetchall()
        
        if active_candidates:
            for candidate in active_candidates:
                print(f"ID: {candidate[0]}, Nombre: {candidate[1]}, Activo: {candidate[2]}")
        else:
            print("No hay candidatos activos")
        
        print(f"\nTotal candidatos activos: {len(active_candidates)}")
        
        # Obtener candidatos inactivos
        print("\n=== CANDIDATOS INACTIVOS ===")
        cursor = conn.execute("""
            SELECT id, name, is_active
            FROM candidates 
            WHERE is_active = 0
            ORDER BY id
        """)
        
        inactive_candidates = cursor.fetchall()
        
        if inactive_candidates:
            for candidate in inactive_candidates:
                print(f"ID: {candidate[0]}, Nombre: {candidate[1]}, Activo: {candidate[2]}")
        else:
            print("No hay candidatos inactivos")
        
        print(f"\nTotal candidatos inactivos: {len(inactive_candidates)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error al acceder a {db_file}: {e}")

if __name__ == "__main__":
    check_candidates()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from app.config import config

def test_web_db_connection():
    print("=== Prueba de Conexión de Base de Datos Web ===")
    print(f"Configuración SQLITE_PATH: {config['SQLITE_PATH']}")
    print(f"Ruta absoluta: {os.path.abspath(config['SQLITE_PATH'])}")
    print(f"¿Archivo existe?: {os.path.exists(config['SQLITE_PATH'])}")
    
    try:
        conn = get_db_connection()
        print("✅ Conexión exitosa")
        
        # Verificar estructura de la tabla candidates
        cursor = conn.execute("PRAGMA table_info(candidates)")
        columns = cursor.fetchall()
        print("\n📋 Estructura de la tabla 'candidates':")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verificar candidatos activos
        cursor = conn.execute("SELECT id, name, is_active FROM candidates ORDER BY id")
        candidates = cursor.fetchall()
        print("\n👥 Candidatos en la base de datos:")
        for candidate in candidates:
            status = "✅ Activo" if candidate[2] == 1 else "❌ Inactivo"
            print(f"  ID: {candidate[0]} | {candidate[1]} | {status}")
        
        # Verificar si hay candidatos activos para eliminar
        cursor = conn.execute("SELECT COUNT(*) FROM candidates WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        print(f"\n📊 Total candidatos activos: {active_count}")
        
        if active_count > 0:
            print("\n🎯 Candidatos disponibles para eliminar:")
            cursor = conn.execute("SELECT id, name FROM candidates WHERE is_active = 1 LIMIT 3")
            for candidate in cursor.fetchall():
                print(f"  - ID: {candidate[0]} | Nombre: {candidate[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_web_db_connection()
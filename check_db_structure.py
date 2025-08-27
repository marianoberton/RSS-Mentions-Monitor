#!/usr/bin/env python3
import sqlite3
import sys

def check_database_structure():
    """Verifica la estructura de la base de datos."""
    try:
        conn = sqlite3.connect('data/mentions.db')
        
        # Listar todas las tablas
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("Tablas en la base de datos:")
        for table in tables:
            print(f"- {table}")
        
        # Si existe la tabla candidates, mostrar su estructura
        if 'candidates' in tables:
            print("\nEstructura de la tabla candidates:")
            cursor = conn.execute("PRAGMA table_info(candidates)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PK' if col[5] else ''}")
        else:
            print("\n⚠️  La tabla 'candidates' no existe")
            
        # Verificar si existen las nuevas tablas
        for table_name in ['electoral_sections', 'political_positions']:
            if table_name in tables:
                print(f"\n✅ Tabla '{table_name}' existe")
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   Registros: {count}")
            else:
                print(f"\n❌ Tabla '{table_name}' no existe")
        
        conn.close()
        
    except Exception as e:
        print(f"Error verificando la base de datos: {e}")
        return False
    
    return True

if __name__ == '__main__':
    check_database_structure()
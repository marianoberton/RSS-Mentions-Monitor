import sqlite3
import os
import sys

# Configurar el path para importar los módulos de la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config

def enable_wal_mode():
    """Habilita el modo WAL (Write-Ahead Logging) en la base de datos SQLite.
    
    El modo WAL permite múltiples lecturas y una escritura concurrente,
    lo que reduce significativamente los bloqueos de la base de datos.
    """
    db_path = config.get("SQLITE_PATH", "data/mentions.db")
    
    # Verificar que la base de datos existe
    if not os.path.exists(db_path):
        print(f"Error: La base de datos {db_path} no existe.")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        
        # Habilitar el modo WAL
        conn.execute("PRAGMA journal_mode=WAL;")
        
        # Verificar que se haya habilitado correctamente
        cursor = conn.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        
        # Configurar otros parámetros para mejorar el rendimiento
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA mmap_size=30000000000;")
        
        # Cerrar la conexión
        conn.close()
        
        print(f"Modo de journal actual: {mode}")
        if mode.upper() == "WAL":
            print("El modo WAL se ha habilitado correctamente.")
            print("Esto debería reducir significativamente los bloqueos de la base de datos.")
            return True
        else:
            print(f"Error: No se pudo habilitar el modo WAL. Modo actual: {mode}")
            return False
    except Exception as e:
        print(f"Error al habilitar el modo WAL: {e}")
        return False

def optimize_database():
    """Realiza optimizaciones adicionales en la base de datos."""
    db_path = config.get("SQLITE_PATH", "data/mentions.db")
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        
        # Ejecutar VACUUM para compactar la base de datos
        print("Ejecutando VACUUM para compactar la base de datos...")
        conn.execute("VACUUM;")
        
        # Analizar la base de datos para optimizar las consultas
        print("Analizando la base de datos para optimizar las consultas...")
        conn.execute("ANALYZE;")
        
        # Cerrar la conexión
        conn.close()
        
        print("Optimización de la base de datos completada.")
        return True
    except Exception as e:
        print(f"Error al optimizar la base de datos: {e}")
        return False

if __name__ == "__main__":
    print("=== Habilitando modo WAL en la base de datos SQLite ===")
    print(f"Ruta de la base de datos: {config.get('SQLITE_PATH', 'data/mentions.db')}")
    if enable_wal_mode():
        print("\n=== Optimizando la base de datos ===")
        optimize_database()
        print("\nLa base de datos ha sido configurada para un mejor rendimiento con operaciones concurrentes.")
        print("Ahora debería experimentar menos bloqueos durante el procesamiento de artículos.")
    else:
        print("\nNo se pudo habilitar el modo WAL. Por favor, verifique que no haya conexiones activas a la base de datos.")
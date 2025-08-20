import os
import sys
import sqlite3

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.storage import init_db

# Ruta de la base de datos
db_path = config["SQLITE_PATH"]

# Verificar si el archivo existe
if os.path.exists(db_path):
    # Eliminar el archivo
    os.remove(db_path)
    print(f"Base de datos eliminada: {db_path}")
else:
    print(f"La base de datos no existe: {db_path}")

# Inicializar una nueva base de datos vacía
init_db()
print("Nueva base de datos inicializada correctamente.")

# Verificar que las tablas estén vacías
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM articles")
articles_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM hits")
hits_count = cursor.fetchone()[0]

print(f"\nEstadísticas de la nueva base de datos:")
print(f"Total de artículos: {articles_count}")
print(f"Total de menciones: {hits_count}")

conn.close()
print("\n✅ Base de datos limpiada correctamente")
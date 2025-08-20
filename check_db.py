#!/usr/bin/env python3
import sqlite3
import os

def check_database():
    db_file = 'data/mentions.db'
    
    if not os.path.exists(db_file):
        print(f"❌ Base de datos {db_file} no existe")
        return
    
    print(f"✅ Base de datos {db_file} encontrada")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Verificar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n📊 Tablas en la base de datos: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Si existe la tabla articles, mostrar algunos datos
    if any('articles' in table for table in tables):
        print("\n📰 Datos en tabla articles:")
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        print(f"  Total artículos: {count}")
        
        if count > 0:
            cursor.execute("SELECT site, COUNT(*) FROM articles GROUP BY site")
            sites = cursor.fetchall()
            print("  Por sitio:")
            for site, site_count in sites:
                print(f"    {site}: {site_count}")
    
    # Si existe la tabla hits, mostrar algunos datos
    if any('hits' in table for table in tables):
        print("\n🎯 Datos en tabla hits:")
        cursor.execute("SELECT COUNT(*) FROM hits")
        count = cursor.fetchone()[0]
        print(f"  Total menciones: {count}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
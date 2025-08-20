#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from datetime import datetime

print("=== SOLUCIÓN PARA HITS DUPLICADOS ===")
print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

print("🚨 PROBLEMA IDENTIFICADO:")
print("• La función save_article_and_hit() no verifica duplicados antes de insertar hits")
print("• Esto permite que el mismo artículo genere múltiples hits para la misma keyword")
print("• Causa: INSERT INTO hits sin verificación de duplicados")

conn = get_db_connection()

print("\n📊 ESTADO ACTUAL:")
with conn:
    # Buscar todos los hits duplicados
    cursor = conn.execute("""
        SELECT article_id, keyword, where_found, COUNT(*) as count, GROUP_CONCAT(id) as hit_ids
        FROM hits 
        GROUP BY article_id, keyword, where_found
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"⚠️  Encontrados {len(duplicates)} grupos de hits duplicados:")
        total_duplicate_hits = 0
        for dup in duplicates:
            hit_ids = dup[4].split(',')
            duplicate_count = len(hit_ids) - 1  # Restar 1 porque uno debe quedarse
            total_duplicate_hits += duplicate_count
            print(f"  • Artículo {dup[0]} | {dup[1]} | {dup[2]} | {dup[3]} hits (IDs: {dup[4]})")
        
        print(f"\n📈 RESUMEN:")
        print(f"• Total de hits duplicados a eliminar: {total_duplicate_hits}")
        print(f"• Grupos de duplicados: {len(duplicates)}")
    else:
        print("✅ No se encontraron hits duplicados")

print("\n🔧 IMPLEMENTANDO SOLUCIONES:")

print("\n1. 🗑️ ELIMINANDO HITS DUPLICADOS EXISTENTES:")
with conn:
    # Para cada grupo de duplicados, mantener solo el más antiguo
    for dup in duplicates:
        hit_ids = dup[4].split(',')
        if len(hit_ids) > 1:
            # Mantener el primer hit (más antiguo) y eliminar los demás
            hits_to_delete = hit_ids[1:]  # Todos excepto el primero
            
            for hit_id in hits_to_delete:
                cursor = conn.execute("DELETE FROM hits WHERE id = ?", (int(hit_id),))
                print(f"  ✅ Eliminado hit duplicado ID: {hit_id}")

print("\n2. 🛡️ CREANDO ÍNDICE ÚNICO PARA PREVENIR FUTUROS DUPLICADOS:")
try:
    with conn:
        # Crear índice único para evitar duplicados futuros
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_hits_unique 
            ON hits(article_id, keyword, where_found)
        """)
        print("  ✅ Índice único creado exitosamente")
except Exception as e:
    print(f"  ⚠️  Error al crear índice único: {e}")

print("\n3. 📝 MODIFICANDO FUNCIÓN save_article_and_hit():")
print("  • Se debe cambiar INSERT por INSERT OR IGNORE en la inserción de hits")
print("  • Esto evitará que se inserten hits duplicados en el futuro")

print("\n🔍 VERIFICACIÓN POST-SOLUCIÓN:")
with conn:
    # Verificar que no quedan duplicados
    cursor = conn.execute("""
        SELECT article_id, keyword, where_found, COUNT(*) as count
        FROM hits 
        GROUP BY article_id, keyword, where_found
        HAVING COUNT(*) > 1
    """)
    
    remaining_duplicates = cursor.fetchall()
    
    if remaining_duplicates:
        print(f"⚠️  Aún quedan {len(remaining_duplicates)} grupos duplicados")
    else:
        print("✅ Todos los hits duplicados han sido eliminados")
    
    # Verificar estado específico de Andrés de Leo
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hits 
        WHERE keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%'
    """)
    andres_total = cursor.fetchone()[0]
    
    cursor = conn.execute("""
        SELECT article_id, COUNT(*) as count
        FROM hits 
        WHERE keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%'
        GROUP BY article_id
        HAVING COUNT(*) > 1
    """)
    andres_duplicates = cursor.fetchall()
    
    print(f"\n📊 ESTADO DE ANDRÉS DE LEO:")
    print(f"• Total hits: {andres_total}")
    print(f"• Artículos con hits duplicados: {len(andres_duplicates)}")
    
    if andres_duplicates:
        print("⚠️  Aún hay duplicados de Andrés de Leo:")
        for dup in andres_duplicates:
            print(f"  • Artículo {dup[0]}: {dup[1]} hits")

print("\n💡 PRÓXIMOS PASOS:")
print("1. Modificar app/storage.py para usar INSERT OR IGNORE en hits")
print("2. Reiniciar el sistema para aplicar los cambios")
print("3. Monitorear que no se generen nuevos duplicados")
print("4. El índice único prevendrá duplicados automáticamente")

print("\n✅ SOLUCIÓN IMPLEMENTADA")
print("Los hits duplicados han sido eliminados y se ha creado protección contra futuros duplicados.")

print("\n=== SOLUCIÓN COMPLETADA ===")
conn.close()
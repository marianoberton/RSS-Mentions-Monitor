#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la función de eliminar duplicados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import remove_duplicate_hits, get_detailed_stats

def test_remove_duplicates():
    print("🧪 Probando función de eliminar duplicados...")
    
    # Primero obtener estadísticas detalladas
    print("\n📊 Estadísticas antes de la limpieza:")
    stats = get_detailed_stats()
    print(f"- Total de hits: {stats['total_hits']}")
    print(f"- Grupos duplicados: {stats['duplicate_groups']}")
    
    # Intentar eliminar duplicados
    print("\n🗑️ Ejecutando eliminación de duplicados...")
    result = remove_duplicate_hits()
    
    print(f"\n✅ Resultado:")
    print(f"- Éxito: {result['success']}")
    print(f"- Mensaje: {result['message']}")
    print(f"- Duplicados encontrados: {result['duplicates_found']}")
    print(f"- Grupos procesados: {result['groups_processed']}")
    print(f"- Hits eliminados: {result['hits_removed']}")
    
    # Estadísticas después
    if result['success'] and result['hits_removed'] > 0:
        print("\n📊 Estadísticas después de la limpieza:")
        stats_after = get_detailed_stats()
        print(f"- Total de hits: {stats_after['total_hits']}")
        print(f"- Grupos duplicados: {stats_after['duplicate_groups']}")
        print(f"- Diferencia: {stats['total_hits'] - stats_after['total_hits']} hits eliminados")
    
    return result['success']

if __name__ == "__main__":
    try:
        success = test_remove_duplicates()
        if success:
            print("\n🎉 Prueba completada exitosamente")
        else:
            print("\n❌ La prueba falló")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error durante la prueba: {e}")
        sys.exit(1)
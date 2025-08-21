#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificación para confirmar que los problemas del dashboard están solucionados.
Ejecuta este script después del redespliegue para verificar el estado del sistema.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_global_stats, get_hourly_stats, get_db_connection
from app.config import config
from datetime import datetime

def verificar_estadisticas():
    """Verifica que las estadísticas se calculen correctamente."""
    print("=== VERIFICACIÓN DE ESTADÍSTICAS ===")
    
    # Estadísticas globales
    print("\n📊 ESTADÍSTICAS GLOBALES:")
    stats_global = get_global_stats()
    for key, value in stats_global.items():
        print(f"  {key}: {value:,}")
    
    # Estadísticas horarias
    print("\n⏰ ESTADÍSTICAS ÚLTIMA HORA:")
    stats_hourly = get_hourly_stats()
    for key, value in stats_hourly.items():
        print(f"  {key}: {value:,}")
    
    # Verificar que total_hits existe y es > 0
    if stats_global['total_hits'] > 0:
        print(f"\n✅ PROBLEMA SOLUCIONADO: Dashboard mostrará {stats_global['total_hits']:,} menciones totales")
    else:
        print("\n❌ PROBLEMA PERSISTE: No hay menciones en la base de datos")
    
    return stats_global, stats_hourly

def verificar_andres_de_leo():
    """Verifica las menciones específicas de Andres de Leo."""
    print("\n=== VERIFICACIÓN ANDRES DE LEO ===")
    
    conn = get_db_connection()
    with conn:
        # Contar menciones totales de Andres de Leo
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits 
            WHERE keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%'
        """)
        total_andres = cursor.fetchone()[0]
        
        # Obtener algunas menciones recientes
        cursor = conn.execute("""
            SELECT h.keyword, h.detected_utc, a.title, a.site
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            WHERE h.keyword LIKE '%Andres de Leo%' OR h.keyword LIKE '%Andrés de Leo%'
            ORDER BY h.detected_utc DESC
            LIMIT 5
        """)
        recent_andres = cursor.fetchall()
    
    print(f"📈 Total menciones Andres de Leo: {total_andres:,}")
    
    if recent_andres:
        print("\n📰 MENCIONES RECIENTES:")
        for keyword, detected, title, site in recent_andres:
            print(f"  • {detected} | {keyword} | {site}")
            print(f"    {title[:60]}...")
    
    if total_andres > 0:
        print(f"\n✅ CONFIGURACIÓN CORRECTA: Andres de Leo tiene {total_andres} menciones registradas")
    else:
        print("\n⚠️  Sin menciones de Andres de Leo encontradas")
    
    return total_andres

def verificar_keywords_config():
    """Verifica la configuración de keywords."""
    print("\n=== VERIFICACIÓN CONFIGURACIÓN KEYWORDS ===")
    
    keywords = config.get('keywords', [])
    print(f"📝 Keywords configuradas: {len(keywords)}")
    
    for keyword in keywords:
        if isinstance(keyword, dict):
            if keyword.get('category') == 'important':
                print(f"  🔥 IMPORTANTE: {keyword.get('terms', [])}")
            else:
                print(f"  📊 ESTÁNDAR: {keyword.get('terms', [])}")
        else:
            print(f"  📊 {keyword}")
    
    # Verificar si Andres de Leo está en importantes
    important_found = False
    for keyword in keywords:
        if isinstance(keyword, dict) and keyword.get('category') == 'important':
            terms = keyword.get('terms', [])
            if any('Andres de Leo' in str(term) or 'Andrés de Leo' in str(term) for term in terms):
                important_found = True
                break
    
    if important_found:
        print("\n✅ CONFIGURACIÓN CORRECTA: Andres de Leo está en notificaciones importantes")
    else:
        print("\n⚠️  Verificar: Andres de Leo podría no estar en notificaciones importantes")
    
    return keywords

def verificar_base_datos():
    """Verifica el estado general de la base de datos."""
    print("\n=== VERIFICACIÓN BASE DE DATOS ===")
    
    conn = get_db_connection()
    with conn:
        # Contar tablas principales
        cursor = conn.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM hits")
        total_hits = cursor.fetchone()[0]
        
        # Artículos por estado de procesamiento
        cursor = conn.execute("SELECT content_processed, COUNT(*) FROM articles GROUP BY content_processed")
        processing_stats = cursor.fetchall()
        
        # Keywords más mencionadas
        cursor = conn.execute("""
            SELECT keyword, COUNT(*) as count 
            FROM hits 
            GROUP BY keyword 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_keywords = cursor.fetchall()
    
    print(f"📚 Total artículos: {total_articles:,}")
    print(f"🎯 Total menciones: {total_hits:,}")
    
    print("\n📊 ESTADO PROCESAMIENTO:")
    for status, count in processing_stats:
        status_name = {0: "Pendiente", 1: "Exitoso", 2: "Fallido"}.get(status, f"Estado {status}")
        print(f"  {status_name}: {count:,} artículos")
    
    print("\n🏆 TOP KEYWORDS:")
    for keyword, count in top_keywords:
        print(f"  {keyword}: {count:,} menciones")
    
    return total_articles, total_hits

def main():
    """Función principal de verificación."""
    print(f"🔍 VERIFICACIÓN DEL SISTEMA RSS MENTIONS MONITOR")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Verificar estadísticas
        stats_global, stats_hourly = verificar_estadisticas()
        
        # Verificar Andres de Leo
        andres_mentions = verificar_andres_de_leo()
        
        # Verificar configuración
        keywords = verificar_keywords_config()
        
        # Verificar base de datos
        total_articles, total_hits = verificar_base_datos()
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📋 RESUMEN DE VERIFICACIÓN")
        print("=" * 60)
        
        print(f"✅ Total menciones en dashboard: {stats_global['total_hits']:,}")
        print(f"✅ Menciones Andres de Leo: {andres_mentions:,}")
        print(f"✅ Artículos procesados: {total_articles:,}")
        print(f"✅ Tasa de éxito: {stats_global['success_rate']:.1f}%")
        
        # Verificar problemas específicos
        problemas_solucionados = 0
        total_problemas = 2
        
        if stats_global['total_hits'] > 0:
            print("✅ PROBLEMA 1 SOLUCIONADO: Dashboard muestra menciones correctamente")
            problemas_solucionados += 1
        else:
            print("❌ PROBLEMA 1 PERSISTE: Dashboard sigue mostrando 0 menciones")
        
        if andres_mentions > 0:
            print("✅ PROBLEMA 2 SOLUCIONADO: Andres de Leo tiene menciones registradas")
            problemas_solucionados += 1
        else:
            print("❌ PROBLEMA 2 PERSISTE: No hay menciones de Andres de Leo")
        
        print(f"\n🎯 ESTADO FINAL: {problemas_solucionados}/{total_problemas} problemas solucionados")
        
        if problemas_solucionados == total_problemas:
            print("🎉 ¡TODOS LOS PROBLEMAS HAN SIDO SOLUCIONADOS!")
        else:
            print("⚠️  Algunos problemas requieren atención adicional")
            
    except Exception as e:
        print(f"❌ ERROR durante la verificación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
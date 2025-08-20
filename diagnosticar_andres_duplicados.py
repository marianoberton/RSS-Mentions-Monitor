#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection, get_important_hits
from datetime import datetime, timedelta

print("=== DIAGNÓSTICO: DUPLICADOS ANDRÉS DE LEO ===")
print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

# Conectar a la base de datos
conn = get_db_connection()

print("📊 ESTADÍSTICAS GENERALES:")
with conn:
    # Total de menciones de Andrés de Leo
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hits 
        WHERE keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%'
    """)
    total_andres = cursor.fetchone()[0]
    
    # Menciones pendientes (no enviadas)
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hits 
        WHERE (keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%') 
        AND notification_sent = 0
    """)
    pending_andres = cursor.fetchone()[0]
    
    # Menciones ya enviadas
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hits 
        WHERE (keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%') 
        AND notification_sent = 1
    """)
    sent_andres = cursor.fetchone()[0]
    
    print(f"• Total menciones Andrés de Leo: {total_andres}")
    print(f"• Notificaciones pendientes: {pending_andres}")
    print(f"• Notificaciones ya enviadas: {sent_andres}")

print("\n🔍 MENCIONES RECIENTES (últimas 24 horas):")
with conn:
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    cursor = conn.execute("""
        SELECT h.id, h.keyword, h.where_found, h.detected_utc, h.notification_sent, a.title, a.site
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        WHERE (h.keyword LIKE '%Andres de Leo%' OR h.keyword LIKE '%Andrés de Leo%')
        AND h.detected_utc > ?
        ORDER BY h.detected_utc DESC
    """, (yesterday,))
    
    recent_hits = cursor.fetchall()
    
    if recent_hits:
        print(f"Encontradas {len(recent_hits)} menciones recientes:")
        for hit in recent_hits:
            status = "✅ ENVIADA" if hit[4] == 1 else "⏳ PENDIENTE"
            print(f"  • ID: {hit[0]} | {status} | {hit[1]} | {hit[5][:50]}...")
    else:
        print("No hay menciones recientes de Andrés de Leo")

print("\n🎯 VERIFICACIÓN CON get_important_hits():")
try:
    hits = get_important_hits(24)
    andres_hits = hits.get('andres_de_leo', [])
    print(f"• Menciones detectadas por get_important_hits: {len(andres_hits)}")
    
    if andres_hits:
        print("Detalles de menciones pendientes:")
        for i, hit in enumerate(andres_hits[:5]):  # Mostrar máximo 5
            print(f"  {i+1}. ID: {hit['id']} | {hit['title'][:50]}...")
except Exception as e:
    print(f"❌ Error al ejecutar get_important_hits: {e}")

print("\n🚨 POSIBLES CAUSAS DE DUPLICADOS:")
print("1. Menciones con notification_sent = 0 (no marcadas como enviadas)")
print("2. Error en la función mark_notification_sent()")
print("3. Múltiples ejecuciones simultáneas del sistema")
print("4. Problema en la lógica de filtrado de get_important_hits()")

print("\n🔧 VERIFICACIÓN DE INTEGRIDAD:")
with conn:
    # Verificar si hay menciones duplicadas en la misma hora
    cursor = conn.execute("""
        SELECT a.title, COUNT(*) as count
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        WHERE (h.keyword LIKE '%Andres de Leo%' OR h.keyword LIKE '%Andrés de Leo%')
        GROUP BY a.title
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"⚠️  Encontrados {len(duplicates)} artículos con múltiples hits:")
        for dup in duplicates[:5]:
            print(f"  • '{dup[0][:50]}...' - {dup[1]} hits")
    else:
        print("✅ No hay artículos duplicados")

print("\n💡 RECOMENDACIONES:")
if pending_andres > 0:
    print(f"• Hay {pending_andres} menciones pendientes que se enviarán")
    print("• Esto podría causar notificaciones múltiples")
    print("• Considera marcar las menciones existentes como enviadas")
else:
    print("• No hay menciones pendientes")
    print("• El problema podría estar en la detección de nuevas menciones")

print("\n=== DIAGNÓSTICO COMPLETADO ===")
conn.close()
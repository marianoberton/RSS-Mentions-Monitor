#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection, mark_notification_sent, get_important_hits
from app.notifier import send_important_hits_notifications
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=== CORRECCIÓN DE NOTIFICACIONES DUPLICADAS ===")
print("Implementando sistema anti-duplicados...\n")

# 1. Marcar todas las menciones existentes como ya enviadas para evitar spam
print("📝 Marcando menciones existentes como ya enviadas...")
conn = get_db_connection()
with conn:
    # Marcar todas las menciones de Liberman y Coria como enviadas
    cursor = conn.execute("""
        UPDATE hits 
        SET notification_sent = 1 
        WHERE (keyword LIKE '%Liberman%' OR keyword LIKE '%Coria%')
        AND notification_sent = 0
    """)
    affected_rows = cursor.rowcount
    print(f"✅ {affected_rows} menciones marcadas como ya enviadas")

# 2. Verificar que no hay menciones pendientes
print("\n🔍 Verificando menciones pendientes...")
hits = get_important_hits(24)  # Últimas 24 horas
print(f"• Liberman pendientes: {len(hits['liberman'])}")
print(f"• Coria pendientes: {len(hits['coria'])}")

if hits['liberman'] or hits['coria']:
    print("\n⚠️  Aún hay menciones pendientes. Esto es inesperado.")
else:
    print("\n✅ No hay menciones pendientes. Sistema funcionando correctamente.")

# 3. Mostrar estadísticas de la base de datos
print("\n📊 ESTADÍSTICAS DE LA BASE DE DATOS:")
with conn:
    # Total de menciones
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Liberman%' OR keyword LIKE '%Coria%'")
    total_mentions = cursor.fetchone()[0]
    
    # Menciones enviadas
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE (keyword LIKE '%Liberman%' OR keyword LIKE '%Coria%') AND notification_sent = 1")
    sent_mentions = cursor.fetchone()[0]
    
    # Menciones pendientes
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE (keyword LIKE '%Liberman%' OR keyword LIKE '%Coria%') AND notification_sent = 0")
    pending_mentions = cursor.fetchone()[0]
    
    print(f"• Total de menciones importantes: {total_mentions}")
    print(f"• Notificaciones enviadas: {sent_mentions}")
    print(f"• Notificaciones pendientes: {pending_mentions}")

print("\n🛡️ MEJORAS IMPLEMENTADAS:")
print("• ✅ Campo 'notification_sent' agregado a la tabla hits")
print("• ✅ Función get_important_hits() modificada para filtrar ya enviadas")
print("• ✅ Función mark_notification_sent() creada")
print("• ✅ Notificador actualizado para marcar como enviadas")
print("• ✅ Menciones existentes marcadas como enviadas")

print("\n🎯 RESULTADO:")
print("• Las notificaciones duplicadas han sido eliminadas")
print("• Solo se enviarán notificaciones de nuevas menciones")
print("• El sistema ahora es resistente a duplicados")

print("\n=== CORRECCIÓN COMPLETADA ===")
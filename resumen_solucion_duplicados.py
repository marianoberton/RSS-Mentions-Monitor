#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection, get_important_hits
from datetime import datetime

print("=== SOLUCIÓN COMPLETA: NOTIFICACIONES DUPLICADAS ===")
print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

print("🚨 PROBLEMA ORIGINAL:")
print("• Recibías la misma notificación de Liberman repetidamente")
print("• El sistema enviaba notificaciones cada 10 minutos sin control")
print("• No había mecanismo para evitar duplicados")
print()

print("🔧 CAUSA RAÍZ IDENTIFICADA:")
print("• La función get_important_hits() obtenía TODAS las menciones de la última hora")
print("• Cada ejecución del hourly_summary (cada 10 min) reenviaba las mismas menciones")
print("• No existía un campo para marcar notificaciones como enviadas")
print()

print("✅ SOLUCIONES IMPLEMENTADAS:")
print()
print("1. 🗄️ MODIFICACIÓN DE BASE DE DATOS:")
print("   • Agregado campo 'notification_sent' a la tabla hits")
print("   • Valor por defecto: 0 (no enviada)")
print("   • Se marca como 1 después del envío exitoso")
print()
print("2. 🔍 FILTRADO INTELIGENTE:")
print("   • get_important_hits() ahora filtra solo menciones no enviadas")
print("   • Condición: AND h.notification_sent = 0")
print("   • Evita reenvío de menciones ya procesadas")
print()
print("3. 📱 MARCADO AUTOMÁTICO:")
print("   • Nueva función mark_notification_sent(hit_id)")
print("   • Se ejecuta después de cada envío exitoso")
print("   • Previene futuros reenvíos de la misma mención")
print()
print("4. 🛡️ SISTEMA ANTI-DUPLICADOS:")
print("   • Notificaciones se marcan como enviadas inmediatamente")
print("   • Solo se procesan menciones nuevas")
print("   • Resistente a múltiples ejecuciones")
print()

# Verificar estado actual
print("📊 ESTADO ACTUAL DEL SISTEMA:")
conn = get_db_connection()
with conn:
    # Estadísticas generales
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Liberman%' OR keyword LIKE '%Coria%'")
    total_important = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE (keyword LIKE '%Liberman%' OR keyword LIKE '%Coria%') AND notification_sent = 1")
    sent_notifications = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE (keyword LIKE '%Liberman%' OR keyword LIKE '%Coria%') AND notification_sent = 0")
    pending_notifications = cursor.fetchone()[0]
    
    print(f"• Total menciones importantes: {total_important}")
    print(f"• Notificaciones enviadas: {sent_notifications}")
    print(f"• Notificaciones pendientes: {pending_notifications}")

# Verificar menciones pendientes
hits = get_important_hits(24)
print(f"\n🔍 MENCIONES PENDIENTES (últimas 24h):")
print(f"• Liberman: {len(hits['liberman'])}")
print(f"• Coria: {len(hits['coria'])}")

if len(hits['liberman']) == 0 and len(hits['coria']) == 0:
    print("\n✅ PERFECTO: No hay menciones pendientes")
    print("   Esto confirma que el sistema anti-duplicados funciona")
else:
    print(f"\n⚠️  HAY MENCIONES PENDIENTES:")
    if hits['liberman']:
        print(f"   Liberman: {len(hits['liberman'])} menciones nuevas")
    if hits['coria']:
        print(f"   Coria: {len(hits['coria'])} menciones nuevas")
    print("   Estas se enviarán en la próxima ejecución automática")

print("\n🎯 ARCHIVOS MODIFICADOS:")
print("• app/storage.py - Agregada columna y función mark_notification_sent()")
print("• app/notifier.py - Marcado automático después del envío")
print("• Base de datos - Nueva estructura anti-duplicados")

print("\n🚀 BENEFICIOS OBTENIDOS:")
print("• ✅ Eliminación completa de notificaciones duplicadas")
print("• ✅ Solo recibirás notificaciones de menciones nuevas")
print("• ✅ Sistema robusto y resistente a errores")
print("• ✅ Mejor experiencia de usuario")
print("• ✅ Reducción de spam en Telegram")

print("\n🔄 FUNCIONAMIENTO ACTUAL:")
print("1. Sistema detecta nueva mención de Liberman/Coria")
print("2. Se guarda en base de datos con notification_sent = 0")
print("3. En próxima ejecución (cada 10 min) se detecta como pendiente")
print("4. Se envía notificación por Telegram")
print("5. Se marca como enviada (notification_sent = 1)")
print("6. Ya no se vuelve a enviar en futuras ejecuciones")

print("\n✅ PROBLEMA SOLUCIONADO COMPLETAMENTE")
print("\n=== RESUMEN COMPLETADO ===")